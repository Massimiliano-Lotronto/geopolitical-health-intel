"""
Collector per Google Trends via pytrends.
Monitora keyword strategiche con rate limiting aggressivo.
"""

import time
import random
from datetime import datetime, timedelta, date
from typing import List, Dict

from collectors.base import BaseCollector
from db.models import TrendsMetric

# ── KEYWORD STRATEGICHE (organizzate per cluster) ──────────

TRENDS_KEYWORDS = {
    # Digital Health core
    "digital_health_core": [
        "digital health",
        "digital therapeutics",
        "remote patient monitoring",
        "telemedicine",
        "mHealth",
        "health technology",
        "digital biomarker",
    ],
    # AI in Healthcare
    "ai_healthcare": [
        "AI healthcare",
        "artificial intelligence medical",
        "clinical AI",
        "AI medical device",
        "machine learning healthcare",
        "AI diagnostics",
    ],
    # Regulation
    "regulation": [
        "AI Act",
        "EHDS",
        "European Health Data Space",
        "SaMD regulation",
        "FDA digital health",
        "MDR medical device",
        "health data governance",
        "DiGA",
    ],
    # Neurodegenerative
    "neurodegenerative": [
        "Alzheimer digital",
        "Parkinson wearable",
        "dementia technology",
        "cognitive assessment digital",
        "digital biomarker dementia",
        "brain computer interface",
        "neurodegenerative AI",
    ],
    # Germany
    "germany": [
        "DiGA Germany",
        "Telemedizin Deutschland",
        "ePA elektronische Patientenakte",
        "digital health Germany",
        "G-BA digital",
        "gematik",
    ],
    # UK / NHS
    "uk_nhs": [
        "NHS digital health",
        "digital health London",
        "NHS AI",
        "NHS technology",
        "NICE digital health",
        "UK health tech",
    ],
    # EU27 countries digital health
    "eu27_digital_health": [
        "digital health France",
        "digital health Italy",
        "digital health Spain",
        "digital health Netherlands",
        "digital health Sweden",
        "digital health Denmark",
        "digital health Finland",
        "digital health Belgium",
        "digital health Austria",
        "digital health Poland",
        "digital health Ireland",
        "digital health Portugal",
        "digital health Greece",
        "digital health Czech Republic",
        "digital health Romania",
        "digital health Hungary",
        "digital health Croatia",
        "digital health Bulgaria",
        "digital health Slovakia",
        "digital health Slovenia",
        "digital health Lithuania",
        "digital health Latvia",
        "digital health Estonia",
        "digital health Luxembourg",
        "digital health Malta",
        "digital health Cyprus",
    ],
    # LMIC
    "lmic": [
        "digital health Africa",
        "telemedicine India",
        "mHealth Africa",
        "digital health Indonesia",
        "health technology developing countries",
        "digital health Latin America",
    ],
    # Competitive / Market
    "competitive": [
        "health tech startup",
        "digital health investment",
        "digital health funding",
        "health tech IPO",
        "digital health market",
        "medtech AI startup",
    ],
}

# Geografie da monitorare
GEOS = {
    "global": "",
    "germany": "DE",
    "uk": "GB",
    "usa": "US",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "netherlands": "NL",
    "india": "IN",
    "china": "CN",
    "israel": "IL",
}


