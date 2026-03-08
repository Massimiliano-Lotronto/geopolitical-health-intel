"""
Classe base per tutti i collector.
Pattern: fetch → parse → deduplicate → store → tag
"""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

import requests
from sqlalchemy.orm import Session

from config.settings import DEFAULT_HEADERS, REQUEST_TIMEOUT
from db.models import Source, Document, DocumentFlag


class BaseCollector(ABC):
    """
    Classe base astratta per i collector di dati.
    Ogni collector concreto deve implementare fetch() e parse().
    """

    def __init__(self, source_name: str, db_session: Session):
        self.source = (
            db_session.query(Source)
            .filter_by(source_name=source_name)
            .first()
        )
        if not self.source:
            raise ValueError(f"Fonte '{source_name}' non trovata nel DB. Esegui seed prima.")

        self.session = db_session
        self.logger = logging.getLogger(f"collector.{source_name}")
        self.logger.setLevel(logging.INFO)
        self.stats = {"fetched": 0, "parsed": 0, "new": 0, "errors": 0}

    def run(self) -> Dict:
        """Pipeline principale: fetch → parse → dedup → store → update timestamp."""
        self.logger.info(f"▶ Avvio collector: {self.source.source_name}")
        start = time.time()

        try:
            # 1. Fetch raw data
            raw_items = self.fetch()
            self.stats["fetched"] = len(raw_items) if raw_items else 0
            self.logger.info(f"  Fetched: {self.stats['fetched']} items")

            if not raw_items:
                self.logger.info("  Nessun dato nuovo. Skip.")
                return self.stats

            # 2. Parse into normalized dicts
            parsed = self.parse(raw_items)
            self.stats["parsed"] = len(parsed)

            # 3. Deduplicate
            new_docs = self._deduplicate(parsed)
            self.stats["new"] = len(new_docs)
            self.logger.info(f"  Nuovi documenti: {self.stats['new']}")

            # 4. Store
            if new_docs:
                self._store(new_docs)

            # 5. Update last_scraped_at
            self.source.last_scraped_at = datetime.utcnow()
            self.session.commit()

        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"  ✗ Errore: {e}", exc_info=True)
            self.session.rollback()

        elapsed = time.time() - start
        self.logger.info(
            f"✓ Completato in {elapsed:.1f}s | "
            f"Fetched={self.stats['fetched']} Parsed={self.stats['parsed']} "
            f"New={self.stats['new']} Errors={self.stats['errors']}"
        )
        return self.stats

    @abstractmethod
    def fetch(self) -> List:
        """Scarica dati raw dalla fonte. Restituisce lista di oggetti raw."""
        pass

    @abstractmethod
    def parse(self, raw_items: List) -> List[Dict]:
        """
        Converte raw items in dizionari normalizzati.
        Ogni dict deve contenere almeno:
        - title: str
        - url: str (nullable)
        - publish_date: date (nullable)
        - external_id: str (nullable)
        - language: str
        - full_text: str (nullable)
        - country: str (nullable)
        - document_type: str
        - extra_data: dict (per tabelle figlie come bundestag_items)
        """
        pass

    def _compute_hash(self, doc: Dict) -> str:
        """Calcola SHA256 del contenuto per deduplicazione."""
        content = f"{doc.get('title', '')}{doc.get('external_id', '')}{doc.get('url', '')}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _deduplicate(self, parsed: List[Dict]) -> List[Dict]:
        """Filtra documenti già presenti nel DB tramite content_hash."""
        new_docs = []
        for doc in parsed:
            doc["content_hash"] = self._compute_hash(doc)
            existing = (
                self.session.query(Document)
                .filter_by(content_hash=doc["content_hash"])
                .first()
            )
            if not existing:
                new_docs.append(doc)
        return new_docs

    def _store(self, docs: List[Dict]):
        """Salva documenti nel DB con flags iniziali."""
        for doc_data in docs:
            doc = Document(
                source_id=self.source.source_id,
                external_id=doc_data.get("external_id"),
                title=doc_data["title"],
                url=doc_data.get("url"),
                publish_date=doc_data.get("publish_date"),
                scraped_at=datetime.utcnow(),
                language=doc_data.get("language", "en"),
                full_text=doc_data.get("full_text"),
                country=doc_data.get("country", self.source.country),
                document_type=doc_data.get("document_type"),
                content_hash=doc_data["content_hash"],
            )
            self.session.add(doc)
            self.session.flush()  # Per ottenere document_id

            # Crea flags iniziali
            flags = DocumentFlag(document_id=doc.document_id)
            self.session.add(flags)

            # Hook per tabelle figlie (bundestag_items, gba_decisions, etc.)
            self._store_extra(doc, doc_data)

        self.session.commit()

    def _store_extra(self, doc: Document, doc_data: Dict):
        """Override nelle sottoclassi per salvare dati in tabelle figlie."""
        pass

    # ── Utility methods ──────────────────────────────────
    def http_get(self, url: str, params: Dict = None, headers: Dict = None,
                 timeout: int = None) -> requests.Response:
        """GET con retry, timeout e headers standard."""
        _headers = {**DEFAULT_HEADERS, **(headers or {})}
        _timeout = timeout or REQUEST_TIMEOUT

        for attempt in range(3):
            try:
                resp = requests.get(url, params=params, headers=_headers, timeout=_timeout)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"  Tentativo {attempt + 1}/3 fallito: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def rate_limit(self, seconds: float = 1.0):
        """Pausa per rispettare rate limit."""
        time.sleep(seconds)
