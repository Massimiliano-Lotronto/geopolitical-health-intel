"""Run this to add MSF South Sudan projects to the database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from config.settings import DATABASE_URL
from db.models import get_engine, get_session, Document, Source

engine = get_engine(DATABASE_URL)
session = get_session(engine)

# Get or create MSF source
source = session.query(Source).filter_by(source_name="MSF South Sudan").first()
if not source:
    source = Source(
        source_name="MSF South Sudan",
        source_type="lmic_digital_health",
        url="https://www.msf.org/south-sudan",
        region="Sub-Saharan Africa",
        country="South Sudan",
        access_method="manual",
        active=True,
    )
    session.add(source)
    session.commit()
    print("Created source: MSF South Sudan")

projects = [
    {
        "title": "MSF Mental Health Support Program - Bentiu, Unity State",
        "summary": "Mental health and psychosocial support for displaced populations in Bentiu camp and state hospital. Individual and group counseling for conflict-related trauma, depression, and anxiety.",
        "date": "2024-01-01",
    },
    {
        "title": "MSF Mental Health Services - Malakal, Upper Nile",
        "summary": "Psychiatric care and psychological support for conflict-affected communities. Integration of mental health into primary healthcare services.",
        "date": "2024-03-01",
    },
    {
        "title": "MSF AI Snake Species Identification - Twic and Abyei",
        "summary": "Innovative AI tool developed with University of Geneva for snake species identification. Piloted in Twic and Abyei to improve clinical management of snakebites using digital technology.",
        "date": "2024-06-01",
    },
    {
        "title": "MSF Academy for Healthcare - South Sudan",
        "summary": "Training program addressing critical shortage of qualified healthcare professionals. Includes digital learning tools and e-health training modules for local health workers.",
        "date": "2024-01-01",
    },
    {
        "title": "MSF Emergency Mental Health Response - Jonglei State",
        "summary": "Emergency psychological support and trauma counseling for communities affected by violence in Lankien and Pieri. Addressing PTSD, depression, and community-level psychological distress.",
        "date": "2025-12-01",
    },
    {
        "title": "MSF Pediatric Healthcare Transition - Bentiu State Hospital",
        "summary": "48-bed pediatric unit opened in collaboration with Ministry of Health. Includes digital patient record keeping and telemedicine consultations.",
        "date": "2024-10-01",
    },
    {
        "title": "MSF Community Health Worker Program - South Sudan",
        "summary": "Mobile health worker network providing primary care and mental health screening in remote areas. Using mHealth tools for data collection and patient referral.",
        "date": "2024-04-01",
    },
    {
        "title": "MSF Malaria and Malnutrition Response with Digital Surveillance - Aweil",
        "summary": "Disease surveillance using digital tools for malaria and malnutrition monitoring. Real-time data collection and reporting to coordinate emergency response.",
        "date": "2024-07-01",
    },
    {
        "title": "MSF Reproductive Health and Psychosocial Support - Juba",
        "summary": "Integrated reproductive health services with mental health counseling for survivors of sexual violence. Psychosocial support programs in Juba PoC sites.",
        "date": "2024-02-01",
    },
    {
        "title": "MSF Water and Health Infrastructure - Multiple Locations",
        "summary": "Clean water provision and health infrastructure support across 12 project sites. Digital monitoring of water quality and disease outbreak early warning systems.",
        "date": "2024-05-01",
    },
]

count = 0
for p in projects:
    existing = session.query(Document).filter_by(title=p["title"]).first()
    if not existing:
        doc = Document(
            source_id=source.source_id,
            title=p["title"],
            url="https://www.msf.org/south-sudan",
            document_type="lmic_dh_project",
            country="South Sudan",
            publish_date=datetime.strptime(p["date"], "%Y-%m-%d").date(),
            summary=p["summary"],
            scraped_at=datetime.utcnow(),
        )
        session.add(doc)
        count += 1

session.commit()
print(f"Added {count} MSF South Sudan projects")
session.close()
