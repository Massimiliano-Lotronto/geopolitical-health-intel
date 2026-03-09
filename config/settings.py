"""
Configurazione centrale del progetto.
Carica variabili da .env e definisce costanti.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carica .env dalla root del progetto
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")


# ── Database ──────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/health_intel"
)

# ── NCBI / PubMed ────────────────────────────────────────
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
NCBI_RATE_LIMIT = 10 if NCBI_API_KEY else 3  # req/sec

# ── Bundestag ─────────────────────────────────────────────
BUNDESTAG_API_KEY = os.getenv("BUNDESTAG_API_KEY", "")

# ── BfArM DiGA ────────────────────────────────────────────
DIGA_FHIR_TOKEN = os.getenv(
    "DIGA_FHIR_TOKEN",
    "116b0a73-6e3b-4a88-9313-9947a4fed9ef"
)
DIGA_FHIR_BASE = "https://diga.bfarm.de/api/fhir/v2.0"

# ── Email ─────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_RECIPIENTS = [
    e.strip() for e in os.getenv("ALERT_RECIPIENTS", "").split(",") if e.strip()
]

# ── Scraping Defaults ─────────────────────────────────────
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = (
    "GeopoliticalHealthIntel/1.0 "
    "(Research Dashboard; contact: {})".format(NCBI_EMAIL or "admin@example.com")
)
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}

# ── Scoring Weights ──────────────────────────────────────
STRATEGIC_WEIGHTS = {
    "regulatory": 0.35,
    "scientific": 0.25,
    "market_trend": 0.20,
    "country_need": 0.20,
}

# ── Keyword Levels ────────────────────────────────────────
KEYWORD_LEVELS = {
    1: "macro_topic",
    2: "regulatory",
    3: "neurodegenerative",
    4: "lmic_access",
    5: "germany_reimbursement",
}
