"""
Orchestratore principale (v2.0)
Esegue: collectors → tagger → scorer → alerts
Con: tracking run nel DB, logging con rotazione, error isolation
"""

import importlib
import logging
import logging.handlers
import os
import sys
import time
import traceback
from datetime import datetime, timezone

from config.settings import DATABASE_URL
from db.models import get_engine, get_session

# ── LOGGING SETUP CON ROTAZIONE ──
os.makedirs("logs", exist_ok=True)

# Formatter condiviso
log_format = logging.Formatter(
    "%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
console_handler.setLevel(logging.INFO)

# File handler con rotazione giornaliera (mantiene 30 giorni)
file_handler = logging.handlers.TimedRotatingFileHandler(
    "logs/pipeline.log", when="midnight", backupCount=30, encoding="utf-8"
)
file_handler.setFormatter(log_format)
file_handler.setLevel(logging.INFO)

# Error-only file handler (solo errori, rotazione settimanale)
error_handler = logging.handlers.TimedRotatingFileHandler(
    "logs/errors.log", when="W0", backupCount=12, encoding="utf-8"
)
error_handler.setFormatter(log_format)
error_handler.setLevel(logging.ERROR)

# Root logger
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler, error_handler])
logger = logging.getLogger("main")


def save_collector_run(session, name, started, finished, status, error_msg, items):
    """Salva il risultato di un collector run nel database."""
    from sqlalchemy import text
    try:
        session.execute(text("""
            INSERT INTO collector_runs (collector_name, started_at, finished_at, status, error_message, items_fetched)
            VALUES (:name, :started, :finished, :status, :error, :items)
        """), {
            "name": name,
            "started": started,
            "finished": finished,
            "status": status,
            "error": error_msg[:500] if error_msg else None,
            "items": items or 0,
        })
        session.commit()
    except Exception as e:
        logger.warning(f"Could not save collector run for '{name}': {e}")
        session.rollback()


