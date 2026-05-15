import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import config

def open_url(url):
    """Open any URL in Brave."""
    if not url.startswith("http"):
        url = "https://" + url
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, url])
    return f"Opening {url}, Sir."

def search_web(query):
    """Search Google in Brave."""
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    return open_url(url)

def open_youtube(query=None):
    if query:
        import urllib.parse
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
    else:
        url = "https://www.youtube.com"
    return open_url(url)

def open_gmail():
    return open_url("https://mail.google.com")

def compose_email(to="", subject="", body=""):
    """Open Gmail compose window with pre-filled fields."""
    import urllib.parse
    params = urllib.parse.urlencode({
        "to": to,
        "su": subject,
        "body": body
    })
    url = f"https://mail.google.com/mail/?view=cm&fs=1&{params}"
    return open_url(url)

def open_spotify():
    return open_url("https://open.spotify.com")

def open_github():
    return open_url("https://github.com/sahilimam007")

def open_maps(location):
    import urllib.parse
    encoded = urllib.parse.quote(location)
    url = f"https://www.google.com/maps/search/{encoded}"
    return open_url(url)

def open_whatsapp():
    subprocess.Popen(["open", "-a", "WhatsApp"])
    return "Opening WhatsApp, Sir."

if __name__ == "__main__":
    print(search_web("Jarvis Iron Man AI"))
    print(open_youtube("Hans Zimmer best music"))
    print(compose_email(
        to="test@example.com",
        subject="Test from Jarvis",
        body="Good evening, Sir has asked me to send this."
    ))
    