"""
Modelli SQLAlchemy per il database PostgreSQL.
Include tutte le tabelle: sources, keywords, documents, signals,
bundestag_items, gba_decisions, diga_apps, country_metrics, trends_metrics.
"""

from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, Date,
    DateTime, Float, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


# ── SOURCES ───────────────────────────────────────────────
class Source(Base):
    __tablename__ = "sources"

    source_id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(200), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # regulatory|scientific|trends|news|telecom|parliamentary|hta
    country = Column(String(100))
    region = Column(String(100))
    url = Column(Text)
    access_method = Column(String(30))  # api|rss|rss_scrape|html_scrape|fhir_api|dataset|pytrends
    refresh_hours = Column(Integer, default=24)
    trust_level = Column(Integer, default=3)  # 1-5
    active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime)

    documents = relationship("Document", back_populates="source")


# ── KEYWORDS ──────────────────────────────────────────────
class Keyword(Base):
    __tablename__ = "keywords"

    keyword_id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    level = Column(Integer, nullable=False)  # 1-5
    cluster = Column(String(100))
    disease_area = Column(String(100))
    geography_tag = Column(String(100))
    active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_keyword_text", "keyword"),
        Index("ix_keyword_level", "level"),
    )


# ── DOCUMENTS ─────────────────────────────────────────────
class Document(Base):
    __tablename__ = "documents"

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"), nullable=False)
    external_id = Column(String(200))  # PMID, trial_id, Drucksache nr, etc.
    title = Column(Text, nullable=False)
    url = Column(Text)
    publish_date = Column(Date)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    language = Column(String(10), default="en")
    full_text = Column(Text)
    summary = Column(Text)
    country = Column(String(100))
    document_type = Column(String(100))
    content_hash = Column(String(64))  # SHA256 per deduplicazione

    source = relationship("Source", back_populates="documents")
    flags = relationship("DocumentFlag", back_populates="document", uselist=False)
    signals = relationship("Signal", back_populates="document")
    bundestag_item = relationship("BundestagItem", back_populates="document", uselist=False)
    gba_decision = relationship("GBADecision", back_populates="document", uselist=False)

    __table_args__ = (
        Index("ix_doc_hash", "content_hash"),
        Index("ix_doc_source", "source_id"),
        Index("ix_doc_date", "publish_date"),
        UniqueConstraint("content_hash", name="uq_content_hash"),
    )


# ── DOCUMENT FLAGS ────────────────────────────────────────
class DocumentFlag(Base):
    __tablename__ = "document_flags"

    document_id = Column(Integer, ForeignKey("documents.document_id"), primary_key=True)
    is_regulatory = Column(Boolean, default=False)
    is_scientific = Column(Boolean, default=False)
    is_neuro = Column(Boolean, default=False)
    is_lmic = Column(Boolean, default=False)
    is_parliamentary = Column(Boolean, default=False)
    is_reimbursement = Column(Boolean, default=False)
    is_diga = Column(Boolean, default=False)

    document = relationship("Document", back_populates="flags")


# ── SIGNALS ───────────────────────────────────────────────
class Signal(Base):
    __tablename__ = "signals"

    signal_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.keyword_id"), nullable=False)
    relevance_score = Column(Float, default=0.0)
    novelty_score = Column(Float, default=0.0)
    impact_score = Column(Float, default=0.0)
    strategic_score = Column(Float, default=0.0)
    sentiment = Column(String(20), default="neutral")  # positive|negative|neutral|mixed
    urgency = Column(String(20), default="informational")  # immediate|short_term|medium_term|informational

    document = relationship("Document", back_populates="signals")
    keyword = relationship("Keyword")

    __table_args__ = (
        Index("ix_signal_doc", "document_id"),
        Index("ix_signal_strategic", "strategic_score"),
    )


# ── BUNDESTAG ITEMS ───────────────────────────────────────
class BundestagItem(Base):
    __tablename__ = "bundestag_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    dip_id = Column(Integer)
    drucksache_type = Column(String(100))
    wahlperiode = Column(Integer)
    institution = Column(String(10))  # BT | BR
    urheber = Column(Text)
    procedure_status = Column(String(100))
    committee = Column(String(200))
    health_relevance = Column(Float, default=0.0)

    document = relationship("Document", back_populates="bundestag_item")


