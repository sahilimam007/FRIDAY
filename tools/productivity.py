import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import subprocess
from datetime import datetime

_pomodoro_running = False
_pomodoro_thread = None
_pomodoro_session = {"count": 0, "phase": None}

def _say(text):
    from config import SAY_VOICE
    subprocess.Popen(["say", "-v", SAY_VOICE, text + " [[slnc 1000]]"])

def _notify(title, message):
    subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'])

def _pomodoro_loop(work_mins=25, break_mins=5, sessions=4):
    global _pomodoro_running, _pomodoro_session
    for i in range(1, sessions + 1):
        if not _pomodoro_running:
            break
        _pomodoro_session["phase"] = "work"
        _pomodoro_session["count"] = i
        _say(f"Pomodoro {i} starting. {work_mins} minutes on the clock, Boss.")
        _notify("Friday", f"Session {i}/{sessions} — {work_mins} min")
        end = time.time() + work_mins * 60
        while time.time() < end:
            if not _pomodoro_running:
                return
            time.sleep(5)
        if not _pomodoro_running:
            break
        _pomodoro_session["phase"] = "break"
        if i < sessions:
            _say(f"Session {i} done. Take a {break_mins} minute break, Boss.")
            end = time.time() + break_mins * 60
            while time.time() < end:
                if not _pomodoro_running:
                    return
                time.sleep(5)
        else:
            _say(f"All {sessions} sessions complete. Outstanding work, Boss.")
    _pomodoro_running = False
    _pomodoro_session = {"count": 0, "phase": None}

def start_pomodoro(work_mins=25, break_mins=5, sessions=4):
    global _pomodoro_thread, _pomodoro_running
    if _pomodoro_running:
        return "Pomodoro already running, Boss."
    _pomodoro_running = True
    _pomodoro_thread = threading.Thread(target=_pomodoro_loop, args=(work_mins, break_mins, sessions), daemon=True)
    _pomodoro_thread.start()
    return f"Pomodoro started — {sessions} sessions of {work_mins} minutes, Boss."

def stop_pomodoro():
    global _pomodoro_running
    if not _pomodoro_running:
        return "No Pomodoro running, Boss."
    _pomodoro_running = False
    return "Pomodoro stopped, Boss."

def pomodoro_status():
    if not _pomodoro_running:
        return "No Pomodoro active, Boss."
    phase = _pomodoro_session.get("phase", "")
    count = _pomodoro_session.get("count", 0)
    if phase == "work":
        return f"Session {count} — work phase active, Boss."
    return f"Session {count} — on break, Boss."

def focus_mode():
    for app in ["Slack", "WhatsApp", "Telegram", "Discord", "Mail", "Messages"]:
        subprocess.run(["osascript", "-e", f'tell application "{app}" to quit'], capture_output=True)
    subprocess.run(["osascript", "-e", "set volume output volume 20"], capture_output=True)
    subprocess.Popen(["open", "-a", "Visual Studio Code"])
    return "Focus mode active. Distractions closed, volume down, VS Code open, Boss."

def vibe_mode():
    subprocess.run(["osascript", "-e", '''
    tell application "Music"
        activate
        play playlist "Vibing"
    end tell
    '''], capture_output=True)
    subprocess.run(["osascript", "-e", "set volume output volume 60"], capture_output=True)
    return "Vibe mode on. Playing Vibing playlist, volume at 60, Boss."

def night_mode():
    subprocess.run(["osascript", "-e", "set volume output volume 20"], capture_output=True)
    return "Night mode on. Volume lowered, Boss."

def meeting_mode():
    subprocess.run(["osascript", "-e", 'tell application "Music" to pause'], capture_output=True)
    subprocess.run(["osascript", "-e", "set volume output volume 35"], capture_output=True)
    subprocess.Popen(["open", "-a", "Calendar"])
    return "Meeting mode on. Music paused, volume at 35, Calendar open, Boss."

def end_of_day_summary():
    now = datetime.now()
    lines = [f"End of day — {now.strftime('%A %d %B, %I:%M %p')}."]
    try:
        from tools.calendar_tools import get_tomorrows_events
        lines.append(get_tomorrows_events())
    except:
        pass
    lines.append("That's the day, Boss.")
    return " ".join(lines)
