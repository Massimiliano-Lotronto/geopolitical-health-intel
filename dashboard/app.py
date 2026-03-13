"""
Streamlit Dashboard - Geopolitical Health Intelligence
8 pagine: Overview, Regulatory, Bundestag/G-BA, Science, Trends, Neuro, LMIC, Telecom
Light Elegant / Editorial Design
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc, text

# Deve essere la prima chiamata Streamlit
st.set_page_config(
    page_title="Geopolitical Health Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL
from db.models import (
    get_engine, get_session,
    Document, Signal, Source, Keyword, DocumentFlag,
    BundestagItem, GBADecision, DIGAApp, TrendsMetric, CountryMetric,
)


# ── DB Connection ─────────────────────────────────────────
@st.cache_resource
def get_db():
    engine = get_engine(DATABASE_URL)
    return engine


def get_session_cached():
    return get_session(get_db())


# ══════════════════════════════════════════════════════════
# EDITORIAL DESIGN SYSTEM
# ══════════════════════════════════════════════════════════

# Plotly template
PLOTLY_TEMPLATE = dict(
    layout=go.Layout(
        font=dict(family="Source Sans Pro, sans-serif", color="#2D3436"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=["#0D2B45", "#1A6B8A", "#2E9E6B", "#E8A838", "#D35C5C",
                   "#7B68AE", "#4DACBD", "#E07B53", "#5B8C5A", "#C97B84"],
        title=dict(font=dict(size=16, color="#2D3436"), x=0, xanchor="left"),
        xaxis=dict(gridcolor="#E8E8E8", linecolor="#CCCCCC", zerolinecolor="#E8E8E8"),
        yaxis=dict(gridcolor="#E8E8E8", linecolor="#CCCCCC", zerolinecolor="#E8E8E8"),
        margin=dict(t=40, b=30, l=40, r=20),
        legend=dict(font=dict(size=11)),
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#CCCCCC"),
    )
)

st.markdown("""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@300;400;600;700&family=Playfair+Display:wght@600;700&family=JetBrains+Mono:wght@400&display=swap');

    /* ── Global ── */
    html, body, [class*="css"] {
        font-family: 'Source Sans Pro', sans-serif;
        color: #2D3436;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #FAFAF8;
        border-right: 1px solid #E8E4DF;
    }
        /* ── Sidebar Navigation Tabs ── */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 0px;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {
        display: none;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.92rem;
        font-weight: 400;
        color: #7F8C8D;
        padding: 0.55rem 0.9rem;
        margin: 1px 0;
        border-left: 3px solid transparent;
        border-radius: 0 6px 6px 0;
        transition: all 0.15s ease;
        cursor: pointer;
        background: transparent;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        color: #0D2B45;
        background: rgba(13,43,69,0.04);
        border-left-color: #B0BEC5;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        color: #0D2B45;
        font-weight: 600;
        background: rgba(26,107,138,0.08);
        border-left-color: #1A6B8A;
    }

        /* ── Page Headers ── */
    .ed-header {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #0D2B45;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .ed-subtitle {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.95rem;
        font-weight: 300;
        color: #7F8C8D;
        margin-bottom: 1.5rem;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .ed-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #0D2B45, #1A6B8A, transparent);
        margin: 0.3rem 0 1.5rem 0;
    }

    /* ── KPI Cards ── */
    .ed-kpi {
        background: #FFFFFF;
        border: 1px solid #E8E4DF;
        border-radius: 6px;
        padding: 1.3rem 1rem;
        text-align: center;
        transition: box-shadow 0.2s;
    }
    .ed-kpi:hover {
        box-shadow: 0 2px 12px rgba(13,43,69,0.08);
    }
    .ed-kpi-value {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-weight: 700;
        color: #0D2B45;
        line-height: 1.1;
    }
    .ed-kpi-label {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        color: #95A5A6;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.3rem;
    }
    .ed-kpi-delta-up {
        font-size: 0.82rem; color: #2E9E6B; font-weight: 600;
    }
    .ed-kpi-delta-down {
        font-size: 0.82rem; color: #D35C5C; font-weight: 600;
    }

    /* ── Alert Cards ── */
    .ed-alert {
        background: #FFFFFF;
        border-left: 3px solid #E8A838;
        padding: 0.9rem 1rem;
        margin: 0.4rem 0;
        border-radius: 0 4px 4px 0;
        font-size: 0.9rem;
        transition: background 0.15s;
    }
    .ed-alert:hover {
        background: #FDFBF6;
    }
    .ed-alert-high {
        border-left-color: #D35C5C;
    }
    .ed-alert strong {
        color: #2D3436;
        font-weight: 600;
    }
    .ed-alert small {
        color: #95A5A6;
    }
    .ed-alert a {
        color: #1A6B8A;
        text-decoration: none;
        font-weight: 600;
    }

    /* ── Section Headers ── */
    .ed-section {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 1.05rem;
        font-weight: 600;
        color: #0D2B45;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 1.5rem 0 0.8rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid #E8E4DF;
    }

    /* ── DataFrames ── */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E8E4DF;
        border-radius: 6px;
    }

    /* ── Metrics override ── */
    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E8E4DF;
        padding: 12px;
        border-radius: 6px;
    }
    div[data-testid="stMetric"] label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #95A5A6;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        font-size: 0.88rem;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        color: #7F8C8D;
    }
    .stTabs [aria-selected="true"] {
        color: #0D2B45;
        border-bottom-color: #0D2B45;
    }

    /* ── Expander ── */
    .streamlit-expanderHeader {
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 600;
        color: #4A4A4A;
    }

    /* ── Footer ── */
    .ed-footer {
        font-size: 0.75rem;
        color: #B0B0B0;
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #E8E4DF;
        margin-top: 3rem;
    }

    /* ── Hide Streamlit branding ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="text-align:center; padding: 0.5rem 0 0.8rem 0;">
            <span style="font-size: 2.2rem;">🌍</span><br>
            <span style="font-family: 'Playfair Display', serif; font-size: 1.3rem;
                         color: #0D2B45; font-weight: 700; letter-spacing: -0.02em;">
                Health Intel
            </span><br>
            <span style="font-size: 0.7rem; color: #95A5A6; text-transform: uppercase;
                         letter-spacing: 0.1em;">
                Geopolitical Intelligence
            </span>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border:none; height:1px; background:#E8E4DF; margin:0.5rem 0;'>",
                unsafe_allow_html=True)

    page = st.radio(
        "Navigazione",
        [
            "📊 Executive Overview",
            "⚖️ Regulatory Radar",
            "🏛️ Bundestag & G-BA",
            "🔬 Science & Trials",
            "📈 Market Trends",
            "🧠 Neurodegenerative Focus",
            "🌍 LMIC Opportunity",
            "📡 Telecom Readiness",
            "⚠️ Cyber Attack Radar",
        ],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border:none; height:1px; background:#E8E4DF; margin:0.8rem 0;'>",
                unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.78rem; font-weight:600; color:#95A5A6; '
                'text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;">'
                'Filters</p>', unsafe_allow_html=True)

    date_range = st.date_input(
        "Periodo",
        value=(datetime.now() - timedelta(days=30), datetime.now()),
        max_value=datetime.now(),
    )

    region_filter = st.multiselect(
        "Regione",
        ["Europe", "North America", "Asia", "Middle East", "Global", "LMIC"],
        default=[],
    )

    source_type_filter = st.multiselect(
        "Tipo fonte",
        ["regulatory", "scientific", "parliamentary", "hta", "trends", "telecom"],
        default=[],
    )

    st.markdown("<hr style='border:none; height:1px; background:#E8E4DF; margin:0.8rem 0;'>",
                unsafe_allow_html=True)

    st.markdown(f"""
        <div style="font-size: 0.72rem; color: #B0B0B0; line-height: 1.6;">
            Last update: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br>
            Python · PostgreSQL · Streamlit
        </div>
    """, unsafe_allow_html=True)


# ── Helper Functions ──────────────────────────────────────
def query_documents(session, filters=None, limit=100):
    """Query documenti con filtri opzionali."""
    q = session.query(Document).join(Source)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        q = q.filter(Document.publish_date >= date_range[0])
        q = q.filter(Document.publish_date <= date_range[1])
    if region_filter:
        q = q.filter(Source.region.in_(region_filter))
    if source_type_filter:
        q = q.filter(Source.source_type.in_(source_type_filter))
    if filters:
        for f in filters:
            q = q.filter(f)
    return q.order_by(desc(Document.publish_date)).limit(limit).all()


def page_header(title, subtitle=""):
    """Render editorial page header."""
    st.markdown(f'<div class="ed-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ed-subtitle">{subtitle}</div>', unsafe_allow_html=True)
    st.markdown('<div class="ed-divider"></div>', unsafe_allow_html=True)


def section_header(title):
    """Render editorial section header."""
    st.markdown(f'<div class="ed-section">{title}</div>', unsafe_allow_html=True)


def kpi_card(label, value, delta=None):
    """Crea KPI card HTML editoriale."""
    delta_html = ""
    if delta is not None:
        css = "ed-kpi-delta-up" if delta >= 0 else "ed-kpi-delta-down"
        arrow = "↑" if delta >= 0 else "↓"
        delta_html = f'<div class="{css}">{arrow} {abs(delta)}</div>'

    st.markdown(f"""
    <div class="ed-kpi">
        <div class="ed-kpi-value">{value}</div>
        <div class="ed-kpi-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def alert_card(title, source, score, url="", high=False):
    """Crea alert card HTML editoriale."""
    css_class = "ed-alert ed-alert-high" if high else "ed-alert"
    link = f' · <a href="{url}" target="_blank">View →</a>' if url else ""
    st.markdown(f"""
    <div class="{css_class}">
        <strong>{title[:80]}{'…' if len(title) > 80 else ''}</strong><br>
        <small>{source} · Score {score:.1f}{link}</small>
    </div>
    """, unsafe_allow_html=True)


def style_plotly(fig, height=420):
    """Apply editorial template to plotly figure."""
    fig.update_layout(
        font=dict(family="Source Sans Pro, sans-serif", color="#2D3436", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#F0EFEC", linecolor="#E8E4DF", zerolinecolor="#F0EFEC"),
        yaxis=dict(gridcolor="#F0EFEC", linecolor="#E8E4DF", zerolinecolor="#F0EFEC"),
        margin=dict(t=40, b=30, l=40, r=20),
        height=height,
        hoverlabel=dict(bgcolor="white", font_size=12, bordercolor="#E8E4DF"),
    )
    return fig


def page_footer():
    """Render page footer."""
    st.markdown("""
    <div class="ed-footer">
        Geopolitical Health Intelligence · Data refreshed every 12h via GitHub Actions
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# PAGE 1: EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════
if page == "📊 Executive Overview":
    page_header("Executive Overview", "Real-time intelligence summary across all monitored sources")

    session = get_session_cached()
    try:
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)

        total_docs = session.query(func.count(Document.document_id)).scalar() or 0
        new_docs_week = session.query(func.count(Document.document_id)).filter(
            Document.scraped_at >= week_ago).scalar() or 0
        total_signals = session.query(func.count(Signal.signal_id)).scalar() or 0
        high_signals = session.query(func.count(Signal.signal_id)).filter(
            Signal.strategic_score >= 7.0).scalar() or 0

        col1, col2, col3, col4 = st.columns(4)
        with col1: kpi_card("Total Documents", f"{total_docs:,}")
        with col2: kpi_card("New This Week", f"{new_docs_week:,}")
        with col3: kpi_card("Signals Detected", f"{total_signals:,}")
        with col4: kpi_card("High Priority", f"{high_signals}")

        st.markdown("<br>", unsafe_allow_html=True)

        col_left, col_right = st.columns([3, 2])

        with col_left:
            section_header("Strategic Alerts")
            top_signals = (
                session.query(Signal, Document, Source)
                .join(Document, Signal.document_id == Document.document_id)
                .join(Source, Document.source_id == Source.source_id)
                .filter(Signal.strategic_score >= 5.0)
                .order_by(desc(Signal.strategic_score))
                .limit(10)
                .all()
            )
            if top_signals:
                for signal, doc, source in top_signals:
                    alert_card(
                        doc.title, source.source_name,
                        signal.strategic_score, doc.url,
                        high=(signal.strategic_score >= 8.0)
                    )
            else:
                st.info("No high-impact signals detected. Run the pipeline to collect data.")

        with col_right:
            section_header("Documents by Source")
            docs_by_source = (
                session.query(Source.source_name, func.count(Document.document_id))
                .join(Document, Source.source_id == Document.source_id)
                .group_by(Source.source_name)
                .order_by(desc(func.count(Document.document_id)))
                .all()
            )
            if docs_by_source:
                df_sources = pd.DataFrame(docs_by_source, columns=["Source", "Count"])
                fig = px.pie(df_sources, values="Count", names="Source",
                             color_discrete_sequence=["#0D2B45", "#1A6B8A", "#2E9E6B",
                                                       "#E8A838", "#D35C5C", "#7B68AE",
                                                       "#4DACBD", "#E07B53"])
                fig.update_layout(height=350, margin=dict(t=10, b=10),
                                  font=dict(family="Source Sans Pro", size=11),
                                  paper_bgcolor="rgba(0,0,0,0)")
                fig.update_traces(textfont_size=11, textposition="inside")
                st.plotly_chart(fig, use_container_width=True)

            section_header("Top Countries")
            docs_by_country = (
                session.query(Document.country, func.count(Document.document_id))
                .filter(Document.country.isnot(None), Document.country != "")
                .group_by(Document.country)
                .order_by(desc(func.count(Document.document_id)))
                .limit(10)
                .all()
            )
            if docs_by_country:
                df_countries = pd.DataFrame(docs_by_country, columns=["Country", "Count"])
                fig = px.bar(df_countries, x="Count", y="Country", orientation="h",
                             color_discrete_sequence=["#1A6B8A"])
                style_plotly(fig, height=280)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Make sure the database is initialized. Run: `python main.py --init-db`")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 2: REGULATORY RADAR
# ══════════════════════════════════════════════════════════
elif page == "⚖️ Regulatory Radar":
    page_header("Regulatory Radar", "Tracking regulatory developments in digital health across jurisdictions")

    session = get_session_cached()
    try:
        reg_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .join(DocumentFlag, Document.document_id == DocumentFlag.document_id)
            .filter(DocumentFlag.is_regulatory == True)
            .order_by(desc(Document.publish_date))
            .limit(50)
            .all()
        )

        if reg_docs:
            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:80],
                "Source": s.source_name,
                "Country": d.country,
                "Type": d.document_type,
                "URL": d.url or "",
            } for d, s in reg_docs])

            st.dataframe(df, use_container_width=True, height=500,
                         column_config={"URL": st.column_config.LinkColumn("Link")},
                         hide_index=True)

            if not df.empty and "Date" in df.columns:
                df_timeline = df.dropna(subset=["Date"])
                if not df_timeline.empty:
                    section_header("Regulatory Timeline")
                    fig = px.scatter(df_timeline, x="Date", y="Country", color="Source",
                                    hover_data=["Title"], size_max=10,
                                    color_discrete_sequence=["#0D2B45", "#1A6B8A", "#2E9E6B",
                                                              "#E8A838", "#D35C5C"])
                    style_plotly(fig, height=400)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No regulatory documents found. Run the pipeline to collect data.")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 3: BUNDESTAG & G-BA
# ══════════════════════════════════════════════════════════
elif page == "🏛️ Bundestag & G-BA":
    page_header("Bundestag & G-BA Monitor", "German parliamentary and HTA body tracking for digital health")

    session = get_session_cached()
    try:
        tab1, tab2, tab3 = st.tabs(["Bundestag", "G-BA Decisions", "DiGA Directory"])

        with tab1:
            bt_items = (
                session.query(BundestagItem, Document)
                .join(Document)
                .order_by(desc(Document.publish_date))
                .limit(50)
                .all()
            )
            if bt_items:
                col1, col2 = st.columns(2)
                with col1: kpi_card("Bundestag Documents", str(len(bt_items)))
                with col2:
                    high_rel = len([b for b, d in bt_items if b.health_relevance >= 7.0])
                    kpi_card("High Health Relevance", str(high_rel))

                st.markdown("<br>", unsafe_allow_html=True)

                df_bt = pd.DataFrame([{
                    "Date": d.publish_date,
                    "Title": d.title[:70],
                    "Type": b.drucksache_type,
                    "Institution": b.institution,
                    "Health Score": f"{b.health_relevance:.1f}",
                    "Author": (b.urheber or "")[:50],
                } for b, d in bt_items])
                st.dataframe(df_bt, use_container_width=True, height=400, hide_index=True)

                if not df_bt.empty:
                    section_header("Documents by Type")
                    fig = px.histogram(df_bt, x="Type", color="Institution",
                                       color_discrete_sequence=["#0D2B45", "#1A6B8A", "#2E9E6B"])
                    style_plotly(fig, height=350)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No Bundestag data. Run the pipeline.")

        with tab2:
            gba_items = (
                session.query(GBADecision, Document)
                .join(Document)
                .order_by(desc(Document.publish_date))
                .limit(50)
                .all()
            )
            if gba_items:
                dh_count = len([g for g, d in gba_items if g.digital_health_flag])
                col1, col2 = st.columns(2)
                with col1: kpi_card("G-BA Decisions", str(len(gba_items)))
                with col2: kpi_card("Digital Health Related", str(dh_count))

                st.markdown("<br>", unsafe_allow_html=True)

                df_gba = pd.DataFrame([{
                    "Date": d.publish_date,
                    "Title": d.title[:70],
                    "Type": g.decision_type,
                    "Subcommittee": g.subcommittee,
                    "Digital Health": "✅" if g.digital_health_flag else "",
                    "Reimbursement Impact": g.reimbursement_impact,
                } for g, d in gba_items])
                st.dataframe(df_gba, use_container_width=True, height=400, hide_index=True)
            else:
                st.info("No G-BA data. Run the pipeline.")

        with tab3:
            diga_apps = session.query(DIGAApp).order_by(desc(DIGAApp.listing_date)).all()
            if diga_apps:
                perm = len([a for a in diga_apps if a.listing_status == "permanent"])
                prov = len([a for a in diga_apps if a.listing_status == "provisional"])
                neuro = len([a for a in diga_apps if a.neuro_relevant])

                col1, col2, col3 = st.columns(3)
                with col1: kpi_card("Permanent", str(perm))
                with col2: kpi_card("Provisional", str(prov))
                with col3: kpi_card("Neuro-relevant", str(neuro))

                st.markdown("<br>", unsafe_allow_html=True)

                df_diga = pd.DataFrame([{
                    "Name": a.app_name,
                    "Manufacturer": a.manufacturer,
                    "Indication": (a.indication or "")[:60],
                    "Status": a.listing_status,
                    "Risk Class": a.risk_class,
                    "Neuro": "🧠" if a.neuro_relevant else "",
                } for a in diga_apps])
                st.dataframe(df_diga, use_container_width=True, height=400, hide_index=True)
            else:
                st.info("No DiGA data. Run the pipeline with the DiGA collector.")

    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 4: SCIENCE & TRIALS
# ══════════════════════════════════════════════════════════
elif page == "🔬 Science & Trials":
    page_header("Science & Clinical Trials", "PubMed publications and ClinicalTrials.gov monitoring")

    session = get_session_cached()
    try:
        sci_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .join(DocumentFlag, Document.document_id == DocumentFlag.document_id)
            .filter(DocumentFlag.is_scientific == True)
            .order_by(desc(Document.publish_date))
            .limit(100)
            .all()
        )

        if sci_docs:
            papers = [d for d, s in sci_docs if d.document_type == "journal_article"]
            trials = [d for d, s in sci_docs if d.document_type == "clinical_trial"]

            col1, col2 = st.columns(2)
            with col1: kpi_card("Papers", str(len(papers)))
            with col2: kpi_card("Clinical Trials", str(len(trials)))

            st.markdown("<br>", unsafe_allow_html=True)

            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:80],
                "Type": d.document_type,
                "Country": d.country,
                "Source": s.source_name,
            } for d, s in sci_docs])

            st.dataframe(df, use_container_width=True, height=500, hide_index=True)

            if not df.empty:
                df["Date"] = pd.to_datetime(df["Date"])
                df_trend = df.dropna(subset=["Date"]).groupby(
                    [pd.Grouper(key="Date", freq="W"), "Type"]
                ).size().reset_index(name="Count")
                if not df_trend.empty:
                    section_header("Publication Trend (Weekly)")
                    fig = px.line(df_trend, x="Date", y="Count", color="Type",
                                 color_discrete_sequence=["#0D2B45", "#2E9E6B"])
                    style_plotly(fig)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No scientific data. Run the pipeline.")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 5: MARKET TRENDS
# ══════════════════════════════════════════════════════════
elif page == "📈 Market Trends":
    page_header("Market Trends", "Google Trends intelligence across 30 countries · Digital health & neurodegenerative")

    COUNTRY_LABELS = {
        "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
        "CY": "Cyprus", "CZ": "Czech Republic", "DK": "Denmark", "EE": "Estonia",
        "FI": "Finland", "FR": "France", "DE": "Germany", "GR": "Greece",
        "HU": "Hungary", "IE": "Ireland", "IT": "Italy", "LV": "Latvia",
        "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "NL": "Netherlands",
        "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia",
        "SI": "Slovenia", "ES": "Spain", "SE": "Sweden",
        "GB": "United Kingdom", "US": "United States", "IL": "Israel",
    }

    KW_CLUSTER = {
        "digital therapeutics": "Digital Health",
        "digital health regulation": "Digital Health",
        "software as medical device": "Digital Health",
        "digital health app CE mark": "Digital Health",
        "DiGA digital health": "Digital Health",
        "Alzheimer digital": "Neurodegenerative",
        "Parkinson digital therapy": "Neurodegenerative",
        "ALS assistive technology": "Neurodegenerative",
        "Huntington disease monitoring": "Neurodegenerative",
        "multiple sclerosis digital": "Neurodegenerative",
        "frontotemporal dementia": "Neurodegenerative",
        "Lewy body dementia diagnosis": "Neurodegenerative",
        "cerebellar ataxia wearable": "Neurodegenerative",
        "digital mental health": "Psychiatric",
        "depression digital therapy": "Psychiatric",
        "postpartum depression digital": "Psychiatric",
        "schizophrenia digital biomarker": "Psychiatric",
        "ADHD digital therapeutic": "Psychiatric",
        "anxiety disorder app": "Psychiatric",
        "bipolar disorder digital": "Psychiatric",
        "health data biobank": "Biobank & Data",
        "neurodegenerative biobank": "Biobank & Data",
        "brain imaging database": "Biobank & Data",
        "real world data neurodegeneration": "Biobank & Data",
        "health data governance": "Biobank & Data",
        "EU health data space": "Regulation",
        "EHDS regulation": "Regulation",
        "AI act medical device": "Regulation",
        "digital health reimbursement": "Regulation",
        "health data interoperability": "Regulation",
    }

    session = get_session_cached()
    try:
        trends = session.query(TrendsMetric).order_by(desc(TrendsMetric.date)).all()

        if trends:
            df = pd.DataFrame([{
                "Date": t.date,
                "Keyword": t.keyword,
                "Geo": t.geography,
                "Country": COUNTRY_LABELS.get(t.geography, t.geography),
                "Interest": t.interest_score,
                "Rising": t.is_rising,
                "Related Topic": t.related_topic,
                "Cluster": KW_CLUSTER.get(t.keyword, "Other"),
            } for t in trends])

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # ── Filters ──
            col_f1, col_f2, col_f3 = st.columns(3)

            available_countries = sorted(df["Country"].dropna().unique())
            available_clusters = sorted(df["Cluster"].dropna().unique())
            available_keywords = sorted(df["Keyword"].dropna().unique())

            default_countries = [c for c in ["United States", "Germany", "United Kingdom",
                                              "France", "Italy", "Israel"]
                                 if c in available_countries]
            if not default_countries:
                default_countries = available_countries[:6]

            with col_f1:
                selected_countries = st.multiselect(
                    "Countries", available_countries, default=default_countries)
            with col_f2:
                selected_clusters = st.multiselect(
                    "Cluster", available_clusters, default=available_clusters)
            with col_f3:
                selected_keywords = st.multiselect(
                    "Keywords", available_keywords, default=[],
                    help="Leave empty = all keywords in selected clusters")

            # ── Apply filters ──
            mask = pd.Series(True, index=df.index)
            if selected_countries:
                mask &= df["Country"].isin(selected_countries)
            if selected_clusters:
                mask &= df["Cluster"].isin(selected_clusters)
            if selected_keywords:
                mask &= df["Keyword"].isin(selected_keywords)

            filtered = df[mask].copy()
            ts_data = filtered[(filtered["Rising"] == False) & (filtered["Interest"].notna())]
            rising_data = filtered[filtered["Rising"] == True]

            # ── KPIs ──
            st.markdown("<br>", unsafe_allow_html=True)
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1: kpi_card("Countries", f"{ts_data['Geo'].nunique()}")
            with kpi2: kpi_card("Keywords", f"{ts_data['Keyword'].nunique()}")
            with kpi3:
                if not ts_data.empty:
                    latest_date = ts_data["Date"].max()
                    avg_score = ts_data[ts_data["Date"] == latest_date]["Interest"].mean()
                    kpi_card("Avg Interest", f"{avg_score:.0f}")
                else:
                    kpi_card("Avg Interest", "N/A")
            with kpi4:
                kpi_card("Rising Topics", f"{len(rising_data)}")

            if not ts_data.empty:
                # ── Chart 1: by Country ──
                section_header("Interest Over Time by Country")
                agg_country = ts_data.groupby(["Date", "Country"])["Interest"].mean().reset_index()
                fig1 = px.line(agg_country, x="Date", y="Interest", color="Country",
                               color_discrete_sequence=["#0D2B45", "#1A6B8A", "#2E9E6B",
                                                         "#E8A838", "#D35C5C", "#7B68AE",
                                                         "#4DACBD", "#E07B53"])
                style_plotly(fig1, height=420)
                fig1.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig1, use_container_width=True)

                # ── Chart 2: by Keyword ──
                section_header("Interest Over Time by Keyword")
                agg_kw = ts_data.groupby(["Date", "Keyword"])["Interest"].mean().reset_index()
                fig2 = px.line(agg_kw, x="Date", y="Interest", color="Keyword")
                style_plotly(fig2, height=420)
                fig2.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.35,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig2, use_container_width=True)

                # ── Chart 3: Heatmap ──
                section_header("Heatmap — Latest Interest by Country × Keyword")
                latest = ts_data[ts_data["Date"] == ts_data["Date"].max()]
                if not latest.empty:
                    pivot = latest.pivot_table(
                        index="Country", columns="Keyword",
                        values="Interest", aggfunc="mean",
                    )
                    fig3 = px.imshow(
                        pivot,
                        labels=dict(x="Keyword", y="Country", color="Interest"),
                        color_continuous_scale=["#FAFAF8", "#E8A838", "#D35C5C", "#0D2B45"],
                        aspect="auto",
                    )
                    style_plotly(fig3, height=max(400, len(pivot) * 24))
                    st.plotly_chart(fig3, use_container_width=True)

            # ── Rising Topics ──
            section_header("Rising Topics")
            if not rising_data.empty:
                rising_display = (
                    rising_data[["Country", "Keyword", "Related Topic", "Date"]]
                    .sort_values("Date", ascending=False)
                    .drop_duplicates(subset=["Country", "Keyword", "Related Topic"])
                    .head(50)
                )
                st.dataframe(rising_display, use_container_width=True, hide_index=True)
            else:
                st.info("No rising topics detected.")

            with st.expander("Raw Data"):
                st.dataframe(
                    filtered.sort_values("Date", ascending=False).head(500),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info("No Google Trends data yet. Run the trends collector.")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 6: NEURODEGENERATIVE FOCUS
# ══════════════════════════════════════════════════════════
elif page == "🧠 Neurodegenerative Focus":
    page_header("Neurodegenerative Focus", "Deep dive into Alzheimer, Parkinson, ALS, MS and related conditions")

    session = get_session_cached()
    try:
        neuro_docs = (
            session.query(Document, Source, Signal, Keyword)
            .join(Source, Document.source_id == Source.source_id)
            .join(Signal, Document.document_id == Signal.document_id)
            .join(Keyword, Signal.keyword_id == Keyword.keyword_id)
            .join(DocumentFlag, Document.document_id == DocumentFlag.document_id)
            .filter(DocumentFlag.is_neuro == True)
            .order_by(desc(Signal.strategic_score))
            .limit(100)
            .all()
        )

        if neuro_docs:
            kpi_card("Neurodegenerative Documents", str(len(neuro_docs)))

            st.markdown("<br>", unsafe_allow_html=True)

            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:70],
                "Disease": kw.disease_area or kw.cluster,
                "Type": d.document_type,
                "Score": f"{s.strategic_score:.1f}",
                "Country": d.country,
                "Source": src.source_name,
            } for d, src, s, kw in neuro_docs])

            section_header("Documents by Disease Area")
            disease_counts = df["Disease"].value_counts().reset_index()
            disease_counts.columns = ["Disease Area", "Count"]
            fig = px.bar(disease_counts, x="Disease Area", y="Count",
                         color="Count", color_continuous_scale=["#E8A838", "#D35C5C", "#0D2B45"])
            style_plotly(fig, height=350)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("No neurodegenerative data. Run the pipeline.")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 7: LMIC OPPORTUNITY
# ══════════════════════════════════════════════════════════
elif page == "🌍 LMIC Opportunity":
    page_header("LMIC Opportunity Map", "Identifying digital health opportunities in low- and middle-income countries")

    session = get_session_cached()
    try:
        country_data = session.query(CountryMetric).order_by(
            desc(CountryMetric.opportunity_score)).all()

        if country_data:
            df = pd.DataFrame([{
                "Country": c.country,
                "Year": c.year,
                "Internet Users %": c.internet_users_pct,
                "Mobile Score": c.mobile_connectivity_score,
                "Neuro Burden": c.burden_neuro,
                "Aging Index": c.aging_index,
                "Workforce Gap": c.health_workforce_gap,
                "DH Strategy": "✅" if c.digital_health_strategy else "❌",
                "Opportunity Score": c.opportunity_score,
            } for c in country_data])

            section_header("Health Need vs Digital Connectivity")
            fig = px.scatter(
                df, x="Internet Users %", y="Neuro Burden",
                size="Opportunity Score", color="Opportunity Score",
                hover_name="Country",
                color_continuous_scale=["#2E9E6B", "#E8A838", "#D35C5C"],
            )
            style_plotly(fig, height=500)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("No country metrics data. Load GSMA/ITU/World Bank data.")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 8: TELECOM READINESS
# ══════════════════════════════════════════════════════════
elif page == "📡 Telecom Readiness":
    page_header("Telecom & Infrastructure Readiness", "Global mobile connectivity and infrastructure assessment")

    session = get_session_cached()
    try:
        telecom_data = session.query(CountryMetric).filter(
            CountryMetric.mobile_connectivity_score.isnot(None)
        ).order_by(desc(CountryMetric.mobile_connectivity_score)).all()

        if telecom_data:
            df = pd.DataFrame([{
                "Country": c.country,
                "Internet %": c.internet_users_pct,
                "Mobile Score": c.mobile_connectivity_score,
                "Opportunity": c.opportunity_score,
            } for c in telecom_data])

            section_header("Global Mobile Connectivity Score")
            fig = px.choropleth(
                df, locations="Country", locationmode="country names",
                color="Mobile Score",
                color_continuous_scale=["#FAFAF8", "#1A6B8A", "#0D2B45"],
            )
            style_plotly(fig, height=500)
            fig.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#FAFAF8"))
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df, use_container_width=True, height=400, hide_index=True)
        else:
            st.info("No telecom data. Load GSMA/ITU data.")
    finally:
        session.close()

    page_footer()


# ══════════════════════════════════════════════════════════
# PAGE 9: CYBER ATTACK RADAR
# ══════════════════════════════════════════════════════════
elif page == "⚠️ Cyber Attack Radar":
    page_header("Cyber Attack Radar", "Healthcare cybersecurity threats · Hospitals, medical devices, health apps & data breaches")

    session = get_session_cached()
    try:
        cyber_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "cyber_alert")
            .order_by(desc(Document.publish_date))
            .limit(200)
            .all()
        )

        if cyber_docs:
            # KPIs
            total = len(cyber_docs)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent = len([d for d, s in cyber_docs if d.scraped_at and d.scraped_at >= week_ago])
            sources_count = len(set(s.source_name for d, s in cyber_docs))

            # Severity estimation based on keywords
            critical_keywords = ["ransomware", "breach", "attack", "hack", "leak", "shutdown", "compromised"]
            critical = len([d for d, s in cyber_docs
                           if any(kw in (d.title or "").lower() for kw in critical_keywords)])

            col1, col2, col3, col4 = st.columns(4)
            with col1: kpi_card("Total Alerts", str(total))
            with col2: kpi_card("This Week", str(recent))
            with col3: kpi_card("Sources", str(sources_count))
            with col4: kpi_card("Critical", str(critical))

            st.markdown("<br>", unsafe_allow_html=True)

            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:90],
                "Source": s.source_name,
                "Country": d.country or "",
                "URL": d.url or "",
                "Summary": (d.summary or "")[:120],
            } for d, s in cyber_docs])

            # ── Threat type classification ──
            def classify_threat(title):
                t = title.lower()
                if any(w in t for w in ["ransomware", "ransom"]):
                    return "Ransomware"
                elif any(w in t for w in ["breach", "leak", "exposed", "unauthorized"]):
                    return "Data Breach"
                elif any(w in t for w in ["phishing", "social engineering"]):
                    return "Phishing"
                elif any(w in t for w in ["vulnerability", "CVE", "patch", "exploit"]):
                    return "Vulnerability"
                elif any(w in t for w in ["malware", "trojan", "virus"]):
                    return "Malware"
                elif any(w in t for w in ["regulation", "compliance", "HIPAA", "fine", "penalty"]):
                    return "Compliance"
                else:
                    return "Advisory"

            df["Threat Type"] = df["Title"].apply(classify_threat)

            # ── Charts ──
            col_left, col_right = st.columns(2)

            with col_left:
                section_header("Threats by Type")
                threat_counts = df["Threat Type"].value_counts().reset_index()
                threat_counts.columns = ["Type", "Count"]
                # Color map for threat types
                color_map = {
                    "Ransomware": "#D35C5C",
                    "Data Breach": "#E8A838",
                    "Phishing": "#E07B53",
                    "Vulnerability": "#7B68AE",
                    "Malware": "#C97B84",
                    "Compliance": "#1A6B8A",
                    "Advisory": "#4DACBD",
                }
                fig = px.bar(threat_counts, x="Type", y="Count",
                             color="Type", color_discrete_map=color_map)
                style_plotly(fig, height=350)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_right:
                section_header("Alerts by Source")
                source_counts = df["Source"].value_counts().reset_index()
                source_counts.columns = ["Source", "Count"]
                fig = px.pie(source_counts, values="Count", names="Source",
                             color_discrete_sequence=["#0D2B45", "#1A6B8A", "#2E9E6B",
                                                       "#E8A838", "#D35C5C"])
                fig.update_layout(height=350, margin=dict(t=10, b=10),
                                  font=dict(family="Source Sans Pro", size=11),
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)

            # ── Geographic Map ──
            section_header("Global Threat Map")
            country_counts = df["Country"].value_counts().reset_index()
            country_counts.columns = ["Country", "Count"]
            if not country_counts.empty and country_counts["Country"].str.len().max() > 0:
                fig_map = px.choropleth(
                    country_counts,
                    locations="Country",
                    locationmode="country names",
                    color="Count",
                    color_continuous_scale=["#FAFAF8", "#E8A838", "#D35C5C", "#0D2B45"],
                    labels={"Count": "Alerts"},
                )
                style_plotly(fig_map, height=400)
                fig_map.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#FAFAF8",
                                               showframe=False, projection_type="natural earth"))
                st.plotly_chart(fig_map, use_container_width=True)

            # ── Timeline ──
            section_header("Threat Timeline")
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df_timeline = df.dropna(subset=["Date"])
            if not df_timeline.empty:
                df_weekly = (
                    df_timeline.groupby([pd.Grouper(key="Date", freq="W"), "Threat Type"])
                    .size().reset_index(name="Count")
                )
                fig = px.area(df_weekly, x="Date", y="Count", color="Threat Type",
                              color_discrete_map=color_map)
                style_plotly(fig, height=380)
                fig.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig, use_container_width=True)

            # ── Recent Critical Alerts ──
            section_header("Recent Alerts")
            critical_df = df[df["Threat Type"].isin(["Ransomware", "Data Breach", "Malware"])]
            if not critical_df.empty:
                for _, row in critical_df.head(10).iterrows():
                    is_critical = row["Threat Type"] == "Ransomware"
                    alert_card(
                        row["Title"],
                        f"{row['Source']} · {row['Threat Type']}",
                        8.0 if is_critical else 5.0,
                        row.get("URL", ""),
                        high=is_critical,
                    )
            st.markdown("<br>", unsafe_allow_html=True)

            # ── Full table ──
            with st.expander("All Cyber Alerts"):
                st.dataframe(
                    df[["Date", "Title", "Threat Type", "Source", "Country"]].sort_values("Date", ascending=False),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info("No cyber threat data yet. Run the cyber collector:")
            st.code("python -c \"from collectors.cyber_collector import run; run()\"")
    finally:
        session.close()

    # ── Attack Flow Intelligence (AbuseIPDB) ──
    session2 = get_session_cached()
    try:
        # Check if cyber_attack_flows table exists and has data
        try:
            flow_result = session2.execute(
                text("SELECT * FROM cyber_attack_flows ORDER BY date DESC, attack_count DESC LIMIT 500")
            )
            flow_rows = flow_result.fetchall()
            flow_columns = flow_result.keys()
        except Exception:
            flow_rows = []
            flow_columns = []

        if flow_rows:
            df_flows = pd.DataFrame(flow_rows, columns=flow_columns)

            section_header("Attack Flow Intelligence — Origin to Target")
            st.caption("Source: AbuseIPDB blacklist · Top malicious IPs aggregated by country of origin")

            # ── Arc Attack Map ──
            COUNTRY_COORDS = {
                "China": (35.86, 104.19), "United States": (37.09, -95.71),
                "Russia": (61.52, 105.32), "Brazil": (-14.24, -51.93),
                "India": (20.59, 78.96), "South Korea": (35.91, 127.77),
                "Germany": (51.17, 10.45), "France": (46.23, 2.21),
                "United Kingdom": (55.38, -3.44), "Netherlands": (52.13, 5.29),
                "Vietnam": (14.06, 108.28), "Indonesia": (-0.79, 113.92),
                "Taiwan": (23.70, 120.96), "Japan": (36.20, 138.25),
                "Thailand": (15.87, 100.99), "Ukraine": (48.38, 31.17),
                "Pakistan": (30.38, 69.35), "Italy": (41.87, 12.57),
                "Argentina": (-38.42, -63.62), "Mexico": (23.63, -102.55),
                "Philippines": (12.88, 121.77), "Bangladesh": (23.68, 90.36),
                "Colombia": (4.57, -74.30), "Turkey": (38.96, 35.24),
                "Iran": (32.43, 53.69), "North Korea": (40.34, 127.51),
                "Romania": (45.94, 24.97), "Poland": (51.92, 19.15),
                "Spain": (40.46, -3.75), "Canada": (56.13, -106.35),
                "Australia": (-25.27, 133.78), "Israel": (31.05, 34.85),
                "Singapore": (1.35, 103.82), "Hong Kong": (22.40, 114.11),
                "South Africa": (-30.56, 22.94), "Egypt": (26.82, 30.80),
                "Healthcare Global": (20.0, 0.0),
                "USA": (37.09, -95.71),
            }

            # Target coordinates (slightly offset for visibility)
            TARGET_COORDS = {
                "USA": (39.0, -98.0),
                "Germany": (52.5, 13.4),
                "United Kingdom": (53.0, -1.0),
                "France": (48.9, 2.3),
                "Italy": (43.0, 11.0),
                "Israel": (32.0, 35.0),
                "Healthcare Global": (30.0, 10.0),
            }

            # Build arc data
            arc_data = (
                df_flows.groupby(["origin_country_name", "target_country"])["attack_count"]
                .sum().reset_index()
            )
            arc_data = arc_data[arc_data["attack_count"] > 0].nlargest(100, "attack_count")

            if not arc_data.empty:
                fig_map = go.Figure()

                # Normalize line widths
                max_attacks = arc_data["attack_count"].max()

                for _, row in arc_data.iterrows():
                    origin = row["origin_country_name"]
                    target = row["target_country"]
                    attacks = row["attack_count"]

                    if origin not in COUNTRY_COORDS or target not in TARGET_COORDS:
                        continue

                    o_lat, o_lon = COUNTRY_COORDS[origin]
                    t_lat, t_lon = TARGET_COORDS[target]

                    # Line width proportional to attacks
                    import math
                    width = max(0.8, math.log1p(attacks) / math.log1p(max_attacks) * 5)
                    opacity = max(0.25, min(0.8, math.log1p(attacks) / math.log1p(max_attacks)))

                    fig_map.add_trace(go.Scattergeo(
                        lon=[o_lon, t_lon],
                        lat=[o_lat, t_lat],
                        mode="lines",
                        line=dict(width=width, color=f"rgba(211,92,92,{opacity})"),
                        hoverinfo="text",
                        text=f"{origin} → {target}: {attacks} attacks",
                        showlegend=False,
                    ))

                # Add origin markers
                origin_agg = arc_data.groupby("origin_country_name")["attack_count"].sum().reset_index()
                for _, row in origin_agg.iterrows():
                    name = row["origin_country_name"]
                    if name not in COUNTRY_COORDS:
                        continue
                    lat, lon = COUNTRY_COORDS[name]
                    size = max(4, min(20, (row["attack_count"] / max_attacks) * 20))

                    fig_map.add_trace(go.Scattergeo(
                        lon=[lon], lat=[lat],
                        mode="markers+text",
                        marker=dict(size=size, color="rgba(211,92,92,0.8)",
                                    line=dict(width=0.5, color="white")),
                        text=name,
                        textposition="top center",
                        textfont=dict(size=8, color="#2D3436"),
                        hoverinfo="text",
                        hovertext=f"{name}: {row['attack_count']} attacks",
                        showlegend=False,
                    ))

                # Add target markers
                for target_name, (lat, lon) in TARGET_COORDS.items():
                    fig_map.add_trace(go.Scattergeo(
                        lon=[lon], lat=[lat],
                        mode="markers",
                        marker=dict(size=10, color="rgba(26,107,138,0.9)",
                                    symbol="diamond",
                                    line=dict(width=1, color="white")),
                        hoverinfo="text",
                        hovertext=f"Target: {target_name}",
                        showlegend=False,
                    ))

                fig_map.update_layout(
                    height=550,
                    margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Source Sans Pro"),
                    geo=dict(
                        bgcolor="rgba(0,0,0,0)",
                        lakecolor="#E8E4DF",
                        landcolor="#FAFAF8",
                        coastlinecolor="#CCCCCC",
                        countrycolor="#E0E0E0",
                        showframe=False,
                        showcoastlines=True,
                        projection_type="natural earth",
                    ),
                )
                st.plotly_chart(fig_map, use_container_width=True)
                st.caption("🔴 Red = attack origins · 🔷 Blue = targets · Line thickness = attack volume")

            # ── Sankey Diagram ──
            # Prepare data: origin → target with attack counts
            sankey_data = (
                df_flows.groupby(["origin_country_name", "target_country"])["attack_count"]
                .sum().reset_index()
            )
            sankey_data = sankey_data[sankey_data["attack_count"] > 0].nlargest(40, "attack_count")

            if not sankey_data.empty:
                # Build Sankey labels and links
                origins = sankey_data["origin_country_name"].unique().tolist()
                targets = sankey_data["target_country"].unique().tolist()
                all_labels = origins + targets

                source_idx = [all_labels.index(o) for o in sankey_data["origin_country_name"]]
                target_idx = [all_labels.index(t) for t in sankey_data["target_country"]]
                values = sankey_data["attack_count"].tolist()

                # Colors: red-ish for origins, blue-ish for targets
                node_colors = (
                    ["rgba(211,92,92,0.7)"] * len(origins) +
                    ["rgba(26,107,138,0.7)"] * len(targets)
                )

                fig_sankey = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15, thickness=20, line=dict(color="#E8E4DF", width=0.5),
                        label=all_labels,
                        color=node_colors,
                    ),
                    link=dict(
                        source=source_idx,
                        target=target_idx,
                        value=values,
                        color="rgba(211,92,92,0.15)",
                    ),
                )])
                fig_sankey.update_layout(
                    font=dict(family="Source Sans Pro", size=11, color="#2D3436"),
                    height=500,
                    margin=dict(t=20, b=20, l=20, r=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_sankey, use_container_width=True)

                # ── Top Attackers Table ──
                col_att_left, col_att_right = st.columns(2)

                with col_att_left:
                    section_header("Top Attack Origins")
                    origin_totals = (
                        df_flows.groupby("origin_country_name")["attack_count"]
                        .sum().reset_index()
                        .sort_values("attack_count", ascending=False)
                        .head(15)
                    )
                    origin_totals.columns = ["Country", "Attacks"]
                    fig_origins = px.bar(
                        origin_totals, x="Attacks", y="Country", orientation="h",
                        color="Attacks",
                        color_continuous_scale=["#E8A838", "#D35C5C", "#0D2B45"],
                    )
                    style_plotly(fig_origins, height=400)
                    fig_origins.update_layout(showlegend=False)
                    st.plotly_chart(fig_origins, use_container_width=True)

                with col_att_right:
                    section_header("Attack Origin Map")
                    fig_origin_map = px.choropleth(
                        origin_totals,
                        locations="Country",
                        locationmode="country names",
                        color="Attacks",
                        color_continuous_scale=["#FAFAF8", "#E8A838", "#D35C5C", "#0D2B45"],
                    )
                    style_plotly(fig_origin_map, height=400)
                    fig_origin_map.update_layout(
                        geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#FAFAF8",
                                 showframe=False, projection_type="natural earth")
                    )
                    st.plotly_chart(fig_origin_map, use_container_width=True)

                # ── Confidence Score by Origin ──
                section_header("Average Threat Confidence by Origin")
                conf_data = (
                    df_flows.groupby("origin_country_name")["avg_confidence"]
                    .mean().reset_index()
                    .sort_values("avg_confidence", ascending=False)
                    .head(20)
                )
                conf_data.columns = ["Country", "Confidence %"]
                fig_conf = px.bar(
                    conf_data, x="Country", y="Confidence %",
                    color="Confidence %",
                    color_continuous_scale=["#2E9E6B", "#E8A838", "#D35C5C"],
                )
                style_plotly(fig_conf, height=350)
                fig_conf.update_layout(showlegend=False)
                st.plotly_chart(fig_conf, use_container_width=True)

        else:
            st.markdown("---")
            st.info("No attack flow data yet. Run the AbuseIPDB collector:")
            st.code("export ABUSEIPDB_API_KEY=\"your-key\"\npython -c \"from collectors.abuseipdb_collector import run; run()\"")

    except Exception as e:
        st.warning(f"Attack flow section error: {e}")
    finally:
        session2.close()

    page_footer()
