import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pyautogui
import re
import math
import config
from datetime import datetime

def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    return result.stdout.strip()

# ── App control ────────────────────────────────────────────────────────────────

def open_app(app_name):
    try:
        subprocess.Popen(["open", "-a", app_name])
        return f"Opening {app_name}."
    except Exception as e:
        return f"Couldn't open {app_name}: {e}"

def close_app(app_name):
    run_applescript(f'tell application "{app_name}" to quit')
    return f"Closing {app_name}."

def minimize_window(app_name: str = ""):
    if app_name:
        script = f'tell application "{app_name}" to set miniaturized of window 1 to true'
    else:
        script = 'tell application "System Events" to keystroke "m" using command down'
    run_applescript(script)
    return "Window minimized."

def hide_app(app_name: str = ""):
    if app_name:
        script = f'tell application "System Events" to set visible of process "{app_name}" to false'
    else:
        script = 'tell application "System Events" to keystroke "h" using command down'
    run_applescript(script)
    return "App hidden."

def picture_in_picture():
    script = '''
    tell application "Brave Browser"
        activate
    end tell
    delay 0.5
    tell application "System Events"
        keystroke "p" using {command down, shift down}
    end tell
    '''
    run_applescript(script)
    return "Picture-in-picture enabled."

# ── Volume ─────────────────────────────────────────────────────────────────────

def set_volume(level):
    level = max(0, min(100, int(level)))
    run_applescript(f"set volume output volume {level}")
    return f"Volume set to {level}%."

def mute():
    run_applescript("set volume output muted true")
    return "Muted."

def unmute():
    run_applescript("set volume output muted false")
    return "Unmuted."

def get_volume():
    vol = run_applescript("output volume of (get volume settings)")
    return f"Volume is at {vol}%."

# ── System ─────────────────────────────────────────────────────────────────────

def take_screenshot(path=None):
    if not path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/Desktop/friday_{timestamp}.png")
    result = subprocess.run(["screencapture", "-x", path])
    if result.returncode == 0:
        return f"Screenshot saved to Desktop as friday_{os.path.basename(path)}."
    return "Screenshot failed."

def lock_screen():
    run_applescript('tell application "System Events" to keystroke "q" using {command down, control down}')
    return "Locking the screen."

def sleep_mac():
    subprocess.run(["pmset", "sleepnow"])
    return "Putting the Mac to sleep."

def get_battery():
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    for line in result.stdout.strip().split("\n"):
        if "%" in line:
            return f"Battery status: {line.strip()}."
    return "Couldn't read battery status."

def get_system_info():
    """Get RAM, CPU, and storage info."""
    lines = []

    # RAM
    try:
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
        pages_free    = int(re.search(r'Pages free:\s+(\d+)', vm).group(1))
        pages_active  = int(re.search(r'Pages active:\s+(\d+)', vm).group(1))
        pages_inactive= int(re.search(r'Pages inactive:\s+(\d+)', vm).group(1))
        pages_wired   = int(re.search(r'Pages wired down:\s+(\d+)', vm).group(1))
        page_size     = 4096
        used_gb  = round((pages_active + pages_wired) * page_size / 1e9, 1)
        free_gb  = round((pages_free + pages_inactive) * page_size / 1e9, 1)
        lines.append(f"RAM: {used_gb}GB used, {free_gb}GB free.")
    except:
        lines.append("RAM info unavailable.")

    # Storage
    try:
        df = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.split("\n")
        parts = df[1].split()
        lines.append(f"Storage: {parts[3]} free of {parts[1]}.")
    except:
        lines.append("Storage info unavailable.")

    # CPU
    try:
        cpu = subprocess.run(
            ["top", "-l", "1", "-n", "0"],
            capture_output=True, text=True
        ).stdout
        match = re.search(r'CPU usage: ([\d.]+)% user', cpu)
        if match:
            lines.append(f"CPU usage: {match.group(1)}%.")
    except:
        pass

    return " ".join(lines)

