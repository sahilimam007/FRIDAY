import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import re
import subprocess
from datetime import datetime, timedelta
from config import SAY_VOICE

# ── Active reminders tracker ───────────────────────────────────────────────────
_active_reminders = []

def _parse_time(text: str) -> int | None:
    """
    Parse natural language time into seconds.
    Examples:
    - "20 minutes" → 1200
    - "1 hour" → 3600
    - "30 seconds" → 30
    - "2 hours and 30 minutes" → 9000
    - "half an hour" → 1800
    """
    text = text.lower().strip()
    total_seconds = 0

    # Half an hour
    if "half an hour" in text or "half hour" in text:
        return 1800

    # Hours
    match = re.search(r'(\d+)\s*hour', text)
    if match:
        total_seconds += int(match.group(1)) * 3600

    # Minutes
    match = re.search(r'(\d+)\s*min', text)
    if match:
        total_seconds += int(match.group(1)) * 60

    # Seconds
    match = re.search(r'(\d+)\s*sec', text)
    if match:
        total_seconds += int(match.group(1))

    return total_seconds if total_seconds > 0 else None


def _fire_reminder(message: str):
    """Called when reminder time is up — speaks and shows notification."""
    # macOS notification
    script = f'''
    display notification "{message}" with title "FRIDAY" sound name "Ping"
    '''
    subprocess.run(["osascript", "-e", script])

    # Speak it
    subprocess.run(["say", "-v", SAY_VOICE, f"Boss, reminder: {message} [[slnc 500]]"])


def set_reminder(time_str: str, message: str) -> str:
    """
    Set a reminder.
    time_str: "20 minutes", "1 hour", "30 seconds"
    message: what to remind about
    """
    seconds = _parse_time(time_str)

    if not seconds:
        return "Couldn't understand the time. Try saying '20 minutes' or '1 hour'."

    if not message:
        message = "You set a reminder."

    # Calculate when it fires
    fire_at = datetime.now() + timedelta(seconds=seconds)
    fire_at_str = fire_at.strftime("%I:%M %p")

    # Schedule in background thread
    timer = threading.Timer(seconds, _fire_reminder, args=[message])
    timer.daemon = True
    timer.start()

    _active_reminders.append({
        "message": message,
        "fire_at": fire_at_str,
        "timer": timer
    })

    # Human readable time
    if seconds < 60:
        time_readable = f"{seconds} seconds"
    elif seconds < 3600:
        time_readable = f"{seconds // 60} minutes"
    else:
        hours = seconds // 3600
        mins  = (seconds % 3600) // 60
        time_readable = f"{hours} hour{'s' if hours > 1 else ''}"
        if mins:
            time_readable += f" and {mins} minutes"

    return f"Reminder set for {time_readable} from now at {fire_at_str}. I'll remind you about: {message}."


def list_reminders() -> str:
    """List all active reminders."""
    active = [r for r in _active_reminders if r["timer"].is_alive()]
    if not active:
        return "No active reminders."
    lines = [f"- {r['message']} at {r['fire_at']}" for r in active]
    return "Active reminders:\n" + "\n".join(lines)


def cancel_reminders() -> str:
    """Cancel all active reminders."""
    count = 0
    for r in _active_reminders:
        if r["timer"].is_alive():
            r["timer"].cancel()
            count += 1
    _active_reminders.clear()
    return f"Cancelled {count} reminder{'s' if count != 1 else ''}."


if __name__ == "__main__":
    print(set_reminder("5 seconds", "drink water"))
    print("Waiting for reminder...")
    import time
    time.sleep(7)
