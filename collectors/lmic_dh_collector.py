"""
LMIC Digital Mental Health Collector
Collects digital health projects for psychiatric and neurological conditions
in developing countries (Asia, India, Africa, South America).

Sources:
- ClinicalTrials.gov API (filtered by LMIC countries + digital health + mental/neuro)
- PubMed (focused search for LMIC digital mental health projects)

Stores in documents table with document_type='lmic_dh_project'.
"""

import os
import sys
import logging
import time
from datetime import datetime
import xml.etree.ElementTree as ET

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL, REQUEST_TIMEOUT
from db.models import get_engine, get_session, Document, Source

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = get_engine(DATABASE_URL)

BROWSER_HEADERS = {
    "User-Agent": "GeopoliticalHealthIntel/1.0 (Research Dashboard)",
    "Accept": "application/json",
}

# LMIC regions and countries
LMIC_REGIONS = {
    "South Asia": ["India", "Bangladesh", "Nepal", "Sri Lanka", "Pakistan", "Afghanistan"],
    "Southeast Asia": ["Vietnam", "Indonesia", "Philippines", "Thailand", "Cambodia", "Myanmar", "Laos"],
    "East Asia": ["China"],
    "Sub-Saharan Africa": ["Kenya", "Nigeria", "South Africa", "Ghana", "Ethiopia", "Tanzania",
                           "Uganda", "Rwanda", "Malawi", "Zimbabwe", "Mozambique", "Senegal",
                           "Cameroon", "Democratic Republic of Congo"],
    "North Africa & Middle East": ["Egypt", "Morocco", "Tunisia", "Jordan", "Lebanon", "Iraq"],
    "South America": ["Brazil", "Colombia", "Peru", "Chile", "Argentina", "Mexico",
                      "Ecuador", "Bolivia", "Paraguay", "Guatemala", "Honduras"],
    "Central Asia": ["Kazakhstan", "Uzbekistan", "Kyrgyzstan"],
}

ALL_LMIC_COUNTRIES = []
COUNTRY_TO_REGION = {}
for region, countries in LMIC_REGIONS.items():
    for country in countries:
        ALL_LMIC_COUNTRIES.append(country)
        COUNTRY_TO_REGION[country] = region


def get_or_create_source(session, name, url, access_method="api"):
    source = session.query(Source).filter_by(source_name=name).first()
    if not source:
        source = Source(
            source_name=name,
            source_type="lmic_digital_health",
            url=url,
            region="Global",
            country="",
            access_method=access_method,
            active=True,
        )
        session.add(source)
        session.commit()
        logger.info(f"Created source: {name}")
    return source


def doc_exists(session, external_id, source_id):
    if not external_id:
        return False
    return session.query(Document).filter_by(
        external_id=external_id, source_id=source_id
    ).first() is not None