def ensure_collector_runs_table(session):
    """Crea la tabella collector_runs se non esiste."""
    from sqlalchemy import text
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS collector_runs (
                id SERIAL PRIMARY KEY,
                collector_name VARCHAR(100) NOT NULL,
                started_at TIMESTAMP NOT NULL,
                finished_at TIMESTAMP NOT NULL,
                status VARCHAR(20) NOT NULL,
                error_message TEXT,
                items_fetched INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_collector_runs_name ON collector_runs(collector_name)
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_collector_runs_date ON collector_runs(started_at)
        """))
        session.commit()
    except Exception as e:
        logger.warning(f"Could not create collector_runs table: {e}")
        session.rollback()


def run_pipeline(collectors_only: bool = False, skip_alerts: bool = False):
    """
    Pipeline completa:
    1. Esegui tutti i collectors attivi
    2. Tagga documenti nuovi
    3. Calcola score
    4. Invia alert
    """
    start = time.time()
    now = datetime.now(timezone.utc)
    logger.info("=" * 70)
    logger.info(f"PIPELINE START: {now.isoformat()}")
    logger.info("=" * 70)

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    # Ensure tracking table exists
    ensure_collector_runs_table(session)

    stats = {
        "collectors": {},
        "tagged": 0,
        "scored": 0,
        "alerts": 0,
        "errors": [],
        "success_count": 0,
        "fail_count": 0,
    }

    # ── STEP 1: COLLECTORS ────────────────────────────────
    logger.info("\n── STEP 1: COLLECTORS ──")

    collectors_config = [
        ("PubMed", "collectors.pubmed_collector", "PubMedCollector"),
        ("ClinicalTrials.gov", "collectors.clinicaltrials_collector", "ClinicalTrialsCollector"),
        ("Bundestag DIP", "collectors.bundestag_collector", "BundestagCollector"),
        ("G-BA Decisions", "collectors.gba_collector", "GBACollector"),
        ("BfArM DiGA Directory", "collectors.diga_collector", "DIGACollector"),
        ("FDA Digital Health CoE", "collectors.rss_collector", "RSSCollector"),
        ("WHO Digital Health", "collectors.rss_collector", "RSSCollector"),
        ("BMG Germany", "collectors.rss_collector", "RSSCollector"),
        ("IQWiG", "collectors.rss_collector", "RSSCollector"),
        # News & Competitive Intelligence
        ("MobiHealthNews", "collectors.news_collector", "NewsCollector"),
        ("Healthcare IT News", "collectors.news_collector", "NewsCollector"),
        ("Fierce Healthcare", "collectors.news_collector", "NewsCollector"),
        ("STAT News", "collectors.news_collector", "NewsCollector"),
        ("Digital Health UK", "collectors.news_collector", "NewsCollector"),
        ("Digital Health London", "collectors.news_collector", "NewsCollector"),
        ("NHS Digital", "collectors.news_collector", "NewsCollector"),
        ("Rock Health", "collectors.news_collector", "NewsCollector"),
        ("MedTech Intelligence", "collectors.news_collector", "NewsCollector"),
        ("Endpoints News", "collectors.news_collector", "NewsCollector"),
        ("Digital Health Global", "collectors.news_collector", "NewsCollector"),
        # Google Trends
        ("Google Trends", "collectors.trends_collector", "TrendsCollector"),
    ]

    for source_name, module_path, class_name in collectors_config:
        col_start = datetime.now(timezone.utc)
        try:
            module = importlib.import_module(module_path)
            CollectorClass = getattr(module, class_name)

            if class_name in ("RSSCollector", "NewsCollector"):
                collector = CollectorClass(source_name, session)
            else:
                collector = CollectorClass(session)

            result = collector.run()
            stats["collectors"][source_name] = result
            stats["success_count"] += 1

            items = result.get("new", 0) if isinstance(result, dict) else 0
            logger.info(f"  ✓ {source_name}: {items} new items")

            save_collector_run(
                session, source_name, col_start, datetime.now(timezone.utc),
                "success", None, items
            )

        except Exception as e:
            stats["fail_count"] += 1
            error_msg = f"{type(e).__name__}: {str(e)}"
            tb = traceback.format_exc()

            logger.error(f"  ✗ {source_name} FAILED: {error_msg}")
            logger.debug(f"  Traceback:\n{tb}")
            stats["errors"].append(f"{source_name}: {error_msg}")

            save_collector_run(
                session, source_name, col_start, datetime.now(timezone.utc),
                "failed", f"{error_msg}\n{tb}", 0
            )

    if collectors_only:
        _print_summary(stats, time.time() - start)
        session.close()
        return stats

    # ── STEP 2: TAGGING ───────────────────────────────────
    logger.info("\n── STEP 2: TAGGING ──")
    try:
        from processors.tagger import tag_documents
        stats["tagged"] = tag_documents(session)
        logger.info(f"  ✓ Tagged {stats['tagged']} documents")
    except Exception as e:
        logger.error(f"  ✗ Tagging FAILED: {e}")
        stats["errors"].append(f"Tagger: {e}")

    # ── STEP 3: SCORING ───────────────────────────────────
    logger.info("\n── STEP 3: SCORING ──")
    try:
        from processors.scorer import score_signals
        stats["scored"] = score_signals(session)
        logger.info(f"  ✓ Scored {stats['scored']} signals")
    except Exception as e:
        logger.error(f"  ✗ Scoring FAILED: {e}")
        stats["errors"].append(f"Scorer: {e}")

    # ── STEP 4: ALERTS ────────────────────────────────────
    if not skip_alerts:
        logger.info("\n── STEP 4: ALERTS ──")
        try:
            from alerts.alert_engine import check_and_send_alerts
            stats["alerts"] = check_and_send_alerts(session)
            logger.info(f"  ✓ Sent {stats['alerts']} alerts")
        except Exception as e:
            logger.error(f"  ✗ Alerts FAILED: {e}")
            stats["errors"].append(f"Alerts: {e}")

    _print_summary(stats, time.time() - start)
    session.close()
    return stats


def _print_summary(stats: dict, elapsed: float):
    """Stampa riepilogo pipeline."""
    total_collectors = stats["success_count"] + stats["fail_count"]
    total_new = sum(
        s.get("new", 0) for s in stats["collectors"].values() if isinstance(s, dict)
    )

    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 70)
    logger.info(f"  Collectors:    {stats['success_count']}/{total_collectors} OK")
    if stats["fail_count"] > 0:
        logger.warning(f"  Failed:        {stats['fail_count']}/{total_collectors} ⚠️")
    logger.info(f"  New documents: {total_new}")
    logger.info(f"  Tagged:        {stats['tagged']}")
    logger.info(f"  Scored:        {stats['scored']}")
    logger.info(f"  Alerts sent:   {stats['alerts']}")
    logger.info(f"  Total errors:  {len(stats['errors'])}")
    logger.info(f"  Duration:      {elapsed:.1f}s")

    if stats["errors"]:
        logger.warning("\n  ERRORS:")
        for err in stats["errors"]:
            logger.warning(f"    ✗ {err}")

    # Status finale
    if stats["fail_count"] == 0:
        logger.info("\n  STATUS: ✅ ALL OK")
    elif stats["success_count"] > 0:
        logger.warning(f"\n  STATUS: ⚠️ PARTIAL ({stats['success_count']} ok, {stats['fail_count']} failed)")
    else:
        logger.error("\n  STATUS: ❌ ALL FAILED")

    logger.info("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Geopolitical Health Intel Pipeline")
    parser.add_argument("--collectors-only", action="store_true",
                        help="Esegui solo i collectors, senza tagging/scoring/alerts")
    parser.add_argument("--skip-alerts", action="store_true",
                        help="Salta l'invio degli alert email")
    parser.add_argument("--init-db", action="store_true",
                        help="Inizializza database e seed dati")
    parser.add_argument("--run-agent", action="store_true",
                        help="Esegui l'agente AI (HealthAnalystAgent) sui documenti recenti")
    args = parser.parse_args()

    if args.init_db:
        from db.init_db import main as init_main
        init_main()
    elif args.run_agent:
        from agents.analyst_agent import HealthAnalystAgent
        engine = get_engine(DATABASE_URL)
        session = get_session(engine)
        try:
            HealthAnalystAgent(session).generate_report()
        finally:
            session.close()
    else:
        run_pipeline(
            collectors_only=args.collectors_only,
            skip_alerts=args.skip_alerts,
        )
