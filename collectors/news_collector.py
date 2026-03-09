"""
Collector per testate specializzate digital health e competitive intelligence.
Copre: MobiHealthNews, Healthcare IT News, Fierce Healthcare, STAT News,
Rock Health, CB Insights Health, MedTech Intelligence, etc.
"""

from datetime import datetime
from typing import List, Dict

import feedparser

from collectors.base import BaseCollector

# ── FEED CONFIGURAZIONE ──────────────────────────────────

NEWS_FEEDS = {
    # ── Testate Digital Health ──
    "MobiHealthNews": {
        "feeds": [
            "https://www.mobihealthnews.com/feed",
            "https://www.mobihealthnews.com/rss-feed",
        ],
        "country": "USA",
        "document_type": "industry_news",
        "source_category": "news",
    },
    "Healthcare IT News": {
        "feeds": [
            "https://www.healthcareitnews.com/rss/comments",
            "https://www.healthcareitnews.com/rss.xml",
        ],
        "country": "USA",
        "document_type": "industry_news",
        "source_category": "news",
    },
    "Fierce Healthcare": {
        "feeds": [
            "https://www.fiercehealthcare.com/rss/xml",
        ],
        "country": "USA",
        "document_type": "industry_news",
        "source_category": "news",
    },
    "STAT News": {
        "feeds": [
            "https://www.statnews.com/feed/",
            "https://www.statnews.com/category/pharma/feed/",
        ],
        "filter_keywords": [
            "digital health", "AI", "artificial intelligence", "technology",
            "digital", "telemedicine", "app", "software", "algorithm",
            "data", "wearable", "remote monitoring", "startup",
            "Alzheimer", "Parkinson", "dementia", "neurodegenerative",
            "FDA", "regulation", "device",
        ],
        "country": "USA",
        "document_type": "health_news",
        "source_category": "news",
    },

    # ── UK / NHS / London ──
    "Digital Health UK": {
        "feeds": [
            "https://www.digitalhealth.net/feed/",
            "https://www.digitalhealth.net/news/feed",
        ],
        "country": "UK",
        "document_type": "industry_news",
        "source_category": "news",
    },
    "Digital Health London": {
        "feeds": [
            "https://digitalhealth.london/feed",
        ],
        "country": "UK",
        "document_type": "industry_news",
        "source_category": "news",
    },
    "NHS Digital": {
        "feeds": [
            "https://digital.nhs.uk/feed",
            "https://transform.england.nhs.uk/feed/",
        ],
        "country": "UK",
        "document_type": "policy_update",
        "source_category": "news",
    },

    # ── Competitive Intelligence ──
    "Rock Health": {
        "feeds": [
            "https://rockhealth.com/feed/",
        ],
        "country": "USA",
        "document_type": "market_intelligence",
        "source_category": "competitive",
    },
    "MedTech Intelligence": {
        "feeds": [
            "https://medtechintelligence.com/feed/",
        ],
        "country": "USA",
        "document_type": "industry_analysis",
        "source_category": "competitive",
    },
    "Endpoints News": {
        "feeds": [
            "https://endpts.com/feed/",
        ],
        "filter_keywords": [
            "digital", "AI", "technology", "software", "device",
            "Alzheimer", "Parkinson", "neurodegenerative", "dementia",
            "biomarker", "diagnostic",
        ],
        "country": "USA",
        "document_type": "pharma_news",
        "source_category": "competitive",
    },
    "Digital Health Global": {
        "feeds": [
            "https://digitalhealthglobal.com/feed",
        ],
        "country": "International",
        "document_type": "industry_news",
        "source_category": "competitive",
    },

    # ── EU focused ──
    "eHealth Network EU": {
        "feeds": [
            "https://health.ec.europa.eu/rss_en",
        ],
        "filter_keywords": [
            "digital", "eHealth", "health data", "EHDS", "AI",
            "interoperability", "telemedicine", "electronic",
        ],
        "country": "EU",
        "document_type": "policy_update",
        "source_category": "news",
    },
    "HIMSS Europe": {
        "feeds": [
            "https://www.himss.org/feed",
        ],
        "filter_keywords": [
            "digital health", "Europe", "AI", "interoperability",
            "EHR", "health data", "EHDS", "NHS",
        ],
        "country": "International",
        "document_type": "industry_news",
        "source_category": "news",
    },
}


