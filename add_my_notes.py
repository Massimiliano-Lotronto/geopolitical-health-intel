"""Run this to add 'Le Mie Note' section to LMIC DH page"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

# Add the section right before the "Add Project or Notes" form
old_form = '''    # ── Add Project / Notes Form ──
    st.markdown("---")
    section_header("Add Project or Notes")'''

new_section = '''    # ── Le Mie Note ──
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
    section_header("Add Project or Notes")'''

c = c.replace(old_form, new_section)

with open(path, "w") as f:
    f.write(c)

print("Done - Le Mie Note section added")
