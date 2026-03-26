"""
ai_agent_hospital_collector.py (v2)
Expanded collector: Tsinghua Agent Hospital + other Chinese university AI healthcare projects
"""
import hashlib, logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    # Tsinghua Agent Hospital core
    "AI Agent Hospital Tsinghua University",
    "MedAgent-Zero AI hospital",
    "Tairex AI hospital China",
    "Zijing AI Doctor Tsinghua",
    "Tsinghua AIR medical AI",
    "Beijing Tsinghua Chang Gung Hospital AI",
    # DeepSeek
    "DeepSeek hospital China healthcare",
    "DeepSeek AI medical diagnosis",
    "DeepSeek pathology clinical",
    # Other Chinese universities AI health
    "China university AI hospital project",
    "Chinese medical AI research university",
    "AI digital health China academic research",
    "Peking University medical AI agent",
    "Fudan University AI healthcare Shanghai",
    "Zhejiang University medical AI",
    "USTC Hefei Alzheimer AI research",
    "MedGo Tongji University medical LLM",
    "Tongji University AI clinical decision",
    "West China Hospital Sichuan AI diagnosis",
    "Sun Yat-sen University medical AI",
    "Harbin Institute Technology medical AI",
    "Shanghai Jiao Tong University AI medicine",
    "Nanjing University digital health AI",
    # Broader topics
    "China AI hospital autonomous agents LLM",
    "virtual hospital AI agents medical simulation",
    "AI doctor training virtual patients China",
    "China medical LLM clinical trials",
    "AI healthcare China rural telemedicine",
    "China AI drug discovery university",
    "brain computer interface China university",
    "China AI mental health digital psychiatry",
    "China neurodegenerative AI research university",
]

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:64]

def search_google_rss(query, num_results=6):
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
                desc = BeautifulSoup(item.description.text, "html.parser").get_text().strip()[:500] if item.description else ""
                if title:
                    articles.append({"title": title, "url": link, "summary": desc, "pub_date": pub_date})
    except Exception as e:
        logger.warning(f"Search failed: {e}")
    return articles

def fetch_tsinghua_news():
    """Fetch news from Tsinghua English site."""
    articles = []
    try:
        resp = requests.get("https://www.tsinghua.edu.cn/en/Research/Research_News.htm",
                           timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                title = a.get_text().strip()
                href = a["href"]
                if title and len(title) > 20 and any(kw in title.lower() for kw in
                    ["ai", "medical", "health", "hospital", "agent", "brain", "neural",
                     "disease", "clinical", "diagnosis", "drug", "pharma", "digital"]):
                    if not href.startswith("http"):
                        href = "https://www.tsinghua.edu.cn" + href
                    articles.append({"title": title, "url": href, "summary": title, "pub_date": ""})
    except Exception as e:
        logger.warning(f"Tsinghua fetch failed: {e}")
    return articles[:15]

def run():
    import sys; sys.path.insert(0, ".")
    from config.settings import DATABASE_URL
    from db.models import get_engine, get_session, Document, Source

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    source = session.query(Source).filter_by(source_name="AI Agent Hospital").first()
    if not source:
        source = Source(source_name="AI Agent Hospital", source_type="research",
                       url="https://air.tsinghua.edu.cn", country="China")
        session.add(source); session.commit()

    all_articles, seen = [], set()

    # Google News searches
    for q in SEARCH_QUERIES:
        for a in search_google_rss(q, 5):
            u = a["url"].split("?")[0]
            if u not in seen and a["title"]:
                seen.add(u); a["url"] = u; all_articles.append(a)

    # Tsinghua direct
    for a in fetch_tsinghua_news():
        u = a["url"].split("?")[0]
        if u not in seen and a["title"]:
            seen.add(u); all_articles.append(a)

    new_count = 0
    for a in all_articles:
        ch = content_hash(a["url"])
        if session.query(Document).filter_by(content_hash=ch).first(): continue
        pub_date = None
        if a.get("pub_date"):
            try:
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(a["pub_date"]).date()
            except: pub_date = datetime.now().date()
        else: pub_date = datetime.now().date()
        session.add(Document(source_id=source.source_id, title=a["title"], url=a["url"],
            summary=a["summary"], publish_date=pub_date, document_type="ai_agent_hospital",
            content_hash=ch, country="China", language="en", scraped_at=datetime.now()))
        new_count += 1

    session.commit(); session.close()
    print(f"✅ AI Agent Hospital: {new_count} new articles saved ({len(all_articles)} found)")
    return new_count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); run()
