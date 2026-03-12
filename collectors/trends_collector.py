"""
Google Trends Collector — Per-Country Edition
Collects Google Trends data for digital therapeutics & neurodegenerative keywords
across EU27 + UK + USA + Israel with rate limiting.

Replaces: collectors/trends_collector.py
"""

import os
import time
import random
import logging
from datetime import datetime, timedelta

from pytrends.request import TrendReq
from supabase import create_client, Client

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supabase client
# ---------------------------------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ISO-3166 two-letter codes used by Google Trends
COUNTRIES = {
    # EU-27
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "GR": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
    # Extra
    "GB": "United Kingdom",
    "US": "United States",
    "IL": "Israel",
}

# Keyword clusters (used for dashboard filtering, not stored in DB)
KEYWORD_CLUSTERS = {
    "digital_health": [
        "digital therapeutics",
        "digital health regulation",
        "software as medical device",
        "digital health app CE mark",
        "DiGA digital health",
    ],
    "neurodegenerative": [
        "Alzheimer digital",
        "Parkinson digital therapy",
        "ALS assistive technology",
        "Huntington disease monitoring",
        "multiple sclerosis digital",
        "frontotemporal dementia",
        "Lewy body dementia diagnosis",
        "cerebellar ataxia wearable",
    ],
    "psychiatric": [
        "digital mental health",
        "depression digital therapy",
        "postpartum depression digital",
        "schizophrenia digital biomarker",
        "ADHD digital therapeutic",
        "anxiety disorder app",
        "bipolar disorder digital",
    ],
    "biobank_data": [
        "health data biobank",
        "neurodegenerative biobank",
        "brain imaging database",
        "real world data neurodegeneration",
        "health data governance",
    ],
    "regulation": [
        "EU health data space",
        "EHDS regulation",
        "AI act medical device",
        "digital health reimbursement",
        "health data interoperability",
    ],
}

# Flatten for iteration
ALL_KEYWORDS = []
KEYWORD_TO_CLUSTER = {}
for cluster, kws in KEYWORD_CLUSTERS.items():
    for kw in kws:
        ALL_KEYWORDS.append(kw)
        KEYWORD_TO_CLUSTER[kw] = cluster

# Rate-limiting
MIN_DELAY_SEC = 60
MAX_DELAY_SEC = 90
MAX_REQUESTS_PER_RUN = 30

# Timeframe: last 12 months
TIMEFRAME = "today 12-m"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sleep_between_requests():
    """Random sleep between MIN and MAX delay to respect rate limits."""
    delay = random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC)
    logger.info(f"Rate-limit pause: {delay:.0f}s")
    time.sleep(delay)


def _build_pytrends():
    """Create a fresh TrendReq session (helps avoid 429 blocks)."""
    return TrendReq(hl="en-US", tz=0, timeout=(10, 30))


def fetch_interest_for_keyword(pytrends: TrendReq, keyword: str, geo: str):
    """
    Fetch interest-over-time + related topics for a single keyword/geo pair.
    Returns a list of row dicts matching the trends_metrics table schema:
    keyword, geography, date, interest_score, is_rising, related_topic
    """
    rows = []
    try:
        pytrends.build_payload(
            kw_list=[keyword],
            timeframe=TIMEFRAME,
            geo=geo,
        )

        # --- Interest over time ---
        iot = pytrends.interest_over_time()
        if iot is not None and not iot.empty and keyword in iot.columns:
            for date_idx, row in iot.iterrows():
                score = int(row[keyword])
                is_partial = bool(row.get("isPartial", False))
                if is_partial:
                    continue  # skip incomplete data points
                rows.append({
                    "keyword": keyword,
                    "geography": geo,
                    "date": date_idx.strftime("%Y-%m-%d"),
                    "interest_score": score,
                    "is_rising": False,
                    "related_topic": None,
                })

        # --- Related topics (rising) ---
        try:
            related = pytrends.related_topics()
            if related and keyword in related:
                rising_df = related[keyword].get("rising")
                if rising_df is not None and not rising_df.empty:
                    top_rising = rising_df.head(5)
                    today_str = datetime.utcnow().strftime("%Y-%m-%d")
                    for _, rt_row in top_rising.iterrows():
                        topic_title = str(
                            rt_row.get("topic_title", rt_row.get("value", ""))
                        )
                        rows.append({
                            "keyword": keyword,
                            "geography": geo,
                            "date": today_str,
                            "interest_score": 0,
                            "is_rising": True,
                            "related_topic": topic_title[:255],
                        })
        except Exception as e:
            logger.warning(f"Related topics failed for {keyword}/{geo}: {e}")

    except Exception as e:
        logger.error(f"Error fetching {keyword} in {geo}: {e}")

    return rows


