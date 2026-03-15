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
            "🌍 LMIC Digital MH",
            "🏛️ Chatham House",
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

            # ── Live Threat Maps ──
            section_header("Live Global Threat Maps")
            st.caption("Real-time cyber threat visualizations from leading security vendors")

            map_tab1, map_tab2 = st.tabs(["Check Point", "Radware"])

            with map_tab1:
                st.components.v1.iframe(
                    "https://threatmap.checkpoint.com/",
                    height=450, scrolling=False,
                )
                st.caption("Source: Check Point ThreatCloud Live Map")

            with map_tab2:
                st.components.v1.iframe(
                    "https://livethreatmap.radware.com/",
                    height=450, scrolling=False,
                )
                st.caption("Source: Radware Live Threat Map")

            st.markdown("""
            <div style="margin-top:0.8rem; font-size:0.85rem; color:#7F8C8D;">
                <strong>Other live maps:</strong>
                <a href="https://cybermap.kaspersky.com/" target="_blank" style="color:#1A6B8A;">Kaspersky</a> &middot;
                <a href="https://horizon.netscout.com/" target="_blank" style="color:#1A6B8A;">NETSCOUT</a> &middot;
                <a href="https://www.digitalattackmap.com/" target="_blank" style="color:#1A6B8A;">Digital Attack Map</a>
            </div>
            """, unsafe_allow_html=True)

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