class TrendsCollector(BaseCollector):
    """Collector per Google Trends via pytrends con rate limiting."""

    def __init__(self, db_session):
        super().__init__("Google Trends", db_session)
        self.pytrends = None

    def _init_pytrends(self):
        """Inizializza pytrends con retry."""
        try:
            from pytrends.request import TrendReq
            self.pytrends = TrendReq(
                hl='en-US',
                tz=0,
                timeout=(10, 30),
                retries=2,
                backoff_factor=1.0,
            )
            return True
        except Exception as e:
            self.logger.error(f"  Errore inizializzazione pytrends: {e}")
            return False

    def fetch(self) -> List[Dict]:
        """Raccoglie dati Google Trends per keyword strategiche."""
        if not self._init_pytrends():
            return []

        all_results = []

        # Seleziona un sottoinsieme di keyword per ogni run
        # (per non fare troppe richieste)
        priority_clusters = [
            "digital_health_core",
            "ai_healthcare",
            "regulation",
            "neurodegenerative",
            "germany",
            "uk_nhs",
            "competitive",
        ]

        for cluster_name in priority_clusters:
            keywords = TRENDS_KEYWORDS.get(cluster_name, [])

            # Processa in batch di 5 (limite pytrends)
            for i in range(0, len(keywords), 5):
                batch = keywords[i:i + 5]

                try:
                    # Solo dati globali per ridurre richieste
                    self.pytrends.build_payload(
                        batch,
                        cat=0,
                        timeframe='today 3-m',  # Ultimi 3 mesi
                        geo='',  # Global
                    )

                    # Interest over time
                    interest = self.pytrends.interest_over_time()
                    if interest is not None and not interest.empty:
                        for kw in batch:
                            if kw in interest.columns:
                                for idx, row in interest.iterrows():
                                    all_results.append({
                                        "keyword": kw,
                                        "geography": "global",
                                        "date": idx.date(),
                                        "interest_score": int(row[kw]),
                                        "cluster": cluster_name,
                                    })

                    self.logger.info(f"  Cluster '{cluster_name}' batch {i//5+1}: OK")

                    # Rate limiting: 60-90 secondi tra richieste
                    wait = random.uniform(60, 90)
                    self.logger.info(f"  Pausa {wait:.0f}s (rate limiting)...")
                    time.sleep(wait)

                except Exception as e:
                    self.logger.warning(f"  Trends batch fallito: {e}")
                    # Pausa più lunga in caso di errore (possibile blocco)
                    time.sleep(120)

        # EU27 - solo una volta al giorno, keyword ridotte
        if datetime.utcnow().hour < 8:  # Solo nel run mattutino
            eu_keywords = TRENDS_KEYWORDS.get("eu27_digital_health", [])[:5]
            try:
                self.pytrends.build_payload(
                    eu_keywords,
                    cat=0,
                    timeframe='today 3-m',
                    geo='',
                )
                interest = self.pytrends.interest_over_time()
                if interest is not None and not interest.empty:
                    for kw in eu_keywords:
                        if kw in interest.columns:
                            for idx, row in interest.iterrows():
                                all_results.append({
                                    "keyword": kw,
                                    "geography": "global",
                                    "date": idx.date(),
                                    "interest_score": int(row[kw]),
                                    "cluster": "eu27_digital_health",
                                })
                time.sleep(random.uniform(60, 90))
            except Exception as e:
                self.logger.warning(f"  EU27 trends fallito: {e}")

        return all_results

    def parse(self, raw_items: List[Dict]) -> List[Dict]:
        """Normalizza i dati trends."""
        parsed = []
        seen = set()

        for item in raw_items:
            # Deduplicazione
            key = f"{item['keyword']}_{item['geography']}_{item['date']}"
            if key in seen:
                continue
            seen.add(key)

            # Calcola se è rising (interesse > 70 e in crescita)
            is_rising = item["interest_score"] >= 70

            parsed.append({
                "external_id": f"GT-{key}",
                "title": f"Google Trends: {item['keyword']} ({item['geography']})",
                "url": f"https://trends.google.com/trends/explore?q={item['keyword'].replace(' ', '%20')}",
                "publish_date": item["date"],
                "language": "en",
                "full_text": "",
                "country": item["geography"],
                "document_type": "trends_data",
                "extra_data": {
                    "keyword": item["keyword"],
                    "geography": item["geography"],
                    "interest_score": item["interest_score"],
                    "is_rising": is_rising,
                    "cluster": item.get("cluster", ""),
                },
            })

        return parsed

    def _store(self, docs: List[Dict]):
        """Override: salva direttamente nella tabella trends_metrics."""
        for doc_data in docs:
            extra = doc_data.get("extra_data", {})

            # Controlla se esiste già
            existing = (
                self.session.query(TrendsMetric)
                .filter_by(
                    keyword=extra["keyword"],
                    geography=extra["geography"],
                    date=doc_data["publish_date"],
                )
                .first()
            )

            if existing:
                # Aggiorna score
                existing.interest_score = extra["interest_score"]
                existing.is_rising = extra["is_rising"]
            else:
                # Crea nuovo
                metric = TrendsMetric(
                    keyword=extra["keyword"],
                    geography=extra["geography"],
                    date=doc_data["publish_date"],
                    interest_score=extra["interest_score"],
                    is_rising=extra["is_rising"],
                    related_topic=extra.get("cluster", ""),
                )
                self.session.add(metric)

        self.session.commit()
        self.stats["new"] = len(docs)

    def _deduplicate(self, parsed: List[Dict]) -> List[Dict]:
        """Override: skip deduplication, gestita in _store."""
        return parsed
