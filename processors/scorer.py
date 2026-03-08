"""
Engine di scoring per i segnali.
Calcola: Relevance, Novelty, Impact, Strategic Score.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from config.settings import STRATEGIC_WEIGHTS
from db.models import Signal, Document, Source, Keyword, DocumentFlag

logger = logging.getLogger("processor.scorer")

# Pesi per tipo documento (Impact score)
DOC_TYPE_IMPACT = {
    "Gesetzentwurf": 10.0,
    "Beschlussempfehlung": 9.5,
    "Richtlinie": 9.0,
    "guidance": 8.5,
    "final_rule": 9.0,
    "regulation": 9.0,
    "G-BA Beschluss": 9.0,
    "G-BA Nutzenbewertung": 8.5,
    "law": 9.5,
    "clinical_trial": 7.0,
    "journal_article": 5.0,
    "policy_update": 6.0,
    "news": 3.0,
    "hta_report": 7.5,
    "Drucksache (Antrag)": 6.0,
    "Drucksache (Kleine Anfrage)": 5.5,
    "Drucksache (Große Anfrage)": 7.0,
    "Drucksache (Unterrichtung)": 5.0,
}

# Paesi prioritari per Relevance score
PRIORITY_COUNTRIES = {
    "Germany": 1.0, "USA": 1.0, "EU": 1.0,
    "China": 0.9, "Israel": 0.9,
    "UK": 0.8, "France": 0.8, "Italy": 0.8,
    "Japan": 0.7, "South Korea": 0.7, "Singapore": 0.7, "India": 0.7,
}


def score_signals(session: Session, limit: int = 1000):
    """
    Calcola i 4 score per tutti i segnali non ancora scored.
    """
    # Segnali con strategic_score = 0 (non scored)
    unscored = (
        session.query(Signal)
        .filter(Signal.strategic_score == 0)
        .limit(limit)
        .all()
    )

    if not unscored:
        logger.info("Nessun segnale da scored.")
        return 0

    logger.info(f"Scoring {len(unscored)} segnali...")

    for signal in unscored:
        doc = session.query(Document).get(signal.document_id)
        kw = session.query(Keyword).get(signal.keyword_id)
        source = session.query(Source).get(doc.source_id) if doc else None

        if not doc or not kw or not source:
            continue

        # 1. Relevance Score
        signal.relevance_score = _calc_relevance(signal, doc, kw, source)

        # 2. Novelty Score
        signal.novelty_score = _calc_novelty(session, doc, kw)

        # 3. Impact Score
        signal.impact_score = _calc_impact(doc, source)

        # 4. Strategic Score (composito)
        signal.strategic_score = _calc_strategic(signal, doc)

        # 5. Urgency
        signal.urgency = _classify_urgency(signal, doc)

    session.commit()
    logger.info(f"✓ Scored {len(unscored)} segnali")
    return len(unscored)


def _calc_relevance(signal: Signal, doc: Document, kw: Keyword, source: Source) -> float:
    """
    Relevance Score (0-10):
    40% keyword match quality + 25% trust fonte + 20% focus area + 15% geography
    """
    # Keyword match (già calcolato nel tagger, qui nel signal.relevance_score iniziale)
    kw_score = signal.relevance_score * 0.4

    # Trust fonte (normalizzato 1-5 → 0-10)
    trust_score = (source.trust_level / 5.0) * 10.0 * 0.25

    # Focus area (livello keyword come proxy)
    focus_scores = {1: 6.0, 2: 8.0, 3: 9.0, 4: 7.0, 5: 9.5}
    focus_score = focus_scores.get(kw.level, 5.0) * 0.20

    # Geography match
    geo_score = PRIORITY_COUNTRIES.get(doc.country, 0.3) * 10.0 * 0.15

    return min(kw_score + trust_score + focus_score + geo_score, 10.0)


def _calc_novelty(session: Session, doc: Document, kw: Keyword) -> float:
    """
    Novelty Score (0-10):
    30% keyword rara + 30% crescita anomala + 25% primo documento + 15% nuova fonte
    """
    score = 0.0
    now = datetime.utcnow()

    # Keyword rara (poche occorrenze storiche)
    kw_count = (
        session.query(func.count(Signal.signal_id))
        .filter(Signal.keyword_id == kw.keyword_id)
        .scalar()
    )
    if kw_count <= 3:
        score += 3.0  # 30% × 10
    elif kw_count <= 10:
        score += 2.0
    elif kw_count <= 30:
        score += 1.0

    # Primo documento simile (nessun documento con stessa keyword nei 30gg precedenti)
    recent_similar = (
        session.query(func.count(Signal.signal_id))
        .join(Document)
        .filter(
            Signal.keyword_id == kw.keyword_id,
            Document.publish_date >= (now - timedelta(days=30)).date(),
            Document.document_id != doc.document_id,
        )
        .scalar()
    )
    if recent_similar == 0:
        score += 2.5  # 25% × 10

    # Nuova fonte per quel topic
    source_topic_count = (
        session.query(func.count(Signal.signal_id))
        .join(Document)
        .filter(
            Signal.keyword_id == kw.keyword_id,
            Document.source_id == doc.source_id,
            Document.document_id != doc.document_id,
        )
        .scalar()
    )
    if source_topic_count == 0:
        score += 1.5  # 15% × 10

    return min(score, 10.0)


def _calc_impact(doc: Document, source: Source) -> float:
    """
    Impact Score (0-10):
    40% tipo documento + 25% copertura geografica + 20% fase trial + 15% autorità fonte
    """
    # Tipo documento
    doc_type = doc.document_type or ""
    type_score = 0.0
    for pattern, impact in DOC_TYPE_IMPACT.items():
        if pattern.lower() in doc_type.lower():
            type_score = impact
            break
    if type_score == 0:
        type_score = 4.0  # Default

    type_component = type_score * 0.40

    # Autorità fonte
    authority_component = (source.trust_level / 5.0) * 10.0 * 0.15

    # Copertura geografica (semplificata)
    geo_component = 5.0 * 0.25  # Default single-country
    if doc.country in ("EU", "International", "Global"):
        geo_component = 9.0 * 0.25

    # Fase trial (solo per clinical_trial)
    trial_component = 5.0 * 0.20  # Default
    if "trial" in doc_type.lower() and doc.full_text:
        text_lower = doc.full_text.lower()
        if "phase 3" in text_lower or "phase iii" in text_lower:
            trial_component = 9.0 * 0.20
        elif "phase 2" in text_lower or "phase ii" in text_lower:
            trial_component = 7.0 * 0.20

    return min(type_component + authority_component + geo_component + trial_component, 10.0)


def _calc_strategic(signal: Signal, doc: Document) -> float:
    """
    Strategic Score (composito):
    0.35 regulatory + 0.25 scientific + 0.20 market + 0.20 country_need
    """
    # Usa i flags per determinare i pesi
    flags = doc.flags
    if not flags:
        return (signal.relevance_score + signal.impact_score) / 2.0

    components = []

    if flags.is_regulatory or flags.is_parliamentary or flags.is_reimbursement:
        components.append(signal.impact_score * STRATEGIC_WEIGHTS["regulatory"])
    else:
        components.append(signal.relevance_score * 0.5 * STRATEGIC_WEIGHTS["regulatory"])

    if flags.is_scientific:
        components.append(signal.impact_score * STRATEGIC_WEIGHTS["scientific"])
    else:
        components.append(signal.relevance_score * 0.5 * STRATEGIC_WEIGHTS["scientific"])

    # Market trend (proxy: novelty)
    components.append(signal.novelty_score * STRATEGIC_WEIGHTS["market_trend"])

    # Country need (proxy: LMIC flag o priority country)
    if flags.is_lmic:
        components.append(8.0 * STRATEGIC_WEIGHTS["country_need"])
    else:
        geo_need = PRIORITY_COUNTRIES.get(doc.country, 3.0) * 10.0
        components.append(geo_need * STRATEGIC_WEIGHTS["country_need"])

    return min(sum(components), 10.0)


def _classify_urgency(signal: Signal, doc: Document) -> str:
    """Classifica urgenza del segnale."""
    if signal.strategic_score >= 8.0:
        return "immediate"
    elif signal.strategic_score >= 6.0:
        return "short_term"
    elif signal.strategic_score >= 4.0:
        return "medium_term"
    return "informational"
