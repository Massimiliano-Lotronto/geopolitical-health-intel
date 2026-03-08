"""
Collector per PubMed via NCBI E-utilities API.
Esegue ricerche su keyword predefinite e scarica abstract.
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict

from collectors.base import BaseCollector
from config.settings import NCBI_API_KEY, NCBI_EMAIL, NCBI_RATE_LIMIT

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Query PubMed predefinite (combinate con OR)
PUBMED_QUERIES = [
    # Digital health + AI
    '("digital health" OR "artificial intelligence" OR "machine learning") '
    'AND (healthcare OR "medical device" OR clinical) '
    'AND (regulation OR governance OR validation OR policy)',

    # Neurodegenerative + digital
    '(dementia OR Alzheimer* OR Parkinson*) '
    'AND ("digital biomarker" OR "remote monitoring" OR wearable OR EEG '
    'OR "brain-computer interface" OR "cognitive assessment")',

    # Digital therapeutics + reimbursement
    '("digital therapeutics" OR "digital health application" OR DiGA) '
    'AND (reimbursement OR "health technology assessment" OR HTA OR approval)',
]


class PubMedCollector(BaseCollector):
    """Collector per PubMed / NCBI E-utilities."""

    def __init__(self, db_session):
        super().__init__("PubMed", db_session)
        self.api_params = {}
        # Only use API key if it's a real value (not the placeholder)
        if NCBI_API_KEY and NCBI_API_KEY != "your_ncbi_api_key_here":
            self.api_params["api_key"] = NCBI_API_KEY
        if NCBI_EMAIL and NCBI_EMAIL != "your_email@example.com":
            self.api_params["email"] = NCBI_EMAIL

    def fetch(self) -> List[str]:
        """Cerca su PubMed e restituisce lista di PMID."""
        all_pmids = set()

        # Calcola data minima (ultimi 7 giorni o dall'ultimo scrape)
        if self.source.last_scraped_at:
            min_date = self.source.last_scraped_at.strftime("%Y/%m/%d")
        else:
            min_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y/%m/%d")

        for query in PUBMED_QUERIES:
            try:
                # ESearch: trova PMID
                params = {
                    **self.api_params,
                    "db": "pubmed",
                    "term": query,
                    "retmax": 100,
                    "sort": "date",
                    "mindate": min_date,
                    "maxdate": "3000",
                    "datetype": "pdat",
                    "retmode": "xml",
                }
                resp = self.http_get(f"{EUTILS_BASE}/esearch.fcgi", params=params)
                root = ET.fromstring(resp.text)

                pmids = [id_elem.text for id_elem in root.findall(".//Id")]
                all_pmids.update(pmids)
                self.logger.info(f"  Query trovati: {len(pmids)} PMID")

                self.rate_limit(1.0 / NCBI_RATE_LIMIT)

            except Exception as e:
                self.logger.warning(f"  Query fallita: {e}")
                continue

        return list(all_pmids)

    def parse(self, pmids: List[str]) -> List[Dict]:
        """Scarica dettagli per ogni PMID con EFetch."""
        if not pmids:
            return []

        parsed = []

        # EFetch in batch di 50
        for i in range(0, len(pmids), 50):
            batch = pmids[i:i + 50]

            try:
                params = {
                    **self.api_params,
                    "db": "pubmed",
                    "id": ",".join(batch),
                    "retmode": "xml",
                    "rettype": "abstract",
                }
                resp = self.http_get(f"{EUTILS_BASE}/efetch.fcgi", params=params)
                root = ET.fromstring(resp.text)

                for article in root.findall(".//PubmedArticle"):
                    try:
                        parsed.append(self._parse_article(article))
                    except Exception as e:
                        self.logger.warning(f"  Errore parsing articolo: {e}")

                self.rate_limit(1.0 / NCBI_RATE_LIMIT)

            except Exception as e:
                self.logger.warning(f"  EFetch batch fallito: {e}")

        return parsed

    def _parse_article(self, article) -> Dict:
        """Estrae campi da un singolo PubmedArticle XML."""
        medline = article.find(".//MedlineCitation")
        pmid = medline.findtext(".//PMID", "")
        art = medline.find(".//Article")

        # Titolo
        title = art.findtext(".//ArticleTitle", "Untitled")

        # Abstract
        abstract_parts = []
        for abs_text in art.findall(".//Abstract/AbstractText"):
            label = abs_text.get("Label", "")
            text = abs_text.text or ""
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = " ".join(abstract_parts)

        # Data pubblicazione
        pub_date = None
        date_elem = art.find(".//ArticleDate")
        if date_elem is None:
            date_elem = art.find(".//Journal/JournalIssue/PubDate")
        if date_elem is not None:
            year = date_elem.findtext("Year")
            month = date_elem.findtext("Month", "01")
            day = date_elem.findtext("Day", "01")
            if year:
                try:
                    # Gestisci mesi come "Jan", "Feb" etc.
                    if not month.isdigit():
                        month_map = {
                            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
                        }
                        month = month_map.get(month[:3], "01")
                    pub_date = datetime.strptime(
                        f"{year}-{month}-{day}", "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pub_date = None

        # Journal
        journal = art.findtext(".//Journal/Title", "")

        # Autori
        authors = []
        for author in art.findall(".//AuthorList/Author"):
            last = author.findtext("LastName", "")
            fore = author.findtext("ForeName", "")
            if last:
                authors.append(f"{last} {fore}".strip())

        # Paese (dalla prima affiliazione)
        country = ""
        affiliation = art.findtext(".//AffiliationInfo/Affiliation", "")
        if affiliation:
            # Prendi l'ultima parte dell'affiliazione (solitamente il paese)
            parts = [p.strip().rstrip(".") for p in affiliation.split(",")]
            if parts:
                country = parts[-1]

        return {
            "external_id": f"PMID:{pmid}",
            "title": title,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "publish_date": pub_date,
            "language": "en",
            "full_text": abstract,
            "country": country,
            "document_type": "journal_article",
            "extra_data": {
                "pmid": pmid,
                "journal": journal,
                "authors": authors[:5],  # Max 5 autori
            }
        }
