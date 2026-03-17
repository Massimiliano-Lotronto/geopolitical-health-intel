"""
china_medtourism_collector.py
Collector per articoli su:
- Medical tourism in China (pazienti internazionali)
- Digital health cinese
- Malattie neurodegenerative e psichiatriche
- Ospedali e servizi sanitari cinesi all'avanguardia
- Sistemi di pagamento, gestione dati, follow-up a distanza
"""

import re
import hashlib
import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── FONTI E QUERY ──
SEARCH_QUERIES = [
    # Medical tourism
    "China medical tourism international patients hospitals",
    "China hospital foreign patients treatment cost",
    "Boao Lecheng medical tourism Hainan",
    "China healthcare foreigners affordable treatment",
    # Digital health
    "China digital health telemedicine AI hospital",
    "China health tech wearable remote monitoring patients",
    "WeDoctor China digital healthcare platform",
    # Neurodegenerative
    "China Alzheimer treatment hospital international",
    "China Parkinson disease stem cell therapy",
    "China neurodegenerative disease treatment research",
    "China ALS motor neuron disease therapy",
    "Beijing Tiantan Hospital neurology international",
    # Psychiatric
    "China mental health psychiatric services international",
    "China psychiatric hospital treatment foreigners",
    # Advanced hospitals
    "Peking Union Medical College Hospital international patients",
    "Shanghai Ruijin Hospital neurology international",
    "West China Hospital Sichuan neurodegenerative",
    "Fudan University Shanghai Cancer Center international",
    # Payment & data
    "China hospital payment system foreign patients insurance",
    "China cross border healthcare data management",
    "China telemedicine follow-up international patients",
    # Advertising & recruitment
    "China medical tourism marketing attract foreign patients",
    "China healthcare promotion international patients campaign",
]

# RSS feeds di fonti rilevanti
RSS_FEEDS = [
    "https://www.globaltimes.cn/rss/outbrain.xml",
    "https://www.chinadaily.com.cn/rss/china_rss.xml",
]

# Siti da scrappare per articoli
SCRAPE_URLS = [
    ("https://www.medbridgenz.com/blog", "MedBridge NZ"),
    ("https://en.firstaidchina.com/useful-info", "Sinoaid China"),
]

HEALTH_FILTER_KEYWORDS = [
    "medical tourism", "hospital", "patient", "treatment", "healthcare",
    "health", "medical", "disease", "therapy", "clinic", "doctor",
    "surgery", "diagnosis", "medicine", "pharmaceutical", "biotech",
    "neurology", "neurodegenerat", "alzheimer", "parkinson", "dementia",
    "psychiatric", "mental health", "stem cell", "digital health",
    "telemedicine", "telehealth", "AI health", "wearable",
]

CHINA_KEYWORDS = [
    "china", "chinese", "beijing", "shanghai", "guangzhou", "shenzhen",
    "hainan", "boao", "lecheng", "tianjin", "chengdu", "wuhan",
    "hangzhou", "nanjing", "xi'an", "ruijin", "tiantan", "peking",
    "fudan", "west china", "zhongshan",
]


def is_relevant(title, summary=""):
    """Check if article is about China + healthcare."""
    text = (title + " " + summary).lower()
    has_health = any(kw in text for kw in HEALTH_FILTER_KEYWORDS)
    has_china = any(kw in text for kw in CHINA_KEYWORDS)
    return has_health and has_china


def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:64]


def search_google_news(query, num_results=10):
    """Search Google News RSS for articles."""
    articles = []
    try:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "xml")
            for item in soup.find_all("item")[:num_results]:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                desc = item.description.text if item.description else ""
                # Clean HTML from description
                desc = BeautifulSoup(desc, "html.parser").get_text()

                if is_relevant(title, desc):
                    articles.append({
                        "title": title.strip(),
                        "url": link.strip(),
                        "summary": desc.strip()[:500],
                        "pub_date": pub_date,
                        "source": "Google News",
                    })
    except Exception as e:
        logger.warning(f"Google News search failed for '{query}': {e}")
    return articles


def fetch_rss(feed_url):
    """Fetch articles from RSS feed."""
    articles = []
    try:
        resp = requests.get(feed_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "xml")
            for item in soup.find_all("item")[:30]:
                title = item.title.text if item.title else ""
                link = item.link.text if item.link else ""
                desc = ""
                if item.description:
                    desc = BeautifulSoup(item.description.text, "html.parser").get_text()
                pub_date = item.pubDate.text if item.pubDate else ""

                if is_relevant(title, desc):
                    articles.append({
                        "title": title.strip(),
                        "url": link.strip(),
                        "summary": desc.strip()[:500],
                        "pub_date": pub_date,
                        "source": feed_url.split("/")[2],
                    })
    except Exception as e:
        logger.warning(f"RSS fetch failed for {feed_url}: {e}")
    return articles


def run():
    """Main collector function."""
    import sys
    sys.path.insert(0, ".")

    from config.settings import DATABASE_URL
    from db.models import get_engine, get_session, Document, Source
    from sqlalchemy import text

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    # Ensure source exists
    source = session.query(Source).filter_by(source_name="China Medical Tourism").first()
    if not source:
        source = Source(
            source_name="China Medical Tourism",
            source_type="aggregator",
            url="https://news.google.com",
            country="China",
        )
        session.add(source)
        session.commit()

    all_articles = []
    seen_urls = set()

    # 1. Google News searches
    for query in SEARCH_QUERIES:
        articles = search_google_news(query, num_results=5)
        for a in articles:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)

    # 2. RSS feeds
    for feed in RSS_FEEDS:
        articles = fetch_rss(feed)
        for a in articles:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)

    logger.info(f"Found {len(all_articles)} relevant articles")

    # 3. Save to DB
    new_count = 0
    for article in all_articles:
        c_hash = content_hash(article["url"])

        existing = session.query(Document).filter_by(content_hash=c_hash).first()
        if existing:
            continue

        # Parse date
        pub_date = None
        if article.get("pub_date"):
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(article["pub_date"]).date()
            except Exception:
                pub_date = datetime.now().date()
        else:
            pub_date = datetime.now().date()

        doc = Document(
            source_id=source.source_id,
            title=article["title"],
            url=article["url"],
            summary=article["summary"],
            publish_date=pub_date,
            document_type="china_medtourism",
            content_hash=c_hash,
            country="China",
            language="en",
            scraped_at=datetime.now(),
        )
        session.add(doc)
        new_count += 1

    session.commit()
    session.close()

    logger.info(f"China Medical Tourism: {new_count} new articles saved")
    print(f"✅ China Medical Tourism: {new_count} new articles saved ({len(all_articles)} found)")
    return new_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
