"""
Inizializza il database e popola le tabelle sources e keywords dal YAML.
Eseguire una sola volta: python -m db.init_db
"""

import yaml
from pathlib import Path

from config.settings import DATABASE_URL
from db.models import init_db, get_engine, get_session, Source, Keyword


def seed_sources(session, yaml_path: str):
    """Popola tabella sources dal file YAML."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    count = 0
    for src in data.get("sources", []):
        existing = session.query(Source).filter_by(source_name=src["name"]).first()
        if existing:
            continue

        source = Source(
            source_name=src["name"],
            source_type=src["source_type"],
            country=src.get("country"),
            region=src.get("region"),
            url=src.get("url"),
            access_method=src.get("access_method"),
            refresh_hours=src.get("refresh_hours", 24),
            trust_level=src.get("trust_level", 3),
            active=True,
        )
        session.add(source)
        count += 1

    session.commit()
    print(f"✓ {count} nuove fonti aggiunte (totale: {session.query(Source).count()})")


def seed_keywords(session, yaml_path: str):
    """Popola tabella keywords dal file YAML."""
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    level_map = {
        "level_1_macro": 1,
        "level_2_regulatory": 2,
        "level_3_neuro": 3,
        "level_4_lmic": 4,
        "level_5_germany": 5,
    }

    count = 0
    for section_key, level in level_map.items():
        for kw in data.get(section_key, []):
            existing = session.query(Keyword).filter_by(
                keyword=kw["keyword"], level=level
            ).first()
            if existing:
                continue

            keyword = Keyword(
                keyword=kw["keyword"],
                level=level,
                cluster=kw.get("cluster"),
                disease_area=kw.get("disease_area"),
                geography_tag=kw.get("geography_tag"),
                active=True,
            )
            session.add(keyword)
            count += 1

    session.commit()
    print(f"✓ {count} nuove keyword aggiunte (totale: {session.query(Keyword).count()})")


def main():
    print("=" * 60)
    print("GEOPOLITICAL HEALTH INTEL - Database Initialization")
    print("=" * 60)
    print(f"\nDatabase: {DATABASE_URL[:50]}...")

    # 1. Crea tabelle
    engine = init_db(DATABASE_URL)

    # 2. Seed dati
    session = get_session(engine)
    config_dir = Path(__file__).parent.parent / "config"

    print("\n── Seeding fonti ──")
    seed_sources(session, config_dir / "sources.yaml")

    print("\n── Seeding keywords ──")
    seed_keywords(session, config_dir / "keywords.yaml")

    session.close()
    print("\n✓ Inizializzazione completata!")


if __name__ == "__main__":
    main()
