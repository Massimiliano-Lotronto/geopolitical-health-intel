"""
Collector per il Bundestag via DIP API.
Monitora documenti parlamentari rilevanti per sanità e digital health.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict

from collectors.base import BaseCollector
from db.models import BundestagItem, Document

# Descriptor (keyword tematiche) nel sistema DIP del Bundestag
BUNDESTAG_DESCRIPTORS = [
    "Gesundheit",
    "Gesundheitswesen",
    "Digitalisierung",
    "Krankenversicherung",
    "Arzneimittel",
    "Medizinprodukt",
    "Künstliche Intelligenz",
    "Telemedizin",
    "Pflege",
    "Pflegeversicherung",
    "Gesundheitsdaten",
    "Datenschutz",
]

# Tipi di Drucksache rilevanti
RELEVANT_DRUCKSACHE_TYPES = [
    "Gesetzentwurf",
    "Antrag",
    "Kleine Anfrage",
    "Große Anfrage",
    "Beschlussempfehlung",
    "Unterrichtung",
    "Bericht",
    "Entschließungsantrag",
]

# API endpoint DIP
DIP_API_BASE = "https://search.dip.bundestag.de/api/v1"
# API key pubblica (default)
DIP_DEFAULT_KEY = "GmEPb1B.bfqJLIhcGAsH9fTJevTglhFpCoZyAAAdhp"


class BundestagCollector(BaseCollector):
    """Collector per Bundestag DIP API."""

    def __init__(self, db_session, api_key: str = ""):
        super().__init__("Bundestag DIP", db_session)
        self.api_key = api_key or DIP_DEFAULT_KEY

    def fetch(self) -> List[Dict]:
        """Cerca documenti parlamentari rilevanti."""
        all_docs = []

        # Data minima
        if self.source.last_scraped_at:
            date_start = self.source.last_scraped_at.strftime("%Y-%m-%d")
        else:
            date_start = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

        for descriptor in BUNDESTAG_DESCRIPTORS:
            try:
                params = {
                    "apikey": self.api_key,
                    "f.datum.start": date_start,
                    "f.deskriptor": descriptor,
                    "format": "json",
                    "cursor": "*",
                }

                resp = self.http_get(
                    f"{DIP_API_BASE}/drucksache",
                    params=params,
                    timeout=30,
                )
                data = resp.json()
                documents = data.get("documents", [])
                all_docs.extend(documents)

                self.logger.info(
                    f"  Descriptor '{descriptor}': {len(documents)} documenti"
                )
                self.rate_limit(0.5)

            except Exception as e:
                self.logger.warning(f"  Descriptor '{descriptor}' fallito: {e}")

        return all_docs

    def parse(self, raw_docs: List[Dict]) -> List[Dict]:
        """Converte documenti DIP in formato normalizzato."""
        parsed = []
        seen_ids = set()

        for doc in raw_docs:
            try:
                dip_id = doc.get("id")
                if not dip_id or dip_id in seen_ids:
                    continue
                seen_ids.add(dip_id)

                drucksache_type = doc.get("drucksachetyp", "")
                if drucksache_type not in RELEVANT_DRUCKSACHE_TYPES:
                    continue

                # Data
                pub_date = None
                datum = doc.get("datum")
                if datum:
                    try:
                        pub_date = datetime.strptime(datum, "%Y-%m-%d").date()
                    except ValueError:
                        pass

                # Autore / Urheber
                urheber_list = doc.get("urheber", [])
                urheber = ", ".join(
                    u.get("titel", "") for u in urheber_list
                ) if isinstance(urheber_list, list) else str(urheber_list)

                # Numero documento
                doc_nummer = doc.get("dokumentnummer", "")

                # Titolo
                title = doc.get("titel", "Ohne Titel")

                # Testo completo (se disponibile)
                full_text = doc.get("text", "")

                # Wahlperiode
                wahlperiode = doc.get("wahlperiode", 0)

                # Istituzione
                institution = doc.get("herausgeber", "BT")

                parsed.append({
                    "external_id": f"BT-{doc_nummer}",
                    "title": title,
                    "url": f"https://dip.bundestag.de/drucksache/{doc_nummer}",
                    "publish_date": pub_date,
                    "language": "de",
                    "full_text": full_text[:5000] if full_text else "",
                    "country": "Germany",
                    "document_type": f"Drucksache ({drucksache_type})",
                    "extra_data": {
                        "dip_id": dip_id,
                        "drucksache_type": drucksache_type,
                        "wahlperiode": wahlperiode,
                        "institution": institution,
                        "urheber": urheber,
                        "doc_nummer": doc_nummer,
                    }
                })

            except Exception as e:
                self.logger.warning(f"  Errore parsing doc BT: {e}")

        return parsed

    def _store_extra(self, doc: Document, doc_data: Dict):
        """Salva dati extra nella tabella bundestag_items."""
        extra = doc_data.get("extra_data", {})
        if not extra.get("dip_id"):
            return

        bt_item = BundestagItem(
            document_id=doc.document_id,
            dip_id=extra.get("dip_id"),
            drucksache_type=extra.get("drucksache_type"),
            wahlperiode=extra.get("wahlperiode"),
            institution=extra.get("institution"),
            urheber=extra.get("urheber"),
            health_relevance=self._calc_health_relevance(doc_data),
        )
        self.session.add(bt_item)

        # Aggiorna flags
        if doc.flags:
            doc.flags.is_parliamentary = True
            # Check se riguarda rimborso/digital health
            title_lower = doc_data["title"].lower()
            text_lower = (doc_data.get("full_text") or "").lower()
            combined = title_lower + " " + text_lower

            diga_keywords = ["diga", "digitale gesundheit", "telemedizin", "epa",
                             "gematik", "gesundheitsdaten", "e-health"]
            reimb_keywords = ["erstattung", "nutzenbewertung", "amnog",
                              "krankenversicherung", "sgb v", "leistung"]

            if any(kw in combined for kw in diga_keywords):
                doc.flags.is_diga = True
            if any(kw in combined for kw in reimb_keywords):
                doc.flags.is_reimbursement = True

    def _calc_health_relevance(self, doc_data: Dict) -> float:
        """Calcola score di rilevanza sanitaria (0-10)."""
        score = 0.0
        title_lower = doc_data["title"].lower()
        text_lower = (doc_data.get("full_text") or "").lower()
        combined = title_lower + " " + text_lower

        # Keyword sanitarie con pesi
        health_kw = {
            "gesundheit": 2.0, "krankenversicherung": 2.0,
            "arzneimittel": 1.5, "medizinprodukt": 2.0,
            "digitale gesundheit": 3.0, "telemedizin": 2.5,
            "diga": 3.0, "pflege": 1.5, "krankenhaus": 1.5,
            "künstliche intelligenz": 2.0, "ki im gesundheit": 3.0,
            "gesundheitsdaten": 2.5, "patientenakte": 2.0,
        }

        for kw, weight in health_kw.items():
            if kw in combined:
                score += weight

        # Bonus per tipo documento ad alto impatto
        drucksache_type = doc_data.get("extra_data", {}).get("drucksache_type", "")
        type_bonus = {
            "Gesetzentwurf": 2.0,
            "Beschlussempfehlung": 2.0,
            "Große Anfrage": 1.0,
            "Antrag": 0.5,
        }
        score += type_bonus.get(drucksache_type, 0)

        return min(score, 10.0)
