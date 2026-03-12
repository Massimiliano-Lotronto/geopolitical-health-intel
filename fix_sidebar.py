"""Run this script to fix sidebar CSS in app.py"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/dashboard/app.py")

with open(path) as f:
    content = f.read()

old = """    /* Hide radio circles */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0 !important;
    }
    section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {
        display: none !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.92rem;
        font-weight: 400;
        color: #7F8C8D;
        padding: 0.6rem 0.9rem;
        margin: 1px 0;
        border-left: 3px solid transparent;
        border-radius: 0 6px 6px 0;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #0D2B45;
        background: rgba(13,43,69,0.04);
        border-left-color: #B0BEC5;
    }
    section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:has(input:checked) {
        color: #0D2B45;
        font-weight: 600;
        background: rgba(13,43,69,0.06);
        border-left-color: #1A6B8A;
    }"""

# If old partial CSS exists, remove it first
if "/* Hide radio circles */" in content:
    # Find and remove the broken CSS block
    start = content.find("/* Hide radio circles */")
    # Find the closing of this CSS block - look for next section or the closing style tag
    # We need to replace from "/* Hide radio circles */" up to but not including the next "/* --" or ".ed-header"
    end = content.find("    /* ── Page Headers", start)
    if end == -1:
        end = content.find("    .ed-header", start)
    if end > start:
        content = content[:start] + content[end:]

# Also check if old simple CSS exists
old_simple = """    section[data-testid="stSidebar"] .stRadio label {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.92rem;
        font-weight: 400;
        color: #4A4A4A;
        padding: 0.35rem 0;
        transition: color 0.2s;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #0D2B45;
    }"""

if old_simple in content:
    content = content.replace(old_simple, "")

# Now insert the correct CSS before .ed-header
new_css = """    /* ── Sidebar Navigation Tabs ── */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 0px;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label > div:first-child {
        display: none;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.92rem;
        font-weight: 400;
        color: #7F8C8D;
        padding: 0.55rem 0.9rem;
        margin: 1px 0;
        border-left: 3px solid transparent;
        border-radius: 0 6px 6px 0;
        transition: all 0.15s ease;
        cursor: pointer;
        background: transparent;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label:hover {
        color: #0D2B45;
        background: rgba(13,43,69,0.04);
        border-left-color: #B0BEC5;
    }
    section[data-testid="stSidebar"] [data-testid="stRadio"] > div > label[data-checked="true"] {
        color: #0D2B45;
        font-weight: 600;
        background: rgba(26,107,138,0.08);
        border-left-color: #1A6B8A;
    }

    """

marker = "    /* ── Page Headers ── */"
if marker in content:
    content = content.replace(marker, new_css + marker)
else:
    marker2 = "    .ed-header {"
    content = content.replace(marker2, new_css + marker2)

with open(path, "w") as f:
    f.write(content)

print("Done - sidebar CSS fixed correctly")
