"""
Chatham House Collector
Collects articles on digital health and healthcare from Chatham House RSS feed.
Stores in documents table with document_type='chatham_house'.
"""

import os
import sys
import logging
from datetime import datetime

import feedparser
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL, REQUEST_TIMEOUT
from db.models import get_engine, get_session, Document, Source

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = get_engine(DATABASE_URL)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

RSS_FEEDS = {
    "Chatham House via Google News": {
        "url": "https://news.google.com/rss/search?q=site:chathamhouse.org+health&hl=en-US&gl=US&ceid=US:en",
        "source_type": "think_tank",
        "region": "Europe",
        "country": "United Kingdom",
    },
    "Chatham House Global Health": {
        "url": "https://news.google.com/rss/search?q=chatham+house+global+health+digital&hl=en-US&gl=US&ceid=US:en",
        "source_type": "think_tank",
        "region": "Europe",
        "country": "United Kingdom",
    },
}

HEALTH_KEYWORDS = [
    "health", "healthcare", "digital health", "mental health", "hospital",
    "medical", "disease", "pandemic", "epidemic", "pharmaceutical",
    "neurodegenerative", "dementia", "alzheimer", "parkinson",
    "psychiatr", "depression", "anxiety", "telemedicine", "telehealth",
    "WHO", "NHS", "biotech", "genomic", "vaccine", "therapeutic",
    "patient", "clinical", "diagnosis", "treatment", "wellbeing",
    "public health", "global health", "health system", "UHC",
    "universal health", "health data", "AI health", "digital therapeut",
    "health equity", "health security", "antimicrobial", "antibiotic",
    "health workforce", "health policy", "health governance",
    "nutrition", "maternal", "child health", "aging", "elderly",
    "disability", "rehabilitation", "palliative",
]


def is_health_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in HEALTH_KEYWORDS)


def get_or_create_source(session, name, config):
    source = session.query(Source).filter_by(source_name=name).first()
    if not source:
        source = Source(
            source_name=name,
            source_type=config.get("source_type", "think_tank"),
            url=config.get("url", ""),
            region=config.get("region", "Global"),
            country=config.get("country", ""),
            access_method="rss",
            active=True,
        )
        session.add(source)
        session.commit()
        logger.info(f"Created source: {name}")
    return source


def doc_exists(session, url):
    if not url:
        return False
    return session.query(Document).filter_by(url=url).first() is not None


def collect_rss():
    session = get_session(engine)
    total = 0
    try:
        for feed_name, config in RSS_FEEDS.items():
            logger.info(f"Fetching RSS: {feed_name}")
            source = get_or_create_source(session, feed_name, config)
            try:
                resp = requests.get(config["url"], headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT)
                feed = feedparser.parse(resp.content)

                if not feed.entries:
                    logger.warning(f"No entries for {feed_name}")
                    continue

                count = 0
                for entry in feed.entries[:50]:
                    title = entry.get("title", "").strip()
                    url = entry.get("link", "").strip()
                    summary_text = entry.get("summary", entry.get("description", "")).strip()

                    if not title or not url:
                        continue
                    if doc_exists(session, url):
                        continue
                    if False:
                        continue

                    pub_date = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        try:
                            pub_date = datetime(*entry.published_parsed[:6])
                        except Exception:
                            pass
                    if not pub_date:
                        pub_date = datetime.utcnow()

                    if summary_text:
                        soup = BeautifulSoup(summary_text, "html.parser")
                        summary_text = soup.get_text()[:500]

                    # Extract tags
                    tags = []
                    if hasattr(entry, "tags"):
                        tags = [t.get("term", "") for t in entry.tags if t.get("term")]
                    tag_str = ", ".join(tags[:5]) if tags else ""

                    summary_with_tags = summary_text
                    if tag_str:
                        summary_with_tags = f"[Tags: {tag_str}] {summary_text}"

                    doc = Document(
                        source_id=source.source_id,
                        title=title[:500],
                        url=url,
                        document_type="chatham_house",
                        country=config.get("country", ""),
                        publish_date=pub_date.date(),
                        summary=summary_with_tags[:1000] if summary_with_tags else None,
                        scraped_at=datetime.utcnow(),
                    )
                    session.add(doc)
                    count += 1

                session.commit()
                total += count
                logger.info(f"  {feed_name}: {count} new health articles")

            except Exception as e:
                session.rollback()
                logger.error(f"Error with {feed_name}: {e}")
    finally:
        session.close()
    return total


def run():
    logger.info("=" * 60)
    logger.info("Chatham House Collector — Run Started")
    logger.info("=" * 60)

    total = collect_rss()

    logger.info("=" * 60)
    logger.info(f"Run complete. Total new articles: {total}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
