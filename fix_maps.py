"""Run this to fix live threat maps - keep Check Point and Radware, add links for others"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    c = f.read()

old = '''            map_tab1, map_tab2, map_tab3, map_tab4 = st.tabs([
                "Kaspersky", "Check Point", "Radware", "NETSCOUT"
            ])

            with map_tab1:
                st.components.v1.iframe(
                    "https://cybermap.kaspersky.com/widget",
                    height=450, scrolling=False,
                )
                st.caption("Source: Kaspersky Cyberthreat Real-Time Map")

            with map_tab2:
                st.components.v1.iframe(
                    "https://threatmap.checkpoint.com/",
                    height=450, scrolling=False,
                )
                st.caption("Source: Check Point ThreatCloud Live Map")

            with map_tab3:
                st.components.v1.iframe(
                    "https://livethreatmap.radware.com/",
                    height=450, scrolling=False,
                )
                st.caption("Source: Radware Live Threat Map")

            with map_tab4:
                st.components.v1.iframe(
                    "https://horizon.netscout.com/",
                    height=450, scrolling=False,
                )
                st.caption("Source: NETSCOUT Cyber Threat Horizon")'''

new = '''            map_tab1, map_tab2 = st.tabs(["Check Point", "Radware"])

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
            """, unsafe_allow_html=True)'''

c = c.replace(old, new)

with open(path, "w") as f:
    f.write(c)

print("Done - Live maps fixed")