# ── G-BA DECISIONS ────────────────────────────────────────
class GBADecision(Base):
    __tablename__ = "gba_decisions"

    decision_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    decision_type = Column(String(100))
    subcommittee = Column(String(200))
    topic_area = Column(String(200))
    effective_date = Column(Date)
    bmg_status = Column(String(50), default="pending")
    digital_health_flag = Column(Boolean, default=False)
    reimbursement_impact = Column(String(100), default="none")

    document = relationship("Document", back_populates="gba_decision")


# ── DIGA APPS ─────────────────────────────────────────────
class DIGAApp(Base):
    __tablename__ = "diga_apps"

    diga_id = Column(Integer, primary_key=True, autoincrement=True)
    bfarm_id = Column(String(100), unique=True)
    app_name = Column(String(200), nullable=False)
    manufacturer = Column(String(200))
    indication = Column(Text)
    listing_status = Column(String(50))  # permanent|provisional|delisted
    listing_date = Column(Date)
    risk_class = Column(String(10))
    price_eur = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    neuro_relevant = Column(Boolean, default=False)


# ── COUNTRY METRICS ───────────────────────────────────────
class CountryMetric(Base):
    __tablename__ = "country_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    internet_users_pct = Column(Float)
    mobile_connectivity_score = Column(Float)
    burden_neuro = Column(Float)
    aging_index = Column(Float)
    health_workforce_gap = Column(Float)
    digital_health_strategy = Column(Boolean, default=False)
    donor_activity_score = Column(Float)
    opportunity_score = Column(Float)  # Calculated composite

    __table_args__ = (
        UniqueConstraint("country", "year", name="uq_country_year"),
    )


# ── GOOGLE TRENDS METRICS ────────────────────────────────
class TrendsMetric(Base):
    __tablename__ = "trends_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    geography = Column(String(100), default="global")
    date = Column(Date, nullable=False)
    interest_score = Column(Integer)
    related_topic = Column(Text)
    is_rising = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_trends_kw_geo_date", "keyword", "geography", "date"),
    )


# ── ENTITIES ──────────────────────────────────────────────
class Entity(Base):
    """Entità estratte dai documenti: aziende, enti regolatori, tecnologie, persone."""
    __tablename__ = "entities"

    entity_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    canonical_name = Column(String(300))  # nome normalizzato per dedup
    entity_type = Column(String(50), nullable=False)  # company|regulator|technology|person|country|ngo|university|hospital
    country = Column(String(100))
    region = Column(String(100))
    website = Column(Text)
    description = Column(Text)
    first_seen_date = Column(Date, default=date.today)
    last_seen_date = Column(Date)
    confidence = Column(Float, default=0.5)  # 0-1, quanto siamo sicuri dell'estrazione
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relazioni
    mentions = relationship("EntityMention", back_populates="entity")
    source_relations = relationship(
        "EntityRelation",
        back_populates="source_entity",
        foreign_keys="EntityRelation.source_entity_id"
    )
    target_relations = relationship(
        "EntityRelation",
        back_populates="target_entity",
        foreign_keys="EntityRelation.target_entity_id"
    )

    __table_args__ = (
        Index("ix_entity_canonical", "canonical_name"),
        Index("ix_entity_type", "entity_type"),
        Index("ix_entity_country", "country"),
        UniqueConstraint("canonical_name", "entity_type", name="uq_entity_canonical_type"),
    )


