"""
Collector per le decisioni del G-BA (Gemeinsamer Bundesausschuss).
Monitora decisioni su rimborsi, DiGA, nuove tecnologie sanitarie.
"""

from datetime import datetime
from typing import List, Dict

import feedparser
from bs4 import BeautifulSoup

from collectors.base import BaseCollector
from db.models import GBADecision, Document

# RSS Feed e pagine G-BA
GBA_RSS_URL = "https://www.g-ba.de/feeds/beschluesse/"
GBA_BESCHLUESSE_URL = "https://www.g-ba.de/beschluesse/"

# Keyword per filtrare decisioni rilevanti
DIGITAL_HEALTH_KEYWORDS = [
    "diga", "digitale gesundheitsanwendung", "digitale pflegeanwendung",
    "telemedizin", "videosprechstunde", "fernbehandlung",
    "künstliche intelligenz", "algorithmus", "software",
    "medizinprodukt", "e-health", "telematik", "gematik",
    "patientenakte", "gesundheitsdaten", "interoperabilität",
    "remote monitoring", "digital", "app",
]

NEURO_KEYWORDS = [
    "demenz", "alzheimer", "parkinson", "neurodegenerativ",
    "kognitiv", "neurologie", "gehirn", "eeg",
]


class GBACollector(BaseCollector):
    """Collector per G-BA decisioni via RSS."""

    def __init__(self, db_session):
        super().__init__("G-BA Decisions", db_session)

    def fetch(self) -> List[Dict]:
        """Scarica feed RSS e pagina decisioni."""
        items = []

        # 1. RSS Feed
        try:
            feed = feedparser.parse(GBA_RSS_URL)
            for entry in feed.entries:
                items.append({
                    "source": "rss",
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                })
            self.logger.info(f"  RSS: {len(feed.entries)} items")
        except Exception as e:
            self.logger.warning(f"  RSS fallito: {e}")

        # 2. Fallback: scraping pagina decisioni
        if not items:
            try:
                resp = self.http_get(GBA_BESCHLUESSE_URL)
                soup = BeautifulSoup(resp.text, "lxml")

                for row in soup.select("table tbody tr, .beschluss-item, article"):
                    title_el = row.select_one("a, .title, h3")
                    date_el = row.select_one("time, .date, td:first-child")

                    if title_el:
                        items.append({
                            "source": "scrape",
                            "title": title_el.get_text(strip=True),
                            "link": title_el.get("href", ""),
                            "published": date_el.get_text(strip=True) if date_el else "",
                            "summary": "",
                        })

                self.logger.info(f"  Scraping: {len(items)} items")
            except Exception as e:
                self.logger.warning(f"  Scraping fallito: {e}")

        return items

    def parse(self, raw_items: List[Dict]) -> List[Dict]:
        """Converte items G-BA in formato normalizzato."""
        parsed = []

        for item in raw_items:
            title = item.get("title", "").strip()
            if not title:
                continue

            # Parse data
            pub_date = None
            date_str = item.get("published", "")
            for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%d.%m.%Y", "%Y-%m-%d"]:
                try:
                    pub_date = datetime.strptime(date_str.strip(), fmt).date()
                    break
                except (ValueError, AttributeError):
                    continue

            # URL completo
            link = item.get("link", "")
            if link and not link.startswith("http"):
                link = f"https://www.g-ba.de{link}"

            # Classifica tipo decisione dal titolo
            decision_type = self._classify_decision(title)

            # Identifica sottocommissione
            subcommittee = self._extract_subcommittee(title)

            # Check digital health relevance
            title_lower = title.lower()
            summary_lower = item.get("summary", "").lower()
            combined = title_lower + " " + summary_lower

            is_digital = any(kw in combined for kw in DIGITAL_HEALTH_KEYWORDS)
            is_neuro = any(kw in combined for kw in NEURO_KEYWORDS)

            parsed.append({
                "external_id": f"GBA-{hash(title) % 10**8}",
                "title": title,
                "url": link,
                "publish_date": pub_date,
                "language": "de",
                "full_text": item.get("summary", ""),
                "country": "Germany",
                "document_type": f"G-BA {decision_type}",
                "extra_data": {
                    "decision_type": decision_type,
                    "subcommittee": subcommittee,
                    "digital_health_flag": is_digital,
                    "is_neuro": is_neuro,
                }
            })

        return parsed

    def _store_extra(self, doc: Document, doc_data: Dict):
        """Salva dati extra nella tabella gba_decisions."""
        extra = doc_data.get("extra_data", {})

        gba_dec = GBADecision(
            document_id=doc.document_id,
            decision_type=extra.get("decision_type", ""),
            subcommittee=extra.get("subcommittee", ""),
            digital_health_flag=extra.get("digital_health_flag", False),
            reimbursement_impact=self._classify_reimbursement_impact(doc_data["title"]),
        )
        self.session.add(gba_dec)

        # Aggiorna flags
        if doc.flags:
            doc.flags.is_reimbursement = True
            doc.flags.is_regulatory = True
            if extra.get("digital_health_flag"):
                doc.flags.is_diga = True
            if extra.get("is_neuro"):
                doc.flags.is_neuro = True

    def _classify_decision(self, title: str) -> str:
        """Classifica tipo di decisione dal titolo."""
        title_lower = title.lower()
        if "richtlinie" in title_lower:
            return "Richtlinie"
        elif "beschluss" in title_lower:
            return "Beschluss"
        elif "nutzenbewertung" in title_lower:
            return "Nutzenbewertung"
        elif "methodenbewertung" in title_lower:
            return "Methodenbewertung"
        elif "erprobung" in title_lower:
            return "Erprobung"
        elif "qualitäts" in title_lower:
            return "Qualitätssicherung"
        else:
            return "Sonstige"

    def _extract_subcommittee(self, title: str) -> str:
        """Identifica sottocommissione dal contesto."""
        title_lower = title.lower()
        subcommittees = {
            "arzneimittel": "Arzneimittel",
            "medizinprodukt": "Methodenbewertung",
            "qualität": "Qualitätssicherung",
            "bedarfsplanung": "Bedarfsplanung",
            "zahnärzt": "Zahnärztliche Behandlung",
            "psychotherap": "Psychotherapie",
            "diga": "Digitale Gesundheitsanwendungen",
            "disease management": "Disease Management Programme",
        }
        for kw, sub in subcommittees.items():
            if kw in title_lower:
                return sub
        return "Allgemein"

    def _classify_reimbursement_impact(self, title: str) -> str:
        """Classifica impatto su rimborso."""
        title_lower = title.lower()
        if any(kw in title_lower for kw in ["aufnahme", "einführung", "zulassung", "erstattung"]):
            return "new_coverage"
        elif any(kw in title_lower for kw in ["änderung", "anpassung", "aktualisierung"]):
            return "update"
        elif any(kw in title_lower for kw in ["ausschluss", "einschränkung", "streichung"]):
            return "restriction"
        return "none"
