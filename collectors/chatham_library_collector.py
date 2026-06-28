"""
chatham_library_collector.py
Collector per la libreria online di Chatham House (https://www.chathamhouse.org/publications).

Raccoglie pubblicazioni/articoli su:
- Health & global health
- Digital health
- Geopolitics (health security, governance, geopolitica sanitaria)
- Neurodegenerative diseases

Strategia (come gli altri collector standalone del progetto):
1. Scraping diretto delle pagine della libreria Chatham House (publications + ricerche per tema).
2. Fallback su Google News RSS (site:chathamhouse.org) per resilienza in CI.
Dedup tramite content_hash, salvataggio in documents con document_type='chatham_library'.
"""

import hashlib
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.chathamhouse.org"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Pagine della libreria da scrappare. Il parametro search_api_fulltext filtra per tema.
LIBRARY_URLS = [
    f"{BASE_URL}/publications",
    f"{BASE_URL}/publications?search_api_fulltext=health",
    f"{BASE_URL}/publications?search_api_fulltext=digital+health",
    f"{BASE_URL}/publications?search_api_fulltext=global+health",
    f"{BASE_URL}/publications?search_api_fulltext=health+security",
    f"{BASE_URL}/publications?search_api_fulltext=geopolitics+health",
    f"{BASE_URL}/publications?search_api_fulltext=pandemic",
    f"{BASE_URL}/publications?search_api_fulltext=neurodegenerative",
    f"{BASE_URL}/publications?search_api_fulltext=dementia",
    f"{BASE_URL}/publications?search_api_fulltext=mental+health",
]

# Ricerche Google News come fallback. Il parametro site: non funziona su Google News,
# quindi filtriamo per editore ("Chatham House") tramite l'elemento <source> dell'RSS.
GOOGLE_NEWS_QUERIES = [
    "chatham house global health",
    "chatham house digital health",
    "chatham house health security",
    "chatham house pandemic preparedness",
    "chatham house health geopolitics",
    "chatham house neurodegenerative dementia",
    "chatham house mental health",
]

RELEVANCE_KEYWORDS = [
    # Health
    "health", "healthcare", "global health", "public health", "health system",
    "health security", "health policy", "health governance", "health data",
    "universal health", "pandemic", "epidemic", "disease", "vaccine",
    "antimicrobial", "antibiotic", "biosecurity", "WHO",
    # Digital health
    "digital health", "telemedicine", "telehealth", "AI health", "health tech",
    "digital therapeut", "e-health", "mhealth",
    # Geopolitics
    "geopolitic", "geopolitical", "global governance", "diplomacy",
    "international", "security", "great power", "sovereignty",
    # Neurodegenerative / neuro
    "neurodegenerative", "neurodegeneration", "dementia", "alzheimer",
    "parkinson", "neurolog", "brain health", "mental health",
    "psychiatr", "cognitive",
]


def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in RELEVANCE_KEYWORDS)


def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:64]


def _looks_like_publication(href):
    """Heuristica per riconoscere i link a una pubblicazione Chatham House."""
    if not href:
        return False
    # URL contenuti tipo /2025/06/titolo  oppure  /publications/...
    if "/publications/" in href:
        return True
    parts = [p for p in href.split("/") if p]
    # pattern /YYYY/MM/slug
    if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 4 and parts[1].isdigit():
        return True
    return False


def scrape_library(url):
    """Scarica una pagina della libreria ed estrae le pubblicazioni rilevanti."""
    articles = []
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
        if resp.status_code != 200:
            logger.warning(f"Library page {url} returned {resp.status_code}")
            return articles

        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            title = a.get_text(strip=True)

            if not title or len(title) < 15:
                continue
            if not _looks_like_publication(href):
                continue

            full_url = href if href.startswith("http") else BASE_URL + href
            full_url = full_url.split("?")[0].split("#")[0]

            if not is_relevant(title):
                continue

            articles.append({
                "title": title[:500],
                "url": full_url,
                "summary": "",
                "pub_date": "",
            })
    except Exception as e:
        logger.warning(f"Library scrape failed for {url}: {e}")
    return articles


def search_google_news(query, num_results=20):
    """Fallback: cerca pubblicazioni Chatham House via Google News RSS.

    Google News restituisce link redirect (news.google.com/...), quindi l'editore
    reale viene letto dall'elemento <source>: teniamo solo le voci di Chatham House.
    """
    articles = []
    try:
        url = (
            "https://news.google.com/rss/search?q="
            f"{requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        )
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=30)
        if resp.status_code != 200:
            return articles
        soup = BeautifulSoup(resp.content, "xml")
        for item in soup.find_all("item")[:num_results]:
            title = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            publisher = item.source.text.strip() if item.source else ""
            pub_date = item.pubDate.text if item.pubDate else ""
            desc = ""
            if item.description:
                desc = BeautifulSoup(item.description.text, "html.parser").get_text().strip()

            if not title or len(title) < 15 or not link:
                continue
            # Tieni solo pubblicazioni effettivamente di Chatham House
            if "chatham house" not in publisher.lower():
                continue
            if not is_relevant(title, desc):
                continue

            # Rimuovi il suffisso " - Chatham House" dal titolo
            if publisher and title.endswith(f"- {publisher}"):
                title = title[: -len(f"- {publisher}")].strip()

            articles.append({
                "title": title[:500],
                "url": link.split("#")[0],
                "summary": desc[:500],
                "pub_date": pub_date,
            })
    except Exception as e:
        logger.warning(f"Google News search failed for '{query}': {e}")
    return articles


def run():
    """Funzione principale del collector."""
    import sys
    sys.path.insert(0, ".")

    from config.settings import DATABASE_URL
    from db.models import get_engine, get_session, Document, Source

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    # Assicura che la fonte esista
    source = session.query(Source).filter_by(source_name="Chatham House Library").first()
    if not source:
        source = Source(
            source_name="Chatham House Library",
            source_type="think_tank",
            url=f"{BASE_URL}/publications",
            region="Europe",
            country="United Kingdom",
            access_method="html_scrape",
            active=True,
        )
        session.add(source)
        session.commit()
        logger.info("Created source: Chatham House Library")

    all_articles = []
    seen_urls = set()

    # 1. Scraping diretto della libreria
    for url in LIBRARY_URLS:
        for a in scrape_library(url):
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)

    # 2. Fallback Google News
    for query in GOOGLE_NEWS_QUERIES:
        for a in search_google_news(query):
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                all_articles.append(a)

    logger.info(f"Found {len(all_articles)} relevant Chatham House publications")

    # 3. Salvataggio con dedup
    new_count = 0
    for article in all_articles:
        c_hash = content_hash(article["url"])
        if session.query(Document).filter_by(content_hash=c_hash).first():
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
            summary=article["summary"] or None,
            publish_date=pub_date,
            document_type="chatham_library",
            content_hash=c_hash,
            country="United Kingdom",
            language="en",
            scraped_at=datetime.now(),
        )
        session.add(doc)
        new_count += 1

    session.commit()
    session.close()

    logger.info(f"Chatham House Library: {new_count} new publications saved")
    print(f"✅ Chatham House Library: {new_count} new publications saved ({len(all_articles)} found)")
    return new_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
