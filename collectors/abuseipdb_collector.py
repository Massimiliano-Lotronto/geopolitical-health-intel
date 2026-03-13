"""
AbuseIPDB Collector — Attack Flow Intelligence
Downloads the top malicious IPs with country of origin.
Stores in a dedicated table for origin→destination flow visualization.

Requires: ABUSEIPDB_API_KEY environment variable
Free tier: 1,000 checks/day, blacklist returns top 10,000 IPs
"""

import os
import sys
import logging
from datetime import datetime
from collections import Counter

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import DATABASE_URL
from db.models import get_engine, get_session, Base
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

engine = get_engine(DATABASE_URL)

ABUSEIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")
if not ABUSEIPDB_API_KEY:
    raise EnvironmentError("ABUSEIPDB_API_KEY must be set")

API_BASE = "https://api.abuseipdb.com/api/v2"

# Country code to name mapping (top attackers + targets)
COUNTRY_NAMES = {
    "CN": "China", "US": "United States", "RU": "Russia", "BR": "Brazil",
    "IN": "India", "KR": "South Korea", "DE": "Germany", "FR": "France",
    "GB": "United Kingdom", "NL": "Netherlands", "VN": "Vietnam",
    "ID": "Indonesia", "TW": "Taiwan", "JP": "Japan", "TH": "Thailand",
    "UA": "Ukraine", "PK": "Pakistan", "IT": "Italy", "AR": "Argentina",
    "MX": "Mexico", "PH": "Philippines", "BD": "Bangladesh", "CO": "Colombia",
    "TR": "Turkey", "IR": "Iran", "KP": "North Korea", "RO": "Romania",
    "PL": "Poland", "ES": "Spain", "CA": "Canada", "AU": "Australia",
    "IL": "Israel", "SG": "Singapore", "HK": "Hong Kong", "ZA": "South Africa",
    "EG": "Egypt", "NG": "Nigeria", "SA": "Saudi Arabia", "AE": "UAE",
    "SE": "Sweden", "NO": "Norway", "FI": "Finland", "DK": "Denmark",
    "BE": "Belgium", "AT": "Austria", "CH": "Switzerland", "CZ": "Czech Republic",
    "HU": "Hungary", "BG": "Bulgaria", "GR": "Greece", "PT": "Portugal",
    "IE": "Ireland", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
    "SK": "Slovakia", "SI": "Slovenia", "HR": "Croatia", "CY": "Cyprus",
    "LU": "Luxembourg", "MT": "Malta",
}


def ensure_table():
    """Create cyber_attack_flows table if it doesn't exist."""
    session = get_session(engine)
    try:
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS cyber_attack_flows (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                origin_country_code VARCHAR(10) NOT NULL,
                origin_country_name VARCHAR(100),
                target_country VARCHAR(100) DEFAULT 'Healthcare Global',
                attack_count INTEGER DEFAULT 0,
                avg_confidence FLOAT DEFAULT 0,
                top_category VARCHAR(100),
                collected_at TIMESTAMP DEFAULT NOW()
            )
        """))
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_caf_date_origin
            ON cyber_attack_flows(date, origin_country_code)
        """))
        session.commit()
        logger.info("Table cyber_attack_flows ready")
    except Exception as e:
        session.rollback()
        logger.error(f"Table creation error: {e}")
    finally:
        session.close()


def fetch_blacklist(limit=5000, confidence_minimum=90):
    """
    Fetch the AbuseIPDB blacklist — top malicious IPs.
    Returns list of dicts with ipAddress, countryCode, abuseConfidenceScore.
    """
    logger.info(f"Fetching blacklist (limit={limit}, confidence>={confidence_minimum})")
    headers = {
        "Key": ABUSEIPDB_API_KEY,
        "Accept": "application/json",
    }
    params = {
        "confidenceMinimum": confidence_minimum,
        "limit": limit,
    }

    try:
        resp = requests.get(
            f"{API_BASE}/blacklist",
            headers=headers,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        ips = data.get("data", [])
        logger.info(f"Blacklist returned {len(ips)} IPs")
        return ips

    except Exception as e:
        logger.error(f"Blacklist fetch error: {e}")
        return []


def check_sample_ips(ips, sample_size=50):
    """
    Check a sample of IPs for detailed info (country, categories, reports).
    Uses the CHECK endpoint — costs 1 request per IP from daily quota.
    """
    logger.info(f"Checking {sample_size} sample IPs for detailed info")
    headers = {
        "Key": ABUSEIPDB_API_KEY,
        "Accept": "application/json",
    }

    results = []
    checked = 0

    for ip_entry in ips[:sample_size]:
        ip = ip_entry.get("ipAddress", "")
        if not ip:
            continue

        try:
            resp = requests.get(
                f"{API_BASE}/check",
                headers=headers,
                params={"ipAddress": ip, "maxAgeInDays": 30, "verbose": ""},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})

            results.append({
                "ip": ip,
                "country_code": data.get("countryCode", "??"),
                "abuse_confidence": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "isp": data.get("isp", ""),
                "usage_type": data.get("usageType", ""),
                "domain": data.get("domain", ""),
            })
            checked += 1

        except Exception as e:
            logger.warning(f"Check failed for {ip}: {e}")

    logger.info(f"Checked {checked}/{sample_size} IPs")
    return results


