"""Run this to update cyber_collector.py with better RSS sources"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/collectors/cyber_collector.py")

with open(path) as f:
    c = f.read()

# Replace RSS_FEEDS with better sources
old_feeds = '''RSS_FEEDS = {
    "CISA Alerts": {
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "HHS HC3": {
        "url": "https://www.hhs.gov/feed/cybersecurity.xml",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "ENISA News": {
        "url": "https://www.enisa.europa.eu/media/news-items/RSS",
        "source_type": "cyber",
        "region": "Europe",
        "country": "",
    },
}'''

new_feeds = '''RSS_FEEDS = {
    "CISA Alerts": {
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "The Hacker News": {
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "source_type": "cyber",
        "region": "Global",
        "country": "",
    },
    "CyberScoop Healthcare": {
        "url": "https://cyberscoop.com/news/healthcare/feed/",
        "source_type": "cyber",
        "region": "Global",
        "country": "",
    },
    "Healthcare IT News Security": {
        "url": "https://www.healthcareitnews.com/taxonomy/term/60/feed",
        "source_type": "cyber",
        "region": "North America",
        "country": "USA",
    },
    "Bleeping Computer": {
        "url": "https://www.bleepingcomputer.com/feed/",
        "source_type": "cyber",
        "region": "Global",
        "country": "",
    },
    "Cyber Security News": {
        "url": "https://cybersecuritynews.com/feed/",
        "source_type": "cyber",
        "region": "Global",
        "country": "",
    },
}'''

c = c.replace(old_feeds, new_feeds)

# For global feeds, filter by health relevance
# The Hacker News and Bleeping Computer need health filtering
old_filter = '''                    if feed_name == "CISA Alerts" and not is_health_cyber_relevant(title, summary_text):
                        continue'''

new_filter = '''                    # Filter non-healthcare-specific feeds for health relevance
                    if feed_name in ("The Hacker News", "Bleeping Computer", "Cyber Security News"):
                        if not is_health_cyber_relevant(title, summary_text):
                            continue'''

c = c.replace(old_filter, new_filter)

with open(path, "w") as f:
    f.write(c)

print("Done - cyber collector updated with 6 RSS sources")
