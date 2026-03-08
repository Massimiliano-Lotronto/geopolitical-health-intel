"""
Collector per ClinicalTrials.gov via API v2.
Monitora trial su digital health, AI, neurodegenerative.
"""

from datetime import datetime, timedelta
from typing import List, Dict

from collectors.base import BaseCollector

CT_API_BASE = "https://clinicaltrials.gov/api/v2"

# Query di ricerca per ClinicalTrials.gov
CT_QUERIES = [
    # Digital health + AI interventions
    {
        "query.intr": "digital health OR artificial intelligence OR machine learning OR wearable OR mobile health",
        "query.cond": "NOT cancer",  # Evita flood di oncologia
        "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING",
    },
    # Neurodegenerative + digital
    {
        "query.cond": "dementia OR Alzheimer OR Parkinson OR cognitive impairment OR ALS",
        "query.intr": "digital OR remote monitoring OR wearable OR app OR biomarker OR EEG",
        "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING",
    },
    # Digital therapeutics
    {
        "query.intr": "digital therapeutics OR DiGA OR software medical device",
        "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING",
    },
]


class ClinicalTrialsCollector(BaseCollector):
    """Collector per ClinicalTrials.gov API v2."""

    def __init__(self, db_session):
        super().__init__("ClinicalTrials.gov", db_session)

    def fetch(self) -> List[Dict]:
        """Cerca trial e restituisce raw JSON."""
        all_studies = []

        for query_params in CT_QUERIES:
            try:
                params = {
                    **query_params,
                    "pageSize": 50,
                    "format": "json",
                    "fields": (
                        "NCTId,BriefTitle,OverallStatus,Phase,StartDate,"
                        "Condition,InterventionName,InterventionType,"
                        "LeadSponsorName,LocationCountry,StudyType,"
                        "EnrollmentCount,BriefSummary"
                    ),
                    "sort": "LastUpdatePostDate:desc",
                }

                # Filtra per data se abbiamo già fatto scraping
                if self.source.last_scraped_at:
                    min_date = self.source.last_scraped_at.strftime("%Y-%m-%d")
                    params["filter.lastUpdatePostDate"] = f"area[LastUpdatePostDate]RANGE[{min_date},MAX]"

                resp = self.http_get(f"{CT_API_BASE}/studies", params=params)
                data = resp.json()
                studies = data.get("studies", [])
                all_studies.extend(studies)

                self.logger.info(f"  Query trovati: {len(studies)} trial")
                self.rate_limit(0.5)

            except Exception as e:
                self.logger.warning(f"  Query fallita: {e}")

        return all_studies

    def parse(self, raw_studies: List[Dict]) -> List[Dict]:
        """Converte raw JSON in dizionari normalizzati."""
        parsed = []
        seen_ncts = set()

        for study in raw_studies:
            try:
                proto = study.get("protocolSection", {})
                ident = proto.get("identificationModule", {})
                status_mod = proto.get("statusModule", {})
                design = proto.get("designModule", {})
                desc = proto.get("descriptionModule", {})
                sponsor_mod = proto.get("sponsorCollaboratorsModule", {})
                contacts_mod = proto.get("contactsLocationsModule", {})
                arms_mod = proto.get("armsInterventionsModule", {})
                cond_mod = proto.get("conditionsModule", {})

                nct_id = ident.get("nctId", "")
                if not nct_id or nct_id in seen_ncts:
                    continue
                seen_ncts.add(nct_id)

                # Condizioni
                conditions = cond_mod.get("conditions", [])

                # Interventi
                interventions = []
                for interv in arms_mod.get("interventions", []):
                    interventions.append(interv.get("name", ""))

                # Paesi
                locations = contacts_mod.get("locations", [])
                countries = list(set(
                    loc.get("country", "") for loc in locations if loc.get("country")
                ))

                # Data inizio
                start_date = None
                start_info = status_mod.get("startDateStruct", {})
                if start_info.get("date"):
                    try:
                        start_date = datetime.strptime(
                            start_info["date"], "%Y-%m-%d"
                        ).date()
                    except ValueError:
                        try:
                            start_date = datetime.strptime(
                                start_info["date"], "%Y-%m"
                            ).date()
                        except ValueError:
                            pass

                # Fase
                phases = design.get("phases", [])
                phase_str = ", ".join(phases) if phases else "N/A"

                parsed.append({
                    "external_id": nct_id,
                    "title": ident.get("briefTitle", "Untitled"),
                    "url": f"https://clinicaltrials.gov/study/{nct_id}",
                    "publish_date": start_date,
                    "language": "en",
                    "full_text": desc.get("briefSummary", ""),
                    "country": countries[0] if countries else "",
                    "document_type": "clinical_trial",
                    "extra_data": {
                        "nct_id": nct_id,
                        "status": status_mod.get("overallStatus", ""),
                        "phase": phase_str,
                        "conditions": conditions,
                        "interventions": interventions,
                        "sponsor": sponsor_mod.get("leadSponsor", {}).get("name", ""),
                        "countries": countries,
                        "enrollment": design.get("enrollmentInfo", {}).get("count"),
                    }
                })

            except Exception as e:
                self.logger.warning(f"  Errore parsing trial: {e}")

        return parsed