def aggregate_by_country(blacklist_ips):
    """
    Aggregate blacklist IPs by country of origin.
    Returns list of (country_code, count, avg_confidence).
    """
    country_counts = Counter()
    country_scores = {}

    for ip_entry in blacklist_ips:
        cc = ip_entry.get("countryCode", "??")
        score = ip_entry.get("abuseConfidenceScore", 0)

        country_counts[cc] += 1
        if cc not in country_scores:
            country_scores[cc] = []
        country_scores[cc].append(score)

    results = []
    for cc, count in country_counts.most_common(50):
        avg_score = sum(country_scores[cc]) / len(country_scores[cc])
        results.append({
            "country_code": cc,
            "count": count,
            "avg_confidence": round(avg_score, 1),
        })

    return results


def store_flows(country_aggregates, target_countries=None):
    """
    Store aggregated attack flows in the database.
    Each origin country gets a row per target country per day.
    """
    if target_countries is None:
        target_countries = [
            "USA", "Germany", "United Kingdom", "France", "Italy",
            "Israel", "Healthcare Global",
        ]

    session = get_session(engine)
    today = datetime.utcnow().date()
    total = 0

    try:
        # Delete today's data first (idempotent)
        session.execute(
            text("DELETE FROM cyber_attack_flows WHERE date = :d"),
            {"d": today},
        )

        for agg in country_aggregates:
            cc = agg["country_code"]
            country_name = COUNTRY_NAMES.get(cc, cc)

            for target in target_countries:
                # Distribute attacks proportionally (simplified model)
                # In reality, we'd need target-specific data
                attack_share = agg["count"] // len(target_countries)
                if attack_share == 0 and agg["count"] > 0:
                    attack_share = 1

                session.execute(
                    text("""
                        INSERT INTO cyber_attack_flows
                        (date, origin_country_code, origin_country_name,
                         target_country, attack_count, avg_confidence, collected_at)
                        VALUES (:date, :occ, :ocn, :tc, :ac, :avgc, :now)
                    """),
                    {
                        "date": today,
                        "occ": cc,
                        "ocn": country_name,
                        "tc": target,
                        "ac": attack_share,
                        "avgc": agg["avg_confidence"],
                        "now": datetime.utcnow(),
                    },
                )
                total += 1

        session.commit()
        logger.info(f"Stored {total} flow records for {today}")

    except Exception as e:
        session.rollback()
        logger.error(f"Store error: {e}")
    finally:
        session.close()


def run():
    """Main collector entry point."""
    logger.info("=" * 60)
    logger.info("AbuseIPDB Collector — Attack Flow Intelligence")
    logger.info("=" * 60)

    # Ensure table exists
    ensure_table()

    # 1. Fetch blacklist (1 API call)
    blacklist = fetch_blacklist(limit=5000, confidence_minimum=90)
    if not blacklist:
        logger.warning("No blacklist data. Check API key and quota.")
        return

    # 2. Aggregate by country of origin
    country_agg = aggregate_by_country(blacklist)
    logger.info(f"Top origins: {', '.join(f'{a['country_code']}({a['count']})' for a in country_agg[:10])}")

    # 3. Store flows
    store_flows(country_agg)

    # 4. Optional: check sample IPs for extra detail (uses ~50 API calls)
    # Uncomment if you want richer data:
    # detailed = check_sample_ips(blacklist, sample_size=50)

    logger.info("=" * 60)
    logger.info("Run complete")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
