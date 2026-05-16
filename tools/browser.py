import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import urllib.parse
import config

def open_url(url: str):
    """Open any URL in Brave."""
    if not url.startswith("http"):
        url = "https://" + url
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, url])
    return f"Opening {url}, Boss."

def search_web(query: str):
    """Search Google in Brave."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, url])
    return f"Searching for {query}, Boss."

def open_youtube(query: str = None):
    """Open YouTube search results."""
    if query:
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
    else:
        url = "https://www.youtube.com"
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, url])
    return f"Opened YouTube search for {query}, Boss."

def open_youtube_autoplay(query: str):
    """Find exact YouTube video URL using yt-dlp and open it in Brave for autoplay."""
    try:
        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            video_url = info['entries'][0]['webpage_url']
        subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, video_url])
        return f"Playing {query} on YouTube, Boss."
    except Exception as e:
        return open_youtube(query)

def open_gmail():
    return open_url("https://mail.google.com")

def compose_email(to: str = "", subject: str = "", body: str = ""):
    """Open Gmail compose window."""
    params = urllib.parse.urlencode({
        "to": to,
        "su": subject,
        "body": body
    })
    url = f"https://mail.google.com/mail/?view=cm&fs=1&{params}"
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, url])
    return "Opening Gmail compose window, Boss."

def open_maps(location: str):
    encoded = urllib.parse.quote(location)
    url = f"https://www.google.com/maps/search/{encoded}"
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, url])
    return f"Opening Maps for {location}, Boss."

def open_whatsapp():
    subprocess.Popen(["open", "-a", "WhatsApp"])
    return "Opening WhatsApp, Boss."

def open_github():
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, "https://github.com/sahilimam007"])
    return "Opening your GitHub, Boss."

def open_news_tabs():
    """Open multiple news sites in Brave."""
    sites = [
        "https://www.bbc.com/news",
        "https://timesofindia.indiatimes.com",
        "https://techcrunch.com"
    ]
    for site in sites:
        subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, site])
    return "Opening news tabs in Brave, Boss."

if __name__ == "__main__":
    print(open_youtube_autoplay("Despacito Luis Fonsi"))
    