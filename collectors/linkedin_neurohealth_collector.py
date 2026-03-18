"""
linkedin_neurohealth_collector.py
Collector per post LinkedIn su:
- Digital health per malattie neurodegenerative
- Mental health & psichiatria digitale
- Telemedicine per pazienti neurologici
- Startup e aziende digital health neuro

Usa Google News RSS con site:linkedin.com per trovare post pubblici.
"""

import hashlib
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    # Digital health + neurodegenerative
    'site:linkedin.com "digital health" neurodegenerative',
    'site:linkedin.com "digital health" Alzheimer',
    'site:linkedin.com "digital health" Parkinson dementia',
    'site:linkedin.com "digital therapeutics" neurological',
    'site:linkedin.com "brain health" digital technology',
    'site:linkedin.com "cognitive health" digital app',
    'site:linkedin.com "neurotechnology" patients',
    'site:linkedin.com "brain computer interface" health',
    'site:linkedin.com "digital biomarker" neurodegeneration',
    'site:linkedin.com "wearable" Parkinson Alzheimer',
    # Mental health & digital psychiatry
    'site:linkedin.com "digital mental health" therapy',
    'site:linkedin.com "mental health" app startup',
    'site:linkedin.com "digital psychiatry" innovation',
    'site:linkedin.com "telepsychiatry" platform',
    'site:linkedin.com "mental health tech" startup',
    'site:linkedin.com "CBT app" digital mental',
    'site:linkedin.com "mental wellness" technology AI',
    'site:linkedin.com "behavioral health" digital platform',
    # Telemedicine neuro
    'site:linkedin.com telemedicine neurology patients',
    'site:linkedin.com "remote monitoring" neurological',
    'site:linkedin.com "telehealth" "brain" patients',
    'site:linkedin.com "virtual care" neurology',
    'site:linkedin.com "remote patient monitoring" neuro',
    # Startup digital health neuro
    'site:linkedin.com "healthtech" "neuroscience" startup',
    'site:linkedin.com "digital health startup" brain',
    'site:linkedin.com "neurotech" funding series',
    'site:linkedin.com "health AI" neurodegenerative startup',
    'site:linkedin.com "medtech" "neurology" innovation',
    # General high-signal queries
    'site:linkedin.com "digital health" "dementia care"',
    'site:linkedin.com "AI diagnostics" neurological disease',
    'site:linkedin.com "precision medicine" neurology digital',
    'site:linkedin.com "EEG" "wearable" "digital health"',
]


def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:64]


def search_google_rss(query, num_results=8):
    """Search Google News RSS for LinkedIn posts."""
    articles = []
    try:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en&gl=US&ceid=US:en"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "xml")
            for item in soup.find_all("item")[:num_results]:
                title = item.title.text.strip() if item.title else ""
                link = item.link.text.strip() if item.link else ""
                pub_date = item.pubDate.text if item.pubDate else ""
                desc = ""
                if item.description:
                    desc = BeautifulSoup(item.description.text, "html.parser").get_text().strip()

                articles.append({
                    "title": title,
                    "url": link,
                    "summary": desc[:500],
                    "pub_date": pub_date,
                    "source": "LinkedIn (via Google)",
                })
    except Exception as e:
        logger.warning(f"Search failed for '{query[:50]}': {e}")
    return articles


def search_google_web(query, num_results=5):
    """Fallback: search regular Google for LinkedIn content."""
    articles = []
    try:
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={num_results}"
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        })
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for g in soup.select("div.g, div[data-sokoban-container]"):
                a_tag = g.find("a", href=True)
                if a_tag and "linkedin.com" in a_tag["href"]:
                    title_el = g.find("h3")
                    title = title_el.text.strip() if title_el else a_tag["href"][:100]
                    link = a_tag["href"]
                    desc_el = g.find("span", class_=lambda c: c and "st" in str(c)) or g.find("div", class_=lambda c: c and "VwiC3b" in str(c))
                    desc = desc_el.text.strip()[:500] if desc_el else ""

                    articles.append({
                        "title": title,
                        "url": link,
                        "summary": desc,
                        "pub_date": "",
                        "source": "LinkedIn (via Google)",
                    })
    except Exception as e:
        logger.warning(f"Web search failed for '{query[:50]}': {e}")
    return articles


def run():
    """Main collector."""
    import sys
    sys.path.insert(0, ".")

    from config.settings import DATABASE_URL
    from db.models import get_engine, get_session, Document, Source

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    # Ensure source
    source = session.query(Source).filter_by(source_name="LinkedIn Neuro Digital Health").first()
    if not source:
        source = Source(
            source_name="LinkedIn Neuro Digital Health",
            source_type="social",
            url="https://linkedin.com",
            country="Global",
        )
        session.add(source)
        session.commit()

    all_articles = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        # Try Google News RSS first
        articles = search_google_rss(query, num_results=5)

        for a in articles:
            url_clean = a["url"].split("?")[0]  # Remove tracking params
            if url_clean not in seen_urls and a["title"]:
                seen_urls.add(url_clean)
                a["url"] = url_clean
                all_articles.append(a)

    logger.info(f"Found {len(all_articles)} LinkedIn posts")

    # Save to DB
    new_count = 0
    for article in all_articles:
        c_hash = content_hash(article["url"])
        existing = session.query(Document).filter_by(content_hash=c_hash).first()
        if existing:
            continue

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
            document_type="linkedin_neurohealth",
            content_hash=c_hash,
            country="Global",
            language="en",
            scraped_at=datetime.now(),
        )
        session.add(doc)
        new_count += 1

    session.commit()
    session.close()

    print(f"✅ LinkedIn Neuro Digital Health: {new_count} new posts saved ({len(all_articles)} found)")
    return new_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
