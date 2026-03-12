"""
Streamlit Dashboard - Geopolitical Health Intelligence
8 pagine: Overview, Regulatory, Bundestag/G-BA, Science, Trends, Neuro, LMIC, Telecom
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


# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem; font-weight: 700; color: #1B4F72;
        margin-bottom: 0.5rem; padding-bottom: 0.5rem;
        border-bottom: 3px solid #2E86C1;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1B4F72, #2E86C1);
        color: white; padding: 1.2rem; border-radius: 10px;
        text-align: center; margin-bottom: 0.5rem;
    }
    .kpi-value { font-size: 2.2rem; font-weight: 700; }
    .kpi-label { font-size: 0.85rem; opacity: 0.85; }
    .alert-card {
        background: #FEF9E7; border-left: 4px solid #F39C12;
        padding: 0.8rem; margin: 0.3rem 0; border-radius: 0 6px 6px 0;
    }
    .alert-card-high {
        background: #FDEDEC; border-left: 4px solid #E74C3C;
    }
    div[data-testid="stMetric"] {
        background: #EBF5FB; padding: 10px; border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/globe.png", width=60)
    st.title("🌍 Health Intel")

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
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Filtri globali
    st.subheader("🔎 Filtri")
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

    st.divider()
    st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    st.caption("Pipeline: Python + PostgreSQL + Streamlit")


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


def kpi_card(label, value, delta=None):
    """Crea KPI card HTML."""
    delta_html = ""
    if delta is not None:
        color = "#27AE60" if delta >= 0 else "#E74C3C"
        arrow = "↑" if delta >= 0 else "↓"
        delta_html = f'<div style="color: {color}; font-size: 0.9rem;">{arrow} {abs(delta)}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def alert_card(title, source, score, url="", high=False):
    """Crea alert card HTML."""
    css_class = "alert-card-high" if high else "alert-card"
    link = f'<a href="{url}" target="_blank">→ View</a>' if url else ""
    st.markdown(f"""
    <div class="{css_class}">
        <strong>{title[:80]}{'...' if len(title) > 80 else ''}</strong><br>
        <small>{source} | Score: {score:.1f} {link}</small>
    </div>
    """, unsafe_allow_html=True)


# ── PAGE 1: EXECUTIVE OVERVIEW ────────────────────────────
if page == "📊 Executive Overview":
    st.markdown('<div class="main-header">📊 Executive Overview</div>', unsafe_allow_html=True)

    session = get_session_cached()

    try:
        # KPI
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
        with col3: kpi_card("Total Signals", f"{total_signals:,}")
        with col4: kpi_card("High Priority", f"{high_signals}", delta=None)

        st.divider()

        # Top Strategic Alerts
        col_left, col_right = st.columns([3, 2])

        with col_left:
            st.subheader("🔴 Top Strategic Alerts")
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
                st.info("Nessun segnale ad alto impatto. Esegui la pipeline per raccogliere dati.")

        with col_right:
            st.subheader("📊 Documenti per Fonte")
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
                             color_discrete_sequence=px.colors.sequential.Blues_r)
                fig.update_layout(height=400, margin=dict(t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

            # Documenti per paese
            st.subheader("🌍 Top Countries")
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
                             color="Count", color_continuous_scale="Blues")
                fig.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        st.info("Assicurati che il database sia inizializzato. Esegui: `python main.py --init-db`")
    finally:
        session.close()


# ── PAGE 2: REGULATORY RADAR ─────────────────────────────
elif page == "⚖️ Regulatory Radar":
    st.markdown('<div class="main-header">⚖️ Regulatory Radar</div>', unsafe_allow_html=True)

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
                         column_config={"URL": st.column_config.LinkColumn("Link")})

            # Timeline
            if not df.empty and "Date" in df.columns:
                df_timeline = df.dropna(subset=["Date"])
                if not df_timeline.empty:
                    fig = px.scatter(df_timeline, x="Date", y="Country", color="Source",
                                    hover_data=["Title"], size_max=10)
                    fig.update_layout(height=400, title="Regulatory Timeline")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nessun documento regolatorio trovato. Esegui la pipeline.")
    finally:
        session.close()


# ── PAGE 3: BUNDESTAG & G-BA ─────────────────────────────
elif page == "🏛️ Bundestag & G-BA":
    st.markdown('<div class="main-header">🏛️ Bundestag & G-BA Monitor</div>', unsafe_allow_html=True)

    session = get_session_cached()
    try:
        tab1, tab2, tab3 = st.tabs(["🏛️ Bundestag", "⚕️ G-BA Decisions", "📱 DiGA Directory"])

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
                with col1:
                    st.metric("Total Bundestag Documents", len(bt_items))
                with col2:
                    high_rel = len([b for b, d in bt_items if b.health_relevance >= 7.0])
                    st.metric("High Health Relevance", high_rel)

                df_bt = pd.DataFrame([{
                    "Date": d.publish_date,
                    "Title": d.title[:70],
                    "Type": b.drucksache_type,
                    "Institution": b.institution,
                    "Health Score": f"{b.health_relevance:.1f}",
                    "Author": (b.urheber or "")[:50],
                } for b, d in bt_items])
                st.dataframe(df_bt, use_container_width=True, height=400)

                # Chart per tipo
                if not df_bt.empty:
                    fig = px.histogram(df_bt, x="Type", color="Institution",
                                       title="Documents by Type")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nessun dato Bundestag. Esegui la pipeline.")

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
                with col1: st.metric("G-BA Decisions", len(gba_items))
                with col2: st.metric("Digital Health Related", dh_count)

                df_gba = pd.DataFrame([{
                    "Date": d.publish_date,
                    "Title": d.title[:70],
                    "Type": g.decision_type,
                    "Subcommittee": g.subcommittee,
                    "Digital Health": "✅" if g.digital_health_flag else "",
                    "Reimbursement Impact": g.reimbursement_impact,
                } for g, d in gba_items])
                st.dataframe(df_gba, use_container_width=True, height=400)
            else:
                st.info("Nessun dato G-BA. Esegui la pipeline.")

        with tab3:
            diga_apps = session.query(DIGAApp).order_by(desc(DIGAApp.listing_date)).all()

            if diga_apps:
                perm = len([a for a in diga_apps if a.listing_status == "permanent"])
                prov = len([a for a in diga_apps if a.listing_status == "provisional"])
                neuro = len([a for a in diga_apps if a.neuro_relevant])

                col1, col2, col3 = st.columns(3)
                with col1: st.metric("Permanent", perm)
                with col2: st.metric("Provisional", prov)
                with col3: st.metric("Neuro-relevant", neuro)

                df_diga = pd.DataFrame([{
                    "Name": a.app_name,
                    "Manufacturer": a.manufacturer,
                    "Indication": (a.indication or "")[:60],
                    "Status": a.listing_status,
                    "Risk Class": a.risk_class,
                    "Neuro": "🧠" if a.neuro_relevant else "",
                } for a in diga_apps])
                st.dataframe(df_diga, use_container_width=True, height=400)
            else:
                st.info("Nessun dato DiGA. Esegui la pipeline con il DiGA collector.")

    finally:
        session.close()


# ── PAGE 4: SCIENCE & TRIALS ─────────────────────────────
elif page == "🔬 Science & Trials":
    st.markdown('<div class="main-header">🔬 Science & Clinical Trials</div>', unsafe_allow_html=True)

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
            with col1: st.metric("Papers", len(papers))
            with col2: st.metric("Clinical Trials", len(trials))

            # Tabella documenti scientifici
            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:80],
                "Type": d.document_type,
                "Country": d.country,
                "Source": s.source_name,
            } for d, s in sci_docs])

            st.dataframe(df, use_container_width=True, height=500)

            # Trend temporale
            if not df.empty:
                df["Date"] = pd.to_datetime(df["Date"])
                df_trend = df.dropna(subset=["Date"]).groupby(
                    [pd.Grouper(key="Date", freq="W"), "Type"]
                ).size().reset_index(name="Count")
                if not df_trend.empty:
                    fig = px.line(df_trend, x="Date", y="Count", color="Type",
                                 title="Publication Trend (Weekly)")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nessun dato scientifico. Esegui la pipeline.")
    finally:
        session.close()


# ── PAGE 5: MARKET TRENDS ────────────────────────────────
elif page == "📈 Market Trends":
    st.markdown('<div class="main-header">📈 Market & Trend Signals</div>', unsafe_allow_html=True)

    # Country labels for display
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

    # Keyword-to-cluster mapping (derived in Python, not in DB)
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
            st.markdown("---")
            col_f1, col_f2, col_f3 = st.columns(3)

            available_countries = sorted(df["Country"].dropna().unique())
            available_clusters = sorted(df["Cluster"].dropna().unique())
            available_keywords = sorted(df["Keyword"].dropna().unique())

            # Smart defaults: pick top markets if available
            default_countries = [c for c in ["United States", "Germany", "United Kingdom",
                                              "France", "Italy", "Israel"]
                                 if c in available_countries]
            if not default_countries:
                default_countries = available_countries[:6]

            with col_f1:
                selected_countries = st.multiselect(
                    "🌍 Countries", available_countries,
                    default=default_countries,
                )
            with col_f2:
                selected_clusters = st.multiselect(
                    "📦 Cluster", available_clusters,
                    default=available_clusters,
                )
            with col_f3:
                selected_keywords = st.multiselect(
                    "🔑 Keywords", available_keywords,
                    default=[],
                    help="Leave empty = all keywords in selected clusters",
                )

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
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                kpi_card("Countries", f"{ts_data['Geo'].nunique()}")
            with kpi2:
                kpi_card("Keywords", f"{ts_data['Keyword'].nunique()}")
            with kpi3:
                if not ts_data.empty:
                    latest_date = ts_data["Date"].max()
                    avg_score = ts_data[ts_data["Date"] == latest_date]["Interest"].mean()
                    kpi_card("Avg Interest (latest)", f"{avg_score:.0f}")
                else:
                    kpi_card("Avg Interest", "N/A")
            with kpi4:
                kpi_card("Rising Topics", f"{len(rising_data)}")

            st.divider()

            if not ts_data.empty:
                # ── Chart 1: Interest over time by Country ──
                st.subheader("📊 Interest Over Time by Country")
                agg_country = (
                    ts_data.groupby(["Date", "Country"])["Interest"]
                    .mean().reset_index()
                )
                fig1 = px.line(
                    agg_country, x="Date", y="Interest", color="Country",
                    labels={"Interest": "Interest Score (avg)", "Date": "Date"},
                    template="plotly_white",
                )
                fig1.update_layout(
                    height=420,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig1, use_container_width=True)

                # ── Chart 2: Interest over time by Keyword ──
                st.subheader("🔑 Interest Over Time by Keyword")
                agg_kw = (
                    ts_data.groupby(["Date", "Keyword"])["Interest"]
                    .mean().reset_index()
                )
                fig2 = px.line(
                    agg_kw, x="Date", y="Interest", color="Keyword",
                    labels={"Interest": "Interest Score (avg)", "Date": "Date"},
                    template="plotly_white",
                )
                fig2.update_layout(
                    height=420,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.4,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                )
                st.plotly_chart(fig2, use_container_width=True)

                # ── Chart 3: Heatmap Country × Keyword ──
                st.subheader("🗺️ Heatmap — Latest Interest by Country × Keyword")
                latest = ts_data[ts_data["Date"] == ts_data["Date"].max()]
                if not latest.empty:
                    pivot = latest.pivot_table(
                        index="Country", columns="Keyword",
                        values="Interest", aggfunc="mean",
                    )
                    fig3 = px.imshow(
                        pivot,
                        labels=dict(x="Keyword", y="Country", color="Interest"),
                        color_continuous_scale="YlOrRd",
                        aspect="auto",
                    )
                    fig3.update_layout(height=max(400, len(pivot) * 22))
                    st.plotly_chart(fig3, use_container_width=True)

            # ── Rising Topics ──
            st.subheader("🔥 Rising Topics")
            if not rising_data.empty:
                rising_display = (
                    rising_data[["Country", "Keyword", "Related Topic", "Date"]]
                    .sort_values("Date", ascending=False)
                    .drop_duplicates(subset=["Country", "Keyword", "Related Topic"])
                    .head(50)
                )
                st.dataframe(rising_display, use_container_width=True, hide_index=True)
            else:
                st.info("Nessun topic in crescita anomala.")

            # ── Raw data ──
            with st.expander("📋 Raw Data Table"):
                st.dataframe(
                    filtered.sort_values("Date", ascending=False).head(500),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info("Nessun dato Google Trends. Esegui il trends collector.")
    finally:
        session.close()


# ── PAGE 6: NEURODEGENERATIVE FOCUS ──────────────────────
elif page == "🧠 Neurodegenerative Focus":
    st.markdown('<div class="main-header">🧠 Neurodegenerative Focus</div>', unsafe_allow_html=True)

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
            st.metric("Neurodegenerative Documents", len(neuro_docs))

            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title[:70],
                "Disease": kw.disease_area or kw.cluster,
                "Type": d.document_type,
                "Score": f"{s.strategic_score:.1f}",
                "Country": d.country,
                "Source": src.source_name,
            } for d, src, s, kw in neuro_docs])

            # Chart per area patologica
            disease_counts = df["Disease"].value_counts().reset_index()
            disease_counts.columns = ["Disease Area", "Count"]
            fig = px.bar(disease_counts, x="Disease Area", y="Count",
                         color="Count", color_continuous_scale="Reds",
                         title="Documents by Disease Area")
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("Nessun dato neurodegenerativo. Esegui la pipeline.")
    finally:
        session.close()


# ── PAGE 7: LMIC OPPORTUNITY ─────────────────────────────
elif page == "🌍 LMIC Opportunity":
    st.markdown('<div class="main-header">🌍 LMIC Opportunity Map</div>', unsafe_allow_html=True)

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

            # Scatter plot: need vs connectivity
            fig = px.scatter(
                df, x="Internet Users %", y="Neuro Burden",
                size="Opportunity Score", color="Opportunity Score",
                hover_name="Country", color_continuous_scale="RdYlGn",
                title="Health Need vs Digital Connectivity"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("Nessun dato country metrics. Carica dati GSMA/ITU/World Bank.")
    finally:
        session.close()


# ── PAGE 8: TELECOM READINESS ─────────────────────────────
elif page == "📡 Telecom Readiness":
    st.markdown('<div class="main-header">📡 Telecom & Infrastructure Readiness</div>', unsafe_allow_html=True)

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

            fig = px.choropleth(
                df, locations="Country", locationmode="country names",
                color="Mobile Score", color_continuous_scale="Blues",
                title="Global Mobile Connectivity Score"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("Nessun dato telecom. Carica dati GSMA/ITU.")
    finally:
        session.close()
