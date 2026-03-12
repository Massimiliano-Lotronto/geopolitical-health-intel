"""Run this to add the Cyber Attack Radar page to app.py"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    content = f.read()

# 1. Add page to sidebar radio list
old_radio = '            "📡 Telecom Readiness",'
new_radio = '            "📡 Telecom Readiness",\n            "⚠️ Cyber Attack Radar",'
content = content.replace(old_radio, new_radio)

# 2. Add PAGE 9 at the end (before the last line or at the end of file)
page9 = '''

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
                "Summary": (d.abstract or "")[:120],
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
            st.code("python -c \\"from collectors.cyber_collector import run; run()\\"")
    finally:
        session.close()

    page_footer()
'''

# Find the last page_footer() call and append after it
last_footer = content.rfind("    page_footer()")
if last_footer > 0:
    # Find the end of that line
    end_of_line = content.index("\n", last_footer)
    content = content[:end_of_line + 1] + page9
else:
    content += page9

with open(path, "w") as f:
    f.write(content)

print("Done - Cyber Attack Radar page added to app.py")
