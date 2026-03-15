"""Run this to fix Chatham House collector - use Google News RSS instead"""
import os

path = os.path.expanduser("~/Desktop/health-Intel/geopolitical-health-intel/collectors/chatham_collector.py")

with open(path) as f:
    c = f.read()

old_feeds = '''RSS_FEEDS = {
    "Chatham House": {
        "url": "https://www.chathamhouse.org/rss",
        "source_type": "think_tank",
        "region": "Europe",
        "country": "United Kingdom",
    },
    "Chatham House Publications": {
        "url": "https://www.chathamhouse.org/publications/rss",
        "source_type": "think_tank",
        "region": "Europe",
        "country": "United Kingdom",
    },
}'''

new_feeds = '''RSS_FEEDS = {
    "Chatham House via Google News": {
        "url": "https://news.google.com/rss/search?q=site:chathamhouse.org+health&hl=en-US&gl=US&ceid=US:en",
        "source_type": "think_tank",
        "region": "Europe",
        "country": "United Kingdom",
    },
    "Chatham House Global Health": {
        "url": "https://news.google.com/rss/search?q=chatham+house+global+health+digital&hl=en-US&gl=US&ceid=US:en",
        "source_type": "think_tank",
        "region": "Europe",
        "country": "United Kingdom",
    },
}'''

c = c.replace(old_feeds, new_feeds)

# Remove health filter since searches are already health-focused
c = c.replace("if not is_health_relevant(title, summary_text):", "if False:")

with open(path, "w") as f:
    f.write(c)

print("Done - Chatham House collector fixed")
