from config.settings import DATABASE_URL
from db.models import get_engine, get_session, Source
engine = get_engine(DATABASE_URL)
session = get_session(engine)
existing = session.query(Source).filter_by(source_name="BfArM DiGA Directory").first()
if existing:
    print("Fonte esiste: id=" + str(existing.source_id))
else:
    s = Source(source_name="BfArM DiGA Directory", source_type="regulatory", country="Germany", region="Europe", url="https://diga.bfarm.de/de/verzeichnis", access_method="fhir_api", refresh_hours=168, trust_level=5, active=True)
    session.add(s)
    session.commit()
    print("Fonte creata: id=" + str(s.source_id))
session.close()
