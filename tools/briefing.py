import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from datetime import datetime
from tools.weather import get_weather
from tools.news import get_news
from tools.mac_control import get_battery
from memory.memory import check_upcoming_events

def morning_briefing() -> str:
    now  = datetime.now()
    hour = now.hour

    if hour < 12:
        greeting = "Good morning, Boss."
    elif hour < 17:
        greeting = "Good afternoon, Boss."
    elif hour < 21:
        greeting = "Good evening, Boss."
    else:
        greeting = "Working late again, Boss."

    parts = [greeting]
    parts.append(f"Today is {now.strftime('%A, %d %B %Y')}.")

    try:
        weather = get_weather()
        match = re.search(r'([\w]+), ([\d.]+)°C', weather)
        if match:
            parts.append(f"It's {match.group(2)}°C and {match.group(1).lower()} in Kolkata.")
        else:
            parts.append(weather)
    except:
        pass

    try:
        events = check_upcoming_events()
        if events:
            parts.append(events)
    except:
        pass

    try:
        news = get_news("world")
        lines = [l.strip() for l in news.split(". ") if l.strip() and "headline" not in l.lower()]
        if lines:
            parts.append(f"Top story: {lines[0]}.")
    except:
        pass

    try:
        battery = get_battery()
        match = re.search(r'(\d+)%', battery)
        if match:
            pct = int(match.group(1))
            if pct < 50:
                parts.append(f"Battery is at {pct}% — you may want to plug in, Boss.")
    except:
        pass

    parts.append("Systems are online and standing by.")
    return " ".join(parts)

if __name__ == "__main__":
    print(morning_briefing())
