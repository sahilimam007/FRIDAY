import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
from datetime import datetime, timedelta

def run_applescript(script: str) -> str:
    # Use stdin instead of -e so multi-line scripts with mixed quotes work correctly.
    # osascript -e silently truncates or misparses multi-line f-strings.
    result = subprocess.run(["osascript"], input=script, capture_output=True, text=True)
    return result.stdout.strip()

def fmt(dt):
    return dt.strftime("%d/%m/%y %I:%M:%S %p")

# ── Read calendar events ───────────────────────────────────────────────────────

def get_todays_events() -> str:
    now = datetime.now()
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
    now  = datetime.now()
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
    now = datetime.now()
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

# ── Create calendar events ─────────────────────────────────────────────────────

def create_event(title: str, date_str: str = "", time_str: str = "", duration_mins: int = 60) -> str:
    now = datetime.now()

    # Parse date
    if not date_str or date_str.lower() == "today":
        event_date = now.date()
    elif date_str.lower() == "tomorrow":
        event_date = (now + timedelta(days=1)).date()
    else:
        days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        matched = False
        for i, day in enumerate(days):
            if day in date_str.lower():
                days_ahead = (i - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                event_date = (now + timedelta(days=days_ahead)).date()
                matched = True
                break
        if not matched:
            try:
                event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except:
                event_date = now.date()

    # Parse time
    if not time_str:
        event_hour, event_min = 9, 0
    else:
        t = time_str.lower().strip()
        try:
            if "pm" in t:
                t = t.replace("pm", "").strip()
                parts = t.split(":")
                event_hour = int(parts[0]) + 12
                if event_hour == 24: event_hour = 12
                event_min = int(parts[1]) if len(parts) > 1 else 0
            elif "am" in t:
                t = t.replace("am", "").strip()
                parts = t.split(":")
                event_hour = int(parts[0])
                if event_hour == 12: event_hour = 0
                event_min = int(parts[1]) if len(parts) > 1 else 0
            else:
                parts = t.split(":")
                event_hour = int(parts[0])
                event_min = int(parts[1]) if len(parts) > 1 else 0
        except:
            event_hour, event_min = 9, 0

    start_dt = datetime(event_date.year, event_date.month, event_date.day, event_hour, event_min)
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
    if "done" in result or result == "":
        return f"Event '{title}' created on {event_date.strftime('%A %d %B')} at {start_dt.strftime('%I:%M %p')}, Boss."
    return f"Couldn't create event, Boss."

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
    print(create_event("Test meeting", "tomorrow", "3pm", 60))