def type_text(text):
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed: {text}"

def press_key(key):
    pyautogui.press(key)
    return f"Pressed {key}."

# ── Calculator ────────────────────────────────────────────────────────────────

def calculate(expression: str) -> str:
    """Evaluate a math expression including percent calculations."""
    try:
        expr = expression.lower().strip()
        # Handle "X percent of Y"
        expr = expr.replace('percent of', '* 0.01 *')
        # Handle "X% of Y"
        expr = expr.replace('% of', '* 0.01 *')
        # Handle "X%"
        expr = expr.replace('%', '* 0.01')
        # Clean up
        expr = expr.replace('x', '*').replace('×', '*').replace('÷', '/')
        result = eval(expr)
        # Clean result
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"The answer is {result}, Boss."
    except Exception as e:
        return f"Couldn't calculate that, Boss: {e}"

# ── Clipboard ─────────────────────────────────────────────────────────────────

def get_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    text = result.stdout.strip()
    if text:
        return f"Clipboard contains: {text[:200]}"
    return "Clipboard is empty."

def set_clipboard(text: str) -> str:
    subprocess.run(["pbcopy"], input=text.encode())
    return f"Copied to clipboard."

# ── Modes ─────────────────────────────────────────────────────────────────────

def focus_mode() -> str:
    """Close distracting apps, set low volume."""
    for app in ["Brave Browser", "Music", "Spotify"]:
        try:
            run_applescript(f'tell application "{app}" to quit')
        except:
            pass
    set_volume(20)
    return "Focus mode activated. Distractions cleared, volume lowered."

def vibe_mode() -> str:
    """Open Spotify, set good volume."""
    subprocess.Popen(["open", "-a", "Music"])
    set_volume(60)
    return "Vibe mode activated. Music is up."

def night_mode() -> str:
    """Lower volume, dim screen."""
    set_volume(10)
    run_applescript('tell application "System Events" to key code 145')
    return "Night mode activated. Volume lowered."

# ── Apple Music control ────────────────────────────────────────────────────────

def play_song(song_name: str):
    script = f'''
    tell application "Music"
        activate
        set searchResults to search playlist "Library" for "{song_name}"
        if (count of searchResults) > 0 then
            play first item of searchResults
            set t to name of current track
            set a to artist of current track
            return t & " by " & a
        else
            return "not found"
        end if
    end tell
    '''
    result = run_applescript(script)
    if result == "not found" or result == "":
        query = song_name.replace(" ", "+")
        subprocess.Popen(["open", f"https://music.apple.com/search?term={query}"])
        return f"Not in your library. Opened Apple Music search for {song_name}."
    return f"Now playing {result}."

def pause_music():
    run_applescript('tell application "Music" to pause')
    return "Music paused."

def resume_music():
    run_applescript('tell application "Music" to play')
    return "Music resumed."

def next_track():
    run_applescript('tell application "Music" to next track')
    track = run_applescript('tell application "Music" to get name of current track')
    return f"Skipped. Now playing {track}."

def previous_track():
    run_applescript('tell application "Music" to previous track')
    track = run_applescript('tell application "Music" to get name of current track')
    return f"Going back. Now playing {track}."

def get_current_track():
    script = '''
    tell application "Music"
        if player state is playing then
            return name of current track & " by " & artist of current track
        else
            return "nothing"
        end if
    end tell
    '''
    result = run_applescript(script)
    if result == "nothing" or result == "":
        return "Nothing is playing right now."
    return f"Currently playing {result}."

def set_music_volume(level: int):
    level = max(0, min(100, level))
    run_applescript(f'tell application "Music" to set sound volume to {level}')
    return f"Music volume set to {level}%."

if __name__ == "__main__":
    print(get_battery())
    print(get_system_info())
    print(calculate("15% of 8500"))
