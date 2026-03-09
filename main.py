"""
Orchestratore principale.
Esegue: collectors → tagger → scorer → alerts
"""

import logging
import sys
import time
from datetime import datetime

from config.settings import DATABASE_URL
from db.models import get_engine, get_session

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", mode="a"),
    ]
)
logger = logging.getLogger("main")


def run_pipeline(collectors_only: bool = False, skip_alerts: bool = False):
    """
    Pipeline completa:
    1. Esegui tutti i collectors attivi
    2. Tagga documenti nuovi
    3. Calcola score
    4. Invia alert
    """
    start = time.time()
    logger.info("=" * 70)
    logger.info(f"PIPELINE START: {datetime.utcnow().isoformat()}")
    logger.info("=" * 70)

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    stats = {
        "collectors": {},
        "tagged": 0,
        "scored": 0,
        "alerts": 0,
        "errors": [],
    }

    # ── STEP 1: COLLECTORS ────────────────────────────────
    logger.info("\n── STEP 1: COLLECTORS ──")

    collectors_config = [
        ("PubMed", "collectors.pubmed_collector", "PubMedCollector"),
        ("ClinicalTrials.gov", "collectors.clinicaltrials_collector", "ClinicalTrialsCollector"),
        ("Bundestag DIP", "collectors.bundestag_collector", "BundestagCollector"),
        ("G-BA Decisions", "collectors.gba_collector", "GBACollector"),
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
        ("NHS Digital", "collectors.news_collector", "NewsCollector"),
        ("Rock Health", "collectors.news_collector", "NewsCollector"),
        ("MedTech Intelligence", "collectors.news_collector", "NewsCollector"),
        ("Endpoints News", "collectors.news_collector", "NewsCollector"),
        # Google Trends
        ("Google Trends", "collectors.trends_collector", "TrendsCollector"),
    ]

    for source_name, module_path, class_name in collectors_config:
        try:
            module = __import__(module_path, fromlist=[class_name])
            CollectorClass = getattr(module, class_name)

            # RSSCollector e NewsCollector richiedono source_name come primo argomento
            if class_name in ("RSSCollector", "NewsCollector"):
                collector = CollectorClass(source_name, session)
            else:
                collector = CollectorClass(session)

            result = collector.run()
            stats["collectors"][source_name] = result

        except Exception as e:
            logger.error(f"✗ Collector '{source_name}' fallito: {e}")
            stats["errors"].append(f"Collector {source_name}: {e}")

    if collectors_only:
        _print_summary(stats, time.time() - start)
        session.close()
        return stats

    # ── STEP 2: TAGGING ───────────────────────────────────
    logger.info("\n── STEP 2: TAGGING ──")
    try:
        from processors.tagger import tag_documents
        stats["tagged"] = tag_documents(session)
    except Exception as e:
        logger.error(f"✗ Tagging fallito: {e}")
        stats["errors"].append(f"Tagger: {e}")

    # ── STEP 3: SCORING ───────────────────────────────────
    logger.info("\n── STEP 3: SCORING ──")
    try:
        from processors.scorer import score_signals
        stats["scored"] = score_signals(session)
    except Exception as e:
        logger.error(f"✗ Scoring fallito: {e}")
        stats["errors"].append(f"Scorer: {e}")

    # ── STEP 4: ALERTS ────────────────────────────────────
    if not skip_alerts:
        logger.info("\n── STEP 4: ALERTS ──")
        try:
            from alerts.alert_engine import check_and_send_alerts
            stats["alerts"] = check_and_send_alerts(session)
        except Exception as e:
            logger.error(f"✗ Alerts fallito: {e}")
            stats["errors"].append(f"Alerts: {e}")

    _print_summary(stats, time.time() - start)
    session.close()
    return stats


def _print_summary(stats: dict, elapsed: float):
    """Stampa riepilogo pipeline."""
    logger.info("\n" + "=" * 70)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 70)

    total_new = sum(
        s.get("new", 0) for s in stats["collectors"].values()
    )
    logger.info(f"  Collectors eseguiti: {len(stats['collectors'])}")
    logger.info(f"  Nuovi documenti:     {total_new}")
    logger.info(f"  Segnali taggati:     {stats['tagged']}")
    logger.info(f"  Segnali scored:      {stats['scored']}")
    logger.info(f"  Alert inviati:       {stats['alerts']}")
    logger.info(f"  Errori:              {len(stats['errors'])}")
    logger.info(f"  Tempo totale:        {elapsed:.1f}s")

    if stats["errors"]:
        logger.warning("\n  ERRORI:")
        for err in stats["errors"]:
            logger.warning(f"    - {err}")

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
    args = parser.parse_args()

    if args.init_db:
        from db.init_db import main as init_main
        init_main()
    else:
        run_pipeline(
            collectors_only=args.collectors_only,
            skip_alerts=args.skip_alerts,
        )
