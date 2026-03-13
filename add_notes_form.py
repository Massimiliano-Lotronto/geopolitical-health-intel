"""Run this to add note-taking form and keyword analysis to LMIC Digital MH page"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# Find the end of the LMIC DH page (before page_footer) and add the form + analysis
# We look for the last page_footer() in the file
old_end = '''            st.info("No LMIC digital mental health data yet. Run the collector:")
            st.code('python -c "from collectors.lmic_dh_collector import run; run()"')

    finally:
        session.close()

    page_footer()'''

new_end = '''            st.info("No LMIC digital mental health data yet. Run the collector:")
            st.code('python -c "from collectors.lmic_dh_collector import run; run()"')

    finally:
        session.close()

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

    page_footer()'''

c = c.replace(old_end, new_end)

with open(path, "w") as f:
    f.write(c)

print("Done - Note form + keyword analysis added to LMIC DH page")