def upsert_rows(rows: list[dict]):
    """
    Upsert rows into trends_metrics table.
    Uses keyword+geography+date as conflict key (matches DB index).
    """
    if not rows:
        return

    try:
        supabase.table("trends_metrics").upsert(
            rows,
            on_conflict="keyword,geography,date",
        ).execute()
        logger.info(f"Upserted {len(rows)} rows into trends_metrics")
    except Exception as e:
        logger.error(f"Upsert error: {e}")
        # Fallback: insert one by one
        success = 0
        for row in rows:
            try:
                supabase.table("trends_metrics").upsert(
                    row,
                    on_conflict="keyword,geography,date",
                ).execute()
                success += 1
            except Exception as inner_e:
                logger.warning(f"Row upsert failed: {inner_e}")
        logger.info(f"Fallback upsert: {success}/{len(rows)} rows succeeded")


def prioritize_pairs() -> list[tuple[str, str]]:
    """
    Build a prioritized list of (keyword, geo) pairs.
    Priority: major markets first (US, DE, GB, FR, IT, IL), then rest.
    Within each tier, randomize to spread load across keywords.
    """
    priority_geos = ["US", "DE", "GB", "FR", "IT", "IL"]
    other_geos = [g for g in COUNTRIES if g not in priority_geos]

    tier1 = [(kw, geo) for geo in priority_geos for kw in ALL_KEYWORDS]
    tier2 = [(kw, geo) for geo in other_geos for kw in ALL_KEYWORDS]

    random.shuffle(tier1)
    random.shuffle(tier2)

    return tier1 + tier2


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run():
    """Main collector entry point."""
    logger.info("=" * 60)
    logger.info("Google Trends Collector — Per-Country Run Started")
    logger.info(
        f"Keywords: {len(ALL_KEYWORDS)} | "
        f"Countries: {len(COUNTRIES)} | "
        f"Max requests: {MAX_REQUESTS_PER_RUN}"
    )
    logger.info("=" * 60)

    pairs = prioritize_pairs()
    request_count = 0
    total_rows = 0

    pytrends = _build_pytrends()

    for keyword, geo in pairs:
        if request_count >= MAX_REQUESTS_PER_RUN:
            logger.info(f"Reached max requests ({MAX_REQUESTS_PER_RUN}). Stopping.")
            break

        logger.info(
            f"[{request_count + 1}/{MAX_REQUESTS_PER_RUN}] "
            f"Fetching: '{keyword}' in {geo} ({COUNTRIES[geo]})"
        )

        # Refresh pytrends session every 10 requests to reduce 429 risk
        if request_count > 0 and request_count % 10 == 0:
            logger.info("Refreshing pytrends session...")
            pytrends = _build_pytrends()

        rows = fetch_interest_for_keyword(pytrends, keyword, geo)
        if rows:
            upsert_rows(rows)
            total_rows += len(rows)

        request_count += 1

        # Rate limit (skip delay after last request)
        if request_count < MAX_REQUESTS_PER_RUN:
            _sleep_between_requests()

    logger.info("=" * 60)
    logger.info(f"Run complete. Requests: {request_count} | Rows upserted: {total_rows}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