# ════════════════════════════════════════════════════════
# PAGE 10: LMIC DIGITAL MENTAL HEALTH
# ════════════════════════════════════════════════════════
elif page == "🌍 LMIC Digital MH":
    page_header("LMIC Digital Mental Health", "Digital health projects for psychiatric & neurological conditions in developing countries")

    LMIC_REGIONS = {
        "South Asia": ["India", "Bangladesh", "Nepal", "Sri Lanka", "Pakistan"],
        "Southeast Asia": ["Vietnam", "Indonesia", "Philippines", "Thailand", "Cambodia", "Myanmar"],
        "East Asia": ["China"],
        "Sub-Saharan Africa": ["Kenya", "Nigeria", "South Africa", "Ghana", "Ethiopia", "Tanzania",
                               "Uganda", "Rwanda", "Malawi", "Zimbabwe", "Senegal"],
        "North Africa & Middle East": ["Egypt", "Morocco", "Tunisia", "Jordan", "Lebanon"],
        "South America": ["Brazil", "Colombia", "Peru", "Chile", "Argentina", "Mexico",
                          "Ecuador", "Bolivia"],
    }
    COUNTRY_TO_REGION = {}
    for region, countries in LMIC_REGIONS.items():
        for country in countries:
            COUNTRY_TO_REGION[country] = region

    session = get_session_cached()
    try:
        lmic_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "lmic_dh_project")
            .order_by(desc(Document.publish_date))
            .limit(500)
            .all()
        )

        if lmic_docs:
            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:90],
                "Country": d.country or "Unknown",
                "Region": COUNTRY_TO_REGION.get(d.country, "Other"),
                "Source": s.source_name,
                "URL": d.url or "",
                "Summary": (d.summary or "")[:150],
                "Type": "Clinical Trial" if "ClinicalTrials" in s.source_name else "Research",
            } for d, s in lmic_docs])

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # ── KPIs ──
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                kpi_card("Total Projects", str(len(df)))
            with col2:
                kpi_card("Countries", str(df["Country"].nunique()))
            with col3:
                kpi_card("Regions", str(df["Region"].nunique()))
            with col4:
                trials = len(df[df["Type"] == "Clinical Trial"])
                kpi_card("Clinical Trials", str(trials))

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Filters ──
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                regions = sorted(df["Region"].unique())
                sel_regions = st.multiselect("Region", regions, default=regions)
            with col_f2:
                countries = sorted(df[df["Region"].isin(sel_regions)]["Country"].unique())
                sel_countries = st.multiselect("Country", countries, default=[])
            with col_f3:
                types = sorted(df["Type"].unique())
                sel_types = st.multiselect("Type", types, default=types)

            mask = df["Region"].isin(sel_regions) & df["Type"].isin(sel_types)
            if sel_countries:
                mask &= df["Country"].isin(sel_countries)
            filtered = df[mask]

            # ── Chart 1: Projects by Region ──
            col_left, col_right = st.columns(2)

            with col_left:
                section_header("Projects by Region")
                region_counts = filtered["Region"].value_counts().reset_index()
                region_counts.columns = ["Region", "Count"]
                fig = px.bar(region_counts, x="Count", y="Region", orientation="h",
                             color="Count",
                             color_continuous_scale=["#2E9E6B", "#E8A838", "#0D2B45"])
                style_plotly(fig, height=350)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_right:
                section_header("Projects by Country (Top 15)")
                country_counts = filtered["Country"].value_counts().head(15).reset_index()
                country_counts.columns = ["Country", "Count"]
                fig = px.bar(country_counts, x="Count", y="Country", orientation="h",
                             color="Count",
                             color_continuous_scale=["#1A6B8A", "#E8A838", "#D35C5C"])
                style_plotly(fig, height=400)
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # ── Chart 2: Global Map ──
            section_header("Global Distribution")
            map_data = filtered["Country"].value_counts().reset_index()
            map_data.columns = ["Country", "Projects"]
            if not map_data.empty:
                fig_map = px.choropleth(
                    map_data, locations="Country", locationmode="country names",
                    color="Projects",
                    color_continuous_scale=["#FAFAF8", "#2E9E6B", "#0D2B45"],
                )
                style_plotly(fig_map, height=450)
                fig_map.update_layout(
                    geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#FAFAF8",
                             showframe=False, projection_type="natural earth")
                )
                st.plotly_chart(fig_map, use_container_width=True)

            # ── Chart 3: Timeline ──
            section_header("Project Timeline")
            df_timeline = filtered.dropna(subset=["Date"])
            if not df_timeline.empty:
                df_monthly = (
                    df_timeline.groupby([pd.Grouper(key="Date", freq="M"), "Region"])
                    .size().reset_index(name="Count")
                )
                fig_time = px.area(df_monthly, x="Date", y="Count", color="Region",
                                   color_discrete_sequence=["#0D2B45", "#1A6B8A", "#2E9E6B",
                                                             "#E8A838", "#D35C5C", "#7B68AE"])
                style_plotly(fig_time, height=380)
                fig_time.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig_time, use_container_width=True)

            # ── Chart 4: Research vs Trials ──
            col_pie1, col_pie2 = st.columns(2)

            with col_pie1:
                section_header("Research vs Clinical Trials")
                type_counts = filtered["Type"].value_counts().reset_index()
                type_counts.columns = ["Type", "Count"]
                fig_type = px.pie(type_counts, values="Count", names="Type",
                                  color_discrete_sequence=["#0D2B45", "#2E9E6B"])
                fig_type.update_layout(height=300, margin=dict(t=10, b=10),
                                       paper_bgcolor="rgba(0,0,0,0)",
                                       font=dict(family="Source Sans Pro", size=11))
                st.plotly_chart(fig_type, use_container_width=True)

            with col_pie2:
                section_header("Source Distribution")
                src_counts = filtered["Source"].value_counts().reset_index()
                src_counts.columns = ["Source", "Count"]
                fig_src = px.pie(src_counts, values="Count", names="Source",
                                 color_discrete_sequence=["#1A6B8A", "#E8A838", "#D35C5C"])
                fig_src.update_layout(height=300, margin=dict(t=10, b=10),
                                       paper_bgcolor="rgba(0,0,0,0)",
                                       font=dict(family="Source Sans Pro", size=11))
                st.plotly_chart(fig_src, use_container_width=True)

            # ── Data Table ──
            section_header("All Projects")
            st.dataframe(
                filtered[["Date", "Title", "Country", "Region", "Type", "Source"]].sort_values("Date", ascending=False),
                use_container_width=True, hide_index=True, height=400,
            )

            with st.expander("Project Details"):
                for _, row in filtered.head(20).iterrows():
                    st.markdown(f"""
                    <div class="ed-alert">
                        <strong>{row['Title']}</strong><br>
                        <small>{row['Country']} · {row['Region']} · {row['Type']} ·
                        <a href="{row['URL']}" target="_blank">View →</a></small><br>
                        <small style="color:#7F8C8D;">{row['Summary']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.info("No LMIC digital mental health data yet. Run the collector:")
            st.code('python -c "from collectors.lmic_dh_collector import run; run()"')

    finally:
        session.close()

    # ── Le Mie Note ──
    st.markdown("---")
    section_header("Le Mie Note")

    session_notes = get_session_cached()
    try:
        manual_src = session_notes.query(Source).filter_by(source_name="Manual Entry").first()
        if manual_src:
            my_notes = (
                session_notes.query(Document)
                .filter_by(source_id=manual_src.source_id, document_type="lmic_dh_project")
                .order_by(desc(Document.publish_date))
                .all()
            )

            if my_notes:
                st.caption(f"{len(my_notes)} personal notes")

                for doc in my_notes:
                    # Extract tags if present
                    import re as re_notes
                    summary = doc.summary or ""
                    tags_html = ""
                    tag_match = re_notes.match(r"\[Tags:\s*(.+?)\]", summary)
                    if tag_match:
                        tags = [t.strip() for t in tag_match.group(1).split(",")]
                        tags_html = " ".join(
                            f'<span style="background:#EBF5FB; color:#1A6B8A; padding:2px 8px; '
                            f'border-radius:12px; font-size:0.75rem; margin-right:4px;">{t}</span>'
                            for t in tags
                        )
                        summary = summary[tag_match.end():].strip()

                    link_html = ""
                    if doc.url:
                        link_html = f' · <a href="{doc.url}" target="_blank" style="color:#1A6B8A;">View →</a>'

                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:1px solid #E8E4DF; border-left:3px solid #1A6B8A;
                                padding:1rem 1.2rem; margin:0.5rem 0; border-radius:0 6px 6px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                            <strong style="color:#0D2B45; font-size:0.95rem;">{doc.title}</strong>
                            <span style="color:#95A5A6; font-size:0.75rem; white-space:nowrap; margin-left:1rem;">
                                {doc.publish_date.strftime('%d/%m/%Y') if doc.publish_date else ''}
                            </span>
                        </div>
                        <div style="margin:0.3rem 0; font-size:0.8rem; color:#7F8C8D;">
                            {doc.country or 'No country'}{link_html}
                        </div>
                        <div style="margin:0.4rem 0;">{tags_html}</div>
                        <div style="color:#4A4A4A; font-size:0.88rem; line-height:1.5; margin-top:0.4rem;
                                    white-space:pre-wrap;">{summary}</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Export option
                with st.expander("Export Notes as CSV"):
                    df_notes = pd.DataFrame([{
                        "Date": d.publish_date,
                        "Title": d.title,
                        "Country": d.country,
                        "Notes": d.summary,
                        "URL": d.url or "",
                    } for d in my_notes])
                    csv = df_notes.to_csv(index=False)
                    st.download_button(
                        "Download CSV",
                        csv,
                        "my_notes.csv",
                        "text/csv",
                    )
            else:
                st.info("No personal notes yet. Use the form below to add projects and notes.")
        else:
            st.info("No personal notes yet. Use the form below to add projects and notes.")
    except Exception as e:
        st.warning(f"Notes section error: {e}")
    finally:
        session_notes.close()

    # ── Add Project / Notes Form ──
    st.markdown("---")
    section_header("Add Project or Notes")

    with st.form("add_lmic_project", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)

        with col_form1:
            new_title = st.text_input("Project Title *")
            new_country = st.selectbox("Country *", [
                "", "India", "Bangladesh", "Nepal", "Sri Lanka", "Pakistan",
                "Vietnam", "Indonesia", "Philippines", "Thailand", "Cambodia", "Myanmar",
                "China", "Kenya", "Nigeria", "South Africa", "Ghana", "Ethiopia",
                "Tanzania", "Uganda", "Rwanda", "Malawi", "Zimbabwe", "Senegal",
                "Egypt", "Morocco", "Tunisia", "Jordan", "Lebanon",
                "Brazil", "Colombia", "Peru", "Chile", "Argentina", "Mexico",
                "Ecuador", "Bolivia", "South Sudan", "Sudan", "Afghanistan",
                "Democratic Republic of Congo", "Cameroon", "Mozambique",
            ])
            new_region = st.selectbox("Region", [
                "South Asia", "Southeast Asia", "East Asia",
                "Sub-Saharan Africa", "North Africa & Middle East",
                "South America", "Central Asia", "Other",
            ])

        with col_form2:
            new_type = st.selectbox("Type", [
                "Research", "Clinical Trial", "NGO Project", "Government Initiative",
                "Startup / App", "WHO Initiative", "Other",
            ])
            new_url = st.text_input("URL (optional)")
            new_tags = st.text_input("Tags / Keywords (comma separated)",
                                     placeholder="e.g. depression, mHealth, telemedicine, AI")

        new_notes = st.text_area("Notes & Analysis *",
                                  height=150,
                                  placeholder="Describe the project, your observations, strategic relevance, key findings...")

        submitted = st.form_submit_button("Add Project")

        if submitted:
            if new_title and new_notes and new_country:
                session_add = get_session_cached()
                try:
                    # Get or create a manual source
                    manual_source = session_add.query(Source).filter_by(
                        source_name="Manual Entry"
                    ).first()
                    if not manual_source:
                        manual_source = Source(
                            source_name="Manual Entry",
                            source_type="lmic_digital_health",
                            url="",
                            region="Global",
                            country="",
                            access_method="manual",
                            active=True,
                        )
                        session_add.add(manual_source)
                        session_add.commit()

                    # Build summary with tags
                    summary_with_tags = new_notes
                    if new_tags:
                        summary_with_tags = f"[Tags: {new_tags.strip()}] {new_notes}"

                    from datetime import datetime as dt
                    new_doc = Document(
                        source_id=manual_source.source_id,
                        title=new_title[:500],
                        url=new_url or None,
                        document_type="lmic_dh_project",
                        country=new_country,
                        publish_date=dt.utcnow().date(),
                        summary=summary_with_tags[:1000],
                        scraped_at=dt.utcnow(),
                    )
                    session_add.add(new_doc)
                    session_add.commit()
                    st.success(f"Added: {new_title}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding project: {e}")
                finally:
                    session_add.close()
            else:
                st.warning("Please fill in Title, Country, and Notes.")

    # ── Keyword / Semantic Analysis ──
    section_header("Keyword Analysis from Notes")

    session_kw = get_session_cached()
    try:
        all_lmic = (
            session_kw.query(Document)
            .filter(Document.document_type == "lmic_dh_project")
            .filter(Document.summary.isnot(None))
            .all()
        )

        if all_lmic:
            import re
            from collections import Counter

            # Extract all tags
            all_tags = []
            all_words = []

            # Stopwords
            stopwords = {
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
                "for", "of", "with", "by", "from", "is", "are", "was", "were",
                "be", "been", "being", "have", "has", "had", "do", "does", "did",
                "will", "would", "could", "should", "may", "might", "can", "shall",
                "this", "that", "these", "those", "it", "its", "they", "them",
                "their", "we", "our", "you", "your", "he", "she", "his", "her",
                "not", "no", "as", "if", "than", "more", "most", "very", "also",
                "about", "up", "out", "so", "what", "which", "who", "how", "when",
                "where", "all", "each", "both", "few", "many", "some", "such",
                "only", "other", "new", "one", "two", "first", "well", "just",
                "into", "over", "after", "through", "between", "under", "during",
                "before", "because", "while", "based", "using", "used", "use",
                "study", "studies", "results", "including", "included",
            }

            for doc in all_lmic:
                summary = doc.summary or ""

                # Extract tags from [Tags: ...] prefix
                tag_match = re.match(r"\[Tags:\s*(.+?)\]", summary)
                if tag_match:
                    tags = [t.strip().lower() for t in tag_match.group(1).split(",")]
                    all_tags.extend(tags)

                # Extract meaningful words
                words = re.findall(r"[a-zA-Z]{4,}", summary.lower())
                meaningful = [w for w in words if w not in stopwords and len(w) > 3]
                all_words.extend(meaningful)

            col_kw1, col_kw2 = st.columns(2)

            with col_kw1:
                if all_tags:
                    st.markdown("**Top Tags**")
                    tag_counts = Counter(all_tags).most_common(20)
                    df_tags = pd.DataFrame(tag_counts, columns=["Tag", "Count"])
                    fig_tags = px.bar(df_tags, x="Count", y="Tag", orientation="h",
                                      color="Count",
                                      color_continuous_scale=["#1A6B8A", "#2E9E6B"])
                    style_plotly(fig_tags, height=400)
                    fig_tags.update_layout(showlegend=False)
                    st.plotly_chart(fig_tags, use_container_width=True)
                else:
                    st.info("No tagged projects yet. Add tags when creating projects.")

            with col_kw2:
                st.markdown("**Top Keywords from All Notes**")
                word_counts = Counter(all_words).most_common(25)
                df_words = pd.DataFrame(word_counts, columns=["Keyword", "Frequency"])
                fig_words = px.bar(df_words, x="Frequency", y="Keyword", orientation="h",
                                    color="Frequency",
                                    color_continuous_scale=["#E8A838", "#D35C5C"])
                style_plotly(fig_words, height=500)
                fig_words.update_layout(showlegend=False)
                st.plotly_chart(fig_words, use_container_width=True)

            # Keyword co-occurrence by country
            section_header("Keywords by Country")
            country_keywords = {}
            for doc in all_lmic:
                if doc.country and doc.summary:
                    words = re.findall(r"[a-zA-Z]{4,}", doc.summary.lower())
                    meaningful = [w for w in words if w not in stopwords]
                    if doc.country not in country_keywords:
                        country_keywords[doc.country] = []
                    country_keywords[doc.country].extend(meaningful)

            # Build country x keyword matrix for top countries and keywords
            top_countries_kw = sorted(country_keywords.keys(),
                                       key=lambda x: len(country_keywords[x]),
                                       reverse=True)[:15]
            top_kws = [w for w, _ in Counter(all_words).most_common(15)]

            if top_countries_kw and top_kws:
                matrix_data = []
                for country in top_countries_kw:
                    word_freq = Counter(country_keywords[country])
                    row = {"Country": country}
                    for kw in top_kws:
                        row[kw] = word_freq.get(kw, 0)
                    matrix_data.append(row)

                df_matrix = pd.DataFrame(matrix_data).set_index("Country")
                fig_heat = px.imshow(
                    df_matrix,
                    labels=dict(x="Keyword", y="Country", color="Frequency"),
                    color_continuous_scale=["#FAFAF8", "#1A6B8A", "#0D2B45"],
                    aspect="auto",
                )
                style_plotly(fig_heat, height=max(350, len(top_countries_kw) * 25))
                st.plotly_chart(fig_heat, use_container_width=True)

    except Exception as e:
        st.warning(f"Keyword analysis error: {e}")
    finally:
        session_kw.close()

    page_footer()


# ════════════════════════════════════════════════════════
# PAGE 11: CHATHAM HOUSE (enhanced v3.0)
# ════════════════════════════════════════════════════════
elif page == "🏛️ Chatham House":
    page_header("Chatham House", "Healthcare intelligence from the Royal Institute of International Affairs")

    session = get_session_cached()
    try:
        # ── Ensure tables exist ──
        from sqlalchemy import text as sa_text
        try:
            session.execute(sa_text("""
                CREATE TABLE IF NOT EXISTS chatham_notes (
                    note_id SERIAL PRIMARY KEY,
                    document_id INTEGER REFERENCES documents(document_id) ON DELETE CASCADE,
                    note_text TEXT,
                    private_url TEXT,
                    ai_keywords TEXT,
                    ai_countries TEXT,
                    ai_sentiment VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            session.execute(sa_text("""
                CREATE TABLE IF NOT EXISTS chatham_private_links (
                    link_id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    ai_keywords TEXT,
                    ai_countries TEXT,
                    ai_summary TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            session.execute(sa_text("CREATE INDEX IF NOT EXISTS idx_chatham_notes_doc ON chatham_notes(document_id)"))
            session.execute(sa_text("CREATE INDEX IF NOT EXISTS idx_chatham_links_created ON chatham_private_links(created_at)"))
            session.commit()
        except Exception:
            session.rollback()

        ch_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "chatham_house")
            .order_by(desc(Document.publish_date))
            .limit(500)
            .all()
        )

        if ch_docs:
            df_ch = pd.DataFrame([{
                "DocID": d.document_id,
                "Date": d.publish_date,
                "Title": d.title or "",
                "Source": s.source_name,
                "URL": d.url or "",
                "Summary": (d.summary or ""),
                "Country": (d.country or ""),
            } for d, s in ch_docs])

            df_ch["Date"] = pd.to_datetime(df_ch["Date"], errors="coerce")
            df_ch["Full_Text"] = (df_ch["Title"] + " " + df_ch["Summary"]).str.lower()

            import re as re_ch
            from collections import Counter

            # ── HEALTHCARE FILTER ──
            HEALTH_KEYWORDS = [
                "health", "healthcare", "medical", "medicine", "clinical",
                "hospital", "patient", "disease", "pandemic", "epidemic",
                "vaccine", "vaccination", "immuniz", "pharma", "drug",
                "therapeut", "diagnos", "treatment", "surgery", "surgical",
                "mental health", "wellbeing", "well-being",
                "who ", "world health", "nhs", "cdc",
                "biotech", "genomic", "gene therapy", "crispr",
                "telemedicine", "telehealth", "digital health", "ehealth",
                "e-health", "mhealth", "m-health", "wearable", "health tech",
                "health data", "electronic health", "ehr ", "emr ",
                "antimicrobial", "antibiotic", "amr ", "biosecurity",
                "nutrition", "obesity", "diabetes", "cancer", "oncolog",
                "cardiovascular", "heart disease", "stroke",
                "maternal", "child health", "infant mortalit", "neonatal",
                "ageing", "aging", "elderly", "dementia", "alzheimer",
                "health system", "universal health", "health coverage",
                "health equit", "health access", "health financ",
                "health workforce", "nursing", "physician",
                "public health", "epidemiol", "surveillance",
                "sanitation", "clean water", "hygiene",
                "tobacco", "alcohol", "substance",
                "disability", "rehabilitation",
                "health security", "health emergency", "outbreak",
                "covid", "coronavirus", "sars", "mers", "influenza", "flu ",
                "malaria", "tuberculosis", "hiv", "aids",
                "neglected tropical", "polio", "ebola", "mpox", "monkeypox",
            ]

            df_ch["is_health"] = df_ch["Full_Text"].apply(
                lambda txt: any(kw in txt for kw in HEALTH_KEYWORDS)
            )
            df_health = df_ch[df_ch["is_health"]].copy()

            if df_health.empty:
                st.warning("No healthcare-related articles found among Chatham House content.")
                st.info(f"Total Chatham House articles: {len(df_ch)}")
            else:
                # ── TOPIC CLASSIFICATION ──
                TOPIC_KEYWORDS = {
                    "Digital Health & Health Tech": ["digital health", "telemedicine", "telehealth", "ehealth", "e-health", "mhealth", "m-health", "wearable", "health tech", "health data", "electronic health", "ehr ", "emr ", "artificial intelligence"],
                    "Pandemic Preparedness": ["pandemic", "epidemic", "outbreak", "preparedness", "health emergency", "covid", "coronavirus", "sars", "mers", "influenza", "health security", "biosecurity"],
                    "Global Health Policy": ["who ", "world health", "universal health", "health coverage", "health system", "health reform", "global health", "health governance"],
                    "Pharma & Biotech": ["pharma", "drug", "vaccine", "vaccination", "biotech", "genomic", "gene therapy", "crispr", "therapeut", "clinical trial"],
                    "Infectious Disease": ["malaria", "tuberculosis", "hiv", "aids", "neglected tropical", "polio", "ebola", "mpox", "monkeypox", "antibiotic", "antimicrobial", "amr "],
                    "Mental Health": ["mental health", "wellbeing", "well-being", "psycholog", "psychiatr", "depression", "anxiety"],
                    "NCDs & Chronic Disease": ["cancer", "oncolog", "diabetes", "cardiovascular", "heart disease", "stroke", "obesity", "tobacco", "alcohol", "chronic"],
                    "Health Equity & Access": ["health equit", "health access", "health financ", "health workforce", "nursing", "physician", "inequality", "disparit"],
                    "Maternal & Child Health": ["maternal", "child health", "infant mortalit", "neonatal", "reproductive", "family planning"],
                    "Ageing & Dementia": ["ageing", "aging", "elderly", "dementia", "alzheimer", "older people", "geriatr"],
                    "Health & Climate": ["climate", "environment", "air quality", "pollution", "heat", "water", "sanitation"],
                    "Public Health": ["public health", "epidemiol", "surveillance", "nutrition", "hygiene", "prevention", "screening"],
                }

                def extract_topics(text):
                    text_lower = text.lower()
                    topics = []
                    for topic, keywords in TOPIC_KEYWORDS.items():
                        if any(kw in text_lower for kw in keywords):
                            topics.append(topic)
                    return topics if topics else ["General Healthcare"]

                # ── COUNTRY EXTRACTION ──
                COUNTRY_MAP = {
                    "united states": "United States", "usa": "United States", "us ": "United States", "america": "United States",
                    "united kingdom": "United Kingdom", "uk ": "United Kingdom", "britain": "United Kingdom", "england": "United Kingdom",
                    "china": "China", "chinese": "China", "beijing": "China",
                    "russia": "Russia", "russian": "Russia", "moscow": "Russia",
                    "india": "India", "indian": "India",
                    "brazil": "Brazil", "brazilian": "Brazil",
                    "germany": "Germany", "german": "Germany",
                    "france": "France", "french": "France",
                    "japan": "Japan", "japanese": "Japan",
                    "south korea": "South Korea", "korea": "South Korea",
                    "australia": "Australia", "australian": "Australia",
                    "canada": "Canada", "canadian": "Canada",
                    "italy": "Italy", "italian": "Italy",
                    "spain": "Spain", "spanish": "Spain",
                    "mexico": "Mexico", "mexican": "Mexico",
                    "indonesia": "Indonesia",
                    "turkey": "Turkey", "turkish": "Turkey",
                    "saudi arabia": "Saudi Arabia", "saudi": "Saudi Arabia",
                    "iran": "Iran", "iranian": "Iran",
                    "israel": "Israel", "israeli": "Israel",
                    "ukraine": "Ukraine", "ukrainian": "Ukraine",
                    "poland": "Poland", "polish": "Poland",
                    "nigeria": "Nigeria", "nigerian": "Nigeria",
                    "south africa": "South Africa",
                    "egypt": "Egypt", "egyptian": "Egypt",
                    "kenya": "Kenya", "kenyan": "Kenya",
                    "ethiopia": "Ethiopia",
                    "pakistan": "Pakistan",
                    "bangladesh": "Bangladesh",
                    "vietnam": "Vietnam",
                    "thailand": "Thailand",
                    "philippines": "Philippines",
                    "colombia": "Colombia",
                    "argentina": "Argentina",
                    "chile": "Chile",
                    "peru": "Peru",
                    "taiwan": "Taiwan",
                    "singapore": "Singapore",
                    "malaysia": "Malaysia",
                    "ghana": "Ghana",
                    "tanzania": "Tanzania",
                    "uganda": "Uganda",
                    "rwanda": "Rwanda",
                    "congo": "DR Congo",
                    "morocco": "Morocco",
                    "tunisia": "Tunisia",
                    "iraq": "Iraq",
                    "syria": "Syria",
                    "yemen": "Yemen",
                    "afghanistan": "Afghanistan",
                    "myanmar": "Myanmar",
                    "cambodia": "Cambodia",
                    "nepal": "Nepal",
                    "sri lanka": "Sri Lanka",
                    "sweden": "Sweden",
                    "norway": "Norway",
                    "denmark": "Denmark",
                    "finland": "Finland",
                    "netherlands": "Netherlands", "dutch": "Netherlands",
                    "belgium": "Belgium",
                    "switzerland": "Switzerland", "swiss": "Switzerland",
                    "austria": "Austria",
                    "portugal": "Portugal",
                    "greece": "Greece",
                    "ireland": "Ireland",
                    "czech": "Czech Republic",
                    "hungary": "Hungary",
                    "romania": "Romania",
                    "africa": "Africa (continent)",
                    "europe": "Europe (continent)",
                    "asia": "Asia (continent)",
                    "latin america": "Latin America",
                    "middle east": "Middle East",
                    "gaza": "Palestine", "palestine": "Palestine",
                }

                # Country coordinates for map
                COUNTRY_COORDS = {
                    "United States": (39.8, -98.5), "United Kingdom": (55.4, -3.4),
                    "China": (35.9, 104.2), "Russia": (61.5, 105.3),
                    "India": (20.6, 78.9), "Brazil": (-14.2, -51.9),
                    "Germany": (51.2, 10.4), "France": (46.2, 2.2),
                    "Japan": (36.2, 138.3), "South Korea": (35.9, 127.8),
                    "Australia": (-25.3, 133.8), "Canada": (56.1, -106.3),
                    "Italy": (41.9, 12.6), "Spain": (40.5, -3.7),
                    "Mexico": (23.6, -102.6), "Indonesia": (-0.8, 113.9),
                    "Turkey": (39.0, 35.2), "Saudi Arabia": (23.9, 45.1),
                    "Iran": (32.4, 53.7), "Israel": (31.0, 34.9),
                    "Ukraine": (48.4, 31.2), "Poland": (51.9, 19.1),
                    "Nigeria": (9.1, 8.7), "South Africa": (-30.6, 22.9),
                    "Egypt": (26.8, 30.8), "Kenya": (-0.02, 37.9),
                    "Ethiopia": (9.1, 40.5), "Pakistan": (30.4, 69.3),
                    "Bangladesh": (23.7, 90.4), "Vietnam": (14.1, 108.3),
                    "Thailand": (15.9, 100.9), "Philippines": (12.9, 121.8),
                    "Colombia": (4.6, -74.3), "Argentina": (-38.4, -63.6),
                    "Chile": (-35.7, -71.5), "Peru": (-9.2, -75.0),
                    "Taiwan": (23.7, 121.0), "Singapore": (1.4, 103.8),
                    "Malaysia": (4.2, 101.9), "Ghana": (7.9, -1.0),
                    "Tanzania": (-6.4, 34.9), "Uganda": (1.4, 32.3),
                    "Rwanda": (-1.9, 29.9), "DR Congo": (-4.0, 21.8),
                    "Morocco": (31.8, -7.1), "Tunisia": (33.9, 9.5),
                    "Iraq": (33.2, 43.7), "Syria": (35.0, 38.5),
                    "Yemen": (15.6, 48.5), "Afghanistan": (33.9, 67.7),
                    "Myanmar": (21.9, 95.9), "Cambodia": (12.6, 105.0),
                    "Nepal": (28.4, 84.1), "Sri Lanka": (7.9, 80.8),
                    "Sweden": (60.1, 18.6), "Norway": (60.5, 8.5),
                    "Denmark": (56.3, 9.5), "Finland": (61.9, 25.7),
                    "Netherlands": (52.1, 5.3), "Belgium": (50.5, 4.5),
                    "Switzerland": (46.8, 8.2), "Austria": (47.5, 14.6),
                    "Portugal": (39.4, -8.2), "Greece": (39.1, 21.8),
                    "Ireland": (53.1, -7.7), "Czech Republic": (49.8, 15.5),
                    "Hungary": (47.2, 19.5), "Romania": (45.9, 25.0),
                    "Palestine": (31.9, 35.2),
                }

                def extract_countries(text):
                    text_lower = text.lower()
                    found = set()
                    for keyword, country in COUNTRY_MAP.items():
                        if keyword in text_lower and not country.endswith("(continent)"):
                            found.add(country)
                    return list(found)

                df_health["Topics"] = df_health["Full_Text"].apply(extract_topics)
                df_health["PrimaryTopic"] = df_health["Topics"].apply(lambda x: x[0])
                df_health["Countries"] = df_health["Full_Text"].apply(extract_countries)

                all_topics = [t for topics in df_health["Topics"] for t in topics]
                all_countries = [c for countries in df_health["Countries"] for c in countries]
                topic_counts_all = Counter(all_topics)
                country_counts_all = Counter(all_countries)

                palette = [
                    "#0D7C66", "#1E3A5F", "#E85D04", "#7B2D8E",
                    "#D4A017", "#2E86AB", "#A23B72", "#F18F01",
                    "#C73E1D", "#44AF69", "#ECA72C", "#226F54",
                    "#DA627D", "#4A4E69", "#00B4D8", "#3B1F2B",
                ]

                # ════════════════════════════════════════
                # TABS LAYOUT
                # ════════════════════════════════════════
                tab_analysis, tab_notes, tab_links = st.tabs([
                    "📊 Analysis & Charts",
                    "📝 Notes & AI Analysis",
                    "🔗 Private Links"
                ])

                # ════════════════════════════════════════════════
                # TAB 1: ANALYSIS & CHARTS
                # ════════════════════════════════════════════════
                with tab_analysis:

                    # FILTRI
                    section_header("🔍 Filters")
                    fcol1, fcol2, fcol3 = st.columns([2, 2, 2])
                    with fcol1:
                        unique_topics = sorted(set(all_topics))
                        selected_topics = st.multiselect(
                            "📌 Filter by health topic", options=unique_topics,
                            default=[], help="Leave empty for all"
                        )
                    with fcol2:
                        valid_dates = df_health["Date"].dropna()
                        if not valid_dates.empty:
                            min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
                            date_range = st.date_input("📅 Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                        else:
                            date_range = None
                    with fcol3:
                        keyword_search = st.text_input("🔎 Keyword search", placeholder="e.g. pandemic, vaccine...")

                    filtered = df_health.copy()
                    if selected_topics:
                        filtered = filtered[filtered["Topics"].apply(lambda t: any(x in selected_topics for x in t))]
                    if date_range and len(date_range) == 2:
                        d_s, d_e = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
                        filtered = filtered[(filtered["Date"] >= d_s) & (filtered["Date"] <= d_e)]
                    if keyword_search.strip():
                        filtered = filtered[filtered["Full_Text"].str.contains(keyword_search.strip().lower(), na=False)]

                    filtered_topics = [t for topics in filtered["Topics"] for t in topics]
                    filtered_topic_counts = Counter(filtered_topics)
                    filtered_countries = [c for countries in filtered["Countries"] for c in countries]
                    filtered_country_counts = Counter(filtered_countries)

                    st.caption(f"**{len(filtered)}** healthcare articles out of {len(df_ch)} total")
                    st.markdown("---")

                    # KPIs
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        kpi_card("Health Articles", str(len(filtered)))
                    with c2:
                        this_month = len(filtered[filtered["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)])
                        kpi_card("This Month", str(this_month))
                    with c3:
                        kpi_card("Health Topics", str(len(set(filtered_topics))))
                    with c4:
                        kpi_card("Countries", str(len(set(filtered_countries))))

                    st.markdown("<br>", unsafe_allow_html=True)

                    # TREEMAP + SUNBURST
                    section_header("🗺️ Healthcare Topic Distribution")
                    col_tree, col_sun = st.columns(2)
                    with col_tree:
                        st.markdown("##### 🌳 Topic Treemap")
                        if filtered_topic_counts:
                            tc_df = pd.DataFrame(filtered_topic_counts.most_common(20), columns=["Topic", "Count"])
                            fig_tree = px.treemap(tc_df, path=["Topic"], values="Count", color="Count",
                                                   color_continuous_scale=["#0D7C66", "#1E3A5F", "#E85D04", "#7B2D8E"])
                            fig_tree.update_traces(textinfo="label+value", textfont_size=13, marker=dict(cornerradius=5))
                            style_plotly(fig_tree, height=420)
                            fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_tree, use_container_width=True)

                    with col_sun:
                        st.markdown("##### ☀️ Sunburst – Source / Topic")
                        sun_rows = []
                        for _, row in filtered.iterrows():
                            for t in row["Topics"]:
                                sun_rows.append({"Source": row["Source"], "Topic": t})
                        if sun_rows:
                            sun_df = pd.DataFrame(sun_rows)
                            sun_agg = sun_df.groupby(["Source", "Topic"]).size().reset_index(name="Count")
                            fig_sun = px.sunburst(sun_agg, path=["Source", "Topic"], values="Count", color="Count",
                                                   color_continuous_scale=["#2E86AB", "#E85D04", "#7B2D8E"])
                            style_plotly(fig_sun, height=420)
                            fig_sun.update_layout(margin=dict(t=10, l=10, r=10, b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_sun, use_container_width=True)

                    st.markdown("---")

                    # COUNTRY MAP
                    section_header("🌍 Country Mentions Map")
                    if filtered_country_counts:
                        map_data = []
                        for country, count in filtered_country_counts.most_common(30):
                            if country in COUNTRY_COORDS:
                                lat, lon = COUNTRY_COORDS[country]
                                map_data.append({"Country": country, "Mentions": count, "lat": lat, "lon": lon})
                        if map_data:
                            map_df = pd.DataFrame(map_data)
                            fig_map = px.scatter_geo(
                                map_df, lat="lat", lon="lon", size="Mentions",
                                hover_name="Country", color="Mentions",
                                color_continuous_scale=["#2E86AB", "#E85D04", "#C73E1D"],
                                size_max=30, projection="natural earth",
                            )
                            fig_map.update_geos(
                                showcoastlines=True, coastlinecolor="#ccc",
                                showland=True, landcolor="#F5F5F5",
                                showocean=True, oceancolor="#EBF5FB",
                                showlakes=False, showcountries=True, countrycolor="#ddd",
                            )
                            style_plotly(fig_map, height=450)
                            fig_map.update_layout(margin=dict(t=10, l=0, r=0, b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_map, use_container_width=True)

                        # Top countries bar
                        cc_df = pd.DataFrame(filtered_country_counts.most_common(15), columns=["Country", "Mentions"])
                        fig_cc = px.bar(cc_df, x="Mentions", y="Country", orientation="h", color="Mentions",
                                        color_continuous_scale=["#2E86AB", "#0D7C66", "#E85D04"])
                        style_plotly(fig_cc, height=350)
                        fig_cc.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig_cc, use_container_width=True)
                    else:
                        st.info("No country mentions detected.")

                    st.markdown("---")

                    # NETWORK GRAPH: COUNTRY × TOPIC
                    section_header("🕸️ Network Graph – Countries × Topics")
                    if filtered_countries and filtered_topics:
                        import json as _json

                        # Build edges: country ↔ topic co-occurrences
                        edges = Counter()
                        for _, row in filtered.iterrows():
                            for c in row["Countries"]:
                                for t in row["Topics"]:
                                    edges[(c, t)] += 1

                        top_edges = edges.most_common(50)
                        if top_edges:
                            nodes_set = set()
                            for (c, t), _ in top_edges:
                                nodes_set.add(("country", c))
                                nodes_set.add(("topic", t))

                            node_list = list(nodes_set)
                            node_idx = {n: i for i, n in enumerate(node_list)}

                            # Build Plotly network
                            import math

                            n = len(node_list)
                            positions = {}
                            countries_nodes = [nd for nd in node_list if nd[0] == "country"]
                            topics_nodes = [nd for nd in node_list if nd[0] == "topic"]

                            for i, nd in enumerate(countries_nodes):
                                angle = 2 * math.pi * i / max(len(countries_nodes), 1)
                                positions[nd] = (math.cos(angle) * 2, math.sin(angle) * 2)
                            for i, nd in enumerate(topics_nodes):
                                angle = 2 * math.pi * i / max(len(topics_nodes), 1)
                                positions[nd] = (math.cos(angle) * 1, math.sin(angle) * 1)

                            edge_x, edge_y = [], []
                            for (c, t), w in top_edges:
                                x0, y0 = positions[("country", c)]
                                x1, y1 = positions[("topic", t)]
                                edge_x += [x0, x1, None]
                                edge_y += [y0, y1, None]

                            import plotly.graph_objects as go

                            fig_net = go.Figure()

                            # Edges
                            max_w = max(w for _, w in top_edges)
                            fig_net.add_trace(go.Scatter(
                                x=edge_x, y=edge_y, mode="lines",
                                line=dict(width=0.8, color="rgba(150,150,150,0.4)"),
                                hoverinfo="none",
                            ))

                            # Country nodes
                            cx = [positions[("country", c)][0] for c in [nd[1] for nd in countries_nodes]]
                            cy = [positions[("country", c)][1] for c in [nd[1] for nd in countries_nodes]]
                            c_names = [nd[1] for nd in countries_nodes]
                            c_sizes = [filtered_country_counts.get(c, 1) for c in c_names]
                            max_cs = max(c_sizes) if c_sizes else 1
                            c_sizes_norm = [max(8, (s / max_cs) * 25) for s in c_sizes]

                            fig_net.add_trace(go.Scatter(
                                x=cx, y=cy, mode="markers+text",
                                marker=dict(size=c_sizes_norm, color="#E85D04", line=dict(width=1, color="white")),
                                text=c_names, textposition="top center", textfont=dict(size=9, color="#1E3A5F"),
                                hovertext=[f"{c}: {filtered_country_counts.get(c, 0)} mentions" for c in c_names],
                                hoverinfo="text", name="Countries",
                            ))

                            # Topic nodes
                            tx = [positions[("topic", t)][0] for t in [nd[1] for nd in topics_nodes]]
                            ty = [positions[("topic", t)][1] for t in [nd[1] for nd in topics_nodes]]
                            t_names = [nd[1] for nd in topics_nodes]
                            t_sizes = [filtered_topic_counts.get(t, 1) for t in t_names]
                            max_ts = max(t_sizes) if t_sizes else 1
                            t_sizes_norm = [max(8, (s / max_ts) * 25) for s in t_sizes]

                            fig_net.add_trace(go.Scatter(
                                x=tx, y=ty, mode="markers+text",
                                marker=dict(size=t_sizes_norm, color="#0D7C66", symbol="diamond",
                                            line=dict(width=1, color="white")),
                                text=t_names, textposition="bottom center", textfont=dict(size=8, color="#0D7C66"),
                                hovertext=[f"{t}: {filtered_topic_counts.get(t, 0)} articles" for t in t_names],
                                hoverinfo="text", name="Topics",
                            ))

                            style_plotly(fig_net, height=550)
                            fig_net.update_layout(
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                margin=dict(l=10, r=10, t=10, b=10),
                            )
                            st.plotly_chart(fig_net, use_container_width=True)
                        else:
                            st.info("Insufficient co-occurrences for network graph.")
                    else:
                        st.info("No country/topic data for network graph.")

                    st.markdown("---")

                    # SCATTER TIMELINE
                    section_header("⏱️ Healthcare Timeline")
                    tl = filtered.dropna(subset=["Date"]).copy()
                    if not tl.empty:
                        tl["TopicCount"] = tl["Topics"].apply(len).clip(lower=1)
                        fig_scatter = px.scatter(
                            tl, x="Date", y="PrimaryTopic", size="TopicCount", color="PrimaryTopic",
                            hover_name="Title", color_discrete_sequence=palette, size_max=18, opacity=0.8)
                        style_plotly(fig_scatter, height=400)
                        fig_scatter.update_layout(xaxis_title="", yaxis_title="", showlegend=False, margin=dict(l=10, r=10, t=10, b=40))
                        fig_scatter.update_xaxes(dtick="M1", tickformat="%b %Y")
                        st.plotly_chart(fig_scatter, use_container_width=True)

                    st.markdown("---")

                    # WORD CLOUD + FREQUENCY
                    section_header("💬 Text Analysis")
                    corpus = " ".join(filtered["Title"].dropna().tolist() + filtered["Summary"].dropna().tolist()).lower()
                    stop_words = {
                        "the","a","an","and","or","but","in","on","at","to","for","of","with","by","from",
                        "is","it","this","that","are","was","were","be","been","being","have","has","had",
                        "do","does","did","will","would","could","should","may","might","shall","can","need",
                        "not","no","its","as","if","than","then","so","up","out","about","into","over","after",
                        "under","between","through","during","before","above","below","more","most","other",
                        "some","such","only","own","same","also","how","all","each","every","both","few",
                        "many","much","any","which","what","who","whom","when","where","why","their","them",
                        "they","he","she","we","you","his","her","our","your","s","new","one","two","us",
                        "my","me","these","those","chatham","house","international","affairs","think","tank",
                    }
                    words = re_ch.findall(r"[a-z]{3,}", corpus)
                    words = [w for w in words if w not in stop_words]
                    word_freq = Counter(words)
                    top_words = word_freq.most_common(30)

                    wc_col, freq_col = st.columns(2)
                    with wc_col:
                        st.markdown("##### ☁️ Word Cloud")
                        if top_words:
                            try:
                                from wordcloud import WordCloud
                                import matplotlib.pyplot as plt
                                wc = WordCloud(width=800, height=400, background_color="white", colormap="viridis",
                                               max_words=80, prefer_horizontal=0.7, contour_width=1, contour_color="#0D7C66"
                                ).generate_from_frequencies(dict(top_words))
                                fig_wc, ax_wc = plt.subplots(figsize=(10, 5))
                                ax_wc.imshow(wc, interpolation="bilinear"); ax_wc.axis("off")
                                st.pyplot(fig_wc, use_container_width=True); plt.close(fig_wc)
                            except ImportError:
                                tw_df = pd.DataFrame(top_words[:15], columns=["Word", "Count"])
                                fig_fb = px.bar(tw_df, x="Count", y="Word", orientation="h", color="Count",
                                                color_continuous_scale=["#0D7C66", "#E85D04"])
                                style_plotly(fig_fb, height=350)
                                fig_fb.update_layout(showlegend=False, coloraxis_showscale=False)
                                st.plotly_chart(fig_fb, use_container_width=True)

                    with freq_col:
                        st.markdown("##### 📊 Top 20 Words")
                        if top_words:
                            tw_df = pd.DataFrame(top_words[:20], columns=["Word", "Frequency"])
                            fig_freq = px.bar(tw_df, x="Frequency", y="Word", orientation="h", color="Frequency",
                                              color_continuous_scale=["#2E86AB", "#0D7C66", "#E85D04"], text="Frequency")
                            fig_freq.update_traces(textposition="outside", textfont_size=11)
                            style_plotly(fig_freq, height=480)
                            fig_freq.update_layout(yaxis=dict(autorange="reversed"), showlegend=False,
                                                    coloraxis_showscale=False, margin=dict(l=10, r=60, t=10, b=10))
                            st.plotly_chart(fig_freq, use_container_width=True)

                    st.markdown("---")

                    # KEYWORD TREND
                    section_header("📈 Health Keyword Trends")
                    top_kw = [w for w, _ in top_words[:8]]
                    tl_kw = filtered.dropna(subset=["Date"]).copy()
                    if not tl_kw.empty and top_kw:
                        tl_kw["YM"] = tl_kw["Date"].dt.to_period("M").astype(str)
                        kw_rows = []
                        for _, row in tl_kw.iterrows():
                            txt = row["Full_Text"]
                            for kw in top_kw:
                                if kw in txt:
                                    kw_rows.append({"Month": row["YM"], "Keyword": kw})
                        if kw_rows:
                            kw_df = pd.DataFrame(kw_rows)
                            kw_agg = kw_df.groupby(["Month", "Keyword"]).size().reset_index(name="Mentions")
                            fig_trend = px.line(kw_agg, x="Month", y="Mentions", color="Keyword",
                                                markers=True, color_discrete_sequence=palette)
                            style_plotly(fig_trend, height=380)
                            fig_trend.update_layout(xaxis_title="Month", yaxis_title="Mentions",
                                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
                            st.plotly_chart(fig_trend, use_container_width=True)

                    st.markdown("---")

                    # HEATMAP
                    section_header("🔥 Seasonality Heatmap")
                    heat = filtered.dropna(subset=["Date"]).copy()
                    if not heat.empty:
                        heat_rows = []
                        for _, row in heat.iterrows():
                            for t in row["Topics"]:
                                heat_rows.append({"Month": row["Date"].strftime("%b"), "MonthNum": row["Date"].month, "Topic": t})
                        if heat_rows:
                            heat_df = pd.DataFrame(heat_rows)
                            heat_pivot = heat_df.pivot_table(index="Topic", columns="Month", values="MonthNum", aggfunc="count", fill_value=0)
                            month_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
                            ordered = [m for m in month_order if m in heat_pivot.columns]
                            heat_pivot = heat_pivot[ordered]
                            top_tp = [t for t, _ in filtered_topic_counts.most_common(15)]
                            heat_pivot = heat_pivot[heat_pivot.index.isin(top_tp)]
                            if not heat_pivot.empty:
                                fig_heat = px.imshow(heat_pivot.values, x=heat_pivot.columns.tolist(), y=heat_pivot.index.tolist(),
                                                     color_continuous_scale=["#F0F4F8", "#2E86AB", "#0D7C66", "#E85D04"],
                                                     aspect="auto", text_auto=True)
                                style_plotly(fig_heat, height=max(300, len(heat_pivot) * 35 + 80))
                                fig_heat.update_layout(xaxis_title="Month", yaxis_title="", coloraxis_showscale=False)
                                st.plotly_chart(fig_heat, use_container_width=True)

                    st.markdown("---")

                    # ARTICLES
                    section_header("📰 Healthcare Articles")
                    sort_opt = st.selectbox("Sort by", ["Most recent", "Alphabetical"], index=0)
                    display = filtered.sort_values("Date", ascending=False) if sort_opt == "Most recent" else filtered.sort_values("Title")
                    PAGE_SIZE = 12
                    total_pages = max(1, -(-len(display) // PAGE_SIZE))
                    page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
                    start_idx = (page_num - 1) * PAGE_SIZE
                    page_slice = display.iloc[start_idx : start_idx + PAGE_SIZE]

                    for _, row in page_slice.iterrows():
                        topics_html = " ".join(
                            f'<span style="background:#EBF5FB; color:#1A6B8A; padding:2px 8px; '
                            f'border-radius:12px; font-size:0.72rem; margin-right:3px;">{t}</span>'
                            for t in row["Topics"][:5])
                        countries_html = " ".join(
                            f'<span style="background:#FFF3E0; color:#E85D04; padding:2px 8px; '
                            f'border-radius:12px; font-size:0.72rem; margin-right:3px;">🌍 {c}</span>'
                            for c in row["Countries"][:3])
                        date_str = row["Date"].strftime("%d %b %Y") if pd.notna(row["Date"]) else ""
                        summary_text = row["Summary"].replace("Chatham House", "").strip()

                        st.markdown(f"""
                        <div style="background:#FFFFFF; border-left:4px solid #0D7C66;
                                    padding:1rem 1.2rem; margin:0.4rem 0; border-radius:0 6px 6px 0;
                                    box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <a href="{row['URL']}" target="_blank"
                                   style="color:#0D2B45; font-weight:600; font-size:0.95rem; text-decoration:none;">
                                    {row['Title'][:120]}
                                </a>
                                <span style="color:#95A5A6; font-size:0.75rem; white-space:nowrap; margin-left:1rem;">{date_str}</span>
                            </div>
                            <div style="margin:0.3rem 0;">{topics_html} {countries_html}</div>
                            <div style="color:#7F8C8D; font-size:0.85rem; line-height:1.5; margin-top:0.3rem;">
                                {summary_text[:200]}{'...' if len(summary_text) > 200 else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.caption(f"Page {page_num} of {total_pages} — {len(display)} healthcare articles")
                    with st.expander("📋 Full Table"):
                        st.dataframe(filtered[["Date", "Title", "PrimaryTopic", "Source"]].sort_values("Date", ascending=False),
                                     use_container_width=True, hide_index=True)

                # ════════════════════════════════════════════════
                # TAB 2: NOTES & AI ANALYSIS
                # ════════════════════════════════════════════════
                with tab_notes:
                    section_header("📝 Personal Notes & AI Semantic Analysis")

                    st.markdown("""
                    <div style="background:#F0F8FF; border:1px solid #B8D4E3; padding:12px 16px; border-radius:8px; margin-bottom:16px;">
                        <strong>How to use:</strong> Select an article below, add your personal notes, and click
                        <em>Save & Analyze</em> to run AI keyword and country extraction on your notes.
                    </div>
                    """, unsafe_allow_html=True)

                    # Article selector
                    article_titles = df_health["Title"].tolist()
                    selected_article = st.selectbox("📄 Select article to annotate", options=article_titles, index=0)
                    sel_row = df_health[df_health["Title"] == selected_article].iloc[0]

                    st.markdown(f"""
                    <div style="background:#FAFAFA; padding:10px 14px; border-radius:6px; border:1px solid #eee; margin:8px 0;">
                        <strong>{sel_row['Title']}</strong><br>
                        <span style="color:#666; font-size:0.85rem;">
                            📅 {sel_row['Date'].strftime('%d %b %Y') if pd.notna(sel_row['Date']) else 'N/A'} |
                            🏷️ {', '.join(sel_row['Topics'][:3])} |
                            🌍 {', '.join(sel_row['Countries'][:3]) if sel_row['Countries'] else 'N/A'}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Load existing note
                    doc_id = int(sel_row["DocID"])
                    existing_note = session.execute(
                        sa_text("SELECT note_text, private_url, ai_keywords, ai_countries FROM chatham_notes WHERE document_id = :did ORDER BY updated_at DESC LIMIT 1"),
                        {"did": doc_id}
                    ).fetchone()

                    default_note = existing_note[0] if existing_note else ""
                    default_url = existing_note[1] if existing_note else ""
                    default_kw = existing_note[2] if existing_note else ""
                    default_countries = existing_note[3] if existing_note else ""

                    ncol1, ncol2 = st.columns([3, 1])
                    with ncol1:
                        note_text = st.text_area("✏️ Your notes", value=default_note, height=200,
                                                  placeholder="Write your analysis, observations, key takeaways...")
                        private_url = st.text_input("🔗 Private Chatham House link", value=default_url,
                                                     placeholder="https://www.chathamhouse.org/members/...")

                    with ncol2:
                        st.markdown("##### 🤖 AI Extracted")
                        if default_kw:
                            st.markdown(f"**Keywords:** {default_kw}")
                        if default_countries:
                            st.markdown(f"**Countries:** {default_countries}")
                        if not default_kw and not default_countries:
                            st.caption("Save & Analyze to extract keywords and countries from your notes.")

                    if st.button("💾 Save & Analyze", type="primary"):
                        # AI-like semantic extraction from notes
                        combined_text = (note_text + " " + sel_row["Title"] + " " + sel_row["Summary"]).lower()

                        # Extract keywords (top meaningful words from note)
                        note_words = re_ch.findall(r"[a-z]{3,}", combined_text)
                        note_words = [w for w in note_words if w not in stop_words and len(w) > 3]
                        ai_kw = ", ".join([w for w, _ in Counter(note_words).most_common(10)])

                        # Extract countries from notes
                        ai_countries_list = extract_countries(combined_text)
                        ai_countries = ", ".join(ai_countries_list) if ai_countries_list else ""

                        # Upsert note
                        if existing_note:
                            session.execute(sa_text("""
                                UPDATE chatham_notes SET note_text = :note, private_url = :url,
                                ai_keywords = :kw, ai_countries = :cc, updated_at = NOW()
                                WHERE document_id = :did
                            """), {"note": note_text, "url": private_url, "kw": ai_kw, "cc": ai_countries, "did": doc_id})
                        else:
                            session.execute(sa_text("""
                                INSERT INTO chatham_notes (document_id, note_text, private_url, ai_keywords, ai_countries)
                                VALUES (:did, :note, :url, :kw, :cc)
                            """), {"did": doc_id, "note": note_text, "url": private_url, "kw": ai_kw, "cc": ai_countries})
                        session.commit()
                        st.success(f"✅ Saved! AI extracted **{len(ai_kw.split(', '))}** keywords and **{len(ai_countries_list)}** countries.")
                        st.rerun()

                    # Show all notes
                    st.markdown("---")
                    section_header("📋 All Notes")
                    all_notes = session.execute(sa_text("""
                        SELECT cn.document_id, cn.note_text, cn.private_url, cn.ai_keywords, cn.ai_countries, cn.updated_at, d.title
                        FROM chatham_notes cn
                        JOIN documents d ON cn.document_id = d.document_id
                        ORDER BY cn.updated_at DESC
                    """)).fetchall()

                    if all_notes:
                        for n in all_notes:
                            with st.expander(f"📄 {n[6][:80]} — {n[5].strftime('%d %b %Y') if n[5] else ''}"):
                                st.markdown(f"**Notes:** {n[1]}")
                                if n[2]:
                                    st.markdown(f"**Private link:** [{n[2][:60]}...]({n[2]})")
                                if n[3]:
                                    kw_html = " ".join(f'<span style="background:#E8F5E9; color:#2E7D32; padding:2px 6px; border-radius:10px; font-size:0.75rem;">{k.strip()}</span>' for k in n[3].split(","))
                                    st.markdown(f"**AI Keywords:** {kw_html}", unsafe_allow_html=True)
                                if n[4]:
                                    st.markdown(f"**AI Countries:** 🌍 {n[4]}")
                    else:
                        st.info("No notes yet. Select an article and add your first note!")

                # ════════════════════════════════════════════════
                # TAB 3: PRIVATE LINKS
                # ════════════════════════════════════════════════
                with tab_links:
                    section_header("🔗 Private Chatham House Links")

                    st.markdown("""
                    <div style="background:#FFF8E1; border:1px solid #FFE082; padding:12px 16px; border-radius:8px; margin-bottom:16px;">
                        <strong>Add private links</strong> from your Chatham House membership area.
                        AI will extract keywords and countries automatically.
                    </div>
                    """, unsafe_allow_html=True)

                    # Add new link form
                    with st.form("add_private_link", clear_on_submit=True):
                        lk_url = st.text_input("🔗 URL", placeholder="https://www.chathamhouse.org/members/...")
                        lk_title = st.text_input("📄 Title", placeholder="Article or report title")
                        lk_desc = st.text_area("📝 Description / Notes", height=100,
                                                placeholder="Your summary or key observations...")
                        submitted = st.form_submit_button("➕ Add Link & Analyze", type="primary")

                        if submitted and lk_url.strip():
                            # AI extraction
                            combined = (lk_title + " " + lk_desc).lower()
                            lk_words = re_ch.findall(r"[a-z]{3,}", combined)
                            lk_words = [w for w in lk_words if w not in stop_words and len(w) > 3]
                            lk_kw = ", ".join([w for w, _ in Counter(lk_words).most_common(10)])
                            lk_countries = ", ".join(extract_countries(combined))

                            # AI summary (first 2 sentences of description or title)
                            lk_summary = lk_desc[:300] if lk_desc else lk_title

                            session.execute(sa_text("""
                                INSERT INTO chatham_private_links (url, title, description, ai_keywords, ai_countries, ai_summary)
                                VALUES (:url, :title, :desc, :kw, :cc, :summary)
                            """), {"url": lk_url, "title": lk_title, "desc": lk_desc,
                                   "kw": lk_kw, "cc": lk_countries, "summary": lk_summary})
                            session.commit()
                            st.success(f"✅ Link added! AI found {len(lk_kw.split(', '))} keywords.")
                            st.rerun()

                    # Display existing links
                    st.markdown("---")
                    private_links = session.execute(sa_text("""
                        SELECT link_id, url, title, description, ai_keywords, ai_countries, created_at
                        FROM chatham_private_links
                        ORDER BY created_at DESC
                    """)).fetchall()

                    if private_links:
                        st.markdown(f"**{len(private_links)} private links saved**")
                        for lk in private_links:
                            lk_id, lk_url, lk_title, lk_desc, lk_kw, lk_cc, lk_date = lk

                            kw_pills = ""
                            if lk_kw:
                                kw_pills = " ".join(
                                    f'<span style="background:#E8F5E9; color:#2E7D32; padding:2px 6px; border-radius:10px; font-size:0.72rem;">{k.strip()}</span>'
                                    for k in lk_kw.split(",")[:8])

                            cc_pills = ""
                            if lk_cc:
                                cc_pills = " ".join(
                                    f'<span style="background:#FFF3E0; color:#E85D04; padding:2px 6px; border-radius:10px; font-size:0.72rem;">🌍 {c.strip()}</span>'
                                    for c in lk_cc.split(",")[:5])

                            st.markdown(f"""
                            <div style="background:#FFFFFF; border-left:4px solid #7B2D8E;
                                        padding:1rem 1.2rem; margin:0.4rem 0; border-radius:0 6px 6px 0;
                                        box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
                                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                    <a href="{lk_url}" target="_blank"
                                       style="color:#7B2D8E; font-weight:600; font-size:0.95rem; text-decoration:none;">
                                        🔒 {lk_title or lk_url[:80]}
                                    </a>
                                    <span style="color:#95A5A6; font-size:0.75rem;">{lk_date.strftime('%d %b %Y') if lk_date else ''}</span>
                                </div>
                                <div style="margin:0.3rem 0;">{kw_pills} {cc_pills}</div>
                                <div style="color:#7F8C8D; font-size:0.85rem; margin-top:0.3rem;">
                                    {(lk_desc or '')[:200]}{'...' if lk_desc and len(lk_desc) > 200 else ''}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Delete button
                            if st.button(f"🗑️ Delete", key=f"del_link_{lk_id}"):
                                session.execute(sa_text("DELETE FROM chatham_private_links WHERE link_id = :lid"), {"lid": lk_id})
                                session.commit()
                                st.rerun()
                    else:
                        st.info("No private links yet. Add your first Chatham House member link above!")

        else:
            st.info("No Chatham House articles yet. Run the collector:")
            st.code('python -c "from collectors.chatham_collector import run; run()"')

    finally:
        session.close()

    page_footer()