class NewsCollector(BaseCollector):
    """Collector per testate specializzate e competitive intelligence."""

    def __init__(self, source_name: str, db_session):
        # Registra la fonte nel DB se non esiste
        from db.models import Source
        source = db_session.query(Source).filter_by(source_name=source_name).first()
        if not source:
            config = NEWS_FEEDS.get(source_name, {})
            source = Source(
                source_name=source_name,
                source_type="news" if config.get("source_category") == "news" else "trends",
                country=config.get("country", "International"),
                region=self._country_to_region(config.get("country", "")),
                url=config.get("feeds", [""])[0],
                access_method="rss",
                refresh_hours=12,
                trust_level=3,
                active=True,
            )
            db_session.add(source)
            db_session.commit()

        super().__init__(source_name, db_session)
        self.config = NEWS_FEEDS.get(source_name, {})

    def _country_to_region(self, country: str) -> str:
        """Mappa paese a regione."""
        mapping = {
            "USA": "North America",
            "UK": "Europe",
            "EU": "Europe",
            "International": "Global",
        }
        return mapping.get(country, "Global")

    def fetch(self) -> List[Dict]:
        """Scarica feed RSS usando requests con User-Agent da browser."""
        import requests as req
        items = []

        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, application/atom+xml, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

        for feed_url in self.config.get("feeds", []):
            try:
                # Scarica con requests (headers da browser)
                resp = req.get(feed_url, headers=browser_headers, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    self.logger.warning(f"  Feed HTTP {resp.status_code}: {feed_url}")
                    continue

                # Passa il contenuto a feedparser (non l'URL)
                feed = feedparser.parse(resp.content)
                if feed.bozo and not feed.entries:
                    self.logger.warning(f"  Feed non valido (parse error): {feed_url}")
                    continue

                for entry in feed.entries[:30]:
                    items.append({
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "published": entry.get("published", entry.get("updated", "")),
                        "summary": entry.get("summary", entry.get("description", "")),
                        "tags": [t.get("term", "") for t in entry.get("tags", [])],
                        "author": entry.get("author", ""),
                    })

                self.logger.info(f"  Feed {feed_url}: {len(feed.entries)} items")
            except req.exceptions.Timeout:
                self.logger.warning(f"  Feed timeout: {feed_url}")
            except req.exceptions.ConnectionError:
                self.logger.warning(f"  Feed connessione fallita: {feed_url}")
            except Exception as e:
                self.logger.warning(f"  Feed fallito {feed_url}: {e}")

        return items

    def parse(self, raw_items: List[Dict]) -> List[Dict]:
        """Filtra e normalizza items."""
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
            for fmt in [
                "%a, %d %b %Y %H:%M:%S %z",
                "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%d.%m.%Y",
                "%Y-%m-%d",
            ]:
                try:
                    pub_date = datetime.strptime(date_str.strip(), fmt).date()
                    break
                except (ValueError, AttributeError):
                    continue

            # Clean summary (rimuovi HTML tags)
            summary = item.get("summary", "")
            if "<" in summary:
                from bs4 import BeautifulSoup
                summary = BeautifulSoup(summary, "html.parser").get_text(separator=" ")
            summary = summary[:1000]  # Limita lunghezza

            parsed.append({
                "external_id": f"NEWS-{hash(item.get('link', title)) % 10**8}",
                "title": title,
                "url": item.get("link", ""),
                "publish_date": pub_date,
                "language": "en",
                "full_text": summary,
                "country": self.config.get("country", ""),
                "document_type": self.config.get("document_type", "news"),
            })

        return parsed
