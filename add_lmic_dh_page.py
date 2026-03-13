"""Run this to add LMIC Digital Mental Health page to app.py"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# 1. Add page to sidebar radio
old_radio = '            "\u26a0\ufe0f Cyber Attack Radar",'
new_radio = '            "\u26a0\ufe0f Cyber Attack Radar",\n            "\U0001f30d LMIC Digital MH",'
c = c.replace(old_radio, new_radio)

# 2. Add PAGE 10 before the Cyber Attack Radar page footer (at end of file)
page10 = '''

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# PAGE 10: LMIC DIGITAL MENTAL HEALTH
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
elif page == "\U0001f30d LMIC Digital MH":
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
                        <small>{row['Country']} \u00b7 {row['Region']} \u00b7 {row['Type']} \u00b7
                        <a href="{row['URL']}" target="_blank">View \u2192</a></small><br>
                        <small style="color:#7F8C8D;">{row['Summary']}</small>
                    </div>
                    """, unsafe_allow_html=True)

        else:
            st.info("No LMIC digital mental health data yet. Run the collector:")
            st.code('python -c "from collectors.lmic_dh_collector import run; run()"')

    finally:
        session.close()

    page_footer()
'''

# Append at the end of file
c += page10

with open(path, "w") as f:
    f.write(c)

print("Done - LMIC Digital Mental Health page added")
