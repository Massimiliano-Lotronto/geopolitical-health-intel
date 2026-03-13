"""Run this to add attack flow visualization to the Cyber Attack Radar page"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# Add sqlalchemy text import if not present (needed for raw SQL)
if "from sqlalchemy import func, and_, desc, text" not in c:
    c = c.replace(
        "from sqlalchemy import func, and_, desc",
        "from sqlalchemy import func, and_, desc, text"
    )

# Find the Cyber page footer and add the flow section before it
# We insert after the "All Cyber Alerts" expander and before page_footer()

old_end = '''        else:
            st.info("No cyber threat data yet. Run the cyber collector:")
            st.code("python -c \\"from collectors.cyber_collector import run; run()\\"")
    finally:
        session.close()

    page_footer()'''

new_end = '''        else:
            st.info("No cyber threat data yet. Run the cyber collector:")
            st.code("python -c \\"from collectors.cyber_collector import run; run()\\"")
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
            st.code("export ABUSEIPDB_API_KEY=\\"your-key\\"\\npython -c \\"from collectors.abuseipdb_collector import run; run()\\"")

    except Exception as e:
        st.warning(f"Attack flow section error: {e}")
    finally:
        session2.close()

    page_footer()'''

c = c.replace(old_end, new_end)

with open(path, "w") as f:
    f.write(c)

print("Done - Attack flow visualization added to Cyber page")
