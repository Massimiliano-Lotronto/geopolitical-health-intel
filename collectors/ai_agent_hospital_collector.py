"""
ai_agent_hospital_collector.py
Collector per articoli su AI Agent Hospital (Tsinghua University AIR)
- MedAgent-Zero framework
- Tairex / Zijing Zhikang startups
- DeepSeek hospital integration
- Virtual hospital AI agents
"""
import hashlib, logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "AI Agent Hospital Tsinghua University",
    "MedAgent-Zero AI hospital",
    "Tairex AI hospital China",
    "Zijing AI Doctor Tsinghua",
    "China AI hospital LLM agents",
    "virtual hospital AI agents medical",
    "DeepSeek hospital China healthcare",
    "DeepSeek AI medical diagnosis China",
    "Tsinghua AIR medical AI research",
    "AI doctor agents self-evolving",
    "China AI diagnostic hospital pilot",
    "LLM medical agents clinical",
    "AI hospital simulation training doctors",
    "Beijing Tsinghua Chang Gung Hospital AI",
    "China AI healthcare autonomous agents",
    "AI medical education virtual patients",
    "agent-based healthcare AI system",
    "China AI telemedicine rural healthcare",
]

def content_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()[:64]

def search_google_rss(query, num_results=8):
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
                    articles.append({"title": title, "url": link, "summary": desc, "pub_date": pub_date, "source": "Google News"})
    except Exception as e:
        logger.warning(f"Search failed: {e}")
    return articles

def run():
    import sys; sys.path.insert(0, ".")
    from config.settings import DATABASE_URL
    from db.models import get_engine, get_session, Document, Source

    engine = get_engine(DATABASE_URL)
    session = get_session(engine)

    source = session.query(Source).filter_by(source_name="AI Agent Hospital").first()
    if not source:
        source = Source(source_name="AI Agent Hospital", source_type="research", url="https://air.tsinghua.edu.cn", country="China")
        session.add(source); session.commit()

    all_articles, seen = [], set()
    for q in SEARCH_QUERIES:
        for a in search_google_rss(q, 5):
            u = a["url"].split("?")[0]
            if u not in seen and a["title"]:
                seen.add(u); a["url"] = u; all_articles.append(a)

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
        session.add(Document(source_id=source.source_id, title=a["title"], url=a["url"], summary=a["summary"],
            publish_date=pub_date, document_type="ai_agent_hospital", content_hash=ch, country="China", language="en", scraped_at=datetime.now()))
        new_count += 1

    session.commit(); session.close()
    print(f"✅ AI Agent Hospital: {new_count} new articles saved ({len(all_articles)} found)")
    return new_count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO); run()
