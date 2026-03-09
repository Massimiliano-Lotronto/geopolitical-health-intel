"""
Collector per il DiGA Verzeichnis (BfArM) via FHIR API.
Monitora app sanitarie digitali rimborsabili in Germania.
Copre: nuove DiGA, cambi stato, delisting, prezzi, indicazioni.
"""

import json
import re
from datetime import datetime
from typing import List, Dict

import requests as req

from collectors.base import BaseCollector
from config.settings import DIGA_FHIR_TOKEN, DIGA_FHIR_BASE
from db.models import DIGAApp, Document

# Keywords neurodegenerative per flag
NEURO_KEYWORDS = [
    "demenz", "alzheimer", "parkinson", "neurodegenerat",
    "kognitiv", "neurolog", "gehirn", "gedächtnis",
    "dementia", "cognitive", "neurology", "brain",
    "depression", "angst", "schlaf", "sleep",
    "schmerz", "pain", "migräne", "migraine",
    "fatigue", "müdigkeit", "stress",
]

# Headers da browser
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, application/fhir+json",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


class DIGACollector(BaseCollector):
    """Collector per BfArM DiGA Directory via FHIR API."""

    def __init__(self, db_session):
        super().__init__("BfArM DiGA Directory", db_session)
        self.token = DIGA_FHIR_TOKEN
        self.base_url = DIGA_FHIR_BASE

    def _refresh_token(self):
        """Prova a ottenere un token aggiornato dalla pagina pubblica."""
        try:
            resp = req.get(
                "https://diga.bfarm.de/de/verzeichnis",
                headers=BROWSER_HEADERS,
                timeout=15,
            )
            if resp.status_code == 200:
                # Cerca il token nel meta tag
                match = re.search(r'"token"\s*:\s*"([a-f0-9-]+)"', resp.text)
                if match:
                    self.token = match.group(1)
                    self.logger.info(f"  Token aggiornato: {self.token[:20]}...")
                    return True
        except Exception as e:
            self.logger.warning(f"  Token refresh fallito: {e}")
        return False

    def fetch(self) -> List[Dict]:
        """Scarica tutte le DiGA dal FHIR API."""
        all_items = []

        # Prova prima con il token esistente, poi refresh se fallisce
        for attempt in range(2):
            try:
                headers = {
                    **BROWSER_HEADERS,
                    "Authorization": f"Bearer {self.token}",
                }

                # 1. Scarica HealthApp (informazioni generali sulle DiGA)
                resp = req.get(
                    f"{self.base_url}/DeviceDefinition",
                    params={
                        "_count": "1000",
                        "_profile": "https://fhir.bfarm.de/StructureDefinition/HealthApp",
                    },
                    headers=headers,
                    timeout=30,
                )

                if resp.status_code == 401 and attempt == 0:
                    self.logger.info("  Token scaduto, provo refresh...")
                    self._refresh_token()
                    continue

                if resp.status_code != 200:
                    self.logger.warning(f"  FHIR API HTTP {resp.status_code}")
                    return []

                data = resp.json()
                entries = data.get("entry", [])
                self.logger.info(f"  HealthApp entries: {len(entries)}")

                for entry in entries:
                    resource = entry.get("resource", {})
                    all_items.append(resource)

                # 2. Scarica CatalogEntry (stato listing, prezzi)
                resp2 = req.get(
                    f"{self.base_url}/CatalogEntry",
                    params={
                        "_count": "1000",
                        "_profile": "https://fhir.bfarm.de/StructureDefinition/HealthAppCatalogEntry",
                    },
                    headers=headers,
                    timeout=30,
                )

                if resp2.status_code == 200:
                    data2 = resp2.json()
                    catalog_entries = data2.get("entry", [])
                    self.logger.info(f"  CatalogEntry entries: {len(catalog_entries)}")

                    # Salva catalog entries per il parsing
                    for entry in catalog_entries:
                        resource = entry.get("resource", {})
                        resource["_resource_type"] = "CatalogEntry"
                        all_items.append(resource)

                break  # Successo, esci dal loop

            except Exception as e:
                self.logger.warning(f"  FHIR fetch fallito: {e}")
                if attempt == 0:
                    self._refresh_token()

        return all_items

    def parse(self, raw_items: List[Dict]) -> List[Dict]:
        """Converte FHIR resources in formato normalizzato."""
        parsed_apps = {}  # Raccolta dati per app
        catalog_data = {}  # Dati dal CatalogEntry

        for item in raw_items:
            resource_type = item.get("_resource_type", item.get("resourceType", ""))

            if resource_type == "CatalogEntry":
                # Estrai stato listing dal CatalogEntry
                ref = item.get("referencedItem", {}).get("reference", "")
                status = item.get("status", "")
                catalog_data[ref] = {
                    "listing_status": self._map_status(status),
                    "effective_date": item.get("validityPeriod", {}).get("start", ""),
                }
                continue

            # DeviceDefinition / HealthApp
            app_id = item.get("id", "")
            if not app_id:
                continue

            # Nome app
            app_name = ""
            for device_name in item.get("deviceName", []):
                if device_name.get("type") == "udi-label-name":
                    app_name = device_name.get("name", "")
                    break
            if not app_name:
                app_name = item.get("deviceName", [{}])[0].get("name", "Unknown") if item.get("deviceName") else "Unknown"

            # Produttore
            manufacturer = ""
            mfr = item.get("manufacturerString", "")
            if mfr:
                manufacturer = mfr
            elif item.get("manufacturerReference"):
                manufacturer = item.get("manufacturerReference", {}).get("display", "")

            # Indicazione
            indication = ""
            for note in item.get("note", []):
                text = note.get("text", "")
                if text:
                    indication = text[:500]
                    break

            # Classe rischio
            risk_class = ""
            for prop in item.get("property", []):
                code = prop.get("type", {}).get("coding", [{}])[0].get("code", "")
                if code == "riskClass":
                    risk_class = prop.get("valueCode", [{}])[0].get("code", "") if prop.get("valueCode") else ""
                    break

            # Check neuro relevance
            combined_text = (app_name + " " + indication + " " + manufacturer).lower()
            neuro_relevant = any(kw in combined_text for kw in NEURO_KEYWORDS)

            parsed_apps[app_id] = {
                "bfarm_id": app_id,
                "app_name": app_name,
                "manufacturer": manufacturer,
                "indication": indication,
                "risk_class": risk_class,
                "neuro_relevant": neuro_relevant,
            }

        # Merge con catalog data
        results = []
        for app_id, app_data in parsed_apps.items():
            ref_key = f"DeviceDefinition/{app_id}"
            cat = catalog_data.get(ref_key, {})

            listing_status = cat.get("listing_status", "unknown")
            listing_date = None
            date_str = cat.get("effective_date", "")
            if date_str:
                try:
                    listing_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                except ValueError:
                    pass

            # Crea documento per la tabella documents
            results.append({
                "external_id": f"DIGA-{app_id}",
                "title": f"DiGA: {app_data['app_name']} ({listing_status})",
                "url": f"https://diga.bfarm.de/de/verzeichnis/{app_id}",
                "publish_date": listing_date,
                "language": "de",
                "full_text": f"DiGA: {app_data['app_name']}. Hersteller: {app_data['manufacturer']}. Indikation: {app_data['indication']}. Risikoklasse: {app_data['risk_class']}. Status: {listing_status}.",
                "country": "Germany",
                "document_type": "diga_listing",
                "extra_data": {
                    **app_data,
                    "listing_status": listing_status,
                    "listing_date": listing_date,
                },
            })

        return results

    def _store_extra(self, doc: Document, doc_data: Dict):
        """Salva/aggiorna dati nella tabella diga_apps."""
        extra = doc_data.get("extra_data", {})
        bfarm_id = extra.get("bfarm_id", "")

        if not bfarm_id:
            return

        # Cerca se esiste già
        existing = (
            self.session.query(DIGAApp)
            .filter_by(bfarm_id=bfarm_id)
            .first()
        )

        if existing:
            # Aggiorna
            existing.app_name = extra.get("app_name", existing.app_name)
            existing.manufacturer = extra.get("manufacturer", existing.manufacturer)
            existing.indication = extra.get("indication", existing.indication)
            existing.listing_status = extra.get("listing_status", existing.listing_status)
            existing.risk_class = extra.get("risk_class", existing.risk_class)
            existing.neuro_relevant = extra.get("neuro_relevant", existing.neuro_relevant)
            existing.last_updated = datetime.utcnow()
        else:
            # Crea nuovo
            diga = DIGAApp(
                bfarm_id=bfarm_id,
                app_name=extra.get("app_name", ""),
                manufacturer=extra.get("manufacturer", ""),
                indication=extra.get("indication", ""),
                listing_status=extra.get("listing_status", "unknown"),
                listing_date=extra.get("listing_date"),
                risk_class=extra.get("risk_class", ""),
                neuro_relevant=extra.get("neuro_relevant", False),
                last_updated=datetime.utcnow(),
            )
            self.session.add(diga)

        # Aggiorna flags del documento
        if doc.flags:
            doc.flags.is_regulatory = True
            doc.flags.is_reimbursement = True
            doc.flags.is_diga = True
            if extra.get("neuro_relevant"):
                doc.flags.is_neuro = True

    def _map_status(self, fhir_status: str) -> str:
        """Mappa lo status FHIR allo status del nostro DB."""
        mapping = {
            "active": "permanent",
            "draft": "provisional",
            "retired": "delisted",
            "unknown": "unknown",
        }
        return mapping.get(fhir_status, "unknown")
