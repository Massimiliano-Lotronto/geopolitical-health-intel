"""
Cyber Health Threat Collector
Collects healthcare cybersecurity alerts and incidents from:
- CISA (Cybersecurity & Infrastructure Security Agency)
- HHS HC3 (Health Sector Cybersecurity Coordination Center)
- ENISA (EU Agency for Cybersecurity)
- HealthITSecurity.com
- HIPAA Journal

Stores in documents table with document_type='cyber_alert'.
"""

import os
import sys
import logging
import re
from datetime import datetime, timedelta

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
    "Accept-Language": "en-US,en;q=0.9",
}

RSS_FEEDS = {
    "CISA Alerts": {
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "HHS HC3": {
        "url": "https://www.hhs.gov/feed/cybersecurity.xml",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "ENISA News": {
        "url": "https://www.enisa.europa.eu/media/news-items/RSS",
        "source_type": "cyber",
        "region": "Europe",
        "country": "",
    },
}

SCRAPE_SOURCES = {
    "HealthITSecurity": {
        "url": "https://healthitsecurity.com/news",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "HIPAA Journal": {
        "url": "https://www.hipaajournal.com/category/hacking-healthcare/",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
}

HEALTH_CYBER_KEYWORDS = [
    "hospital", "healthcare", "health", "medical", "patient", "clinical",
    "pharma", "biotech", "EHR", "electronic health record", "HIPAA",
    "ransomware", "breach", "cyberattack", "data leak", "vulnerability",
    "medical device", "IoMT", "telehealth", "digital health",
    "NHS", "HHS", "clinic", "health system", "health data",
]


def is_health_cyber_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in HEALTH_CYBER_KEYWORDS)


def get_or_create_source(session, name, config):
    source = session.query(Source).filter_by(source_name=name).first()
    if not source:
        source = Source(
            source_name=name,
            source_type=config.get("source_type", "cyber"),
            url=config.get("url", ""),
            region=config.get("region", "Global"),
            country=config.get("country", ""),
            access_method="rss" if name in RSS_FEEDS else "html_scrape",
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


def collect_rss_feeds():
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
                for entry in feed.entries[:30]:
                    title = entry.get("title", "").strip()
                    url = entry.get("link", "").strip()
                    summary_text = entry.get("summary", entry.get("description", "")).strip()

                    if not title or not url:
                        continue
                    if doc_exists(session, url):
                        continue
                    if feed_name == "CISA Alerts" and not is_health_cyber_relevant(title, summary_text):
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

                    doc = Document(
                        source_id=source.source_id,
                        title=title[:500],
                        url=url,
                        document_type="cyber_alert",
                        country=config.get("country", ""),
                        publish_date=pub_date.date(),
                        summary=summary_text[:1000] if summary_text else None,
                        scraped_at=datetime.utcnow(),
                    )
                    session.add(doc)
                    count += 1

                session.commit()
                total += count
                logger.info(f"  {feed_name}: {count} new articles")

            except Exception as e:
                session.rollback()
                logger.error(f"Error with {feed_name}: {e}")
    finally:
        session.close()
    return total


def scrape_healthitsecurity():
    session = get_session(engine)
    total = 0
    config = SCRAPE_SOURCES["HealthITSecurity"]
    try:
        source = get_or_create_source(session, "HealthITSecurity", config)
        resp = requests.get(config["url"], headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = soup.find_all("article", limit=20)
        if not articles:
            articles = soup.find_all("div", class_=re.compile(r"article|post|entry"), limit=20)

        for article in articles:
            a_tag = article.find("a", href=True)
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            url = a_tag["href"]
            if not url.startswith("http"):
                url = "https://healthitsecurity.com" + url
            if not title or doc_exists(session, url):
                continue

            pub_date = datetime.utcnow()
            time_tag = article.find("time")
            if time_tag and time_tag.get("datetime"):
                try:
                    pub_date = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
                except Exception:
                    pass

            summary_text = ""
            p_tag = article.find("p")
            if p_tag:
                summary_text = p_tag.get_text(strip=True)[:500]

            doc = Document(
                source_id=source.source_id,
                title=title[:500],
                url=url,
                document_type="cyber_alert",
                country="USA",
                publish_date=pub_date.date() if hasattr(pub_date, "date") else pub_date,
                summary=summary_text or None,
                scraped_at=datetime.utcnow(),
            )
            session.add(doc)
            total += 1

        session.commit()
        logger.info(f"HealthITSecurity: {total} new articles")
    except Exception as e:
        session.rollback()
        logger.error(f"Error scraping HealthITSecurity: {e}")
    finally:
        session.close()
    return total


def scrape_hipaa_journal():
    session = get_session(engine)
    total = 0
    config = SCRAPE_SOURCES["HIPAA Journal"]
    try:
        source = get_or_create_source(session, "HIPAA Journal", config)
        resp = requests.get(config["url"], headers=BROWSER_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        articles = soup.find_all("article", limit=20)
        if not articles:
            articles = soup.find_all("div", class_=re.compile(r"post|entry"), limit=20)

        for article in articles:
            h_tag = article.find(["h2", "h3"])
            if not h_tag:
                continue
            a_tag = h_tag.find("a", href=True)
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            url = a_tag["href"]
            if not url.startswith("http"):
                url = "https://www.hipaajournal.com" + url
            if not title or doc_exists(session, url):
                continue

            pub_date = datetime.utcnow()
            time_tag = article.find("time")
            if time_tag and time_tag.get("datetime"):
                try:
                    pub_date = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
                except Exception:
                    pass

            summary_text = ""
            p_tag = article.find("p")
            if p_tag:
                summary_text = p_tag.get_text(strip=True)[:500]

            doc = Document(
                source_id=source.source_id,
                title=title[:500],
                url=url,
                document_type="cyber_alert",
                country="USA",
                publish_date=pub_date.date() if hasattr(pub_date, "date") else pub_date,
                summary=summary_text or None,
                scraped_at=datetime.utcnow(),
            )
            session.add(doc)
            total += 1

        session.commit()
        logger.info(f"HIPAA Journal: {total} new articles")
    except Exception as e:
        session.rollback()
        logger.error(f"Error scraping HIPAA Journal: {e}")
    finally:
        session.close()
    return total


def run():
    logger.info("=" * 60)
    logger.info("Cyber Health Threat Collector — Run Started")
    logger.info("=" * 60)

    total = 0
    total += collect_rss_feeds()
    total += scrape_healthitsecurity()
    total += scrape_hipaa_journal()

    logger.info("=" * 60)
    logger.info(f"Run complete. Total new articles: {total}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
