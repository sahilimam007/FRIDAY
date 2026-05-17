import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import re
from datetime import datetime, timedelta

def run_applescript(script: str) -> str:
    result = subprocess.run(["osascript"], input=script, capture_output=True, text=True)
    return result.stdout.strip()

def fmt(dt):
    return dt.strftime("%d/%m/%y %I:%M:%S %p")

# ── Read calendar events ───────────────────────────────────────────────────────

def get_todays_events() -> str:
    now   = datetime.now()
    start = now.replace(hour=0, minute=0, second=0)
    end   = now.replace(hour=23, minute=59, second=59)
    script = f'''
    set startOfDay to date "{fmt(start)}"
    set endOfDay to date "{fmt(end)}"
    set eventList to ""
    tell application "Calendar"
        try
            repeat with e in (every event of calendar "Home")
                set d to start date of e
                if d >= startOfDay and d <= endOfDay then
                    set eventList to eventList & summary of e & " at " & (time string of d) & ", "
                end if
            end repeat
        end try
        try
            repeat with e in (every event of calendar "Work")
                set d to start date of e
                if d >= startOfDay and d <= endOfDay then
                    set eventList to eventList & summary of e & " at " & (time string of d) & ", "
                end if
            end repeat
        end try
    end tell
    return eventList
    '''
    result = run_applescript(script)
    if not result.strip():
        return "No events scheduled for today, Boss."
    return f"Today's events: {result.strip().rstrip(',')}, Boss."

def get_tomorrows_events() -> str:
    tomorrow = datetime.now() + timedelta(days=1)
    start = tomorrow.replace(hour=0, minute=0, second=0)
    end   = tomorrow.replace(hour=23, minute=59, second=59)
    script = f'''
    set startOfDay to date "{fmt(start)}"
    set endOfDay to date "{fmt(end)}"
    set eventList to ""
    tell application "Calendar"
        try
            repeat with e in (every event of calendar "Home")
                set d to start date of e
                if d >= startOfDay and d <= endOfDay then
                    set eventList to eventList & summary of e & " at " & (time string of d) & ", "
                end if
            end repeat
        end try
        try
            repeat with e in (every event of calendar "Work")
                set d to start date of e
                if d >= startOfDay and d <= endOfDay then
                    set eventList to eventList & summary of e & " at " & (time string of d) & ", "
                end if
            end repeat
        end try
    end tell
    return eventList
    '''
    result = run_applescript(script)
    if not result.strip():
        return "Nothing scheduled for tomorrow, Boss."
    return f"Tomorrow's events: {result.strip().rstrip(',')}, Boss."

def get_weeks_events() -> str:
    now   = datetime.now()
    start = now.replace(hour=0, minute=0, second=0)
    end   = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59)
    script = f'''
    set startOfDay to date "{fmt(start)}"
    set endOfWeek to date "{fmt(end)}"
    set eventList to ""
    tell application "Calendar"
        try
            repeat with e in (every event of calendar "Home")
                if (start date of e) >= startOfDay and (start date of e) <= endOfWeek then
                    set d to start date of e
                    set eventList to eventList & summary of e & " on " & (short date string of d) & " at " & (time string of d) & ", "
                end if
            end repeat
        end try
        try
            repeat with e in (every event of calendar "Work")
                if (start date of e) >= startOfDay and (start date of e) <= endOfWeek then
                    set d to start date of e
                    set eventList to eventList & summary of e & " on " & (short date string of d) & " at " & (time string of d) & ", "
                end if
            end repeat
        end try
    end tell
    return eventList
    '''
    result = run_applescript(script)
    if not result.strip():
        return "Nothing scheduled this week, Boss."
    return f"This week: {result.strip().rstrip(',')}, Boss."

def get_next_event() -> str:
    now   = datetime.now()
    start = now.replace(second=0)
    end   = (now + timedelta(days=365)).replace(hour=23, minute=59, second=59)
    script = f'''
    set startNow to date "{fmt(start)}"
    set endFuture to date "{fmt(end)}"
    set eventList to ""
    tell application "Calendar"
        try
            repeat with e in (every event of calendar "Home")
                if (start date of e) >= startNow and (start date of e) <= endFuture then
                    set d to start date of e
                    set eventList to eventList & summary of e & "|" & (short date string of d) & "|" & (time string of d) & "~"
                end if
            end repeat
        end try
        try
            repeat with e in (every event of calendar "Work")
                if (start date of e) >= startNow and (start date of e) <= endFuture then
                    set d to start date of e
                    set eventList to eventList & summary of e & "|" & (short date string of d) & "|" & (time string of d) & "~"
                end if
            end repeat
        end try
    end tell
    return eventList
    '''
    result = run_applescript(script)
    if not result.strip():
        return "No upcoming events found, Boss."
    events = [e.strip() for e in result.split("~") if e.strip()]
    if not events:
        return "No upcoming events found, Boss."
    first = events[0].split("|")
    if len(first) >= 3:
        return f"Next event: {first[0]} on {first[1]} at {first[2]}, Boss."
    return f"Next event: {events[0]}, Boss."

# ── Create calendar event ──────────────────────────────────────────────────────

