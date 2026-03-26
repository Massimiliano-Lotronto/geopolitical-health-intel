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
        font-size: 0.84rem;
        font-weight: 400;
        color: #3D4F5F;
        padding: 0.45rem 0.9rem;
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
        border-left-color: #C0CDD8;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        color: #0D2B45;
        font-weight: 600;
        background: rgba(13,124,102,0.06);
        border-left-color: #0D7C66;
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
        color: #3D4F5F;
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
        color: #3D4F5F;
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
    # ── CUSTOM CSS FOR SIDEBAR ──
    st.markdown("""
    <style>
        /* Sidebar radio buttons — compact & elegant */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 0px !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            padding: 6px 12px !important;
            margin: 0 !important;
            border-radius: 6px !important;
            font-size: 0.82rem !important;
            transition: all 0.15s ease !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(13, 43, 69, 0.05) !important;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {
            background: rgba(13, 124, 102, 0.08) !important;
            border-left: 3px solid #0D7C66 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ── BRANDING ──
    st.markdown("""
        <div style="text-align:center; padding:1rem 0 0.5rem 0;">
            <div style="width:44px; height:44px; border-radius:10px;
                        background:linear-gradient(145deg, #0D2B45 0%, #1A5276 50%, #0D7C66 100%);
                        margin:0 auto 10px auto; display:flex; align-items:center; justify-content:center;
                        box-shadow: 0 2px 8px rgba(13,43,69,0.25);">
                <span style="font-size:1.3rem; line-height:44px; display:block; text-align:center;">🛡️</span>
            </div>
            <div style="font-family:'Georgia', serif; font-size:1.1rem;
                        color:#0D2B45; font-weight:700; letter-spacing:0.01em; line-height:1.2;">
                BrAIn Democracy
            </div>
            <div style="font-size:0.56rem; color:#8899AA; text-transform:uppercase;
                        letter-spacing:0.18em; margin-top:3px; font-weight:500;">
                Intelligence Platform
            </div>
            <div style="margin-top:8px;">
                <span style="font-size:0.52rem; color:#0D7C66; font-weight:700; letter-spacing:0.08em;
                             background:rgba(13,124,102,0.08); padding:3px 10px; border-radius:10px;
                             border:1px solid rgba(13,124,102,0.15);">
                    ● LIVE — TS/SCI
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── SECTION HEADER HELPER ──
    def _nav_section(icon, title):
        st.markdown(f"""
            <div style="margin:16px 0 4px 4px; padding:0;">
                <span style="font-size:0.58rem; font-weight:700; color:#7A8A99;
                            text-transform:uppercase; letter-spacing:0.16em;">
                    {icon} {title}
                </span>
                <div style="height:1px; background:linear-gradient(90deg, #D0D8E0 0%, transparent 80%);
                            margin-top:3px;"></div>
            </div>
        """, unsafe_allow_html=True)

    # ── SECTION 1: STRATEGIC OVERVIEW ──
    _nav_section("◆", "Strategic Overview")

    page = st.radio(
        "nav",
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
            "🇨🇳 China Health",
            "💼 LinkedIn NeuroHealth",
            "🤖 AI Agent Hospital",
        ],
        label_visibility="collapsed",
        key="main_nav",
        format_func=lambda x: x,
    )


    # ── SIDEBAR FOOTER ──
    st.markdown("""
        <div style="margin-top:20px; padding:10px 8px; text-align:center;
                    border-top:1px solid #E0DCD7;">
            <div style="font-size:0.5rem; color:#AAA; letter-spacing:0.06em; line-height:1.6;">
                BrAIn Democracy Intel Platform<br>
                <span style="color:#C0C0C0;">v3.0 · Confidential · Need-to-Know</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.68rem; font-weight:600; color:#7A8A99; '
                'text-transform:uppercase; letter-spacing:0.12em; margin-bottom:0.5rem;">'
                '🎛️ Filters</p>', unsafe_allow_html=True)

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
        from sqlalchemy import text as sa_text
        try:
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS chatham_notes (
                note_id SERIAL PRIMARY KEY, document_id INTEGER REFERENCES documents(document_id) ON DELETE CASCADE,
                note_text TEXT, private_url TEXT, ai_keywords TEXT, ai_countries TEXT,
                ai_sentiment VARCHAR(20), created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"""))
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS chatham_private_links (
                link_id SERIAL PRIMARY KEY, url TEXT NOT NULL, title TEXT, description TEXT,
                ai_keywords TEXT, ai_countries TEXT, ai_summary TEXT, created_at TIMESTAMP DEFAULT NOW())"""))
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
                "DocID": d.document_id, "Date": d.publish_date,
                "Title": d.title or "", "Source": s.source_name,
                "URL": d.url or "", "Summary": (d.summary or ""),
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
                "antimicrobial", "antibiotic", "amr ", "biosecurity",
                "nutrition", "obesity", "diabetes", "cancer", "oncolog",
                "cardiovascular", "heart disease", "stroke",
                "maternal", "child health", "infant mortalit", "neonatal",
                "ageing", "aging", "elderly", "dementia", "alzheimer",
                "health system", "universal health", "health coverage",
                "health equit", "health access", "health financ",
                "public health", "epidemiol", "surveillance",
                "health security", "health emergency", "outbreak",
                "covid", "coronavirus", "sars", "influenza",
                "malaria", "tuberculosis", "hiv", "aids", "ebola", "mpox",
            ]

            df_ch["is_health"] = df_ch["Full_Text"].apply(lambda txt: any(kw in txt for kw in HEALTH_KEYWORDS))
            df_health = df_ch[df_ch["is_health"]].copy()

            if df_health.empty:
                st.warning("No healthcare-related articles found.")
                st.info(f"Total Chatham House articles: {len(df_ch)}")
            else:
                # ── TOPIC CLASSIFICATION ──
                TOPIC_KEYWORDS = {
                    "Digital Health & Health Tech": ["digital health", "telemedicine", "telehealth", "ehealth", "wearable", "health tech", "health data", "artificial intelligence"],
                    "Pandemic Preparedness": ["pandemic", "epidemic", "outbreak", "preparedness", "health emergency", "covid", "coronavirus", "health security", "biosecurity"],
                    "Global Health Policy": ["who ", "world health", "universal health", "health coverage", "health system", "global health"],
                    "Pharma & Biotech": ["pharma", "drug", "vaccine", "vaccination", "biotech", "genomic", "gene therapy", "crispr", "clinical trial"],
                    "Infectious Disease": ["malaria", "tuberculosis", "hiv", "aids", "polio", "ebola", "mpox", "antibiotic", "antimicrobial"],
                    "Mental Health": ["mental health", "wellbeing", "well-being", "psycholog", "psychiatr", "depression", "anxiety"],
                    "NCDs & Chronic Disease": ["cancer", "oncolog", "diabetes", "cardiovascular", "heart disease", "stroke", "obesity", "chronic"],
                    "Health Equity & Access": ["health equit", "health access", "health financ", "health workforce", "inequality"],
                    "Maternal & Child Health": ["maternal", "child health", "infant mortalit", "neonatal", "reproductive"],
                    "Ageing & Dementia": ["ageing", "aging", "elderly", "dementia", "alzheimer", "older people"],
                    "Health & Climate": ["climate", "environment", "air quality", "pollution", "sanitation"],
                    "Public Health": ["public health", "epidemiol", "surveillance", "nutrition", "prevention"],
                }

                COUNTRY_MAP = {
                    "united states": "United States", "usa": "United States", "america": "United States",
                    "united kingdom": "United Kingdom", "uk ": "United Kingdom", "britain": "United Kingdom",
                    "china": "China", "chinese": "China", "russia": "Russia", "russian": "Russia",
                    "india": "India", "brazil": "Brazil", "germany": "Germany", "france": "France",
                    "japan": "Japan", "south korea": "South Korea", "australia": "Australia", "canada": "Canada",
                    "italy": "Italy", "spain": "Spain", "mexico": "Mexico", "indonesia": "Indonesia",
                    "turkey": "Turkey", "saudi arabia": "Saudi Arabia", "iran": "Iran", "israel": "Israel",
                    "ukraine": "Ukraine", "nigeria": "Nigeria", "south africa": "South Africa",
                    "egypt": "Egypt", "kenya": "Kenya", "pakistan": "Pakistan", "bangladesh": "Bangladesh",
                    "vietnam": "Vietnam", "thailand": "Thailand", "philippines": "Philippines",
                    "colombia": "Colombia", "argentina": "Argentina", "taiwan": "Taiwan",
                    "singapore": "Singapore", "malaysia": "Malaysia", "ghana": "Ghana",
                    "iraq": "Iraq", "syria": "Syria", "yemen": "Yemen", "afghanistan": "Afghanistan",
                    "sweden": "Sweden", "norway": "Norway", "netherlands": "Netherlands",
                    "switzerland": "Switzerland", "ireland": "Ireland", "poland": "Poland",
                    "gaza": "Palestine", "palestine": "Palestine", "africa": "Africa (region)",
                    "europe": "Europe (region)", "middle east": "Middle East (region)",
                }

                COUNTRY_COORDS = {
                    "United States": (39.8, -98.5), "United Kingdom": (55.4, -3.4),
                    "China": (35.9, 104.2), "Russia": (61.5, 105.3), "India": (20.6, 78.9),
                    "Brazil": (-14.2, -51.9), "Germany": (51.2, 10.4), "France": (46.2, 2.2),
                    "Japan": (36.2, 138.3), "South Korea": (35.9, 127.8), "Australia": (-25.3, 133.8),
                    "Canada": (56.1, -106.3), "Italy": (41.9, 12.6), "Spain": (40.5, -3.7),
                    "Nigeria": (9.1, 8.7), "South Africa": (-30.6, 22.9), "Egypt": (26.8, 30.8),
                    "Kenya": (-0.02, 37.9), "Pakistan": (30.4, 69.3), "Iran": (32.4, 53.7),
                    "Israel": (31.0, 34.9), "Ukraine": (48.4, 31.2), "Turkey": (39.0, 35.2),
                    "Saudi Arabia": (23.9, 45.1), "Indonesia": (-0.8, 113.9),
                    "Mexico": (23.6, -102.6), "Thailand": (15.9, 100.9),
                    "Vietnam": (14.1, 108.3), "Philippines": (12.9, 121.8),
                    "Colombia": (4.6, -74.3), "Argentina": (-38.4, -63.6),
                    "Taiwan": (23.7, 121.0), "Singapore": (1.4, 103.8),
                    "Malaysia": (4.2, 101.9), "Ghana": (7.9, -1.0),
                    "Sweden": (60.1, 18.6), "Netherlands": (52.1, 5.3),
                    "Switzerland": (46.8, 8.2), "Ireland": (53.1, -7.7),
                    "Poland": (51.9, 19.1), "Palestine": (31.9, 35.2),
                    "Iraq": (33.2, 43.7), "Syria": (35.0, 38.5), "Afghanistan": (33.9, 67.7),
                    "Bangladesh": (23.7, 90.4), "Norway": (60.5, 8.5),
                }

                def extract_topics(text):
                    topics = []
                    for topic, kws in TOPIC_KEYWORDS.items():
                        if any(kw in text for kw in kws):
                            topics.append(topic)
                    return topics if topics else ["General Healthcare"]

                def extract_countries(text):
                    found = set()
                    for kw, country in COUNTRY_MAP.items():
                        if kw in text and not country.endswith("(region)"):
                            found.add(country)
                    return list(found)

                df_health["Topics"] = df_health["Full_Text"].apply(extract_topics)
                df_health["PrimaryTopic"] = df_health["Topics"].apply(lambda x: x[0])
                df_health["Countries"] = df_health["Full_Text"].apply(extract_countries)

                all_topics = [t for ts in df_health["Topics"] for t in ts]
                all_countries = [c for cs in df_health["Countries"] for c in cs]
                topic_counts_all = Counter(all_topics)
                country_counts_all = Counter(all_countries)

                palette = ["#0D7C66", "#1E3A5F", "#E85D04", "#7B2D8E", "#D4A017", "#2E86AB",
                            "#A23B72", "#F18F01", "#C73E1D", "#44AF69", "#ECA72C", "#226F54",
                            "#DA627D", "#4A4E69", "#00B4D8", "#3B1F2B"]

                stop_words = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","from","is","it","this","that","are","was","were","be","been","have","has","had","do","does","did","will","would","could","should","not","no","its","as","if","than","so","up","out","about","into","over","after","under","between","through","during","before","more","most","other","some","also","all","each","both","few","many","much","any","which","what","who","when","where","why","their","them","they","he","she","we","you","his","her","our","your","s","new","one","two","us","my","me","these","those","chatham","house","international","affairs","think","tank"}

                tab_analysis, tab_notes, tab_links = st.tabs(["📊 Analysis & Charts", "📝 Notes & AI Analysis", "🔗 Private Links"])

                # ════════════════ TAB 1: ANALYSIS ════════════════
                with tab_analysis:
                    section_header("🔍 Filters")
                    fcol1, fcol2, fcol3 = st.columns([2, 2, 2])
                    with fcol1:
                        selected_topics = st.multiselect("📌 Health topic", sorted(set(all_topics)), default=[], help="Leave empty for all")
                    with fcol2:
                        valid_dates = df_health["Date"].dropna()
                        date_range = st.date_input("📅 Date range", value=(valid_dates.min().date(), valid_dates.max().date()), min_value=valid_dates.min().date(), max_value=valid_dates.max().date()) if not valid_dates.empty else None
                    with fcol3:
                        keyword_search = st.text_input("🔎 Keyword search", placeholder="e.g. pandemic, vaccine...")

                    filtered = df_health.copy()
                    if selected_topics:
                        filtered = filtered[filtered["Topics"].apply(lambda t: any(x in selected_topics for x in t))]
                    if date_range and len(date_range) == 2:
                        filtered = filtered[(filtered["Date"] >= pd.Timestamp(date_range[0])) & (filtered["Date"] <= pd.Timestamp(date_range[1]))]
                    if keyword_search.strip():
                        filtered = filtered[filtered["Full_Text"].str.contains(keyword_search.strip().lower(), na=False)]

                    filtered_topics = [t for ts in filtered["Topics"] for t in ts]
                    filtered_topic_counts = Counter(filtered_topics)
                    filtered_countries = [c for cs in filtered["Countries"] for c in cs]
                    filtered_country_counts = Counter(filtered_countries)

                    st.caption(f"**{len(filtered)}** healthcare articles out of {len(df_ch)} total")
                    st.markdown("---")

                    # KPIs
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: kpi_card("Health Articles", str(len(filtered)))
                    with c2: kpi_card("This Month", str(len(filtered[filtered["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)])))
                    with c3: kpi_card("Health Topics", str(len(set(filtered_topics))))
                    with c4: kpi_card("Countries", str(len(set(filtered_countries))))

                    st.markdown("<br>", unsafe_allow_html=True)

                    # TREEMAP + SUNBURST
                    section_header("🗺️ Healthcare Topic Distribution")
                    col_t, col_s = st.columns(2)
                    with col_t:
                        st.markdown("##### 🌳 Health Topic Treemap")
                        if filtered_topic_counts:
                            tc_df = pd.DataFrame(filtered_topic_counts.most_common(20), columns=["Topic", "Count"])
                            fig_tree = px.treemap(tc_df, path=["Topic"], values="Count", color="Count", color_continuous_scale=["#0D7C66", "#1E3A5F", "#E85D04", "#7B2D8E"])
                            fig_tree.update_traces(textinfo="label+value", textfont_size=13, marker=dict(cornerradius=5))
                            style_plotly(fig_tree, height=420); fig_tree.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_tree, use_container_width=True)

                    with col_s:
                        st.markdown("##### ☀️ Sunburst – Source / Topic")
                        sun_rows = [{"Source": row["Source"], "Topic": t} for _, row in filtered.iterrows() for t in row["Topics"]]
                        if sun_rows:
                            sun_agg = pd.DataFrame(sun_rows).groupby(["Source", "Topic"]).size().reset_index(name="Count")
                            fig_sun = px.sunburst(sun_agg, path=["Source", "Topic"], values="Count", color="Count", color_continuous_scale=["#2E86AB", "#E85D04", "#7B2D8E"])
                            style_plotly(fig_sun, height=420); fig_sun.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_sun, use_container_width=True)

                    st.markdown("---")

                    # COUNTRY MAP
                    section_header("🌍 Country Mentions Map")
                    if filtered_country_counts:
                        map_data = [{"Country": c, "Mentions": n, "lat": COUNTRY_COORDS[c][0], "lon": COUNTRY_COORDS[c][1]} for c, n in filtered_country_counts.most_common(30) if c in COUNTRY_COORDS]
                        if map_data:
                            fig_map = px.scatter_geo(pd.DataFrame(map_data), lat="lat", lon="lon", size="Mentions", hover_name="Country", color="Mentions", color_continuous_scale=["#2E86AB", "#E85D04", "#C73E1D"], size_max=30, projection="natural earth")
                            fig_map.update_geos(showcoastlines=True, coastlinecolor="#ccc", showland=True, landcolor="#F5F5F5", showocean=True, oceancolor="#EBF5FB", showcountries=True, countrycolor="#ddd")
                            style_plotly(fig_map, height=450); fig_map.update_layout(margin=dict(t=10,l=0,r=0,b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_map, use_container_width=True)

                    st.markdown("---")

                    # NETWORK GRAPH
                    section_header("🕸️ Network Graph – Countries × Topics")
                    if filtered_countries and filtered_topics:
                        import math
                        import plotly.graph_objects as go
                        edges = Counter()
                        for _, row in filtered.iterrows():
                            for c in row["Countries"]:
                                for t in row["Topics"]:
                                    edges[(c, t)] += 1
                        top_edges = edges.most_common(50)
                        if top_edges:
                            ns = set()
                            for (c, t), _ in top_edges: ns.add(("country", c)); ns.add(("topic", t))
                            nl = list(ns); cos = [n for n in nl if n[0]=="country"]; tps = [n for n in nl if n[0]=="topic"]
                            pos = {}
                            for i, n in enumerate(cos): a = 2*math.pi*i/max(len(cos),1); pos[n] = (math.cos(a)*2, math.sin(a)*2)
                            for i, n in enumerate(tps): a = 2*math.pi*i/max(len(tps),1); pos[n] = (math.cos(a)*1, math.sin(a)*1)
                            ex, ey = [], []
                            for (c, t), _ in top_edges:
                                x0,y0 = pos[("country",c)]; x1,y1 = pos[("topic",t)]
                                ex += [x0,x1,None]; ey += [y0,y1,None]
                            fig_net = go.Figure()
                            fig_net.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.8, color="rgba(150,150,150,0.4)"), hoverinfo="none"))
                            fig_net.add_trace(go.Scatter(x=[pos[n][0] for n in cos], y=[pos[n][1] for n in cos], mode="markers+text",
                                marker=dict(size=[max(8,filtered_country_counts.get(n[1],1)*3) for n in cos], color="#E85D04"), text=[n[1] for n in cos], textposition="top center", textfont=dict(size=9), name="Countries"))
                            fig_net.add_trace(go.Scatter(x=[pos[n][0] for n in tps], y=[pos[n][1] for n in tps], mode="markers+text",
                                marker=dict(size=[max(8,filtered_topic_counts.get(n[1],1)*2) for n in tps], color="#0D7C66", symbol="diamond"), text=[n[1] for n in tps], textposition="bottom center", textfont=dict(size=8, color="#0D7C66"), name="Topics"))
                            style_plotly(fig_net, height=550); fig_net.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                            st.plotly_chart(fig_net, use_container_width=True)

                    st.markdown("---")

                    # TIMELINE
                    section_header("⏱️ Healthcare Timeline")
                    tl = filtered.dropna(subset=["Date"]).copy()
                    if not tl.empty:
                        tl["TopicCount"] = tl["Topics"].apply(len).clip(lower=1)
                        fig_sc = px.scatter(tl, x="Date", y="PrimaryTopic", size="TopicCount", color="PrimaryTopic", hover_name="Title", color_discrete_sequence=palette, size_max=18, opacity=0.8)
                        style_plotly(fig_sc, height=400); fig_sc.update_layout(xaxis_title="", yaxis_title="", showlegend=False, margin=dict(l=10,r=10,t=10,b=40))
                        st.plotly_chart(fig_sc, use_container_width=True)

                    st.markdown("---")

                    # WORD CLOUD + FREQUENCY
                    section_header("💬 Text Analysis")
                    corpus = " ".join(filtered["Title"].dropna().tolist() + filtered["Summary"].dropna().tolist()).lower()
                    words = [w for w in re_ch.findall(r"[a-z]{3,}", corpus) if w not in stop_words]
                    word_freq = Counter(words); top_words = word_freq.most_common(30)
                    wc1, wc2 = st.columns(2)
                    with wc1:
                        st.markdown("##### ☁️ Word Cloud")
                        if top_words:
                            try:
                                from wordcloud import WordCloud; import matplotlib.pyplot as plt
                                wc = WordCloud(width=800, height=400, background_color="white", colormap="viridis", max_words=80, contour_color="#0D7C66").generate_from_frequencies(dict(top_words))
                                fig_wc, ax = plt.subplots(figsize=(10,5)); ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
                                st.pyplot(fig_wc, use_container_width=True); plt.close(fig_wc)
                            except ImportError:
                                tw_df = pd.DataFrame(top_words[:15], columns=["Word","Count"])
                                fig_fb = px.bar(tw_df, x="Count", y="Word", orientation="h", color="Count", color_continuous_scale=["#0D7C66","#E85D04"])
                                style_plotly(fig_fb, height=350); fig_fb.update_layout(showlegend=False, coloraxis_showscale=False)
                                st.plotly_chart(fig_fb, use_container_width=True)
                    with wc2:
                        st.markdown("##### 📊 Top 20 Words")
                        if top_words:
                            tw_df = pd.DataFrame(top_words[:20], columns=["Word","Frequency"])
                            fig_freq = px.bar(tw_df, x="Frequency", y="Word", orientation="h", color="Frequency", color_continuous_scale=["#2E86AB","#0D7C66","#E85D04"], text="Frequency")
                            fig_freq.update_traces(textposition="outside"); style_plotly(fig_freq, height=480)
                            fig_freq.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                            st.plotly_chart(fig_freq, use_container_width=True)

                    st.markdown("---")

                    # KEYWORD TREND
                    section_header("📈 Health Keyword Trends")
                    top_kw = [w for w, _ in top_words[:8]]
                    tl_kw = filtered.dropna(subset=["Date"]).copy()
                    if not tl_kw.empty and top_kw:
                        tl_kw["YM"] = tl_kw["Date"].dt.to_period("M").astype(str)
                        kw_rows = [{"Month": row["YM"], "Keyword": kw} for _, row in tl_kw.iterrows() for kw in top_kw if kw in row["Full_Text"]]
                        if kw_rows:
                            kw_agg = pd.DataFrame(kw_rows).groupby(["Month","Keyword"]).size().reset_index(name="Mentions")
                            fig_tr = px.line(kw_agg, x="Month", y="Mentions", color="Keyword", markers=True, color_discrete_sequence=palette)
                            style_plotly(fig_tr, height=380); fig_tr.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=11)))
                            st.plotly_chart(fig_tr, use_container_width=True)

                    st.markdown("---")

                    # HEATMAP
                    section_header("🔥 Seasonality Heatmap")
                    heat = filtered.dropna(subset=["Date"]).copy()
                    if not heat.empty:
                        hr = [{"Month": row["Date"].strftime("%b"), "MN": row["Date"].month, "Topic": t} for _, row in heat.iterrows() for t in row["Topics"]]
                        if hr:
                            hdf = pd.DataFrame(hr); hp = hdf.pivot_table(index="Topic", columns="Month", values="MN", aggfunc="count", fill_value=0)
                            mo = [m for m in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"] if m in hp.columns]
                            hp = hp[mo]; tp15 = [t for t, _ in filtered_topic_counts.most_common(15)]; hp = hp[hp.index.isin(tp15)]
                            if not hp.empty:
                                fig_hm = px.imshow(hp.values, x=hp.columns.tolist(), y=hp.index.tolist(), color_continuous_scale=["#F0F4F8","#2E86AB","#0D7C66","#E85D04"], aspect="auto", text_auto=True)
                                style_plotly(fig_hm, height=max(300, len(hp)*35+80)); fig_hm.update_layout(coloraxis_showscale=False)
                                st.plotly_chart(fig_hm, use_container_width=True)

                    st.markdown("---")

                    # ARTICLES
                    section_header("📰 Healthcare Articles")
                    sort_opt = st.selectbox("Sort by", ["Most recent", "Alphabetical"], index=0, key="ch_sort")
                    display = filtered.sort_values("Date", ascending=False) if sort_opt == "Most recent" else filtered.sort_values("Title")
                    PAGE_SIZE = 12; total_pages = max(1, -(-len(display)//PAGE_SIZE))
                    page_num = st.number_input("Page", 1, total_pages, 1, key="ch_page")
                    for _, row in display.iloc[(page_num-1)*PAGE_SIZE:page_num*PAGE_SIZE].iterrows():
                        topics_html = " ".join(f'<span style="background:#EBF5FB;color:#1A6B8A;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">{t}</span>' for t in row["Topics"][:5])
                        countries_html = " ".join(f'<span style="background:#FFF3E0;color:#E85D04;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">🌍 {c}</span>' for c in row["Countries"][:3])
                        date_str = row["Date"].strftime("%d %b %Y") if pd.notna(row["Date"]) else ""
                        summary_text = row["Summary"].replace("Chatham House", "").strip()
                        st.markdown(f"""<div style="background:#FFF;border-left:4px solid #0D7C66;padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                                <a href="{row['URL']}" target="_blank" style="color:#0D2B45;font-weight:600;font-size:0.95rem;text-decoration:none;">{row['Title'][:120]}</a>
                                <span style="color:#95A5A6;font-size:0.75rem;white-space:nowrap;margin-left:1rem;">{date_str}</span>
                            </div><div style="margin:0.3rem 0;">{topics_html} {countries_html}</div>
                            <div style="color:#7F8C8D;font-size:0.85rem;line-height:1.5;margin-top:0.3rem;">{summary_text[:200]}{'...' if len(summary_text)>200 else ''}</div></div>""", unsafe_allow_html=True)
                    st.caption(f"Page {page_num} of {total_pages} — {len(display)} healthcare articles")
                    with st.expander("📋 Full Table"):
                        st.dataframe(filtered[["Date","Title","PrimaryTopic","Source"]].sort_values("Date", ascending=False), use_container_width=True, hide_index=True)

                # ════════════════ TAB 2: NOTES ════════════════
                with tab_notes:
                    section_header("📝 Personal Notes & AI Semantic Analysis")
                    st.markdown('<div style="background:#F0F8FF;border:1px solid #B8D4E3;padding:12px 16px;border-radius:8px;margin-bottom:16px;"><strong>How to use:</strong> Select an article, add notes, click Save & Analyze for AI keyword extraction.</div>', unsafe_allow_html=True)

                    sel_art = st.selectbox("📄 Select article", df_health["Title"].tolist(), index=0, key="ch_sel")
                    sel_r = df_health[df_health["Title"]==sel_art].iloc[0]
                    doc_id = int(sel_r["DocID"])

                    existing = session.execute(sa_text("SELECT note_text, private_url, ai_keywords, ai_countries FROM chatham_notes WHERE document_id=:d ORDER BY updated_at DESC LIMIT 1"), {"d": doc_id}).fetchone()

                    nc1, nc2 = st.columns([3,1])
                    with nc1:
                        note_text = st.text_area("✏️ Your notes", value=existing[0] if existing else "", height=200, key="ch_note", placeholder="Write your analysis...")
                        private_url = st.text_input("🔗 Private link", value=existing[1] if existing else "", key="ch_url")
                    with nc2:
                        st.markdown("##### 🤖 AI Extracted")
                        if existing and existing[2]: st.markdown(f"**Keywords:** {existing[2]}")
                        if existing and existing[3]: st.markdown(f"**Countries:** {existing[3]}")
                        if not existing or (not existing[2] and not existing[3]): st.caption("Save & Analyze to extract.")

                    if st.button("💾 Save & Analyze", type="primary", key="ch_save"):
                        combined = (note_text + " " + sel_r["Title"] + " " + sel_r["Summary"]).lower()
                        nw = [w for w in re_ch.findall(r"[a-z]{3,}", combined) if w not in stop_words and len(w) > 3]
                        ai_kw = ", ".join([w for w, _ in Counter(nw).most_common(10)])
                        ai_cc = ", ".join(extract_countries(combined)) or ""
                        if existing:
                            session.execute(sa_text("UPDATE chatham_notes SET note_text=:n, private_url=:u, ai_keywords=:k, ai_countries=:c, updated_at=NOW() WHERE document_id=:d"), {"n":note_text,"u":private_url,"k":ai_kw,"c":ai_cc,"d":doc_id})
                        else:
                            session.execute(sa_text("INSERT INTO chatham_notes (document_id,note_text,private_url,ai_keywords,ai_countries) VALUES (:d,:n,:u,:k,:c)"), {"d":doc_id,"n":note_text,"u":private_url,"k":ai_kw,"c":ai_cc})
                        session.commit(); st.success("✅ Saved!"); st.rerun()

                    st.markdown("---")
                    section_header("📋 All Notes")
                    all_notes = session.execute(sa_text("SELECT cn.note_text,cn.private_url,cn.ai_keywords,cn.ai_countries,cn.updated_at,d.title FROM chatham_notes cn JOIN documents d ON cn.document_id=d.document_id ORDER BY cn.updated_at DESC")).fetchall()
                    if all_notes:
                        for n in all_notes:
                            with st.expander(f"📄 {n[5][:80]}"):
                                st.markdown(n[0])
                                if n[1]: st.markdown(f"**Link:** [{n[1][:60]}...]({n[1]})")
                                if n[2]: st.markdown(f"**Keywords:** {n[2]}")
                                if n[3]: st.markdown(f"**Countries:** 🌍 {n[3]}")
                    else:
                        st.info("No notes yet.")

                # ════════════════ TAB 3: PRIVATE LINKS ════════════════
                with tab_links:
                    section_header("🔗 Private Chatham House Links")
                    st.markdown('<div style="background:#FFF8E1;border:1px solid #FFE082;padding:12px 16px;border-radius:8px;margin-bottom:16px;"><strong>Add private links</strong> from your Chatham House membership. AI extracts keywords automatically.</div>', unsafe_allow_html=True)

                    with st.form("ch_add_link", clear_on_submit=True):
                        lk_url = st.text_input("🔗 URL", placeholder="https://www.chathamhouse.org/members/...")
                        lk_title = st.text_input("📄 Title")
                        lk_desc = st.text_area("📝 Description", height=100)
                        if st.form_submit_button("➕ Add Link & Analyze", type="primary") and lk_url.strip():
                            combined = (lk_title + " " + lk_desc).lower()
                            lk_kw = ", ".join([w for w, _ in Counter([w for w in re_ch.findall(r"[a-z]{3,}", combined) if w not in stop_words and len(w)>3]).most_common(10)])
                            lk_cc = ", ".join(extract_countries(combined))
                            session.execute(sa_text("INSERT INTO chatham_private_links (url,title,description,ai_keywords,ai_countries) VALUES (:u,:t,:d,:k,:c)"), {"u":lk_url,"t":lk_title,"d":lk_desc,"k":lk_kw,"c":lk_cc})
                            session.commit(); st.success("✅ Link added!"); st.rerun()

                    st.markdown("---")
                    links = session.execute(sa_text("SELECT link_id,url,title,description,ai_keywords,ai_countries,created_at FROM chatham_private_links ORDER BY created_at DESC")).fetchall()
                    if links:
                        for lk in links:
                            kw_pills = " ".join(f'<span style="background:#E8F5E9;color:#2E7D32;padding:2px 6px;border-radius:10px;font-size:0.72rem;">{k.strip()}</span>' for k in (lk[4] or "").split(",")[:8] if k.strip())
                            cc_pills = " ".join(f'<span style="background:#FFF3E0;color:#E85D04;padding:2px 6px;border-radius:10px;font-size:0.72rem;">🌍 {c.strip()}</span>' for c in (lk[5] or "").split(",")[:5] if c.strip())
                            st.markdown(f"""<div style="background:#FFF;border-left:4px solid #7B2D8E;padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                                <div style="display:flex;justify-content:space-between;"><a href="{lk[1]}" target="_blank" style="color:#7B2D8E;font-weight:600;font-size:0.95rem;text-decoration:none;">🔒 {lk[2] or lk[1][:80]}</a>
                                <span style="color:#95A5A6;font-size:0.75rem;">{lk[6].strftime('%d %b %Y') if lk[6] else ''}</span></div>
                                <div style="margin:0.3rem 0;">{kw_pills} {cc_pills}</div>
                                <div style="color:#7F8C8D;font-size:0.85rem;">{(lk[3] or '')[:200]}</div></div>""", unsafe_allow_html=True)
                            if st.button("🗑️ Delete", key=f"ch_del_{lk[0]}"):
                                session.execute(sa_text("DELETE FROM chatham_private_links WHERE link_id=:id"), {"id": lk[0]}); session.commit(); st.rerun()
                    else:
                        st.info("No private links yet.")

        else:
            st.info("No Chatham House articles yet. Run the collector:")
            st.code('python -c "from collectors.chatham_collector import run; run()"')

    finally:
        session.close()

    page_footer()

# PAGE 12: CHINA HEALTH - Medical Tourism & Neurodegenerative Research
# ════════════════════════════════════════════════════════
elif page == "🇨🇳 China Health":
    page_header("China Health Intelligence", "Medical tourism, digital health, neurodegenerative research & international patient flows")

    session = get_session_cached()
    try:
        # ── Ensure notes tables exist ──
        from sqlalchemy import text as sa_text
        try:
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS china_health_notes (
                note_id SERIAL PRIMARY KEY, document_id INTEGER REFERENCES documents(document_id) ON DELETE CASCADE,
                note_text TEXT, private_url TEXT, ai_keywords TEXT, ai_countries TEXT,
                created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"""))
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS china_health_links (
                link_id SERIAL PRIMARY KEY, url TEXT NOT NULL, title TEXT, description TEXT,
                link_category VARCHAR(50), ai_keywords TEXT, created_at TIMESTAMP DEFAULT NOW())"""))
            session.commit()
        except Exception:
            session.rollback()

        ch_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "china_medtourism")
            .order_by(desc(Document.publish_date))
            .limit(500)
            .all()
        )

        if ch_docs:
            df_cn = pd.DataFrame([{
                "DocID": d.document_id, "Date": d.publish_date,
                "Title": d.title or "", "Source": s.source_name,
                "URL": d.url or "", "Summary": (d.summary or ""),
                "Country": (d.country or "China"),
            } for d, s in ch_docs])

            df_cn["Date"] = pd.to_datetime(df_cn["Date"], errors="coerce")
            df_cn["Full_Text"] = (df_cn["Title"] + " " + df_cn["Summary"]).str.lower()

            import re as re_cn
            import math
            from collections import Counter
            import plotly.graph_objects as go

            # ── TOPIC CLASSIFICATION ──
            CN_TOPICS = {
                "Medical Tourism": ["medical tourism", "foreign patient", "international patient", "medical travel", "health tourism", "medical visitor"],
                "Digital Health & AI": ["digital health", "telemedicine", "telehealth", "ai health", "artificial intelligence", "wearable", "health tech", "health data", "remote monitoring"],
                "Neurodegenerative Disease": ["alzheimer", "parkinson", "dementia", "neurodegen", "motor neuron", "als ", "amyotrophic", "huntington", "cognitive impairment", "neurolog"],
                "Stem Cell Therapy": ["stem cell", "cell therapy", "regenerat", "ipsc", "mesenchymal", "gene therapy", "crispr"],
                "Psychiatric Services": ["psychiatric", "mental health", "depression", "anxiety", "psycholog", "bipolar", "schizophren"],
                "Traditional Chinese Medicine": ["traditional chinese", "tcm", "acupuncture", "herbal medicine", "moxibustion"],
                "Cancer Treatment": ["cancer", "oncolog", "tumor", "chemotherapy", "radiotherapy", "immunotherapy"],
                "Hospital Infrastructure": ["hospital", "medical center", "jci accredit", "infrastructure", "medical zone"],
                "Payment & Insurance": ["payment", "insurance", "cost", "afford", "price", "billing", "medical bill"],
                "Data & Privacy": ["data", "privacy", "electronic health record", "patient data", "cross-border data"],
                "Follow-up & Telemedicine": ["follow-up", "remote care", "post-treatment", "aftercare", "distance care"],
                "Policy & Regulation": ["policy", "regulation", "government", "reform", "pilot zone", "free trade", "visa"],
            }

            HOSPITALS = {
                "Peking Union Medical College Hospital": ["peking union", "pumch"],
                "Beijing Tiantan Hospital": ["tiantan"],
                "Shanghai Ruijin Hospital": ["ruijin"],
                "Fudan University Shanghai Cancer Center": ["fudan cancer", "fudan university"],
                "West China Hospital (Sichuan)": ["west china hospital", "huaxi"],
                "Zhongshan Hospital Shanghai": ["zhongshan"],
                "Boao Lecheng Medical Zone": ["boao", "lecheng"],
                "Shenzhen Qianhai Taikang Hospital": ["qianhai taikang"],
                "Peking University Shenzhen Hospital": ["peking university shenzhen"],
                "United Family Healthcare": ["united family"],
                "Perennial General Hospital Tianjin": ["perennial", "tianjin hospital"],
                "Shanghai Huashan Hospital": ["huashan"],
                "Renji Hospital Shanghai": ["renji"],
                "Longhua TCM Hospital": ["longhua"],
            }

            REGIONS = {
                "Beijing": ["beijing"], "Shanghai": ["shanghai"],
                "Guangzhou": ["guangzhou", "guangdong"], "Shenzhen": ["shenzhen"],
                "Hainan": ["hainan", "boao", "lecheng"], "Tianjin": ["tianjin"],
                "Chengdu": ["chengdu", "sichuan"], "Wuhan": ["wuhan", "hubei"],
                "Hangzhou": ["hangzhou", "zhejiang"], "Nanjing": ["nanjing", "jiangsu"],
                "Fangchenggang": ["fangchenggang", "guangxi"], "Xi'an": ["xi'an", "shaanxi"],
            }

            # ── ORIGIN COUNTRY EXTRACTION (source countries of medical tourists) ──
            ORIGIN_COUNTRIES = {
                "Russia": ["russia", "russian", "moscow"],
                "Vietnam": ["vietnam", "vietnamese"],
                "Indonesia": ["indonesia", "indonesian", "jakarta"],
                "Malaysia": ["malaysia", "malaysian"],
                "Singapore": ["singapore", "singaporean"],
                "Thailand": ["thailand", "thai"],
                "Philippines": ["philippines", "filipino"],
                "Cambodia": ["cambodia", "cambodian"],
                "Myanmar": ["myanmar", "burmese"],
                "Kazakhstan": ["kazakhstan", "kazakh"],
                "Uzbekistan": ["uzbekistan", "uzbek"],
                "Mongolia": ["mongolia", "mongolian"],
                "South Korea": ["south korea", "korean"],
                "Japan": ["japan", "japanese"],
                "India": ["india", "indian"],
                "Pakistan": ["pakistan", "pakistani"],
                "Bangladesh": ["bangladesh", "bangladeshi"],
                "Saudi Arabia": ["saudi", "saudi arabia"],
                "UAE": ["uae", "emirates", "dubai", "abu dhabi"],
                "Kuwait": ["kuwait", "kuwaiti"],
                "Qatar": ["qatar", "qatari"],
                "Iran": ["iran", "iranian"],
                "Iraq": ["iraq", "iraqi"],
                "Nigeria": ["nigeria", "nigerian"],
                "Kenya": ["kenya", "kenyan"],
                "South Africa": ["south africa"],
                "Ethiopia": ["ethiopia", "ethiopian"],
                "Tanzania": ["tanzania"],
                "United States": ["united states", "american", "usa", "u.s."],
                "Canada": ["canada", "canadian"],
                "United Kingdom": ["united kingdom", "british", "uk "],
                "Australia": ["australia", "australian"],
                "France": ["france", "french"],
                "Germany": ["germany", "german"],
            }

            ORIGIN_COORDS = {
                "Russia": (61.5, 105.3), "Vietnam": (14.1, 108.3), "Indonesia": (-0.8, 113.9),
                "Malaysia": (4.2, 101.9), "Singapore": (1.4, 103.8), "Thailand": (15.9, 100.9),
                "Philippines": (12.9, 121.8), "Cambodia": (12.6, 105.0), "Myanmar": (21.9, 95.9),
                "Kazakhstan": (48.0, 68.0), "Uzbekistan": (41.3, 64.6), "Mongolia": (46.9, 103.8),
                "South Korea": (35.9, 127.8), "Japan": (36.2, 138.3), "India": (20.6, 78.9),
                "Pakistan": (30.4, 69.3), "Bangladesh": (23.7, 90.4),
                "Saudi Arabia": (23.9, 45.1), "UAE": (23.4, 53.8), "Kuwait": (29.3, 47.5),
                "Qatar": (25.4, 51.2), "Iran": (32.4, 53.7), "Iraq": (33.2, 43.7),
                "Nigeria": (9.1, 8.7), "Kenya": (-0.02, 37.9), "South Africa": (-30.6, 22.9),
                "Ethiopia": (9.1, 40.5), "Tanzania": (-6.4, 34.9),
                "United States": (39.8, -98.5), "Canada": (56.1, -106.3),
                "United Kingdom": (55.4, -3.4), "Australia": (-25.3, 133.8),
                "France": (46.2, 2.2), "Germany": (51.2, 10.4),
            }

            # Region groupings for Sankey
            ORIGIN_REGIONS = {
                "Southeast Asia": ["Vietnam", "Indonesia", "Malaysia", "Singapore", "Thailand", "Philippines", "Cambodia", "Myanmar"],
                "Central Asia": ["Kazakhstan", "Uzbekistan", "Mongolia"],
                "East Asia": ["South Korea", "Japan"],
                "South Asia": ["India", "Pakistan", "Bangladesh"],
                "Middle East": ["Saudi Arabia", "UAE", "Kuwait", "Qatar", "Iran", "Iraq"],
                "Africa": ["Nigeria", "Kenya", "South Africa", "Ethiopia", "Tanzania"],
                "Russia & CIS": ["Russia"],
                "Western Countries": ["United States", "Canada", "United Kingdom", "Australia", "France", "Germany"],
            }

            def extract_cn_topics(text):
                topics = []
                for topic, kws in CN_TOPICS.items():
                    if any(kw in text for kw in kws):
                        topics.append(topic)
                return topics if topics else ["General"]

            def extract_hospitals(text):
                return [h for h, kws in HOSPITALS.items() if any(kw in text for kw in kws)]

            def extract_regions(text):
                return [r for r, kws in REGIONS.items() if any(kw in text for kw in kws)]

            def extract_origins(text):
                return list(set(c for c, kws in ORIGIN_COUNTRIES.items() if any(kw in text for kw in kws)))

            def get_origin_region(country):
                for region, countries in ORIGIN_REGIONS.items():
                    if country in countries:
                        return region
                return "Other"

            df_cn["Topics"] = df_cn["Full_Text"].apply(extract_cn_topics)
            df_cn["PrimaryTopic"] = df_cn["Topics"].apply(lambda x: x[0])
            df_cn["Hospitals"] = df_cn["Full_Text"].apply(extract_hospitals)
            df_cn["Regions"] = df_cn["Full_Text"].apply(extract_regions)
            df_cn["Origins"] = df_cn["Full_Text"].apply(extract_origins)
            df_cn["OriginRegions"] = df_cn["Origins"].apply(lambda os: list(set(get_origin_region(o) for o in os)))

            all_topics = [t for ts in df_cn["Topics"] for t in ts]
            all_hospitals = [h for hs in df_cn["Hospitals"] for h in hs]
            all_regions = [r for rs in df_cn["Regions"] for r in rs]
            all_origins = [o for os in df_cn["Origins"] for o in os]
            all_origin_regions = [r for rs in df_cn["OriginRegions"] for r in rs]

            palette = ["#C73E1D", "#D4A017", "#0D7C66", "#1E3A5F", "#E85D04", "#7B2D8E",
                        "#2E86AB", "#A23B72", "#F18F01", "#44AF69", "#ECA72C", "#226F54",
                        "#DA627D", "#4A4E69", "#00B4D8", "#3B1F2B"]

            stop_w = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","from","is","it","this","that","are","was","were","be","been","have","has","had","do","does","did","will","would","could","should","not","no","its","as","if","than","so","up","out","about","into","over","after","under","between","through","during","before","more","most","other","some","also","all","each","both","few","many","much","any","which","what","who","when","where","why","their","them","they","he","she","we","you","his","her","our","your","s","new","one","two","us","my","me","these","those","china","chinese","has","been","can","may","its","such","only","said","according","year","years","per","cent","million","billion","first"}

            # ════════════════════════════════════════
            # TABS
            # ════════════════════════════════════════
            tab_dash, tab_flows, tab_hospitals, tab_notes, tab_links = st.tabs([
                "📊 Dashboard",
                "🌊 Patient Flows",
                "🏥 Hospitals & Regions",
                "📝 Notes & Research",
                "🔗 Links & Resources",
            ])

            # ═══════════════════════════════════════
            # TAB 1: DASHBOARD
            # ═══════════════════════════════════════
            with tab_dash:
                section_header("🔍 Filters")
                fc1, fc2, fc3 = st.columns([2, 2, 2])
                with fc1:
                    sel_topics = st.multiselect("📌 Topic", sorted(set(all_topics)), default=[], key="cn_tp")
                with fc2:
                    vd = df_cn["Date"].dropna()
                    dr = st.date_input("📅 Date range", value=(vd.min().date(), vd.max().date()), min_value=vd.min().date(), max_value=vd.max().date(), key="cn_dr") if not vd.empty else None
                with fc3:
                    kw_search = st.text_input("🔎 Keyword", placeholder="e.g. stem cell, Alzheimer...", key="cn_kw")

                filtered = df_cn.copy()
                if sel_topics:
                    filtered = filtered[filtered["Topics"].apply(lambda t: any(x in sel_topics for x in t))]
                if dr and len(dr) == 2:
                    filtered = filtered[(filtered["Date"] >= pd.Timestamp(dr[0])) & (filtered["Date"] <= pd.Timestamp(dr[1]))]
                if kw_search.strip():
                    filtered = filtered[filtered["Full_Text"].str.contains(kw_search.strip().lower(), na=False)]

                f_topics = [t for ts in filtered["Topics"] for t in ts]
                f_origins = [o for os in filtered["Origins"] for o in os]
                f_hospitals = [h for hs in filtered["Hospitals"] for h in hs]
                f_regions = [r for rs in filtered["Regions"] for r in rs]

                st.caption(f"**{len(filtered)}** articles after filters")
                st.markdown("---")

                # KPIs
                k1, k2, k3, k4, k5 = st.columns(5)
                with k1: kpi_card("Articles", str(len(filtered)))
                with k2: kpi_card("Topics", str(len(set(f_topics))))
                with k3: kpi_card("Origin Countries", str(len(set(f_origins))))
                with k4: kpi_card("Hospitals", str(len(set(f_hospitals))))
                with k5: kpi_card("CN Regions", str(len(set(f_regions))))

                st.markdown("<br>", unsafe_allow_html=True)

                # TREEMAP + SUNBURST
                section_header("🗺️ Topic Distribution")
                ct, cs = st.columns(2)
                with ct:
                    st.markdown("##### 🌳 Topic Treemap")
                    tc = Counter(f_topics)
                    if tc:
                        tc_df = pd.DataFrame(tc.most_common(15), columns=["Topic", "Count"])
                        fig = px.treemap(tc_df, path=["Topic"], values="Count", color="Count",
                                          color_continuous_scale=["#C73E1D", "#D4A017", "#0D7C66"])
                        fig.update_traces(textinfo="label+value", textfont_size=12)
                        style_plotly(fig, height=400); fig.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig, use_container_width=True)

                with cs:
                    st.markdown("##### ☀️ Origin Region / Topic")
                    sun_rows = []
                    for _, row in filtered.iterrows():
                        for org in (row["OriginRegions"] or ["Unknown"]):
                            for t in row["Topics"]:
                                sun_rows.append({"Origin": org, "Topic": t})
                    if sun_rows:
                        sun_df = pd.DataFrame(sun_rows)
                        sun_agg = sun_df.groupby(["Origin", "Topic"]).size().reset_index(name="Count")
                        fig_s = px.sunburst(sun_agg, path=["Origin", "Topic"], values="Count", color="Count",
                                             color_continuous_scale=["#2E86AB", "#E85D04", "#C73E1D"])
                        style_plotly(fig_s, height=400); fig_s.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig_s, use_container_width=True)

                st.markdown("---")

                # TIMELINE
                section_header("⏱️ Timeline")
                tl = filtered.dropna(subset=["Date"]).copy()
                if not tl.empty:
                    tl["TC"] = tl["Topics"].apply(len).clip(lower=1)
                    fig_tl = px.scatter(tl, x="Date", y="PrimaryTopic", size="TC", color="PrimaryTopic",
                                         hover_name="Title", color_discrete_sequence=palette, size_max=16, opacity=0.8)
                    style_plotly(fig_tl, height=380); fig_tl.update_layout(showlegend=False, margin=dict(l=10,r=10,t=10,b=40))
                    st.plotly_chart(fig_tl, use_container_width=True)

                st.markdown("---")

                # WORD CLOUD + FREQUENCY
                section_header("💬 Text Analysis")
                corpus = " ".join(filtered["Title"].dropna().tolist() + filtered["Summary"].dropna().tolist()).lower()
                words = [w for w in re_cn.findall(r"[a-z]{3,}", corpus) if w not in stop_w]
                wf = Counter(words); tw = wf.most_common(25)

                wc1, wc2 = st.columns(2)
                with wc1:
                    st.markdown("##### ☁️ Word Cloud")
                    if tw:
                        try:
                            from wordcloud import WordCloud; import matplotlib.pyplot as plt
                            wc = WordCloud(width=800, height=400, background_color="white", colormap="YlOrRd", max_words=60, contour_color="#C73E1D").generate_from_frequencies(dict(tw))
                            fig_wc, ax = plt.subplots(figsize=(10,5)); ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
                            st.pyplot(fig_wc, use_container_width=True); plt.close(fig_wc)
                        except ImportError:
                            tw_df = pd.DataFrame(tw[:15], columns=["Word","Count"])
                            fig_fb = px.bar(tw_df, x="Count", y="Word", orientation="h", color="Count", color_continuous_scale=["#C73E1D","#D4A017"])
                            style_plotly(fig_fb, height=350); fig_fb.update_layout(showlegend=False, coloraxis_showscale=False)
                            st.plotly_chart(fig_fb, use_container_width=True)
                with wc2:
                    st.markdown("##### 📊 Top 20 Words")
                    if tw:
                        tw_df = pd.DataFrame(tw[:20], columns=["Word","Freq"])
                        fig_f = px.bar(tw_df, x="Freq", y="Word", orientation="h", color="Freq", text="Freq", color_continuous_scale=["#2E86AB","#C73E1D"])
                        fig_f.update_traces(textposition="outside"); style_plotly(fig_f, height=450)
                        fig_f.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig_f, use_container_width=True)

                st.markdown("---")

                # KEYWORD TREND
                section_header("📈 Keyword Trends Over Time")
                top_kw = [w for w, _ in tw[:8]]
                tl_kw = filtered.dropna(subset=["Date"]).copy()
                if not tl_kw.empty and top_kw:
                    tl_kw["YM"] = tl_kw["Date"].dt.to_period("M").astype(str)
                    kw_rows = []
                    for _, row in tl_kw.iterrows():
                        for kw in top_kw:
                            if kw in row["Full_Text"]:
                                kw_rows.append({"Month": row["YM"], "Keyword": kw})
                    if kw_rows:
                        kw_agg = pd.DataFrame(kw_rows).groupby(["Month","Keyword"]).size().reset_index(name="Mentions")
                        fig_kt = px.line(kw_agg, x="Month", y="Mentions", color="Keyword", markers=True, color_discrete_sequence=palette)
                        style_plotly(fig_kt, height=350)
                        fig_kt.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=10)))
                        st.plotly_chart(fig_kt, use_container_width=True)

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
                        hdf = pd.DataFrame(heat_rows)
                        hp = hdf.pivot_table(index="Topic", columns="Month", values="MonthNum", aggfunc="count", fill_value=0)
                        mo = [m for m in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"] if m in hp.columns]
                        hp = hp[mo]
                        top_tp = [t for t, _ in Counter(f_topics).most_common(12)]
                        hp = hp[hp.index.isin(top_tp)]
                        if not hp.empty:
                            fig_hm = px.imshow(hp.values, x=hp.columns.tolist(), y=hp.index.tolist(), color_continuous_scale=["#F0F4F8","#2E86AB","#C73E1D"], aspect="auto", text_auto=True)
                            style_plotly(fig_hm, height=max(280, len(hp)*35+60)); fig_hm.update_layout(coloraxis_showscale=False)
                            st.plotly_chart(fig_hm, use_container_width=True)

                st.markdown("---")

                # ARTICLES
                section_header("📰 Articles")
                sort_o = st.selectbox("Sort", ["Most recent", "Alphabetical"], index=0, key="cn_sort")
                display = filtered.sort_values("Date", ascending=False) if sort_o == "Most recent" else filtered.sort_values("Title")
                PS = 12; tp = max(1, -(-len(display)//PS)); pn = st.number_input("Page", 1, tp, 1, key="cn_page")
                sl = display.iloc[(pn-1)*PS : pn*PS]
                for _, row in sl.iterrows():
                    t_html = " ".join(f'<span style="background:#FFF3E0;color:#C73E1D;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">{t}</span>' for t in row["Topics"][:4])
                    o_html = " ".join(f'<span style="background:#E3F2FD;color:#1565C0;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">✈️ {o}</span>' for o in row["Origins"][:3])
                    h_html = " ".join(f'<span style="background:#E8F5E9;color:#2E7D32;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">🏥 {h}</span>' for h in row["Hospitals"][:2])
                    ds = row["Date"].strftime("%d %b %Y") if pd.notna(row["Date"]) else ""
                    st.markdown(f"""
                    <div style="background:#FFF;border-left:4px solid #C73E1D;padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <a href="{row['URL']}" target="_blank" style="color:#0D2B45;font-weight:600;font-size:0.95rem;text-decoration:none;">{row['Title'][:120]}</a>
                            <span style="color:#95A5A6;font-size:0.75rem;white-space:nowrap;margin-left:1rem;">{ds}</span>
                        </div>
                        <div style="margin:0.3rem 0;">{t_html} {o_html} {h_html}</div>
                        <div style="color:#7F8C8D;font-size:0.85rem;line-height:1.5;margin-top:0.3rem;">{row['Summary'][:200]}{'...' if len(row['Summary'])>200 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.caption(f"Page {pn} of {tp} — {len(display)} articles")

            # ═══════════════════════════════════════
            # TAB 2: PATIENT FLOWS
            # ═══════════════════════════════════════
            with tab_flows:
                section_header("🌊 International Patient Flow Analysis")

                st.markdown("""
                <div style="background:#FFF3E0;border:1px solid #FFE0B2;padding:12px 16px;border-radius:8px;margin-bottom:16px;">
                    <strong>Patient flow intelligence</strong> — Extracted from article mentions of origin countries, destination regions and hospitals in China.
                    Based on <strong>{}</strong> articles mentioning {} origin countries.
                </div>
                """.format(len(df_cn[df_cn["Origins"].apply(len) > 0]), len(set(all_origins))), unsafe_allow_html=True)

                # ── SANKEY DIAGRAM: Origin Region → China Region → Hospital ──
                section_header("🔀 Sankey Flow: Origin → China Region → Treatment Area")

                # Build sankey data
                sankey_edges_1 = Counter()  # origin_region → china_region
                sankey_edges_2 = Counter()  # china_region → topic

                for _, row in df_cn.iterrows():
                    for org in row["OriginRegions"]:
                        for creg in (row["Regions"] or ["China (general)"]):
                            sankey_edges_1[(org, creg)] += 1
                        for tp in row["Topics"][:2]:
                            for creg in (row["Regions"] or ["China (general)"]):
                                sankey_edges_2[(creg, tp)] += 1

                if sankey_edges_1:
                    # Build node list
                    all_nodes = []
                    node_colors = []

                    # Level 0: Origin regions
                    origin_set = sorted(set(k[0] for k in sankey_edges_1))
                    for n in origin_set:
                        all_nodes.append(n)
                        node_colors.append("#2E86AB")

                    # Level 1: China regions
                    china_set = sorted(set(k[1] for k in sankey_edges_1) | set(k[0] for k in sankey_edges_2))
                    for n in china_set:
                        all_nodes.append(n)
                        node_colors.append("#C73E1D")

                    # Level 2: Topics
                    topic_set = sorted(set(k[1] for k in sankey_edges_2))
                    for n in topic_set:
                        all_nodes.append(n)
                        node_colors.append("#0D7C66")

                    node_idx = {n: i for i, n in enumerate(all_nodes)}

                    sources, targets, values = [], [], []
                    link_colors = []

                    for (org, creg), v in sankey_edges_1.most_common(40):
                        if org in node_idx and creg in node_idx:
                            sources.append(node_idx[org])
                            targets.append(node_idx[creg])
                            values.append(v)
                            link_colors.append("rgba(46,134,171,0.3)")

                    for (creg, tp), v in sankey_edges_2.most_common(40):
                        if creg in node_idx and tp in node_idx:
                            sources.append(node_idx[creg])
                            targets.append(node_idx[tp])
                            values.append(v)
                            link_colors.append("rgba(199,62,29,0.3)")

                    fig_sankey = go.Figure(go.Sankey(
                        node=dict(pad=15, thickness=20, line=dict(color="#333", width=0.5),
                                  label=all_nodes, color=node_colors),
                        link=dict(source=sources, target=targets, value=values, color=link_colors),
                    ))
                    style_plotly(fig_sankey, height=500)
                    fig_sankey.update_layout(margin=dict(t=20, l=10, r=10, b=10))
                    st.plotly_chart(fig_sankey, use_container_width=True)

                    st.caption("🔵 Origin regions → 🔴 China destinations → 🟢 Treatment areas")
                else:
                    st.info("Insufficient data for Sankey flow diagram.")

                st.markdown("---")

                # ── ORIGIN COUNTRIES BAR + MAP ──
                section_header("✈️ Top Origin Countries")
                oc = Counter(all_origins)

                oc1, oc2 = st.columns(2)
                with oc1:
                    st.markdown("##### 📊 Country Mentions")
                    if oc:
                        oc_df = pd.DataFrame(oc.most_common(20), columns=["Country", "Mentions"])
                        fig_oc = px.bar(oc_df, x="Mentions", y="Country", orientation="h", color="Mentions",
                                         color_continuous_scale=["#2E86AB", "#C73E1D"], text="Mentions")
                        fig_oc.update_traces(textposition="outside")
                        style_plotly(fig_oc, height=500)
                        fig_oc.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig_oc, use_container_width=True)

                with oc2:
                    st.markdown("##### 🌍 Global Patient Origins")
                    if oc:
                        map_rows = []
                        for country, count in oc.items():
                            if country in ORIGIN_COORDS:
                                lat, lon = ORIGIN_COORDS[country]
                                map_rows.append({"Country": country, "Mentions": count, "lat": lat, "lon": lon})
                        if map_rows:
                            mdf = pd.DataFrame(map_rows)
                            fig_gm = px.scatter_geo(mdf, lat="lat", lon="lon", size="Mentions", hover_name="Country",
                                                     color="Mentions", color_continuous_scale=["#D4A017", "#C73E1D"],
                                                     size_max=30, projection="natural earth")
                            fig_gm.update_geos(showland=True, landcolor="#F5F0E8", showocean=True, oceancolor="#EBF5FB",
                                                showcountries=True, countrycolor="#ddd")
                            # Add lines from origin to Beijing (China center)
                            for _, r in mdf.iterrows():
                                fig_gm.add_trace(go.Scattergeo(
                                    lon=[r["lon"], 116.4], lat=[r["lat"], 39.9],
                                    mode="lines", line=dict(width=max(0.5, r["Mentions"]*0.3), color="rgba(199,62,29,0.25)"),
                                    showlegend=False, hoverinfo="skip"))

                            style_plotly(fig_gm, height=500)
                            fig_gm.update_layout(margin=dict(t=10, l=0, r=0, b=10), coloraxis_showscale=False)
                            st.plotly_chart(fig_gm, use_container_width=True)

                st.markdown("---")

                # ── ORIGIN REGION PIE ──
                section_header("🥧 Patient Origins by World Region")
                orc = Counter(all_origin_regions)
                if orc:
                    or_df = pd.DataFrame(orc.most_common(), columns=["Region", "Mentions"])
                    fig_pie = px.pie(or_df, values="Mentions", names="Region", color_discrete_sequence=palette, hole=0.4)
                    fig_pie.update_traces(textinfo="label+percent", textfont_size=12)
                    style_plotly(fig_pie, height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)

                st.markdown("---")

                # ── NETWORK: Origin Country ↔ China Region ──
                section_header("🕸️ Network: Origin Countries × China Destinations")
                edges_net = Counter()
                for _, row in df_cn.iterrows():
                    for org in row["Origins"]:
                        for creg in (row["Regions"] or ["China"]):
                            edges_net[(org, creg)] += 1

                top_edges = edges_net.most_common(50)
                if top_edges:
                    nodes_set = set()
                    for (a, b), _ in top_edges:
                        nodes_set.add(("origin", a))
                        nodes_set.add(("dest", b))

                    node_list = list(nodes_set)
                    origins_n = [n for n in node_list if n[0] == "origin"]
                    dests_n = [n for n in node_list if n[0] == "dest"]
                    positions = {}

                    for i, nd in enumerate(origins_n):
                        angle = 2 * math.pi * i / max(len(origins_n), 1)
                        positions[nd] = (math.cos(angle) * 2.5, math.sin(angle) * 2.5)
                    for i, nd in enumerate(dests_n):
                        angle = 2 * math.pi * i / max(len(dests_n), 1)
                        positions[nd] = (math.cos(angle) * 1, math.sin(angle) * 1)

                    edge_x, edge_y = [], []
                    for (a, b), w in top_edges:
                        x0, y0 = positions[("origin", a)]
                        x1, y1 = positions[("dest", b)]
                        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]

                    fig_net = go.Figure()
                    fig_net.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                        line=dict(width=0.7, color="rgba(150,150,150,0.4)"), hoverinfo="none"))

                    # Origin nodes
                    oc_counts = Counter(all_origins)
                    ox = [positions[("origin", n[1])][0] for n in origins_n]
                    oy = [positions[("origin", n[1])][1] for n in origins_n]
                    o_names = [n[1] for n in origins_n]
                    o_sizes = [max(8, min(25, oc_counts.get(n, 1) * 3)) for n in o_names]
                    fig_net.add_trace(go.Scatter(x=ox, y=oy, mode="markers+text",
                        marker=dict(size=o_sizes, color="#2E86AB", line=dict(width=1, color="white")),
                        text=o_names, textposition="top center", textfont=dict(size=8), name="Origin Countries",
                        hovertext=[f"{n}: {oc_counts.get(n,0)} mentions" for n in o_names], hoverinfo="text"))

                    # Destination nodes
                    rc = Counter(all_regions)
                    dx = [positions[("dest", n[1])][0] for n in dests_n]
                    dy = [positions[("dest", n[1])][1] for n in dests_n]
                    d_names = [n[1] for n in dests_n]
                    d_sizes = [max(10, min(30, rc.get(n, 1) * 4)) for n in d_names]
                    fig_net.add_trace(go.Scatter(x=dx, y=dy, mode="markers+text",
                        marker=dict(size=d_sizes, color="#C73E1D", symbol="diamond", line=dict(width=1, color="white")),
                        text=d_names, textposition="bottom center", textfont=dict(size=9, color="#C73E1D"), name="China Destinations",
                        hovertext=[f"{n}: {rc.get(n,0)} articles" for n in d_names], hoverinfo="text"))

                    style_plotly(fig_net, height=500)
                    fig_net.update_layout(showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    st.plotly_chart(fig_net, use_container_width=True)

                st.markdown("---")

                # ── TREATMENT SPECIALTIES BY ORIGIN ──
                section_header("🩺 What Treatments Do Different Regions Seek?")
                treat_rows = []
                for _, row in df_cn.iterrows():
                    for org_r in row["OriginRegions"]:
                        for tp in row["Topics"]:
                            treat_rows.append({"Origin Region": org_r, "Treatment": tp})
                if treat_rows:
                    treat_df = pd.DataFrame(treat_rows)
                    treat_pivot = treat_df.pivot_table(index="Treatment", columns="Origin Region", aggfunc="size", fill_value=0)
                    if not treat_pivot.empty:
                        fig_th = px.imshow(treat_pivot.values, x=treat_pivot.columns.tolist(), y=treat_pivot.index.tolist(),
                                            color_continuous_scale=["#F5F0E8", "#D4A017", "#C73E1D"], aspect="auto", text_auto=True)
                        style_plotly(fig_th, height=max(300, len(treat_pivot)*30+80))
                        fig_th.update_layout(xaxis_title="Origin Region", yaxis_title="", coloraxis_showscale=False)
                        st.plotly_chart(fig_th, use_container_width=True)

            # ═══════════════════════════════════════
            # TAB 3: HOSPITALS & REGIONS
            # ═══════════════════════════════════════
            with tab_hospitals:
                section_header("🏥 Top Hospitals & Regions")
                hc1, hc2 = st.columns(2)
                with hc1:
                    st.markdown("##### 🏥 Most Mentioned Hospitals")
                    hc = Counter(all_hospitals)
                    if hc:
                        h_df = pd.DataFrame(hc.most_common(15), columns=["Hospital","Mentions"])
                        fig_h = px.bar(h_df, x="Mentions", y="Hospital", orientation="h", color="Mentions", color_continuous_scale=["#C73E1D","#D4A017","#0D7C66"])
                        style_plotly(fig_h, height=400); fig_h.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig_h, use_container_width=True)
                with hc2:
                    st.markdown("##### 📍 Top Regions")
                    rc = Counter(all_regions)
                    if rc:
                        r_df = pd.DataFrame(rc.most_common(12), columns=["Region","Mentions"])
                        fig_r = px.bar(r_df, x="Mentions", y="Region", orientation="h", color="Mentions", color_continuous_scale=["#2E86AB","#E85D04"])
                        style_plotly(fig_r, height=400); fig_r.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig_r, use_container_width=True)

                st.markdown("---")

                # CHINA MAP
                section_header("🗺️ China Healthcare Hubs")
                REGION_COORDS = {"Beijing":(39.9,116.4),"Shanghai":(31.2,121.5),"Guangzhou":(23.1,113.3),"Shenzhen":(22.5,114.1),
                    "Hainan":(19.2,109.7),"Tianjin":(39.1,117.2),"Chengdu":(30.6,104.1),"Wuhan":(30.6,114.3),
                    "Hangzhou":(30.3,120.2),"Nanjing":(32.1,118.8),"Fangchenggang":(21.7,108.4),"Xi'an":(34.3,109.0)}
                rc = Counter(all_regions)
                if rc:
                    mr = [{"Region":r, "Articles":c, "lat":REGION_COORDS[r][0], "lon":REGION_COORDS[r][1]} for r,c in rc.items() if r in REGION_COORDS]
                    if mr:
                        mdf = pd.DataFrame(mr)
                        fig_m = px.scatter_geo(mdf, lat="lat", lon="lon", size="Articles", hover_name="Region", color="Articles",
                                               color_continuous_scale=["#D4A017","#C73E1D"], size_max=35, scope="asia")
                        fig_m.update_geos(center=dict(lat=35,lon=105), projection_scale=3, showland=True, landcolor="#F5F0E8", showocean=True, oceancolor="#EBF5FB", showcountries=True, countrycolor="#ccc")
                        style_plotly(fig_m, height=450); fig_m.update_layout(margin=dict(t=10,l=0,r=0,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig_m, use_container_width=True)

                st.markdown("---")
                section_header("📋 Key Information")
                with st.expander("💳 Payment Systems"): st.markdown("**Out-of-pocket** (WeChat Pay, Alipay, Visa/MC) • **International insurance** (Cigna, Bupa, Allianz) • **Medical packages** (procedure + hotel + interpreter) • **Boao Lecheng** special billing • **30-70% cheaper** than US/Europe")
                with st.expander("📡 Remote Follow-up"): st.markdown("**WeDoctor/Good Doctor** platforms • **Hospital apps** (Ruijin, Tiantan) • **Video consultations** at JCI facilities • **Wearable monitoring** for cardiac/neuro • **International coordinators** assigned post-discharge")
                with st.expander("🔒 Data Management"): st.markdown("**PIPL** (China's GDPR) since 2021 • **Data localization** required • **Cross-border transfer** needs security assessment • **JCI hospitals** follow international protocols • **EHR interoperability** improving")

            # ═══════════════════════════════════════
            # TAB 4: NOTES
            # ═══════════════════════════════════════
            with tab_notes:
                section_header("📝 Notes & Research")
                titles = df_cn["Title"].tolist()
                sel_art = st.selectbox("📄 Select article", options=titles, index=0, key="cn_sel")
                sel_r = df_cn[df_cn["Title"] == sel_art].iloc[0]
                doc_id = int(sel_r["DocID"])

                existing = session.execute(sa_text("SELECT note_text, private_url, ai_keywords FROM china_health_notes WHERE document_id = :d ORDER BY updated_at DESC LIMIT 1"), {"d": doc_id}).fetchone()
                nc1, nc2 = st.columns([3,1])
                with nc1:
                    note_text = st.text_area("✏️ Notes", value=existing[0] if existing else "", height=180, key="cn_note")
                    priv_url = st.text_input("🔗 Link", value=existing[1] if existing else "", key="cn_url")
                with nc2:
                    st.markdown("##### 🤖 AI Keywords")
                    if existing and existing[2]:
                        for k in existing[2].split(", "): st.markdown(f'<span style="background:#E8F5E9;color:#2E7D32;padding:2px 6px;border-radius:10px;font-size:0.75rem;">{k}</span>', unsafe_allow_html=True)

                if st.button("💾 Save & Analyze", type="primary", key="cn_save"):
                    combined = (note_text + " " + sel_r["Title"] + " " + sel_r["Summary"]).lower()
                    nw = [w for w in re_cn.findall(r"[a-z]{4,}", combined) if w not in stop_w]
                    ai_kw = ", ".join([w for w, _ in Counter(nw).most_common(10)])
                    if existing:
                        session.execute(sa_text("UPDATE china_health_notes SET note_text=:n, private_url=:u, ai_keywords=:k, updated_at=NOW() WHERE document_id=:d"), {"n":note_text,"u":priv_url,"k":ai_kw,"d":doc_id})
                    else:
                        session.execute(sa_text("INSERT INTO china_health_notes (document_id,note_text,private_url,ai_keywords) VALUES (:d,:n,:u,:k)"), {"d":doc_id,"n":note_text,"u":priv_url,"k":ai_kw})
                    session.commit(); st.success("✅ Saved!"); st.rerun()

                st.markdown("---")
                all_notes = session.execute(sa_text("SELECT cn.note_text,cn.ai_keywords,cn.updated_at,d.title FROM china_health_notes cn JOIN documents d ON cn.document_id=d.document_id ORDER BY cn.updated_at DESC")).fetchall()
                if all_notes:
                    for n in all_notes:
                        with st.expander(f"📄 {n[3][:70]}"): st.markdown(n[0]); st.markdown(f"**Keywords:** {n[1]}" if n[1] else "")

            # ═══════════════════════════════════════
            # TAB 5: LINKS
            # ═══════════════════════════════════════
            with tab_links:
                section_header("🔗 Links & Resources")
                categories = ["Research Paper","News Article","Hospital Website","Government Policy","Advertising / Marketing","Patient Testimonial","Other"]
                with st.form("cn_add_link", clear_on_submit=True):
                    lk_url = st.text_input("🔗 URL"); lk_title = st.text_input("📄 Title")
                    lk_cat = st.selectbox("📁 Category", categories); lk_desc = st.text_area("📝 Description", height=80)
                    if st.form_submit_button("➕ Add Link", type="primary") and lk_url.strip():
                        lk_kw = ", ".join([w for w,_ in Counter([w for w in re_cn.findall(r"[a-z]{4,}", (lk_title+" "+lk_desc).lower()) if w not in stop_w]).most_common(8)])
                        session.execute(sa_text("INSERT INTO china_health_links (url,title,description,link_category,ai_keywords) VALUES (:u,:t,:d,:c,:k)"), {"u":lk_url,"t":lk_title,"d":lk_desc,"c":lk_cat,"k":lk_kw})
                        session.commit(); st.success("✅ Added!"); st.rerun()

                st.markdown("---")
                links = session.execute(sa_text("SELECT link_id,url,title,description,link_category,ai_keywords,created_at FROM china_health_links ORDER BY created_at DESC")).fetchall()
                if links:
                    for lk in links:
                        cc = {"Research Paper":"#7B2D8E","News Article":"#2E86AB","Hospital Website":"#0D7C66","Government Policy":"#1E3A5F","Advertising / Marketing":"#E85D04","Patient Testimonial":"#D4A017"}.get(lk[4],"#95A5A6")
                        kp = " ".join(f'<span style="background:#F5F5F5;color:#444;padding:2px 6px;border-radius:10px;font-size:0.72rem;">{k.strip()}</span>' for k in (lk[5] or "").split(",")[:6] if k.strip())
                        st.markdown(f'<div style="background:#FFF;border-left:4px solid {cc};padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;"><div style="display:flex;justify-content:space-between;"><a href="{lk[1]}" target="_blank" style="color:#0D2B45;font-weight:600;text-decoration:none;">{lk[2] or lk[1][:80]}</a><span style="background:{cc};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.72rem;">{lk[4]}</span></div><div style="margin:0.3rem 0;">{kp}</div><div style="color:#7F8C8D;font-size:0.85rem;">{(lk[3] or "")[:200]}</div></div>', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"cn_del_{lk[0]}"):
                            session.execute(sa_text("DELETE FROM china_health_links WHERE link_id=:id"), {"id":lk[0]}); session.commit(); st.rerun()
                else:
                    st.info("No links yet.")

        else:
            st.info("No China health articles yet. Run the collector:")
            st.code('python -c "from collectors.china_medtourism_collector import run; run()"')

    finally:
        session.close()

    page_footer()

# PAGE 13: LINKEDIN NEURO DIGITAL HEALTH
# ════════════════════════════════════════════════════════
elif page == "💼 LinkedIn NeuroHealth":
    page_header("LinkedIn NeuroHealth", "Digital health intelligence from LinkedIn — neurodegenerative, mental health, telemedicine & startups")

    session = get_session_cached()
    try:
        from sqlalchemy import text as sa_text
        try:
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS linkedin_neuro_notes (
                note_id SERIAL PRIMARY KEY, document_id INTEGER REFERENCES documents(document_id) ON DELETE CASCADE,
                note_text TEXT, ai_keywords TEXT, author TEXT, post_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"""))
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS linkedin_neuro_links (
                link_id SERIAL PRIMARY KEY, url TEXT NOT NULL, title TEXT, description TEXT,
                link_category VARCHAR(50), author TEXT, ai_keywords TEXT, created_at TIMESTAMP DEFAULT NOW())"""))
            session.commit()
        except Exception:
            session.rollback()

        li_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "linkedin_neurohealth")
            .order_by(desc(Document.publish_date))
            .limit(500)
            .all()
        )

        if li_docs:
            df_li = pd.DataFrame([{
                "DocID": d.document_id, "Date": d.publish_date,
                "Title": d.title or "", "Source": s.source_name,
                "URL": d.url or "", "Summary": (d.summary or ""),
            } for d, s in li_docs])

            df_li["Date"] = pd.to_datetime(df_li["Date"], errors="coerce")
            df_li["Full_Text"] = (df_li["Title"] + " " + df_li["Summary"]).str.lower()

            import re as re_li
            from collections import Counter
            import plotly.graph_objects as go

            # ── TOPIC CLASSIFICATION ──
            LI_TOPICS = {
                "Digital Therapeutics (DTx)": ["digital therapeutics", "dtx", "prescription digital", "software as medical"],
                "Neurodegenerative AI/ML": ["alzheimer", "parkinson", "dementia", "neurodegen", "als ", "amyotrophic", "huntington", "cognitive decline", "brain health"],
                "Mental Health Apps": ["mental health", "depression", "anxiety", "wellness app", "mindfulness", "meditation", "behavioral health", "cbt ", "cognitive behavioral"],
                "Digital Psychiatry": ["psychiatr", "telepsychiatry", "psycholog", "bipolar", "schizophren", "ptsd", "adhd", "mental disorder"],
                "Telemedicine Neuro": ["telemedicine", "telehealth", "remote monitoring", "virtual care", "teleconsult", "remote patient"],
                "Brain-Computer Interface": ["brain computer", "bci ", "neurointerface", "neural interface", "eeg wearable", "neurofeedback", "brain machine"],
                "Wearables & Sensors": ["wearable", "sensor", "smartwatch", "biomarker", "continuous monitoring", "digital biomarker", "accelerometer"],
                "Neurotech Startups": ["startup", "funding", "series a", "series b", "seed round", "venture", "incubator", "accelerator", "raised"],
                "AI Diagnostics": ["ai diagnos", "machine learning", "deep learning", "computer vision", "image analysis", "mri analysis", "prediction model"],
                "Drug Discovery & Biotech": ["drug discovery", "biotech", "clinical trial", "pharma", "pipeline", "fda approv", "ema approv"],
                "Regulation & Policy": ["regulation", "policy", "fda", "ema", "ce mark", "compliance", "approval", "guideline"],
                "Patient Outcomes": ["patient outcome", "quality of life", "caregiver", "patient experience", "real world evidence", "rwe"],
            }

            # ── COMPANY/ORG EXTRACTION ──
            COMPANIES = {
                "Biogen": ["biogen"], "Roche": ["roche"], "Eli Lilly": ["eli lilly", "lilly"],
                "Novartis": ["novartis"], "AbbVie": ["abbvie"], "Eisai": ["eisai"],
                "Akili Interactive": ["akili"], "Pear Therapeutics": ["pear therapeutics"],
                "Woebot Health": ["woebot"], "Headspace": ["headspace"], "Calm": ["calm app", "calm "],
                "BetterHelp": ["betterhelp"], "Talkspace": ["talkspace"],
                "Neuralink": ["neuralink"], "Kernel": ["kernel neuro"],
                "Verily (Google)": ["verily"], "Apple Health": ["apple health", "apple watch health"],
                "Fitbit": ["fitbit"], "SWORD Health": ["sword health"],
                "Oura": ["oura ring", "oura health"], "Medtronic": ["medtronic"],
                "Boston Scientific": ["boston scientific"], "Philips": ["philips health"],
                "Siemens Healthineers": ["siemens health"],
                "Tempus": ["tempus ai"], "Flatiron": ["flatiron health"],
            }

            def extract_li_topics(text):
                topics = []
                for topic, kws in LI_TOPICS.items():
                    if any(kw in text for kw in kws):
                        topics.append(topic)
                return topics if topics else ["General"]

            def extract_companies(text):
                return [c for c, kws in COMPANIES.items() if any(kw in text for kw in kws)]

            # Detect post type from URL
            def detect_post_type(url):
                url_l = url.lower()
                if "/pulse/" in url_l: return "Article"
                elif "/posts/" in url_l: return "Post"
                elif "/events/" in url_l: return "Event"
                elif "/company/" in url_l: return "Company Page"
                else: return "Other"

            df_li["Topics"] = df_li["Full_Text"].apply(extract_li_topics)
            df_li["PrimaryTopic"] = df_li["Topics"].apply(lambda x: x[0])
            df_li["Companies"] = df_li["Full_Text"].apply(extract_companies)
            df_li["PostType"] = df_li["URL"].apply(detect_post_type)

            all_topics = [t for ts in df_li["Topics"] for t in ts]
            all_companies = [c for cs in df_li["Companies"] for c in cs]

            palette = ["#0077B5", "#1E3A5F", "#E85D04", "#7B2D8E", "#0D7C66",
                        "#D4A017", "#2E86AB", "#A23B72", "#C73E1D", "#44AF69",
                        "#F18F01", "#ECA72C", "#226F54", "#DA627D", "#4A4E69", "#00B4D8"]

            stop_w = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","from","is","it","this","that","are","was","were","be","been","have","has","had","do","does","did","will","would","could","should","not","no","its","as","if","than","so","up","out","about","into","over","after","under","between","through","during","before","more","most","other","some","also","all","each","both","few","many","much","any","which","what","who","when","where","why","their","them","they","he","she","we","you","his","her","our","your","s","new","one","two","us","my","me","these","those","has","been","can","may","its","such","only","said","like","just","know","get","make","way","linkedin","post","article","share","read","comment","published"}

            # ════════════════════════════════════════
            # TABS
            # ════════════════════════════════════════
            tab_dash, tab_companies, tab_notes, tab_links = st.tabs([
                "📊 Dashboard & Trends",
                "🏢 Companies & Players",
                "📝 Notes & Analysis",
                "🔗 Saved Posts & Links",
            ])

            # ═══════════════════════════════════════
            # TAB 1: DASHBOARD
            # ═══════════════════════════════════════
            with tab_dash:
                section_header("🔍 Filters")
                fc1, fc2, fc3 = st.columns([2, 2, 2])
                with fc1:
                    sel_topics = st.multiselect("📌 Topic", sorted(set(all_topics)), default=[], key="li_tp")
                with fc2:
                    vd = df_li["Date"].dropna()
                    dr = st.date_input("📅 Dates", value=(vd.min().date(), vd.max().date()), min_value=vd.min().date(), max_value=vd.max().date(), key="li_dr") if not vd.empty else None
                with fc3:
                    kw_s = st.text_input("🔎 Keyword", placeholder="e.g. Alzheimer, startup, wearable...", key="li_kw")

                filtered = df_li.copy()
                if sel_topics:
                    filtered = filtered[filtered["Topics"].apply(lambda t: any(x in sel_topics for x in t))]
                if dr and len(dr) == 2:
                    filtered = filtered[(filtered["Date"] >= pd.Timestamp(dr[0])) & (filtered["Date"] <= pd.Timestamp(dr[1]))]
                if kw_s.strip():
                    filtered = filtered[filtered["Full_Text"].str.contains(kw_s.strip().lower(), na=False)]

                f_topics = [t for ts in filtered["Topics"] for t in ts]
                f_companies = [c for cs in filtered["Companies"] for c in cs]
                f_types = filtered["PostType"].tolist()

                st.caption(f"**{len(filtered)}** posts after filters")
                st.markdown("---")

                # KPIs
                k1, k2, k3, k4 = st.columns(4)
                with k1: kpi_card("Posts", str(len(filtered)))
                with k2: kpi_card("Topics", str(len(set(f_topics))))
                with k3: kpi_card("Companies", str(len(set(f_companies))))
                with k4: kpi_card("Post Types", str(len(set(f_types))))

                st.markdown("<br>", unsafe_allow_html=True)

                # TREEMAP + POST TYPE PIE
                section_header("🗺️ Topic Landscape")
                ct, cp = st.columns(2)
                with ct:
                    st.markdown("##### 🌳 Topic Treemap")
                    tc = Counter(f_topics)
                    if tc:
                        tc_df = pd.DataFrame(tc.most_common(15), columns=["Topic", "Count"])
                        fig = px.treemap(tc_df, path=["Topic"], values="Count", color="Count",
                                          color_continuous_scale=["#0077B5", "#1E3A5F", "#E85D04"])
                        fig.update_traces(textinfo="label+value", textfont_size=12)
                        style_plotly(fig, height=400); fig.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig, use_container_width=True)

                with cp:
                    st.markdown("##### 📋 Content Type")
                    ptc = Counter(f_types)
                    if ptc:
                        pt_df = pd.DataFrame(ptc.most_common(), columns=["Type", "Count"])
                        fig_pt = px.pie(pt_df, values="Count", names="Type", color_discrete_sequence=palette, hole=0.4)
                        fig_pt.update_traces(textinfo="label+percent"); style_plotly(fig_pt, height=400)
                        st.plotly_chart(fig_pt, use_container_width=True)

                st.markdown("---")

                # SUNBURST: Topic → Company
                section_header("☀️ Topic × Company Landscape")
                sun_rows = []
                for _, row in filtered.iterrows():
                    for t in row["Topics"]:
                        for c in (row["Companies"] or ["Independent"]):
                            sun_rows.append({"Topic": t, "Company": c})
                if sun_rows:
                    sun_df = pd.DataFrame(sun_rows)
                    sun_agg = sun_df.groupby(["Topic", "Company"]).size().reset_index(name="Count")
                    fig_sb = px.sunburst(sun_agg, path=["Topic", "Company"], values="Count", color="Count",
                                          color_continuous_scale=["#0077B5", "#E85D04", "#7B2D8E"])
                    style_plotly(fig_sb, height=450); fig_sb.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                    st.plotly_chart(fig_sb, use_container_width=True)

                st.markdown("---")

                # TIMELINE
                section_header("⏱️ Timeline")
                tl = filtered.dropna(subset=["Date"]).copy()
                if not tl.empty:
                    tl["TC"] = tl["Topics"].apply(len).clip(lower=1)
                    fig_tl = px.scatter(tl, x="Date", y="PrimaryTopic", size="TC", color="PrimaryTopic",
                                         hover_name="Title", color_discrete_sequence=palette, size_max=16, opacity=0.8)
                    style_plotly(fig_tl, height=380); fig_tl.update_layout(showlegend=False, margin=dict(l=10,r=10,t=10,b=40))
                    st.plotly_chart(fig_tl, use_container_width=True)

                st.markdown("---")

                # WORD CLOUD + FREQUENCY
                section_header("💬 Text Analysis")
                corpus = " ".join(filtered["Title"].dropna().tolist() + filtered["Summary"].dropna().tolist()).lower()
                words = [w for w in re_li.findall(r"[a-z]{3,}", corpus) if w not in stop_w]
                wf = Counter(words); tw = wf.most_common(25)

                wc1, wc2 = st.columns(2)
                with wc1:
                    st.markdown("##### ☁️ Word Cloud")
                    if tw:
                        try:
                            from wordcloud import WordCloud; import matplotlib.pyplot as plt
                            wc = WordCloud(width=800, height=400, background_color="white", colormap="Blues", max_words=60, contour_color="#0077B5").generate_from_frequencies(dict(tw))
                            fig_wc, ax = plt.subplots(figsize=(10,5)); ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
                            st.pyplot(fig_wc, use_container_width=True); plt.close(fig_wc)
                        except ImportError:
                            tw_df = pd.DataFrame(tw[:15], columns=["Word","Count"])
                            fig_fb = px.bar(tw_df, x="Count", y="Word", orientation="h", color="Count", color_continuous_scale=["#0077B5","#1E3A5F"])
                            style_plotly(fig_fb, height=350); fig_fb.update_layout(showlegend=False, coloraxis_showscale=False)
                            st.plotly_chart(fig_fb, use_container_width=True)
                with wc2:
                    st.markdown("##### 📊 Top Words")
                    if tw:
                        tw_df = pd.DataFrame(tw[:20], columns=["Word","Freq"])
                        fig_f = px.bar(tw_df, x="Freq", y="Word", orientation="h", color="Freq", text="Freq", color_continuous_scale=["#0077B5","#E85D04"])
                        fig_f.update_traces(textposition="outside"); style_plotly(fig_f, height=450)
                        fig_f.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(fig_f, use_container_width=True)

                st.markdown("---")

                # KEYWORD TREND
                section_header("📈 Keyword Trends")
                top_kw = [w for w, _ in tw[:8]]
                tl_kw = filtered.dropna(subset=["Date"]).copy()
                if not tl_kw.empty and top_kw:
                    # Filter to last 24 months for cleaner visualization
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=730)
                    tl_kw_recent = tl_kw[tl_kw["Date"] >= cutoff].copy()
                    if tl_kw_recent.empty:
                        tl_kw_recent = tl_kw.copy()

                    tl_kw_recent["YM"] = tl_kw_recent["Date"].dt.to_period("M").astype(str)
                    kw_rows = []
                    for _, row in tl_kw_recent.iterrows():
                        for kw in top_kw:
                            if kw in row["Full_Text"]: kw_rows.append({"Month": row["YM"], "Keyword": kw})
                    if kw_rows:
                        kw_agg = pd.DataFrame(kw_rows).groupby(["Month","Keyword"]).size().reset_index(name="Mentions")

                        # AI Insight box
                        top_month = kw_agg.groupby("Month")["Mentions"].sum().idxmax()
                        top_kw_name = kw_agg.groupby("Keyword")["Mentions"].sum().idxmax()
                        top_kw_val = int(kw_agg.groupby("Keyword")["Mentions"].sum().max())
                        n_months = kw_agg["Month"].nunique()
                        avg_per_month = round(kw_agg.groupby("Month")["Mentions"].sum().mean(), 1)

                        # Detect rising keywords
                        months_sorted = sorted(kw_agg["Month"].unique())
                        rising_kws = []
                        if len(months_sorted) >= 2:
                            last_2 = months_sorted[-2:]
                            for kw in top_kw:
                                recent = kw_agg[(kw_agg["Keyword"]==kw) & (kw_agg["Month"].isin(last_2))]["Mentions"].sum()
                                total = kw_agg[kw_agg["Keyword"]==kw]["Mentions"].sum()
                                if total > 0 and recent / total > 0.5:
                                    rising_kws.append(kw)

                        rising_text = f"<b>Rising keywords:</b> {', '.join(rising_kws[:4])}" if rising_kws else "<b>No clear rising trend</b> — mentions distributed evenly"

                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg, #F8FBFF 0%, #F0F7FF 100%);
                                    border:1px solid #D6E4F0; border-left:4px solid #0077B5;
                                    padding:14px 18px; border-radius:0 8px 8px 0; margin-bottom:16px;">
                            <div style="font-size:0.8rem; font-weight:700; color:#0D2B45; margin-bottom:6px;">
                                🤖 Trend Intelligence
                            </div>
                            <div style="font-size:0.82rem; color:#444; line-height:1.6;">
                                Analyzed <b>{n_months} months</b> of LinkedIn discourse with avg <b>{avg_per_month} mentions/month</b>.<br>
                                Dominant keyword: <b>"{top_kw_name}"</b> with {top_kw_val} total mentions. Peak activity: <b>{top_month}</b>.<br>
                                {rising_text}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Area chart instead of line for better visual
                        fig_kt = px.area(kw_agg, x="Month", y="Mentions", color="Keyword",
                                          color_discrete_sequence=palette, line_shape="spline")
                        fig_kt.update_traces(line=dict(width=2), opacity=0.7)
                        style_plotly(fig_kt, height=380)
                        fig_kt.update_layout(
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=10)),
                            xaxis_title="", yaxis_title="Mentions",
                            margin=dict(l=10, r=10, t=40, b=10),
                        )
                        st.plotly_chart(fig_kt, use_container_width=True)

                st.markdown("---")

                # HEATMAP
                section_header("🔥 Topic Seasonality")
                heat = filtered.dropna(subset=["Date"]).copy()
                if not heat.empty:
                    hr = []
                    for _, row in heat.iterrows():
                        for t in row["Topics"]: hr.append({"Month": row["Date"].strftime("%b"), "MN": row["Date"].month, "Topic": t})
                    if hr:
                        hdf = pd.DataFrame(hr)
                        hp = hdf.pivot_table(index="Topic", columns="Month", values="MN", aggfunc="count", fill_value=0)
                        mo = [m for m in ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"] if m in hp.columns]
                        hp = hp[mo]; tp12 = [t for t, _ in Counter(f_topics).most_common(12)]; hp = hp[hp.index.isin(tp12)]
                        if not hp.empty:
                            fig_hm = px.imshow(hp.values, x=hp.columns.tolist(), y=hp.index.tolist(), color_continuous_scale=["#F0F4F8","#0077B5","#1E3A5F"], aspect="auto", text_auto=True)
                            style_plotly(fig_hm, height=max(280, len(hp)*35+60)); fig_hm.update_layout(coloraxis_showscale=False)
                            st.plotly_chart(fig_hm, use_container_width=True)

                st.markdown("---")

                # POSTS
                section_header("💼 LinkedIn Posts")
                sort_o = st.selectbox("Sort", ["Most recent", "Alphabetical"], index=0, key="li_sort")
                display = filtered.sort_values("Date", ascending=False) if sort_o == "Most recent" else filtered.sort_values("Title")
                PS = 12; tp = max(1, -(-len(display)//PS)); pn = st.number_input("Page", 1, tp, 1, key="li_page")
                sl = display.iloc[(pn-1)*PS : pn*PS]
                for _, row in sl.iterrows():
                    t_html = " ".join(f'<span style="background:#E3F2FD;color:#0077B5;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">{t}</span>' for t in row["Topics"][:4])
                    c_html = " ".join(f'<span style="background:#F3E5F5;color:#7B2D8E;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">🏢 {c}</span>' for c in row["Companies"][:2])
                    type_color = {"Article":"#0077B5","Post":"#0D7C66","Event":"#E85D04","Company Page":"#7B2D8E"}.get(row["PostType"], "#95A5A6")
                    ds = row["Date"].strftime("%d %b %Y") if pd.notna(row["Date"]) else ""
                    st.markdown(f"""
                    <div style="background:#FFF;border-left:4px solid #0077B5;padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <a href="{row['URL']}" target="_blank" style="color:#0D2B45;font-weight:600;font-size:0.95rem;text-decoration:none;">{row['Title'][:120]}</a>
                            <div><span style="background:{type_color};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.7rem;">{row['PostType']}</span>
                            <span style="color:#95A5A6;font-size:0.75rem;margin-left:8px;">{ds}</span></div>
                        </div>
                        <div style="margin:0.3rem 0;">{t_html} {c_html}</div>
                        <div style="color:#7F8C8D;font-size:0.85rem;line-height:1.5;margin-top:0.3rem;">{row['Summary'][:200]}{'...' if len(row['Summary'])>200 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.caption(f"Page {pn} of {tp} — {len(display)} posts")

            # ═══════════════════════════════════════
            # TAB 2: COMPANIES
            # ═══════════════════════════════════════
            with tab_companies:
                section_header("🏢 Key Companies & Players")
                cc = Counter(all_companies)
                if cc:
                    cc_df = pd.DataFrame(cc.most_common(20), columns=["Company","Mentions"])
                    fig_cc = px.bar(cc_df, x="Mentions", y="Company", orientation="h", color="Mentions", text="Mentions",
                                     color_continuous_scale=["#0077B5","#7B2D8E","#E85D04"])
                    fig_cc.update_traces(textposition="outside"); style_plotly(fig_cc, height=500)
                    fig_cc.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig_cc, use_container_width=True)

                    st.markdown("---")

                    # Network: Company ↔ Topic
                    section_header("🕸️ Company × Topic Network")
                    import math
                    edges = Counter()
                    for _, row in df_li.iterrows():
                        for c in row["Companies"]:
                            for t in row["Topics"]:
                                edges[(c, t)] += 1
                    top_e = edges.most_common(40)
                    if top_e:
                        ns = set()
                        for (c, t), _ in top_e: ns.add(("co", c)); ns.add(("tp", t))
                        nl = list(ns); cos = [n for n in nl if n[0]=="co"]; tps = [n for n in nl if n[0]=="tp"]
                        pos = {}
                        for i, n in enumerate(cos): a = 2*math.pi*i/max(len(cos),1); pos[n] = (math.cos(a)*2.5, math.sin(a)*2.5)
                        for i, n in enumerate(tps): a = 2*math.pi*i/max(len(tps),1); pos[n] = (math.cos(a)*1, math.sin(a)*1)

                        ex, ey = [], []
                        for (c, t), _ in top_e:
                            x0,y0 = pos[("co",c)]; x1,y1 = pos[("tp",t)]
                            ex += [x0,x1,None]; ey += [y0,y1,None]

                        fig_n = go.Figure()
                        fig_n.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.7, color="rgba(150,150,150,0.4)"), hoverinfo="none"))
                        fig_n.add_trace(go.Scatter(
                            x=[pos[("co",n[1])][0] for n in cos], y=[pos[("co",n[1])][1] for n in cos],
                            mode="markers+text", marker=dict(size=[max(8, cc.get(n[1],1)*3) for n in cos], color="#0077B5"),
                            text=[n[1] for n in cos], textposition="top center", textfont=dict(size=8), name="Companies"))
                        fig_n.add_trace(go.Scatter(
                            x=[pos[("tp",n[1])][0] for n in tps], y=[pos[("tp",n[1])][1] for n in tps],
                            mode="markers+text", marker=dict(size=12, color="#E85D04", symbol="diamond"),
                            text=[n[1] for n in tps], textposition="bottom center", textfont=dict(size=7, color="#E85D04"), name="Topics"))
                        style_plotly(fig_n, height=500)
                        fig_n.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        st.plotly_chart(fig_n, use_container_width=True)
                else:
                    st.info("No company mentions detected yet.")

            # ═══════════════════════════════════════
            # TAB 3: NOTES
            # ═══════════════════════════════════════
            with tab_notes:
                section_header("📝 Notes & Analysis")
                titles = df_li["Title"].tolist()
                sel_art = st.selectbox("📄 Select post", options=titles, index=0, key="li_sel")
                sel_r = df_li[df_li["Title"] == sel_art].iloc[0]
                doc_id = int(sel_r["DocID"])

                existing = session.execute(sa_text("SELECT note_text, ai_keywords, author FROM linkedin_neuro_notes WHERE document_id=:d ORDER BY updated_at DESC LIMIT 1"), {"d": doc_id}).fetchone()

                nc1, nc2 = st.columns([3,1])
                with nc1:
                    note_text = st.text_area("✏️ Notes", value=existing[0] if existing else "", height=180, key="li_note")
                    author = st.text_input("👤 Author / Influencer", value=existing[2] if existing else "", key="li_auth")
                with nc2:
                    st.markdown("##### 🤖 AI Keywords")
                    if existing and existing[1]:
                        for k in existing[1].split(", "): st.markdown(f'<span style="background:#E3F2FD;color:#0077B5;padding:2px 6px;border-radius:10px;font-size:0.75rem;">{k}</span>', unsafe_allow_html=True)

                if st.button("💾 Save & Analyze", type="primary", key="li_save"):
                    combined = (note_text + " " + sel_r["Title"] + " " + sel_r["Summary"]).lower()
                    nw = [w for w in re_li.findall(r"[a-z]{4,}", combined) if w not in stop_w]
                    ai_kw = ", ".join([w for w, _ in Counter(nw).most_common(10)])
                    if existing:
                        session.execute(sa_text("UPDATE linkedin_neuro_notes SET note_text=:n, ai_keywords=:k, author=:a, updated_at=NOW() WHERE document_id=:d"), {"n":note_text,"k":ai_kw,"a":author,"d":doc_id})
                    else:
                        session.execute(sa_text("INSERT INTO linkedin_neuro_notes (document_id,note_text,ai_keywords,author) VALUES (:d,:n,:k,:a)"), {"d":doc_id,"n":note_text,"k":ai_kw,"a":author})
                    session.commit(); st.success("✅ Saved!"); st.rerun()

                st.markdown("---")
                all_n = session.execute(sa_text("SELECT n.note_text,n.ai_keywords,n.author,n.updated_at,d.title FROM linkedin_neuro_notes n JOIN documents d ON n.document_id=d.document_id ORDER BY n.updated_at DESC")).fetchall()
                if all_n:
                    for n in all_n:
                        with st.expander(f"💼 {n[4][:70]}"): st.markdown(n[0]); st.markdown(f"**Author:** {n[2]}" if n[2] else ""); st.markdown(f"**Keywords:** {n[1]}" if n[1] else "")

            # ═══════════════════════════════════════
            # TAB 4: LINKS
            # ═══════════════════════════════════════
            with tab_links:
                section_header("🔗 Saved Posts & Resources")
                categories = ["LinkedIn Post","LinkedIn Article","Company Profile","Research Paper","News","Podcast/Video","Other"]
                with st.form("li_add_link", clear_on_submit=True):
                    lk_url = st.text_input("🔗 URL"); lk_title = st.text_input("📄 Title")
                    lk_cat = st.selectbox("📁 Category", categories); lk_auth = st.text_input("👤 Author")
                    lk_desc = st.text_area("📝 Notes", height=80)
                    if st.form_submit_button("➕ Add", type="primary") and lk_url.strip():
                        lk_kw = ", ".join([w for w,_ in Counter([w for w in re_li.findall(r"[a-z]{4,}", (lk_title+" "+lk_desc).lower()) if w not in stop_w]).most_common(8)])
                        session.execute(sa_text("INSERT INTO linkedin_neuro_links (url,title,description,link_category,author,ai_keywords) VALUES (:u,:t,:d,:c,:a,:k)"), {"u":lk_url,"t":lk_title,"d":lk_desc,"c":lk_cat,"a":lk_auth,"k":lk_kw})
                        session.commit(); st.success("✅ Added!"); st.rerun()

                st.markdown("---")
                links = session.execute(sa_text("SELECT link_id,url,title,description,link_category,author,ai_keywords,created_at FROM linkedin_neuro_links ORDER BY created_at DESC")).fetchall()
                if links:
                    for lk in links:
                        cc = {"LinkedIn Post":"#0077B5","LinkedIn Article":"#1E3A5F","Company Profile":"#7B2D8E","Research Paper":"#0D7C66","News":"#2E86AB","Podcast/Video":"#E85D04"}.get(lk[4],"#95A5A6")
                        kp = " ".join(f'<span style="background:#F5F5F5;color:#444;padding:2px 6px;border-radius:10px;font-size:0.72rem;">{k.strip()}</span>' for k in (lk[6] or "").split(",")[:6] if k.strip())
                        st.markdown(f'<div style="background:#FFF;border-left:4px solid {cc};padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;"><div style="display:flex;justify-content:space-between;"><a href="{lk[1]}" target="_blank" style="color:#0077B5;font-weight:600;text-decoration:none;">{lk[2] or lk[1][:80]}</a><span style="background:{cc};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.72rem;">{lk[4]}</span></div><div style="margin:0.2rem 0;font-size:0.8rem;color:#666;">👤 {lk[5] or "Unknown"}</div><div style="margin:0.3rem 0;">{kp}</div><div style="color:#7F8C8D;font-size:0.85rem;">{(lk[3] or "")[:200]}</div></div>', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"li_del_{lk[0]}"):
                            session.execute(sa_text("DELETE FROM linkedin_neuro_links WHERE link_id=:id"), {"id":lk[0]}); session.commit(); st.rerun()
                else:
                    st.info("No saved posts yet. Add LinkedIn posts and resources above!")

        else:
            st.info("No LinkedIn posts yet. Run the collector:")
            st.code('python -c "from collectors.linkedin_neurohealth_collector import run; run()"')

    finally:
        session.close()

    page_footer()

# PAGE 14: AI AGENT HOSPITAL (Tsinghua AIR) v2.0
# ════════════════════════════════════════════════════════
elif page == "🤖 AI Agent Hospital":
    page_header("AI Agent Hospital", "Tsinghua University AIR — MedAgent-Zero, Chinese university AI healthcare & DeepSeek integration")

    session = get_session_cached()
    try:
        from sqlalchemy import text as sa_text
        try:
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS ai_hospital_notes (
                note_id SERIAL PRIMARY KEY, document_id INTEGER REFERENCES documents(document_id) ON DELETE CASCADE,
                note_text TEXT, ai_keywords TEXT, university TEXT, project TEXT,
                created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW())"""))
            session.execute(sa_text("""CREATE TABLE IF NOT EXISTS ai_hospital_links (
                link_id SERIAL PRIMARY KEY, url TEXT NOT NULL, title TEXT, description TEXT,
                link_category VARCHAR(50), ai_keywords TEXT, created_at TIMESTAMP DEFAULT NOW())"""))
            session.commit()
        except Exception:
            session.rollback()

        ai_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "ai_agent_hospital")
            .order_by(desc(Document.publish_date))
            .limit(500)
            .all()
        )

        if ai_docs:
            df_ai = pd.DataFrame([{
                "DocID": d.document_id, "Date": d.publish_date,
                "Title": d.title or "", "Source": s.source_name,
                "URL": d.url or "", "Summary": (d.summary or ""),
            } for d, s in ai_docs])

            df_ai["Date"] = pd.to_datetime(df_ai["Date"], errors="coerce")
            df_ai["Full_Text"] = (df_ai["Title"] + " " + df_ai["Summary"]).str.lower()

            import re as re_ai
            import math
            from collections import Counter
            import plotly.graph_objects as go

            AI_TOPICS = {
                "AI Agents & LLM": ["agent", "llm", "large language model", "chatgpt", "gpt-4", "autonomous"],
                "Self-Evolution": ["self-evolv", "medagent-zero", "evolution", "self-improv"],
                "Clinical Diagnostics": ["diagnos", "accuracy", "medqa", "clinical decision"],
                "Virtual Hospital": ["virtual hospital", "simulacrum", "simulation", "virtual patient", "digital twin"],
                "Telemedicine": ["telemedicine", "telehealth", "remote", "rural", "smartphone"],
                "Medical Education": ["medical education", "training", "medical student", "teaching"],
                "DeepSeek Integration": ["deepseek", "open-source", "local deployment"],
                "Data Privacy": ["data privacy", "data sovereign", "anonymiz", "cybersecurity", "pipl"],
                "Drug Discovery": ["drug", "drugclip", "pharmaceutical", "virtual screening"],
                "Neurodegenerative AI": ["alzheimer", "parkinson", "dementia", "neurodegen", "brain", "cognitive"],
                "Mental Health AI": ["mental health", "psychiatric", "depression", "anxiety", "psycholog"],
                "Medical Imaging": ["imaging", "pathology", "radiology", "mri", "ct scan", "computer vision"],
                "Startups & Pilots": ["tairex", "zijing", "startup", "spinoff", "pilot", "commerc"],
            }

            UNIVERSITIES = {
                "Tsinghua University": ["tsinghua", "air ", "institute for ai industry"],
                "Peking University": ["peking university", "pku", "peking union"],
                "Fudan University": ["fudan"],
                "Shanghai Jiao Tong University": ["jiao tong", "sjtu"],
                "Zhejiang University": ["zhejiang university"],
                "USTC Hefei": ["ustc", "university of science and technology of china"],
                "Tongji University": ["tongji"],
                "West China / Sichuan University": ["west china", "sichuan university"],
                "Sun Yat-sen University": ["sun yat-sen", "zhongshan university"],
                "Harbin Institute of Technology": ["harbin institute", "hit "],
                "Nanjing University": ["nanjing university"],
                "Wuhan University": ["wuhan university"],
                "Huazhong UST": ["huazhong", "hust"],
            }

            UNI_COORDS = {
                "Tsinghua University": (39.99, 116.32), "Peking University": (39.99, 116.30),
                "Fudan University": (31.30, 121.50), "Shanghai Jiao Tong University": (31.03, 121.43),
                "Zhejiang University": (30.26, 120.12), "USTC Hefei": (31.84, 117.26),
                "Tongji University": (31.28, 121.50), "West China / Sichuan University": (30.63, 104.09),
                "Sun Yat-sen University": (23.09, 113.29), "Harbin Institute of Technology": (45.75, 126.68),
                "Nanjing University": (32.06, 118.78), "Wuhan University": (30.54, 114.36),
                "Huazhong UST": (30.51, 114.42),
            }

            ENTITIES = {
                "Prof. Liu Yang": ["liu yang", "yang liu"],
                "MedAgent-Zero": ["medagent", "med-agent"],
                "Tairex": ["tairex"],
                "Zijing Zhikang": ["zijing", "zhikang"],
                "DeepSeek": ["deepseek"],
                "Chang Gung Hospital": ["chang gung"],
                "MedGo (Tongji)": ["medgo"],
            }

            def extract_ai_topics(text):
                return [t for t, kws in AI_TOPICS.items() if any(kw in text for kw in kws)] or ["General"]
            def extract_universities(text):
                return [u for u, kws in UNIVERSITIES.items() if any(kw in text for kw in kws)]
            def extract_entities(text):
                return [e for e, kws in ENTITIES.items() if any(kw in text for kw in kws)]

            df_ai["Topics"] = df_ai["Full_Text"].apply(extract_ai_topics)
            df_ai["PrimaryTopic"] = df_ai["Topics"].apply(lambda x: x[0])
            df_ai["Universities"] = df_ai["Full_Text"].apply(extract_universities)
            df_ai["Entities"] = df_ai["Full_Text"].apply(extract_entities)

            all_topics = [t for ts in df_ai["Topics"] for t in ts]
            all_unis = [u for us in df_ai["Universities"] for u in us]
            all_entities = [e for es in df_ai["Entities"] for e in es]

            palette = ["#7B2D8E", "#0D7C66", "#E85D04", "#1E3A5F", "#C73E1D", "#D4A017",
                        "#2E86AB", "#A23B72", "#F18F01", "#44AF69", "#00B4D8", "#226F54"]

            stop_w = {"the","a","an","and","or","but","in","on","at","to","for","of","with","by","from","is","it","this","that","are","was","were","be","been","have","has","had","do","does","did","will","would","could","should","not","no","its","as","if","than","so","up","out","about","into","over","after","under","between","through","during","before","more","most","other","some","also","all","each","both","few","many","much","any","which","what","who","when","where","why","their","them","they","he","she","we","you","his","her","our","your","s","new","one","two","us","my","me","these","those","china","chinese","has","been","can","may","its","such","only","said","according","first","using","based","used","including","university"}

            tab_dash, tab_unis, tab_arch, tab_notes, tab_links = st.tabs([
                "📊 Dashboard", "🎓 Universities & Projects", "🏗️ Architecture", "📝 Notes", "🔗 Links & Papers"])

            # ═══════════ TAB 1: DASHBOARD ═══════════
            with tab_dash:
                section_header("🔍 Filters")
                fc1, fc2, fc3 = st.columns([2,2,2])
                with fc1: sel_tp = st.multiselect("📌 Topic", sorted(set(all_topics)), default=[], key="aih_tp")
                with fc2:
                    vd = df_ai["Date"].dropna()
                    dr = st.date_input("📅 Dates", value=(vd.min().date(), vd.max().date()), min_value=vd.min().date(), max_value=vd.max().date(), key="aih_dr") if not vd.empty else None
                with fc3: kw = st.text_input("🔎 Keyword", key="aih_kw")

                filtered = df_ai.copy()
                if sel_tp: filtered = filtered[filtered["Topics"].apply(lambda t: any(x in sel_tp for x in t))]
                if dr and len(dr)==2: filtered = filtered[(filtered["Date"]>=pd.Timestamp(dr[0]))&(filtered["Date"]<=pd.Timestamp(dr[1]))]
                if kw.strip(): filtered = filtered[filtered["Full_Text"].str.contains(kw.strip().lower(), na=False)]

                f_topics = [t for ts in filtered["Topics"] for t in ts]
                f_unis = [u for us in filtered["Universities"] for u in us]
                st.caption(f"**{len(filtered)}** articles"); st.markdown("---")

                k1,k2,k3,k4 = st.columns(4)
                with k1: kpi_card("Articles", str(len(filtered)))
                with k2: kpi_card("Topics", str(len(set(f_topics))))
                with k3: kpi_card("Universities", str(len(set(f_unis))))
                with k4: kpi_card("This Month", str(len(filtered[filtered["Date"]>=pd.Timestamp.now()-pd.Timedelta(days=30)])))

                st.markdown("<br>", unsafe_allow_html=True)

                # TREEMAP + SUNBURST
                section_header("🗺️ Topic Landscape")
                ct, cs = st.columns(2)
                with ct:
                    st.markdown("##### 🌳 Topic Treemap")
                    tc = Counter(f_topics)
                    if tc:
                        tc_df = pd.DataFrame(tc.most_common(15), columns=["Topic","Count"])
                        fig = px.treemap(tc_df, path=["Topic"], values="Count", color="Count", color_continuous_scale=["#7B2D8E","#0D7C66","#E85D04"])
                        fig.update_traces(textinfo="label+value", textfont_size=12); style_plotly(fig, height=400)
                        fig.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig, use_container_width=True)
                with cs:
                    st.markdown("##### ☀️ University × Topic")
                    sr = [{"University": u, "Topic": t} for _, row in filtered.iterrows() for u in (row["Universities"] or ["Unknown"]) for t in row["Topics"]]
                    if sr:
                        sa = pd.DataFrame(sr).groupby(["University","Topic"]).size().reset_index(name="Count")
                        fs = px.sunburst(sa, path=["University","Topic"], values="Count", color="Count", color_continuous_scale=["#2E86AB","#7B2D8E","#E85D04"])
                        style_plotly(fs, height=400); fs.update_layout(margin=dict(t=10,l=10,r=10,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fs, use_container_width=True)

                st.markdown("---")

                # NETWORK: University × Topic
                section_header("🕸️ Network: Universities × Research Areas")
                edges = Counter()
                for _, row in filtered.iterrows():
                    for u in row["Universities"]:
                        for t in row["Topics"]:
                            edges[(u, t)] += 1
                top_edges = edges.most_common(50)
                if top_edges:
                    ns = set()
                    for (u, t), _ in top_edges: ns.add(("uni", u)); ns.add(("topic", t))
                    nl = list(ns); unis_n = [n for n in nl if n[0]=="uni"]; tps_n = [n for n in nl if n[0]=="topic"]
                    pos = {}
                    for i, n in enumerate(unis_n): a = 2*math.pi*i/max(len(unis_n),1); pos[n] = (math.cos(a)*2.5, math.sin(a)*2.5)
                    for i, n in enumerate(tps_n): a = 2*math.pi*i/max(len(tps_n),1); pos[n] = (math.cos(a)*1, math.sin(a)*1)
                    ex, ey = [], []
                    for (u, t), _ in top_edges:
                        x0,y0 = pos[("uni",u)]; x1,y1 = pos[("topic",t)]; ex += [x0,x1,None]; ey += [y0,y1,None]
                    uc = Counter(f_unis)
                    fig_n = go.Figure()
                    fig_n.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=0.7, color="rgba(150,150,150,0.4)"), hoverinfo="none"))
                    fig_n.add_trace(go.Scatter(x=[pos[n][0] for n in unis_n], y=[pos[n][1] for n in unis_n], mode="markers+text",
                        marker=dict(size=[max(10, uc.get(n[1],1)*3) for n in unis_n], color="#7B2D8E", line=dict(width=1, color="white")),
                        text=[n[1].replace(" University","").replace(" of Technology","") for n in unis_n], textposition="top center", textfont=dict(size=8), name="Universities"))
                    ttc = Counter(f_topics)
                    fig_n.add_trace(go.Scatter(x=[pos[n][0] for n in tps_n], y=[pos[n][1] for n in tps_n], mode="markers+text",
                        marker=dict(size=[max(8, ttc.get(n[1],1)*2) for n in tps_n], color="#0D7C66", symbol="diamond"),
                        text=[n[1] for n in tps_n], textposition="bottom center", textfont=dict(size=7, color="#0D7C66"), name="Topics"))
                    style_plotly(fig_n, height=500)
                    fig_n.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    st.plotly_chart(fig_n, use_container_width=True)

                st.markdown("---")

                # HEATMAP: University × Topic
                section_header("🔥 Heatmap: University × Research Area")
                heat_rows = [{"University": u, "Topic": t} for _, row in filtered.iterrows() for u in row["Universities"] for t in row["Topics"]]
                if heat_rows:
                    hdf = pd.DataFrame(heat_rows)
                    hp = hdf.pivot_table(index="University", columns="Topic", aggfunc="size", fill_value=0)
                    if not hp.empty:
                        fig_hm = px.imshow(hp.values, x=hp.columns.tolist(), y=hp.index.tolist(), color_continuous_scale=["#F5F0FF","#7B2D8E","#E85D04"], aspect="auto", text_auto=True)
                        style_plotly(fig_hm, height=max(280, len(hp)*40+80)); fig_hm.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="")
                        st.plotly_chart(fig_hm, use_container_width=True)

                st.markdown("---")

                # TIMELINE
                section_header("⏱️ Timeline")
                tl = filtered.dropna(subset=["Date"]).copy()
                if not tl.empty:
                    tl["TC"] = tl["Topics"].apply(len).clip(lower=1)
                    ft = px.scatter(tl, x="Date", y="PrimaryTopic", size="TC", color="PrimaryTopic", hover_name="Title", color_discrete_sequence=palette, size_max=16, opacity=0.8)
                    style_plotly(ft, height=380); ft.update_layout(showlegend=False, margin=dict(l=10,r=10,t=10,b=40))
                    st.plotly_chart(ft, use_container_width=True)

                st.markdown("---")

                # WORD CLOUD + FREQ
                section_header("💬 Semantic Analysis")
                corpus = " ".join(filtered["Title"].dropna().tolist()+filtered["Summary"].dropna().tolist()).lower()
                words = [w for w in re_ai.findall(r"[a-z]{3,}", corpus) if w not in stop_w]
                wf = Counter(words); tw = wf.most_common(25)
                wc1, wc2 = st.columns(2)
                with wc1:
                    st.markdown("##### ☁️ Word Cloud")
                    if tw:
                        try:
                            from wordcloud import WordCloud; import matplotlib.pyplot as plt
                            wc = WordCloud(width=800, height=400, background_color="white", colormap="Purples", max_words=60, contour_color="#7B2D8E").generate_from_frequencies(dict(tw))
                            fig_wc, ax = plt.subplots(figsize=(10,5)); ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
                            st.pyplot(fig_wc, use_container_width=True); plt.close(fig_wc)
                        except ImportError:
                            tw_df = pd.DataFrame(tw[:15], columns=["Word","Count"])
                            fig_fb = px.bar(tw_df, x="Count", y="Word", orientation="h", color="Count", color_continuous_scale=["#7B2D8E","#E85D04"])
                            style_plotly(fig_fb, height=350); st.plotly_chart(fig_fb, use_container_width=True)
                with wc2:
                    st.markdown("##### 📊 Top Keywords")
                    if tw:
                        tw_df = pd.DataFrame(tw[:20], columns=["Word","Freq"])
                        ff = px.bar(tw_df, x="Freq", y="Word", orientation="h", color="Freq", text="Freq", color_continuous_scale=["#2E86AB","#7B2D8E"])
                        ff.update_traces(textposition="outside"); style_plotly(ff, height=450)
                        ff.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                        st.plotly_chart(ff, use_container_width=True)

                st.markdown("---")

                # KEYWORD TREND + AI INSIGHT
                section_header("📈 Keyword Trends")
                top_kw = [w for w, _ in tw[:8]]
                tl_kw = filtered.dropna(subset=["Date"]).copy()
                if not tl_kw.empty and top_kw:
                    cutoff = pd.Timestamp.now() - pd.Timedelta(days=730)
                    tl_r = tl_kw[tl_kw["Date"]>=cutoff].copy()
                    if tl_r.empty: tl_r = tl_kw.copy()
                    tl_r["YM"] = tl_r["Date"].dt.to_period("M").astype(str)
                    kr = [{"Month":row["YM"],"Keyword":k} for _,row in tl_r.iterrows() for k in top_kw if k in row["Full_Text"]]
                    if kr:
                        ka = pd.DataFrame(kr).groupby(["Month","Keyword"]).size().reset_index(name="Mentions")

                        # AI Insight box
                        top_kw_name = ka.groupby("Keyword")["Mentions"].sum().idxmax()
                        top_kw_val = int(ka.groupby("Keyword")["Mentions"].sum().max())
                        n_months = ka["Month"].nunique()
                        avg_pm = round(ka.groupby("Month")["Mentions"].sum().mean(), 1)
                        months_sorted = sorted(ka["Month"].unique())
                        rising = []
                        if len(months_sorted) >= 2:
                            last2 = months_sorted[-2:]
                            for k in top_kw:
                                rec = ka[(ka["Keyword"]==k)&(ka["Month"].isin(last2))]["Mentions"].sum()
                                tot = ka[ka["Keyword"]==k]["Mentions"].sum()
                                if tot > 0 and rec/tot > 0.5: rising.append(k)
                        rising_t = f"<b>Rising:</b> {', '.join(rising[:4])}" if rising else "<b>No clear rising trend</b>"

                        st.markdown(f"""
                        <div style="background:linear-gradient(135deg, #F5F0FF 0%, #F0F8FF 100%);border:1px solid #D6CCE6;border-left:4px solid #7B2D8E;
                                    padding:14px 18px;border-radius:0 8px 8px 0;margin-bottom:16px;">
                            <div style="font-size:0.8rem;font-weight:700;color:#3C3489;margin-bottom:6px;">🤖 Trend Intelligence</div>
                            <div style="font-size:0.82rem;color:#444;line-height:1.6;">
                                Analyzed <b>{n_months} months</b> with avg <b>{avg_pm} mentions/month</b>.
                                Dominant keyword: <b>"{top_kw_name}"</b> ({top_kw_val} mentions). {rising_t}
                            </div>
                        </div>""", unsafe_allow_html=True)

                        fkt = px.area(ka, x="Month", y="Mentions", color="Keyword", color_discrete_sequence=palette, line_shape="spline")
                        fkt.update_traces(line=dict(width=2), opacity=0.7); style_plotly(fkt, height=350)
                        fkt.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=10)))
                        st.plotly_chart(fkt, use_container_width=True)

                st.markdown("---")

                # ARTICLES
                section_header("📰 Articles")
                so = st.selectbox("Sort", ["Most recent","Alphabetical"], index=0, key="aih_sort")
                disp = filtered.sort_values("Date", ascending=False) if so=="Most recent" else filtered.sort_values("Title")
                PS=12; tp=max(1,-(-len(disp)//PS)); pn=st.number_input("Page",1,tp,1,key="aih_page")
                for _, row in disp.iloc[(pn-1)*PS:pn*PS].iterrows():
                    t_html = " ".join(f'<span style="background:#F3E5F5;color:#7B2D8E;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">{t}</span>' for t in row["Topics"][:4])
                    u_html = " ".join(f'<span style="background:#E3F2FD;color:#1565C0;padding:2px 8px;border-radius:12px;font-size:0.72rem;margin-right:3px;">🎓 {u}</span>' for u in row["Universities"][:2])
                    ds = row["Date"].strftime("%d %b %Y") if pd.notna(row["Date"]) else ""
                    st.markdown(f"""<div style="background:#FFF;border-left:4px solid #7B2D8E;padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;"><a href="{row['URL']}" target="_blank" style="color:#0D2B45;font-weight:600;font-size:0.95rem;text-decoration:none;">{row['Title'][:120]}</a>
                        <span style="color:#95A5A6;font-size:0.75rem;white-space:nowrap;margin-left:1rem;">{ds}</span></div>
                        <div style="margin:0.3rem 0;">{t_html} {u_html}</div>
                        <div style="color:#7F8C8D;font-size:0.85rem;line-height:1.5;margin-top:0.3rem;">{row['Summary'][:200]}{'...' if len(row['Summary'])>200 else ''}</div></div>""", unsafe_allow_html=True)
                st.caption(f"Page {pn} of {tp} — {len(disp)} articles")

            # ═══════════ TAB 2: UNIVERSITIES ═══════════
            with tab_unis:
                section_header("🎓 Chinese Universities in AI Healthcare")

                uc = Counter(all_unis)
                if uc:
                    st.markdown("##### 📊 Most Active Universities")
                    uc_df = pd.DataFrame(uc.most_common(15), columns=["University","Mentions"])
                    fig_u = px.bar(uc_df, x="Mentions", y="University", orientation="h", color="Mentions", text="Mentions", color_continuous_scale=["#7B2D8E","#0D7C66"])
                    fig_u.update_traces(textposition="outside"); style_plotly(fig_u, height=400)
                    fig_u.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, coloraxis_showscale=False)
                    st.plotly_chart(fig_u, use_container_width=True)

                st.markdown("---")

                # CHINA MAP
                section_header("🗺️ University AI Healthcare Hubs")
                if uc:
                    mr = [{"University": u, "Articles": c, "lat": UNI_COORDS[u][0], "lon": UNI_COORDS[u][1]} for u, c in uc.items() if u in UNI_COORDS]
                    if mr:
                        mdf = pd.DataFrame(mr)
                        fig_m = px.scatter_geo(mdf, lat="lat", lon="lon", size="Articles", hover_name="University", color="Articles",
                                               color_continuous_scale=["#D4A017","#7B2D8E"], size_max=35, scope="asia")
                        fig_m.update_geos(center=dict(lat=33, lon=108), projection_scale=3, showland=True, landcolor="#F5F0E8",
                                           showocean=True, oceancolor="#EBF5FB", showcountries=True, countrycolor="#ccc")
                        style_plotly(fig_m, height=450); fig_m.update_layout(margin=dict(t=10,l=0,r=0,b=10), coloraxis_showscale=False)
                        st.plotly_chart(fig_m, use_container_width=True)

                st.markdown("---")

                # KEY PROJECTS
                section_header("🔬 Key Projects")
                projects = [
                    ("🤖 Agent Hospital", "Tsinghua AIR", "World's first AI virtual hospital. 42 AI doctors, 21 specialties, 300+ diseases. MedAgent-Zero self-evolution framework. 93.06% accuracy on MedQA.", "https://arxiv.org/abs/2405.02957"),
                    ("💊 MedGo", "Tongji University", "Medical LLM trained on 6,000 textbooks. Integrated at Shanghai East Hospital for clinical decision support.", ""),
                    ("🧬 CANDI Cohort", "USTC Hefei", "China Aging and Neurodegenerative Initiative. 500+ participants, ATN biomarker framework for Alzheimer's screening.", ""),
                    ("🔬 DeepSeek Medical", "DeepSeek AI", "Open-source LLM deployed in 260+ hospitals across 93.5% of provinces. Local deployment on hospital intranets.", ""),
                    ("🏥 Zijing AI Doctor", "Tsinghua spin-off", "42 AI doctors across 21 specialties. Commercial deployment via Zijing Zhikang startup.", ""),
                ]
                for icon_name, uni, desc, link in projects:
                    link_html = f' <a href="{link}" target="_blank" style="color:#7B2D8E;font-size:0.8rem;">[Paper]</a>' if link else ""
                    st.markdown(f"""<div style="background:#FFF;border-left:4px solid #7B2D8E;padding:1rem 1.2rem;margin:0.5rem 0;border-radius:0 6px 6px 0;">
                        <div style="font-weight:600;color:#0D2B45;font-size:0.95rem;">{icon_name}{link_html}</div>
                        <div style="font-size:0.8rem;color:#7B2D8E;margin:2px 0;">🎓 {uni}</div>
                        <div style="color:#666;font-size:0.85rem;margin-top:4px;">{desc}</div></div>""", unsafe_allow_html=True)

            # ═══════════ TAB 3: ARCHITECTURE ═══════════
            with tab_arch:
                section_header("🏗️ AI Agent Hospital Architecture")
                st.markdown("""
                <div style="background:linear-gradient(135deg, #F5F0FF 0%, #F0F8FF 100%);border:1px solid #D6CCE6;border-left:4px solid #7B2D8E;padding:16px 20px;border-radius:0 10px 10px 0;margin-bottom:20px;">
                    <div style="font-size:1rem;font-weight:700;color:#3C3489;margin-bottom:8px;">🤖 Agent Hospital — World's First AI Virtual Hospital</div>
                    <div style="font-size:0.88rem;color:#444;line-height:1.7;">
                        Developed by <strong>Tsinghua University AIR</strong>, led by <strong>Prof. Liu Yang</strong>.<br>
                        Paper: <a href="https://arxiv.org/abs/2405.02957" target="_blank" style="color:#7B2D8E;">arXiv:2405.02957</a>
                    </div>
                </div>""", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### MedAgent-Zero Framework")
                    st.markdown("- **Self-evolving** AI doctors learning from cases\n- No manual labeling needed\n- 10,000 virtual patients → **93.06% accuracy**\n- Time-compression engine for full patient journey")
                with c2:
                    st.markdown("##### Scale & Deployment")
                    st.markdown("- **42 AI doctors**, **21 specialties**, **300+ diseases**\n- Chang Gung Hospital: **1,500 beds**, 10k outpatients/day\n- International: Middle East, SE Asia, Western countries\n- DeepSeek: **260+ hospitals**, 93.5% provinces")

                st.markdown("---")
                st.markdown("##### Key Milestones")
                for date, event in [("May 2024","Paper on arXiv"),("Nov 2024","Zijing AI Doctor launched"),("Q1 2025","Tairex pilot"),("Apr 2025","Official inauguration"),("May 2025","Chang Gung Phase II (+500 beds)")]:
                    st.markdown(f'<div style="display:flex;gap:12px;margin:6px 0;"><span style="background:#7B2D8E;color:#fff;padding:2px 10px;border-radius:12px;font-size:0.72rem;font-weight:600;white-space:nowrap;">{date}</span><span style="font-size:0.88rem;color:#444;">{event}</span></div>', unsafe_allow_html=True)

            # ═══════════ TAB 4: NOTES ═══════════
            with tab_notes:
                section_header("📝 Notes & Research")
                titles = df_ai["Title"].tolist()
                sel = st.selectbox("📄 Article", titles, index=0, key="aih_sel")
                sr = df_ai[df_ai["Title"]==sel].iloc[0]; did = int(sr["DocID"])
                ex = session.execute(sa_text("SELECT note_text,ai_keywords,university,project FROM ai_hospital_notes WHERE document_id=:d ORDER BY updated_at DESC LIMIT 1"), {"d":did}).fetchone()
                nc1,nc2 = st.columns([3,1])
                with nc1:
                    nt = st.text_area("✏️ Notes", value=ex[0] if ex else "", height=160, key="aih_note")
                    n_uni = st.text_input("🎓 University/Institution", value=ex[2] if ex and ex[2] else "", key="aih_uni")
                    n_proj = st.text_input("🔬 Project name", value=ex[3] if ex and ex[3] else "", key="aih_proj")
                with nc2:
                    st.markdown("##### 🤖 AI Keywords")
                    if ex and ex[1]:
                        for k in ex[1].split(", "): st.markdown(f'<span style="background:#F3E5F5;color:#7B2D8E;padding:2px 6px;border-radius:10px;font-size:0.75rem;">{k}</span>', unsafe_allow_html=True)
                if st.button("💾 Save & Analyze", type="primary", key="aih_save"):
                    combined = (nt+" "+sr["Title"]+" "+sr["Summary"]).lower()
                    nw = [w for w in re_ai.findall(r"[a-z]{4,}", combined) if w not in stop_w]
                    ak = ", ".join([w for w,_ in Counter(nw).most_common(10)])
                    if ex: session.execute(sa_text("UPDATE ai_hospital_notes SET note_text=:n,ai_keywords=:k,university=:u,project=:p,updated_at=NOW() WHERE document_id=:d"), {"n":nt,"k":ak,"u":n_uni,"p":n_proj,"d":did})
                    else: session.execute(sa_text("INSERT INTO ai_hospital_notes (document_id,note_text,ai_keywords,university,project) VALUES (:d,:n,:k,:u,:p)"), {"d":did,"n":nt,"k":ak,"u":n_uni,"p":n_proj})
                    session.commit(); st.success("✅ Saved!"); st.rerun()

                st.markdown("---")
                an = session.execute(sa_text("SELECT n.note_text,n.ai_keywords,n.university,n.project,n.updated_at,d.title FROM ai_hospital_notes n JOIN documents d ON n.document_id=d.document_id ORDER BY n.updated_at DESC")).fetchall()
                if an:
                    for n in an:
                        with st.expander(f"📄 {n[5][:70]}"):
                            st.markdown(n[0])
                            if n[2]: st.markdown(f"**University:** 🎓 {n[2]}")
                            if n[3]: st.markdown(f"**Project:** 🔬 {n[3]}")
                            if n[1]: st.markdown(f"**Keywords:** {n[1]}")

            # ═══════════ TAB 5: LINKS ═══════════
            with tab_links:
                section_header("🔗 Links & Papers")
                cats = ["arXiv Paper","Research Article","University Website","News","Clinical Trial","GitHub Repo","Video/Presentation","Other"]
                with st.form("aih_add", clear_on_submit=True):
                    lu = st.text_input("🔗 URL"); lt = st.text_input("📄 Title")
                    lc = st.selectbox("📁 Category", cats); ld = st.text_area("📝 Notes", height=80)
                    if st.form_submit_button("➕ Add", type="primary") and lu.strip():
                        lk = ", ".join([w for w,_ in Counter([w for w in re_ai.findall(r"[a-z]{4,}", (lt+" "+ld).lower()) if w not in stop_w]).most_common(8)])
                        session.execute(sa_text("INSERT INTO ai_hospital_links (url,title,description,link_category,ai_keywords) VALUES (:u,:t,:d,:c,:k)"), {"u":lu,"t":lt,"d":ld,"c":lc,"k":lk})
                        session.commit(); st.success("✅ Added!"); st.rerun()

                st.markdown("---")
                links = session.execute(sa_text("SELECT link_id,url,title,description,link_category,ai_keywords,created_at FROM ai_hospital_links ORDER BY created_at DESC")).fetchall()
                if links:
                    for lk in links:
                        cc = {"arXiv Paper":"#7B2D8E","Research Article":"#0D7C66","University Website":"#1E3A5F","News":"#2E86AB","Clinical Trial":"#C73E1D","GitHub Repo":"#444","Video/Presentation":"#D4A017"}.get(lk[4],"#95A5A6")
                        kp = " ".join(f'<span style="background:#F5F5F5;color:#444;padding:2px 6px;border-radius:10px;font-size:0.72rem;">{k.strip()}</span>' for k in (lk[5] or "").split(",")[:6] if k.strip())
                        st.markdown(f'<div style="background:#FFF;border-left:4px solid {cc};padding:1rem 1.2rem;margin:0.4rem 0;border-radius:0 6px 6px 0;"><div style="display:flex;justify-content:space-between;"><a href="{lk[1]}" target="_blank" style="color:#0D2B45;font-weight:600;text-decoration:none;">{lk[2] or lk[1][:80]}</a><span style="background:{cc};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.72rem;">{lk[4]}</span></div><div style="margin:0.3rem 0;">{kp}</div><div style="color:#7F8C8D;font-size:0.85rem;">{(lk[3] or "")[:200]}</div></div>', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"aih_del_{lk[0]}"):
                            session.execute(sa_text("DELETE FROM ai_hospital_links WHERE link_id=:id"), {"id":lk[0]}); session.commit(); st.rerun()
                else:
                    st.info("No links yet. Add arXiv papers, university websites, and resources!")

        else:
            st.info("No AI Agent Hospital articles yet. Run the collector:")
            st.code('python -c "from collectors.ai_agent_hospital_collector import run; run()"')

    finally:
        session.close()

    page_footer()
