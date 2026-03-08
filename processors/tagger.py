"""
Processore NLP per tagging e keyword matching.
Assegna keyword, geography, flags e crea segnali.
"""

import logging
from typing import List

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from db.models import Document, DocumentFlag, Signal, Keyword

logger = logging.getLogger("processor.tagger")

# Soglia fuzzy matching
FUZZY_THRESHOLD = 85

# Mappatura paesi per normalizzazione
COUNTRY_ALIASES = {
    "united states": "USA", "us": "USA", "u.s.": "USA", "america": "USA",
    "united kingdom": "UK", "uk": "UK", "england": "UK", "britain": "UK",
    "people's republic of china": "China", "prc": "China", "cn": "China",
    "federal republic of germany": "Germany", "deutschland": "Germany",
    "brd": "Germany", "de": "Germany",
    "republic of korea": "South Korea", "south korea": "South Korea",
    "republic of india": "India",
}

# Document type → flag mapping
DOC_TYPE_FLAGS = {
    "regulatory": ["guidance", "regulation", "directive", "act", "law",
                    "Richtlinie", "Verordnung", "Gesetz"],
    "scientific": ["journal_article", "clinical_trial", "review", "meta-analysis"],
    "parliamentary": ["Drucksache", "Plenarprotokoll"],
    "reimbursement": ["G-BA", "Nutzenbewertung", "AMNOG", "erstattung", "hta_report"],
}


def tag_documents(session: Session, limit: int = 500):
    """
    Processa documenti non ancora taggati.
    Applica keyword matching, geography extraction e flag assignment.
    """
    # Trova documenti senza segnali
    docs_without_signals = (
        session.query(Document)
        .outerjoin(Signal)
        .filter(Signal.signal_id.is_(None))
        .limit(limit)
        .all()
    )

    if not docs_without_signals:
        logger.info("Nessun documento da taggare.")
        return 0

    # Carica keyword attive
    keywords = session.query(Keyword).filter_by(active=True).all()
    logger.info(f"Tagging {len(docs_without_signals)} documenti con {len(keywords)} keyword")

    total_signals = 0

    for doc in docs_without_signals:
        # Testo da analizzare
        text = _get_searchable_text(doc)
        if not text:
            continue

        # 1. Keyword matching
        matched_keywords = _match_keywords(text, keywords)

        # 2. Crea segnali per ogni match
        for kw, score in matched_keywords:
            signal = Signal(
                document_id=doc.document_id,
                keyword_id=kw.keyword_id,
                relevance_score=score,
            )
            session.add(signal)
            total_signals += 1

        # 3. Aggiorna flags
        _update_flags(doc, matched_keywords)

        # 4. Normalizza paese
        if doc.country:
            normalized = COUNTRY_ALIASES.get(doc.country.lower(), doc.country)
            doc.country = normalized

    session.commit()
    logger.info(f"✓ Creati {total_signals} segnali per {len(docs_without_signals)} documenti")
    return total_signals


def _get_searchable_text(doc: Document) -> str:
    """Combina titolo e full_text per la ricerca."""
    parts = [doc.title or ""]
    if doc.full_text:
        parts.append(doc.full_text[:3000])  # Limita per performance
    return " ".join(parts).lower()


def _match_keywords(text: str, keywords: List[Keyword]) -> List[tuple]:
    """
    Cerca keyword nel testo con matching esatto e fuzzy.
    Restituisce lista di (keyword, score).
    """
    matches = []

    for kw in keywords:
        kw_lower = kw.keyword.lower()

        # Matching esatto (più veloce)
        if kw_lower in text:
            # Score basato su livello keyword e posizione
            base_score = 8.0
            if kw_lower in (text[:200]):  # Nel titolo/inizio
                base_score = 9.5
            matches.append((kw, base_score))
            continue

        # Fuzzy matching solo per keyword lunghe (> 3 parole)
        if len(kw_lower.split()) >= 3:
            # Controlla se una porzione del testo matcha
            words = text.split()
            kw_len = len(kw_lower.split())
            for i in range(0, min(len(words), 500) - kw_len + 1, kw_len):
                chunk = " ".join(words[i:i + kw_len])
                ratio = fuzz.ratio(kw_lower, chunk)
                if ratio >= FUZZY_THRESHOLD:
                    score = (ratio / 100) * 7.0
                    matches.append((kw, score))
                    break

    return matches


def _update_flags(doc: Document, matched_keywords: List[tuple]):
    """Aggiorna i flags del documento basandosi su keyword matchate e tipo."""
    if not doc.flags:
        doc.flags = DocumentFlag(document_id=doc.document_id)

    for kw, score in matched_keywords:
        # Flag basato su livello keyword
        if kw.level == 2:  # Regulatory
            doc.flags.is_regulatory = True
        elif kw.level == 3:  # Neurodegenerative
            doc.flags.is_neuro = True
        elif kw.level == 4:  # LMIC
            doc.flags.is_lmic = True
        elif kw.level == 5:  # Germany
            doc.flags.is_reimbursement = True

        # Flag specifici per cluster
        if kw.cluster in ("diga", "dipa"):
            doc.flags.is_diga = True

    # Flag basato su document_type
    doc_type = (doc.document_type or "").lower()
    source_type = ""
    if doc.source:
        source_type = doc.source.source_type or ""

    if source_type == "scientific" or doc_type in ("journal_article", "clinical_trial"):
        doc.flags.is_scientific = True
    if source_type in ("regulatory", "hta") or any(
        kw in doc_type for kw in DOC_TYPE_FLAGS["regulatory"]
    ):
        doc.flags.is_regulatory = True
    if source_type == "parliamentary" or any(
        kw in doc_type for kw in DOC_TYPE_FLAGS["parliamentary"]
    ):
        doc.flags.is_parliamentary = True
