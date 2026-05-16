import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import subprocess
import requests
from datetime import datetime

# ── Internal state ─────────────────────────────────────────────────────────────
_battery_monitor_running   = False
_weather_monitor_running   = False
_news_monitor_running      = False
_repeating_alerts: dict    = {}   # label -> {"interval": secs, "thread": Thread, "running": bool}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _say(text: str):
    from config import SAY_VOICE
    ssml = f"[[pbas 50]][[rate 175]]{text.strip()} [[slnc 1000]]"
    subprocess.Popen(["say", "-v", SAY_VOICE, ssml]).wait()


def _notify(title: str, message: str):
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{message}" with title "{title}"'],
        capture_output=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# BATTERY LOW ALERT
# ══════════════════════════════════════════════════════════════════════════════

def _get_battery_level() -> int | None:
    """Return current battery percentage as int, or None if on AC only."""
    try:
        result = subprocess.run(
            ["pmset", "-g", "batt"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if "%" in line:
                pct = int(line.split("%")[0].strip().split()[-1])
                return pct
    except Exception:
        pass
    return None


def _battery_loop(threshold: int = 20, interval_mins: int = 5):
    global _battery_monitor_running
    alerted = False
    while _battery_monitor_running:
        level = _get_battery_level()
        if level is not None and level <= threshold:
            if not alerted:
                msg = f"Battery at {level} percent, Boss. Plug in soon."
                _say(msg)
                _notify("Friday — Battery Low", f"{level}% remaining — plug in now")
                alerted = True
        else:
            alerted = False  # Reset so it alerts again if drops back down
        time.sleep(interval_mins * 60)


def start_battery_monitor(threshold: int = 20) -> str:
    global _battery_monitor_running
    if _battery_monitor_running:
        return "Battery monitor already running, Boss."
    _battery_monitor_running = True
    t = threading.Thread(
        target=_battery_loop,
        args=(threshold, 5),
        daemon=True
    )
    t.start()
    return f"Battery monitor active — will alert you below {threshold}%, Boss."


def stop_battery_monitor() -> str:
    global _battery_monitor_running
    _battery_monitor_running = False
    return "Battery monitor stopped, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# PROACTIVE WEATHER ALERTS
# ══════════════════════════════════════════════════════════════════════════════

def check_weather_alert() -> str:
    """
    Check current weather for Kolkata and return an alert string
    if conditions are worth flagging (rain, extreme heat, storm).
    Returns empty string if no alert needed.
    """
    from config import WEATHER_LAT, WEATHER_LON, WEATHER_URL
    try:
        params = {
            "latitude":    WEATHER_LAT,
            "longitude":   WEATHER_LON,
            "current":     "temperature_2m,weathercode,precipitation,windspeed_10m",
            "hourly":      "precipitation_probability",
            "forecast_days": 1,
            "timezone":    "Asia/Kolkata"
        }
        r = requests.get(WEATHER_URL, params=params, timeout=10)
        data = r.json()
        current = data.get("current", {})
        temp     = current.get("temperature_2m", 0)
        code     = current.get("weathercode", 0)
        precip   = current.get("precipitation", 0)
        wind     = current.get("windspeed_10m", 0)

        alerts = []

        # Rain / thunderstorm codes: 51-67, 80-82, 95-99
        rain_codes = list(range(51, 68)) + list(range(80, 83)) + list(range(95, 100))
        if code in rain_codes:
            alerts.append("Rain is likely — carry an umbrella, Boss.")

        # Extreme heat
        if temp >= 40:
            alerts.append(f"It's {temp}°C outside — extreme heat. Stay hydrated, Boss.")
        elif temp >= 36:
            alerts.append(f"It's {temp}°C — quite hot outside, Boss.")

        # Strong wind
        if wind >= 50:
            alerts.append(f"Strong winds at {wind} km/h — heads up, Boss.")

        return " ".join(alerts)

    except Exception:
        return ""


def _weather_alert_loop(interval_mins: int = 60):
    global _weather_monitor_running
    while _weather_monitor_running:
        alert = check_weather_alert()
        if alert:
            _say(alert)
            _notify("Friday — Weather Alert", alert)
        time.sleep(interval_mins * 60)


def start_weather_monitor(interval_mins: int = 60) -> str:
    global _weather_monitor_running
    if _weather_monitor_running:
        return "Weather monitor already active, Boss."
    _weather_monitor_running = True
    t = threading.Thread(
        target=_weather_alert_loop,
        args=(interval_mins,),
        daemon=True
    )
    t.start()
    # Run an immediate check
    alert = check_weather_alert()
    if alert:
        return f"Weather monitor active. Current alert: {alert}"
    return f"Weather monitor active. Checking every {interval_mins} minutes, Boss."


def stop_weather_monitor() -> str:
    global _weather_monitor_running
    _weather_monitor_running = False
    return "Weather monitor stopped, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# REPEATING REMINDERS
# ══════════════════════════════════════════════════════════════════════════════

def _repeating_loop(label: str, interval_secs: int):
    while _repeating_alerts.get(label, {}).get("running", False):
        time.sleep(interval_secs)
        if not _repeating_alerts.get(label, {}).get("running", False):
            break
        _say(f"Reminder, Boss — {label}.")
        _notify("Friday — Reminder", label)


def set_repeating_alert(label: str, interval_mins: int = 30) -> str:
    """Set a repeating voice + notification alert every N minutes."""
    global _repeating_alerts
    if label in _repeating_alerts and _repeating_alerts[label].get("running"):
        return f"Repeating alert '{label}' is already active, Boss."

    interval_secs = interval_mins * 60
    entry = {"interval": interval_secs, "running": True}
    _repeating_alerts[label] = entry
    t = threading.Thread(
        target=_repeating_loop,
        args=(label, interval_secs),
        daemon=True
    )
    t.start()
    entry["thread"] = t
    return f"Repeating reminder set — '{label}' every {interval_mins} minutes, Boss."


def stop_repeating_alert(label: str) -> str:
    """Stop a specific repeating alert."""
    if label not in _repeating_alerts:
        return f"No repeating alert called '{label}' found, Boss."
    _repeating_alerts[label]["running"] = False
    del _repeating_alerts[label]
    return f"Repeating reminder '{label}' stopped, Boss."


def list_repeating_alerts() -> str:
    """List all active repeating alerts."""
    active = [
        f"{label} (every {int(v['interval'] // 60)} min)"
        for label, v in _repeating_alerts.items()
        if v.get("running")
    ]
    if not active:
        return "No active repeating reminders, Boss."
    return "Active repeating reminders: " + ", ".join(active) + ", Boss."


# ══════════════════════════════════════════════════════════════════════════════
# BREAKING NEWS ALERTS
# ══════════════════════════════════════════════════════════════════════════════

_seen_headlines: set = set()

def _news_alert_loop(interval_mins: int = 30):
    global _news_monitor_running, _seen_headlines
    import feedparser
    from config import NEWS_FEEDS, NEWS_MAX_ARTICLES

    while _news_monitor_running:
        time.sleep(interval_mins * 60)
        if not _news_monitor_running:
            break
        try:
            for feed_url in NEWS_FEEDS[:2]:  # Top 2 feeds only for alerts
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:NEWS_MAX_ARTICLES]:
                    title = entry.get("title", "").strip()
                    if title and title not in _seen_headlines:
                        _seen_headlines.add(title)
                        # Flag as breaking if it contains urgent keywords
                        urgent_words = [
                            "breaking", "urgent", "alert", "earthquake",
                            "crash", "attack", "flood", "explosion",
                            "emergency", "killed", "dead", "war"
                        ]
                        if any(w in title.lower() for w in urgent_words):
                            short = title[:120]
                            _say(f"Breaking news, Boss. {short}.")
                            _notify("Friday — Breaking News", short)
                            break  # Only alert once per cycle
        except Exception:
            pass


def start_news_monitor(interval_mins: int = 30) -> str:
    global _news_monitor_running
    if _news_monitor_running:
        return "News monitor already active, Boss."
    _news_monitor_running = True
    t = threading.Thread(
        target=_news_alert_loop,
        args=(interval_mins,),
        daemon=True
    )
    t.start()
    return f"Breaking news monitor active — checking every {interval_mins} minutes, Boss."


def stop_news_monitor() -> str:
    global _news_monitor_running
    _news_monitor_running = False
    return "News monitor stopped, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# MASTER ALERT STATUS
# ══════════════════════════════════════════════════════════════════════════════

def alert_status() -> str:
    """Report which monitors are currently running."""
    parts = []
    parts.append(f"Battery monitor: {'on' if _battery_monitor_running else 'off'}")
    parts.append(f"Weather monitor: {'on' if _weather_monitor_running else 'off'}")
    parts.append(f"News monitor: {'on' if _news_monitor_running else 'off'}")
    active_repeating = [
        label for label, v in _repeating_alerts.items() if v.get("running")
    ]
    if active_repeating:
        parts.append(f"Repeating alerts: {', '.join(active_repeating)}")
    else:
        parts.append("Repeating alerts: none")
    return " | ".join(parts) + ", Boss."


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== alert_status() ===")
    print(alert_status())

    print()
    print("=== check_weather_alert() ===")
    result = check_weather_alert()
    print(result if result else "No weather alerts right now.")

    print()
    print("=== set_repeating_alert() test ===")
    print(set_repeating_alert("Drink water", interval_mins=1))
    print(list_repeating_alerts())
    time.sleep(3)
    print(stop_repeating_alert("Drink water"))

    print()
    print("=== start_battery_monitor() ===")
    print(start_battery_monitor(threshold=95))  # High threshold for testing
    time.sleep(3)
    print(stop_battery_monitor())
