"""
Collector generico per fonti basate su RSS Feed.
Copre: FDA DHCOE, EC AI/EHDS, WHO, BMG, IQWiG, OECD.
"""

from datetime import datetime
from typing import List, Dict

import feedparser

from collectors.base import BaseCollector

# Configurazione RSS per ogni fonte
RSS_FEEDS = {
    "FDA Digital Health CoE": {
        "feeds": [
            "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medical-devices/rss.xml",
            "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml",
            "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/medwatch-safety-alerts-human-medical-products/rss.xml",
        ],
        "filter_keywords": ["digital", "software", "artificial intelligence", "AI",
                            "device", "cyber", "machine learning", "SaMD",
                            "health data", "algorithm", "clinical decision"],
        "country": "USA",
        "document_type": "regulatory_update",
    },
    "WHO Digital Health": {
        "feeds": [
            "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
            "https://www.who.int/feeds/entity/bulletin/volumes/en/rss.xml",
        ],
        "filter_keywords": ["digital health", "telemedicine", "artificial intelligence",
                            "eHealth", "mHealth", "health data", "digital",
                            "technology", "innovation", "data"],
        "country": "International",
        "document_type": "policy_update",
    },
    "BMG Germany": {
        "feeds": [
            "https://www.bundesgesundheitsministerium.de/presse/pressemitteilungen.rss",
            "https://www.bundesgesundheitsministerium.de/presse/aktuelle-meldungen.rss",
        ],
        "filter_keywords": ["digital", "telemedizin", "diga", "gesundheit",
                            "arzneimittel", "medizinprodukt", "ki", "daten",
                            "pflege", "krankenversicherung", "epa",
                            "gematik", "innovation", "reform"],
        "country": "Germany",
        "document_type": "policy_update",
    },
    "IQWiG": {
        "feeds": [
            "https://www.iqwig.de/presse/pressemitteilungen.rss",
            "https://www.iqwig.de/en/presse/press-releases.rss",
        ],
        "country": "Germany",
        "document_type": "hta_report",
    },
    "G-BA Decisions": {
        "feeds": [
            "https://www.g-ba.de/letzte-aenderungen/?rss=1",
            "https://www.g-ba.de/presse/pressemitteilungen/?rss=1",
        ],
        "filter_keywords": ["digital", "diga", "telemedizin", "software",
                            "ki", "künstliche intelligenz", "medizinprodukt",
                            "fernbehandlung", "innovation", "arzneimittel",
                            "nutzenbewertung", "methodenbewertung",
                            "demenz", "neurolog", "parkinson", "alzheimer"],
        "country": "Germany",
        "document_type": "hta_decision",
    },
}


class RSSCollector(BaseCollector):
    """Collector generico per fonti RSS."""

    def __init__(self, source_name: str, db_session):
        super().__init__(source_name, db_session)
        self.config = RSS_FEEDS.get(source_name, {})

    def fetch(self) -> List[Dict]:
        """Scarica e parsa tutti i feed RSS configurati."""
        items = []

        for feed_url in self.config.get("feeds", []):
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries:
                    items.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", ""),
                        "tags": [t.get("term", "") for t in entry.get("tags", [])],
                    })
                self.logger.info(f"  Feed {feed_url}: {len(feed.entries)} items")
            except Exception as e:
                self.logger.warning(f"  Feed fallito {feed_url}: {e}")

        return items

    def parse(self, raw_items: List[Dict]) -> List[Dict]:
        """Filtra e normalizza items RSS."""
        parsed = []
        filter_kw = self.config.get("filter_keywords", [])

        for item in raw_items:
            title = item.get("title", "").strip()
            if not title:
                continue

            # Applica filtro keyword se configurato
            if filter_kw:
                combined = (title + " " + item.get("summary", "")).lower()
                if not any(kw.lower() in combined for kw in filter_kw):
                    continue

            # Parse data
            pub_date = None
            date_str = item.get("published", "")
            for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                        "%Y-%m-%dT%H:%M:%S%z", "%d.%m.%Y", "%Y-%m-%d"]:
                try:
                    pub_date = datetime.strptime(date_str.strip(), fmt).date()
                    break
                except (ValueError, AttributeError):
                    continue

            parsed.append({
                "external_id": f"RSS-{hash(item.get('link', title)) % 10**8}",
                "title": title,
                "url": item.get("link", ""),
                "publish_date": pub_date,
                "language": "de" if self.config.get("country") == "Germany" else "en",
                "full_text": item.get("summary", ""),
                "country": self.config.get("country", ""),
                "document_type": self.config.get("document_type", "news"),
            })

        return parsed