def _parse_time(time_str: str):
    """
    Parse time string like '3pm', '15:00', '3:30pm', '9am' into (hour, minute).
    Returns (9, 0) as default if parsing fails.
    """
    if not time_str:
        return 9, 0

    t = time_str.lower().strip()

    # Match patterns like 3pm, 3:30pm, 15:00, 9am
    match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$', t)
    if not match:
        return 9, 0

    hour   = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    period = match.group(3)

    if period == "pm":
        if hour != 12:
            hour += 12
    elif period == "am":
        if hour == 12:
            hour = 0
    # No period — treat as 24hr if > 12, else assume am/pm based on value
    else:
        if hour < 7:  # 1-6 without am/pm → assume pm
            hour += 12

    hour = min(hour, 23)
    minute = min(minute, 59)
    return hour, minute

def _parse_date(date_str: str):
    """Parse date string into a date object. Returns today if parsing fails."""
    now = datetime.now()
    if not date_str or date_str.lower() in ("today", ""):
        return now.date()
    if date_str.lower() == "tomorrow":
        return (now + timedelta(days=1)).date()

    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(days):
        if day in date_str.lower():
            days_ahead = (i - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (now + timedelta(days=days_ahead)).date()

    # Try explicit date formats
    for fmt_str in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%B %d", "%b %d"):
        try:
            parsed = datetime.strptime(date_str.strip(), fmt_str)
            if parsed.year == 1900:
                parsed = parsed.replace(year=now.year)
            return parsed.date()
        except ValueError:
            continue

    return now.date()

def create_event(title: str, date_str: str = "", time_str: str = "", duration_mins: int = 60) -> str:
    """
    Create a calendar event.
    Handles cases where time is embedded in date_str (e.g. 'tomorrow at 3pm').
    """
    # Extract time from date_str if time_str is empty
    if not time_str and date_str:
        # Pattern: "tomorrow at 3pm", "today at 15:00", "friday at 9:30am"
        time_in_date = re.search(
            r'\bat\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            date_str, re.IGNORECASE
        )
        if time_in_date:
            time_str = time_in_date.group(1).strip()
            date_str = date_str[:time_in_date.start()].strip()

    event_date  = _parse_date(date_str)
    event_hour, event_min = _parse_time(time_str)

    start_dt = datetime(event_date.year, event_date.month, event_date.day,
                        event_hour, event_min)
    end_dt   = start_dt + timedelta(minutes=duration_mins)

    script = f'''
    tell application "Calendar"
        tell calendar "Home"
            make new event with properties {{summary:"{title}", start date:date "{fmt(start_dt)}", end date:date "{fmt(end_dt)}"}}
        end tell
    end tell
    return "done"
    '''
    result = run_applescript(script)
    time_display = start_dt.strftime('%I:%M %p').lstrip('0')
    date_display = event_date.strftime('%A %d %B')
    return f"Event '{title}' created on {date_display} at {time_display}, Boss."

def delete_event(title: str) -> str:
    script = f'''
    tell application "Calendar"
        try
            repeat with e in (every event of calendar "Home")
                if summary of e contains "{title}" then
                    delete e
                end if
            end repeat
        end try
        try
            repeat with e in (every event of calendar "Work")
                if summary of e contains "{title}" then
                    delete e
                end if
            end repeat
        end try
    end tell
    return "done"
    '''
    run_applescript(script)
    return f"Deleted events matching '{title}', Boss."

# ── Reminders ──────────────────────────────────────────────────────────────────

def get_todays_reminders() -> str:
    script = '''
    set taskList to ""
    tell application "Reminders"
        set incompleteTasks to (every reminder whose completed is false)
        repeat with t in incompleteTasks
            set taskList to taskList & name of t & ", "
        end repeat
    end tell
    return taskList
    '''
    result = run_applescript(script)
    if not result.strip():
        return "No pending reminders, Boss."
    return f"Pending tasks: {result.strip().rstrip(',')}, Boss."

def add_reminder(task: str, due_date: str = "") -> str:
    script = f'''
    tell application "Reminders"
        make new reminder with properties {{name:"{task}"}}
    end tell
    return "done"
    '''
    run_applescript(script)
    return f"Added '{task}' to your reminders, Boss."

def complete_reminder(task: str) -> str:
    script = f'''
    tell application "Reminders"
        repeat with t in (every reminder whose completed is false)
            if name of t contains "{task}" then
                set completed of t to true
            end if
        end repeat
    end tell
    return "done"
    '''
    run_applescript(script)
    return f"Marked '{task}' as complete, Boss."

def open_calendar() -> str:
    subprocess.Popen(["open", "-a", "Calendar"])
    return "Opened Calendar, Boss."

def open_reminders() -> str:
    subprocess.Popen(["open", "-a", "Reminders"])
    return "Opened Reminders, Boss."

if __name__ == "__main__":
    print(get_todays_events())
    print(get_tomorrows_events())
    print(get_next_event())
    print(get_todays_reminders())
    # Test time parsing
    print(create_event("Team meeting", "tomorrow at 3pm", "", 60))
    print(create_event("Standup", "today", "9:30am", 30))
    print(create_event("Dinner", "friday", "7pm", 90))