def collect_clinicaltrials():
    """
    Collect digital health trials for mental/neurological conditions in LMIC countries
    using ClinicalTrials.gov API v2.
    """
    session = get_session(engine)
    total = 0

    source = get_or_create_source(
        session, "ClinicalTrials.gov LMIC DH",
        "https://clinicaltrials.gov", "api"
    )

    # Search queries combining digital health + mental/neuro + LMIC
    search_terms = [
        "digital health mental health developing country",
        "mHealth depression low income country",
        "telemedicine psychiatry Africa",
        "digital therapeutics neurological developing",
        "mobile health anxiety India",
        "eHealth mental health Latin America",
        "telepsychiatry low middle income",
        "digital intervention dementia developing",
        "app-based therapy depression Asia",
        "wearable neurological monitoring LMIC",
    ]

    try:
        for query in search_terms:
            logger.info(f"ClinicalTrials.gov: searching '{query}'")
            try:
                params = {
                    "query.term": query,
                    "pageSize": 20,
                    "format": "json",
                }
                resp = requests.get(
                    "https://clinicaltrials.gov/api/v2/studies",
                    params=params,
                    headers=BROWSER_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()

                studies = data.get("studies", [])
                count = 0

                for study in studies:
                    proto = study.get("protocolSection", {})
                    id_mod = proto.get("identificationModule", {})
                    status_mod = proto.get("statusModule", {})
                    desc_mod = proto.get("descriptionModule", {})
                    contact_mod = proto.get("contactsLocationsModule", {})

                    nct_id = id_mod.get("nctId", "")
                    title = id_mod.get("officialTitle", id_mod.get("briefTitle", ""))

                    if not nct_id or not title:
                        continue
                    if doc_exists(session, nct_id, source.source_id):
                        continue

                    # Extract country from locations
                    country = ""
                    locations = contact_mod.get("locations", [])
                    for loc in locations:
                        loc_country = loc.get("country", "")
                        if loc_country in ALL_LMIC_COUNTRIES:
                            country = loc_country
                            break

                    # Get dates
                    start_date_str = status_mod.get("startDateStruct", {}).get("date", "")
                    pub_date = None
                    if start_date_str:
                        try:
                            pub_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                        except ValueError:
                            try:
                                pub_date = datetime.strptime(start_date_str, "%Y-%m")
                            except ValueError:
                                pass
                    if not pub_date:
                        pub_date = datetime.utcnow()

                    summary = desc_mod.get("briefSummary", "")[:1000]
                    url = f"https://clinicaltrials.gov/study/{nct_id}"
                    status = status_mod.get("overallStatus", "")

                    doc = Document(
                        source_id=source.source_id,
                        external_id=nct_id,
                        title=title[:500],
                        url=url,
                        document_type="lmic_dh_project",
                        country=country,
                        publish_date=pub_date.date() if hasattr(pub_date, "date") else pub_date,
                        summary=f"[{status}] {summary}" if status else summary,
                        scraped_at=datetime.utcnow(),
                    )
                    session.add(doc)
                    count += 1

                session.commit()
                total += count
                logger.info(f"  Found {count} new studies")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                session.rollback()
                logger.error(f"Error searching '{query}': {e}")

    finally:
        session.close()

    return total


def collect_pubmed_lmic():
    """
    Collect PubMed articles on digital mental health in LMIC.
    Uses E-utilities API.
    """
    session = get_session(engine)
    total = 0

    source = get_or_create_source(
        session, "PubMed LMIC DH",
        "https://pubmed.ncbi.nlm.nih.gov", "api"
    )

    search_queries = [
        "digital mental health low middle income countries",
        "mHealth psychiatry developing countries",
        "telemedicine neurological disorders Africa Asia",
        "digital therapeutics depression India Brazil Kenya",
        "mobile app psychotherapy LMIC",
    ]

    try:
        for query in search_queries:
            logger.info(f"PubMed: searching '{query}'")
            try:
                # Step 1: Search
                search_resp = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                    params={
                        "db": "pubmed",
                        "term": query,
                        "retmax": 20,
                        "sort": "date",
                        "retmode": "json",
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                search_resp.raise_for_status()
                ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

                if not ids:
                    continue

                # Step 2: Fetch details
                fetch_resp = requests.get(
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                    params={
                        "db": "pubmed",
                        "id": ",".join(ids),
                        "retmode": "xml",
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                fetch_resp.raise_for_status()

                root = ET.fromstring(fetch_resp.content)
                count = 0

                for article in root.findall(".//PubmedArticle"):
                    pmid_el = article.find(".//PMID")
                    title_el = article.find(".//ArticleTitle")

                    if pmid_el is None or title_el is None:
                        continue

                    pmid = pmid_el.text
                    title = title_el.text or ""

                    if not pmid or not title:
                        continue
                    if doc_exists(session, pmid, source.source_id):
                        continue

                    # Extract abstract
                    abstract_parts = article.findall(".//AbstractText")
                    abstract = " ".join(
                        (a.text or "") for a in abstract_parts
                    )[:1000]

                    # Extract date
                    pub_date = None
                    date_el = article.find(".//PubDate")
                    if date_el is not None:
                        year = date_el.findtext("Year", "")
                        month = date_el.findtext("Month", "01")
                        day = date_el.findtext("Day", "01")
                        try:
                            month_num = month if month.isdigit() else str(
                                ["jan","feb","mar","apr","may","jun",
                                 "jul","aug","sep","oct","nov","dec"
                                ].index(month.lower()[:3]) + 1
                            )
                            pub_date = datetime(int(year), int(month_num), int(day))
                        except (ValueError, IndexError):
                            pass
                    if not pub_date:
                        pub_date = datetime.utcnow()

                    # Try to extract country from affiliations
                    country = ""
                    affiliations = article.findall(".//Affiliation")
                    for aff in affiliations:
                        aff_text = (aff.text or "").lower()
                        for c in ALL_LMIC_COUNTRIES:
                            if c.lower() in aff_text:
                                country = c
                                break
                        if country:
                            break

                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                    doc = Document(
                        source_id=source.source_id,
                        external_id=pmid,
                        title=title[:500],
                        url=url,
                        document_type="lmic_dh_project",
                        country=country,
                        publish_date=pub_date.date() if hasattr(pub_date, "date") else pub_date,
                        summary=abstract or None,
                        scraped_at=datetime.utcnow(),
                    )
                    session.add(doc)
                    count += 1

                session.commit()
                total += count
                logger.info(f"  Found {count} new articles")

                time.sleep(1)  # Rate limiting

            except Exception as e:
                session.rollback()
                logger.error(f"Error searching '{query}': {e}")

    finally:
        session.close()

    return total


def run():
    logger.info("=" * 60)
    logger.info("LMIC Digital Mental Health Collector — Run Started")
    logger.info("=" * 60)

    total = 0
    total += collect_clinicaltrials()
    total += collect_pubmed_lmic()

    logger.info("=" * 60)
    logger.info(f"Run complete. Total new entries: {total}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
