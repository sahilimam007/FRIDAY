import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import subprocess
from datetime import datetime

# ── Internal state ─────────────────────────────────────────────────────────────
_pomodoro_thread  = None
_pomodoro_running = False
_pomodoro_session = {"count": 0, "phase": None}  # phase: "work" | "break"

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _say(text: str):
    """Speak text without importing speaker to avoid circular imports."""
    from config import SAY_VOICE
    ssml = f"[[pbas 50]][[rate 175]]{text.strip()} [[slnc 1000]]"
    subprocess.Popen(["say", "-v", SAY_VOICE, ssml]).wait()


def _notify(title: str, message: str):
    """Send a macOS notification."""
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}"'
    ])


# ══════════════════════════════════════════════════════════════════════════════
# POMODORO TIMER
# ══════════════════════════════════════════════════════════════════════════════

def _pomodoro_loop(work_mins: int = 25, break_mins: int = 5, sessions: int = 4):
    """Background thread that runs the full Pomodoro cycle."""
    global _pomodoro_running, _pomodoro_session

    for i in range(1, sessions + 1):
        if not _pomodoro_running:
            break

        # ── Work phase ─────────────────────────────────────────────────────
        _pomodoro_session["phase"] = "work"
        _pomodoro_session["count"] = i
        _say(f"Pomodoro {i} starting. {work_mins} minutes on the clock, Boss.")
        _notify("Friday — Pomodoro", f"Session {i}/{sessions} — Work for {work_mins} min")

        work_end = time.time() + (work_mins * 60)
        while time.time() < work_end:
            if not _pomodoro_running:
                return
            time.sleep(5)

        if not _pomodoro_running:
            break

        # ── Break phase ────────────────────────────────────────────────────
        _pomodoro_session["phase"] = "break"
        if i < sessions:
            _say(f"Session {i} done. Take a {break_mins}-minute break, Boss.")
            _notify("Friday — Break Time", f"Session {i} complete — {break_mins} min break")
            break_end = time.time() + (break_mins * 60)
            while time.time() < break_end:
                if not _pomodoro_running:
                    return
                time.sleep(5)
        else:
            # Long break after last session
            long_break = break_mins * 3
            _say(f"All {sessions} sessions complete. Outstanding focus, Boss. Take a {long_break}-minute break — you've earned it.")
            _notify("Friday — All Done", f"{sessions} Pomodoros complete! Take {long_break} min.")

    _pomodoro_running = False
    _pomodoro_session = {"count": 0, "phase": None}


def start_pomodoro(work_mins: int = 25, break_mins: int = 5, sessions: int = 4) -> str:
    """Start a Pomodoro timer cycle in the background."""
    global _pomodoro_thread, _pomodoro_running

    if _pomodoro_running:
        return "Pomodoro already running, Boss. Stop it first if you want to restart."

    _pomodoro_running = True
    _pomodoro_thread = threading.Thread(
        target=_pomodoro_loop,
        args=(work_mins, break_mins, sessions),
        daemon=True
    )
    _pomodoro_thread.start()
    return (
        f"Pomodoro started — {sessions} sessions of {work_mins} minutes "
        f"with {break_mins}-minute breaks. Stay locked in, Boss."
    )


def stop_pomodoro() -> str:
    """Stop the running Pomodoro timer."""
    global _pomodoro_running
    if not _pomodoro_running:
        return "No Pomodoro running, Boss."
    _pomodoro_running = False
    _pomodoro_session["phase"] = None
    return "Pomodoro stopped, Boss."


def pomodoro_status() -> str:
    """Check current Pomodoro state."""
    if not _pomodoro_running:
        return "No Pomodoro active, Boss."
    phase = _pomodoro_session.get("phase", "")
    count = _pomodoro_session.get("count", 0)
    if phase == "work":
        return f"Session {count} — work phase active, Boss."
    elif phase == "break":
        return f"Session {count} complete — on break, Boss."
    return "Pomodoro is running, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# FOCUS MODE
# ══════════════════════════════════════════════════════════════════════════════

def focus_mode() -> str:
    """
    Deep focus: close distracting apps, enable Do Not Disturb,
    lower volume, open VS Code.
    """
    distracting_apps = ["Slack", "WhatsApp", "Telegram", "Discord",
                        "Mail", "Messages", "Twitter", "Instagram"]

    closed = []
    for app in distracting_apps:
        result = subprocess.run(
            ["osascript", "-e", f'tell application "{app}" to quit'],
            capture_output=True
        )
        if result.returncode == 0:
            closed.append(app)

    # Enable Do Not Disturb
    subprocess.run([
        "osascript", "-e",
        'tell application "System Events" to tell process "Control Center" to click menu bar item "Control Center" of menu bar 1'
    ], capture_output=True)

    # Set volume low
    subprocess.run(["osascript", "-e", "set volume output volume 20"], capture_output=True)

    # Open VS Code
    subprocess.Popen(["open", "-a", "Visual Studio Code"])

    closed_str = ", ".join(closed) if closed else "none needed closing"
    return f"Focus mode active. Closed: {closed_str}. Volume down to 20. VS Code open, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# MEETING MODE
# ══════════════════════════════════════════════════════════════════════════════

def meeting_mode() -> str:
    """
    Pre-meeting setup: stop music, lower volume, open Calendar, DND on.
    """
    # Stop music
    subprocess.run(
        ["osascript", "-e", 'tell application "Music" to pause'],
        capture_output=True
    )

    # Set volume to a meeting-appropriate level
    subprocess.run(["osascript", "-e", "set volume output volume 35"], capture_output=True)

    # Open Calendar
    subprocess.Popen(["open", "-a", "Calendar"])

    return "Meeting mode on. Music paused, volume at 35, Calendar open, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# END OF DAY SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

def end_of_day_summary() -> str:
    """
    Generate an end-of-day wrap-up:
    - Time now
    - Pomodoro sessions completed today
    - Tomorrow's calendar events
    - Pending reminders
    """
    now = datetime.now()
    lines = [f"End of day wrap-up — {now.strftime('%A %d %B, %I:%M %p')}."]

    # Pomodoro count from this session
    sessions_done = _pomodoro_session.get("count", 0)
    if sessions_done > 0:
        lines.append(f"You completed {sessions_done} Pomodoro session(s) today.")

    # Tomorrow's events
    try:
        from tools.calendar import get_tomorrows_events
        tomorrow = get_tomorrows_events()
        lines.append(f"Tomorrow: {tomorrow}")
    except Exception:
        pass

    # Pending reminders
    try:
        from tools.calendar import get_todays_reminders
        reminders = get_todays_reminders()
        lines.append(f"Pending: {reminders}")
    except Exception:
        pass

    lines.append("That's the day, Boss.")
    return " ".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing Pomodoro (5s work, 3s break, 2 sessions for speed)...")
    # Quick test with very short timers
    _pomodoro_running = True
    _t = threading.Thread(target=_pomodoro_loop, args=(0.1, 0.05, 2), daemon=True)
    _t.start()
    _t.join(timeout=30)
    print("Pomodoro test done.")

    print()
    print("End of day summary:")
    print(end_of_day_summary())
