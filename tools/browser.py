import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import urllib.parse
import config

# ── Browser aliases ────────────────────────────────────────────────────────────
BROWSER_ALIASES = {
    "brave":   "Brave Browser",
    "chrome":  "Google Chrome",
    "safari":  "Safari",
    "firefox": "Firefox",
    "arc":     "Arc",
    "edge":    "Microsoft Edge",
}

def _get_browser(name: str = None) -> str:
    """Return browser app name. Defaults to config.DEFAULT_BROWSER."""
    if not name:
        return config.DEFAULT_BROWSER
    return BROWSER_ALIASES.get(name.lower().strip(), config.DEFAULT_BROWSER)

def open_url(url: str, browser: str = None) -> str:
    """Open any URL. Defaults to Brave. Pass browser name to override."""
    if not url.startswith("http"):
        url = "https://" + url
    b = _get_browser(browser)
    subprocess.Popen(["open", "-a", b, url])
    return f"Opening {url} in {b}, Boss."

def search_web(query: str, browser: str = None) -> str:
    """Search Google. Defaults to Brave."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    b = _get_browser(browser)
    subprocess.Popen(["open", "-a", b, url])
    return f"Searching for {query} in {b}, Boss."

def open_youtube(query: str = None, browser: str = None) -> str:
    """Open YouTube search results in Brave by default."""
    if query:
        encoded = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
    else:
        url = "https://www.youtube.com"
    b = _get_browser(browser)
    subprocess.Popen(["open", "-a", b, url])
    return f"Opened YouTube{' search for ' + query if query else ''} in {b}, Boss."

def open_youtube_autoplay(query: str, browser: str = None) -> str:
    """Find exact YouTube video URL using yt-dlp and open in Brave."""
    try:
        import yt_dlp
        ydl_opts = {'quiet': True, 'no_warnings': True, 'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            video_url = info['entries'][0]['webpage_url']
        b = _get_browser(browser)
        subprocess.Popen(["open", "-a", b, video_url])
        return f"Playing {query} on YouTube in {b}, Boss."
    except Exception:
        return open_youtube(query, browser)

def open_gmail(browser: str = None) -> str:
    return open_url("https://mail.google.com", browser)

def compose_email(to: str = "", subject: str = "", body: str = "", browser: str = None) -> str:
    """Open Gmail compose window in Brave."""
    params = urllib.parse.urlencode({"to": to, "su": subject, "body": body})
    url = f"https://mail.google.com/mail/?view=cm&fs=1&{params}"
    b = _get_browser(browser)
    subprocess.Popen(["open", "-a", b, url])
    return "Opening Gmail compose window, Boss."

def open_maps(location: str, browser: str = None) -> str:
    encoded = urllib.parse.quote(location)
    url = f"https://www.google.com/maps/search/{encoded}"
    b = _get_browser(browser)
    subprocess.Popen(["open", "-a", b, url])
    return f"Opening Maps for {location}, Boss."

def open_whatsapp() -> str:
    subprocess.Popen(["open", "-a", "WhatsApp"])
    return "Opening WhatsApp, Boss."

def open_github(browser: str = None) -> str:
    b = _get_browser(browser)
    subprocess.Popen(["open", "-a", b, "https://github.com/sahilimam007"])
    return "Opening your GitHub, Boss."

def open_incognito(url: str = "", browser: str = None) -> str:
    """Open Brave (or specified browser) in private/incognito mode."""
    b = _get_browser(browser)
    if url:
        if not url.startswith("http"):
            url = "https://" + url
        subprocess.Popen(["open", "-na", b, "--args", "--incognito", url])
        return f"Opening {url} in private mode in {b}, Boss."
    subprocess.Popen(["open", "-na", b, "--args", "--incognito"])
    return f"Private browsing window opened in {b}, Boss."

def open_news_tabs(browser: str = None) -> str:
    """Open news sites in Brave by default."""
    sites = [
        "https://www.bbc.com/news",
        "https://timesofindia.indiatimes.com",
        "https://techcrunch.com",
    ]
    b = _get_browser(browser)
    for site in sites:
        subprocess.Popen(["open", "-a", b, site])
    return f"Opening news tabs in {b}, Boss."

def open_spotify(browser: str = None) -> str:
    try:
        subprocess.Popen(["open", "-a", "Spotify"])
        return "Opening Spotify, Boss."
    except Exception:
        return open_url("https://open.spotify.com", browser)

if __name__ == "__main__":
    print(open_youtube_autoplay("Despacito Luis Fonsi"))