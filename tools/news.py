import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser

FEEDS = {
    "world":    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "india":    "https://feeds.feedburner.com/ndtvnews-india-news",
    "tech":     "https://feeds.feedburner.com/TechCrunch",
    "science":  "https://www.sciencedaily.com/rss/top/science.xml",
    "business": "https://feeds.bbci.co.uk/news/business/rss.xml",
    "sports":   "https://feeds.bbci.co.uk/sport/rss.xml",
}

def get_news(topic="world", count=5):
    url  = FEEDS.get(topic.lower(), FEEDS["world"])
    feed = feedparser.parse(url)

    if not feed.entries:
        return f"I couldn't fetch {topic} news at the moment, Sir."

    headlines = []
    for entry in feed.entries[:count]:
        title = entry.get("title", "").strip()
        if title:
            headlines.append(title)

    if not headlines:
        return f"No headlines found for {topic}, Sir."

    # Join with period+space so TTS pauses naturally between headlines
    return f"Top {topic} headlines. " + ". ".join(headlines) + "."

if __name__ == "__main__":
    for topic in ["world", "india", "tech"]:
        print(f"\n--- {topic.upper()} ---")
        print(get_news(topic, count=3))