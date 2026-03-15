"""Run this to add Chatham House page to the dashboard"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# 1. Add to sidebar
old_radio = '            "\U0001f30d LMIC Digital MH",'
new_radio = '            "\U0001f30d LMIC Digital MH",\n            "\U0001f3db\ufe0f Chatham House",'
c = c.replace(old_radio, new_radio)

# 2. Add page at end of file
page11 = '''

# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# PAGE 11: CHATHAM HOUSE
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
elif page == "\U0001f3db\ufe0f Chatham House":
    page_header("Chatham House", "Digital health & healthcare policy analysis from the Royal Institute of International Affairs")

    session = get_session_cached()
    try:
        ch_docs = (
            session.query(Document, Source)
            .join(Source, Document.source_id == Source.source_id)
            .filter(Document.document_type == "chatham_house")
            .order_by(desc(Document.publish_date))
            .limit(200)
            .all()
        )

        if ch_docs:
            df = pd.DataFrame([{
                "Date": d.publish_date,
                "Title": d.title,
                "Source": s.source_name,
                "URL": d.url or "",
                "Summary": (d.summary or ""),
            } for d, s in ch_docs])

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            # Extract tags from summaries
            import re as re_ch
            def extract_tags(summary):
                match = re_ch.match(r"\\[Tags:\\s*(.+?)\\]", summary)
                if match:
                    return [t.strip() for t in match.group(1).split(",")]
                return []

            def clean_summary(summary):
                return re_ch.sub(r"\\[Tags:\\s*(.+?)\\]\\s*", "", summary)

            df["Tags"] = df["Summary"].apply(extract_tags)
            df["Clean Summary"] = df["Summary"].apply(clean_summary)

            # KPIs
            col1, col2, col3 = st.columns(3)
            with col1:
                kpi_card("Total Articles", str(len(df)))
            with col2:
                this_month = len(df[df["Date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)])
                kpi_card("This Month", str(this_month))
            with col3:
                all_tags = [t for tags in df["Tags"] for t in tags]
                kpi_card("Topics Covered", str(len(set(all_tags))))

            st.markdown("<br>", unsafe_allow_html=True)

            # Timeline
            section_header("Publication Timeline")
            df_timeline = df.dropna(subset=["Date"])
            if not df_timeline.empty:
                df_monthly = (
                    df_timeline.groupby(pd.Grouper(key="Date", freq="M"))
                    .size().reset_index(name="Count")
                )
                fig = px.bar(df_monthly, x="Date", y="Count",
                             color_discrete_sequence=["#0D2B45"])
                style_plotly(fig, height=300)
                fig.update_layout(xaxis_title="", yaxis_title="Articles")
                st.plotly_chart(fig, use_container_width=True)

            # Topic analysis
            if all_tags:
                section_header("Top Topics")
                from collections import Counter
                tag_counts = Counter(all_tags).most_common(15)
                df_tags = pd.DataFrame(tag_counts, columns=["Topic", "Count"])
                fig_tags = px.bar(df_tags, x="Count", y="Topic", orientation="h",
                                   color="Count",
                                   color_continuous_scale=["#1A6B8A", "#0D2B45"])
                style_plotly(fig_tags, height=400)
                fig_tags.update_layout(showlegend=False)
                st.plotly_chart(fig_tags, use_container_width=True)

            # Articles list
            section_header("Latest Articles")
            for _, row in df.head(30).iterrows():
                tags_html = ""
                if row["Tags"]:
                    tags_html = " ".join(
                        f'<span style="background:#EBF5FB; color:#1A6B8A; padding:2px 8px; '
                        f'border-radius:12px; font-size:0.72rem; margin-right:3px;">{t}</span>'
                        for t in row["Tags"][:5]
                    )

                date_str = row["Date"].strftime("%d %b %Y") if pd.notna(row["Date"]) else ""

                st.markdown(f"""
                <div style="background:#FFFFFF; border:1px solid #E8E4DF;
                            padding:1rem 1.2rem; margin:0.4rem 0; border-radius:6px;
                            transition: box-shadow 0.2s;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <a href="{row['URL']}" target="_blank"
                           style="color:#0D2B45; font-weight:600; font-size:0.95rem;
                                  text-decoration:none;">
                            {row['Title'][:120]}
                        </a>
                        <span style="color:#95A5A6; font-size:0.75rem; white-space:nowrap;
                                     margin-left:1rem;">{date_str}</span>
                    </div>
                    <div style="margin:0.3rem 0;">{tags_html}</div>
                    <div style="color:#7F8C8D; font-size:0.85rem; line-height:1.5;
                                margin-top:0.3rem;">
                        {row['Clean Summary'][:200]}{'...' if len(row['Clean Summary']) > 200 else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Full table
            with st.expander("All Articles Table"):
                st.dataframe(
                    df[["Date", "Title", "Source"]].sort_values("Date", ascending=False),
                    use_container_width=True, hide_index=True,
                )
        else:
            st.info("No Chatham House articles yet. Run the collector:")
            st.code('python -c "from collectors.chatham_collector import run; run()"')

    finally:
        session.close()

    page_footer()
'''

c += page11

with open(path, "w") as f:
    f.write(c)

print("Done - Chatham House page added")