# ── ENTITY MENTIONS (collega entità a documenti) ──────────
class EntityMention(Base):
    """Ogni volta che un'entità appare in un documento."""
    __tablename__ = "entity_mentions"

    mention_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey("entities.entity_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    context_text = Column(Text)  # estratto del testo attorno alla menzione
    mention_count = Column(Integer, default=1)  # quante volte appare nel documento
    sentiment = Column(String(20), default="neutral")
    role = Column(String(100))  # es. "approvatore", "investitore", "target"
    extracted_at = Column(DateTime, default=datetime.utcnow)

    entity = relationship("Entity", back_populates="mentions")
    document = relationship("Document")

    __table_args__ = (
        Index("ix_mention_entity", "entity_id"),
        Index("ix_mention_document", "document_id"),
        UniqueConstraint("entity_id", "document_id", name="uq_entity_doc"),
    )


# ── ENTITY RELATIONS (grafo di relazioni) ─────────────────
class EntityRelation(Base):
    """Relazioni tra entità: partnership, investimenti, acquisizioni, etc."""
    __tablename__ = "entity_relations"

    relation_id = Column(Integer, primary_key=True, autoincrement=True)
    source_entity_id = Column(Integer, ForeignKey("entities.entity_id"), nullable=False)
    target_entity_id = Column(Integer, ForeignKey("entities.entity_id"), nullable=False)
    relation_type = Column(String(50), nullable=False)  # partnership|investment|acquisition|approval|regulation|competitor|supplier|research
    direction = Column(String(20), default="directed")  # directed|bidirectional
    strength = Column(Float, default=0.5)  # 0-1, forza/frequenza della relazione
    confidence = Column(Float, default=0.5)  # 0-1, certezza dell'estrazione
    first_observed_date = Column(Date, default=date.today)
    last_observed_date = Column(Date)
    document_count = Column(Integer, default=1)  # in quanti documenti appare questa relazione
    evidence_document_ids = Column(Text)  # JSON array di document_id
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_entity = relationship(
        "Entity",
        back_populates="source_relations",
        foreign_keys=[source_entity_id]
    )
    target_entity = relationship(
        "Entity",
        back_populates="target_relations",
        foreign_keys=[target_entity_id]
    )

    __table_args__ = (
        Index("ix_relation_source", "source_entity_id"),
        Index("ix_relation_target", "target_entity_id"),
        Index("ix_relation_type", "relation_type"),
        UniqueConstraint("source_entity_id", "target_entity_id", "relation_type", name="uq_entity_relation"),
    )


# ── TECHNOLOGY RADAR ──────────────────────────────────────
class TechnologyRadar(Base):
    """Tecnologie emergenti monitorate nel radar."""
    __tablename__ = "technology_radar"

    tech_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    category = Column(String(100))  # ai_diagnostics|telemedicine|wearables|genomics|digital_therapeutics
    subcategory = Column(String(100))
    trl_level = Column(Integer, default=1)  # 1-9 Technology Readiness Level
    description = Column(Text)
    dual_use_potential = Column(Boolean, default=False)
    first_detected_date = Column(Date, default=date.today)
    last_signal_date = Column(Date)
    signal_count = Column(Integer, default=0)
    momentum_score = Column(Float, default=0.0)  # 0-100, trend
    hype_cycle_phase = Column(String(30))  # emerging|peak|trough|plateau|mature
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_tech_category", "category"),
        Index("ix_tech_momentum", "momentum_score"),
    )


# ── TECHNOLOGY SIGNALS (collega tecnologie a documenti) ──
class TechnologySignal(Base):
    """Segnali di adozione/regolamentazione per ogni tecnologia."""
    __tablename__ = "technology_signals"

    tech_signal_id = Column(Integer, primary_key=True, autoincrement=True)
    tech_id = Column(Integer, ForeignKey("technology_radar.tech_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.document_id"), nullable=False)
    signal_type = Column(String(50))  # regulatory|funding|partnership|approval|market_entry|research
    country = Column(String(100))
    impact_score = Column(Float, default=0.0)
    notes = Column(Text)
    extracted_at = Column(DateTime, default=datetime.utcnow)

    technology = relationship("TechnologyRadar")
    document = relationship("Document")

    __table_args__ = (
        Index("ix_techsignal_tech", "tech_id"),
        Index("ix_techsignal_doc", "document_id"),
        UniqueConstraint("tech_id", "document_id", "signal_type", name="uq_tech_signal"),
    )
    
# ── ENGINE & SESSION FACTORY ─────────────────────────────
def get_engine(database_url: str):
    """Crea engine SQLAlchemy."""
    return create_engine(database_url, echo=False, pool_pre_ping=True)


def get_session(engine):
    """Crea sessione DB."""
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(database_url: str):
    """Crea tutte le tabelle nel database."""
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)
    print(f"✓ Database inizializzato con {len(Base.metadata.tables)} tabelle:")
    for table_name in Base.metadata.tables:
        print(f"  - {table_name}")
    return engine
