"""Run this to add attack arc map to the Cyber Attack Radar page"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# Find the Sankey section header and add the arc map right after it
old_section = '''            section_header("Attack Flow Intelligence — Origin to Target")
            st.caption("Source: AbuseIPDB blacklist · Top malicious IPs aggregated by country of origin")'''

new_section = '''            section_header("Attack Flow Intelligence — Origin to Target")
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
            arc_data = arc_data[arc_data["attack_count"] > 0].nlargest(60, "attack_count")

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
                    width = max(0.5, (attacks / max_attacks) * 4)
                    opacity = max(0.15, min(0.7, attacks / max_attacks))

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
                st.caption("🔴 Red = attack origins · 🔷 Blue = targets · Line thickness = attack volume")'''

c = c.replace(old_section, new_section)

with open(path, "w") as f:
    f.write(c)

print("Done - Arc attack map added to Cyber page")
