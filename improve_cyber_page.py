"""Run this to improve the Cyber Attack Radar page in app.py"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# Replace the Timeline section with daily timeline + country extraction
old_timeline = '''            # ── Timeline ──
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
                st.plotly_chart(fig, use_container_width=True)'''

new_timeline = '''            # ── Daily Timeline ──
            section_header("Daily Threat Timeline")
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df_timeline = df.dropna(subset=["Date"])
            if not df_timeline.empty:
                # Daily count
                df_daily = (
                    df_timeline.groupby([pd.Grouper(key="Date", freq="D"), "Threat Type"])
                    .size().reset_index(name="Count")
                )
                fig_daily = px.bar(df_daily, x="Date", y="Count", color="Threat Type",
                                   color_discrete_map=color_map, barmode="stack")
                style_plotly(fig_daily, height=380)
                fig_daily.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25,
                                x=0.5, xanchor="center"),
                    hovermode="x unified",
                    xaxis_title="Date",
                    yaxis_title="Alerts per Day",
                )
                st.plotly_chart(fig_daily, use_container_width=True)

                # Cumulative trend
                df_cumul = df_timeline.groupby(pd.Grouper(key="Date", freq="D")).size().reset_index(name="Count")
                df_cumul["Cumulative"] = df_cumul["Count"].cumsum()
                fig_cumul = px.area(df_cumul, x="Date", y="Cumulative",
                                    color_discrete_sequence=["#D35C5C"])
                style_plotly(fig_cumul, height=280)
                fig_cumul.update_layout(xaxis_title="", yaxis_title="Cumulative Alerts")
                st.plotly_chart(fig_cumul, use_container_width=True)

            # ── Country Analysis ──
            section_header("Alerts by Target Country")
            # Extract countries from titles using keyword matching
            COUNTRY_KEYWORDS = {
                "USA": ["united states", "u.s.", "us hospital", "american", "hhs", "fbi", "cisa", "hipaa"],
                "UK": ["united kingdom", "u.k.", "nhs", "british"],
                "Germany": ["germany", "german", "deutschland"],
                "France": ["france", "french"],
                "Italy": ["italy", "italian"],
                "Israel": ["israel", "israeli"],
                "Canada": ["canada", "canadian"],
                "Australia": ["australia", "australian"],
                "India": ["india", "indian"],
                "China": ["china", "chinese"],
                "Russia": ["russia", "russian"],
                "North Korea": ["north korea", "dprk", "lazarus"],
                "Iran": ["iran", "iranian"],
            }

            def extract_countries(title, summary, default_country):
                text = (title + " " + (summary or "")).lower()
                found = []
                for country, keywords in COUNTRY_KEYWORDS.items():
                    if any(kw in text for kw in keywords):
                        found.append(country)
                if not found and default_country:
                    found = [default_country]
                return found if found else ["Unknown"]

            country_rows = []
            for _, row in df.iterrows():
                countries = extract_countries(row["Title"], row.get("Summary", ""), row["Country"])
                for country in countries:
                    country_rows.append({"Country": country, "Threat Type": row["Threat Type"]})

            df_countries = pd.DataFrame(country_rows)
            if not df_countries.empty:
                col_map_left, col_map_right = st.columns([3, 2])

                with col_map_left:
                    country_agg = df_countries["Country"].value_counts().reset_index()
                    country_agg.columns = ["Country", "Alerts"]
                    fig_geo = px.choropleth(
                        country_agg,
                        locations="Country",
                        locationmode="country names",
                        color="Alerts",
                        color_continuous_scale=["#FAFAF8", "#E8A838", "#D35C5C", "#0D2B45"],
                    )
                    style_plotly(fig_geo, height=400)
                    fig_geo.update_layout(geo=dict(bgcolor="rgba(0,0,0,0)", lakecolor="#FAFAF8",
                                                    showframe=False, projection_type="natural earth"))
                    st.plotly_chart(fig_geo, use_container_width=True)

                with col_map_right:
                    # Country x Threat Type breakdown
                    ct_pivot = pd.crosstab(df_countries["Country"], df_countries["Threat Type"])
                    fig_heatmap = px.imshow(
                        ct_pivot,
                        labels=dict(x="Threat Type", y="Country", color="Count"),
                        color_continuous_scale=["#FAFAF8", "#E8A838", "#D35C5C"],
                        aspect="auto",
                    )
                    style_plotly(fig_heatmap, height=400)
                    st.plotly_chart(fig_heatmap, use_container_width=True)'''

c = c.replace(old_timeline, new_timeline)

with open(path, "w") as f:
    f.write(c)

print("Done - Cyber page improved with daily timeline + country analysis")
