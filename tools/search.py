import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddgs import DDGS
import config

def search(query, max_results=5):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"I couldn't find anything on '{query}', Sir."

        lines = []
        for i, r in enumerate(results):
            title = r.get("title", "").strip()
            body  = r.get("body", "").strip()
            if title and body:
                lines.append(f"{i+1}. {title}\n   {body[:150]}...")

        return "\n\n".join(lines)

    except Exception as e:
        return f"Search failed, Sir: {e}"

def search_summary(query):
    """Returns a single clean summary sentence for Jarvis to speak."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))

        if not results:
            return f"I couldn't find anything on '{query}', Sir."

        top = results[0]
        title = top.get("title", "")
        body  = top.get("body", "")[:300]
        return f"Here's what I found, Sir. {title} — {body}"

    except Exception as e:
        return f"Search failed, Sir: {e}"

if __name__ == "__main__":
    query = input("Search: ")
    print(search(query, max_results=3))

