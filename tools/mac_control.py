import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pyautogui
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
        return f"Opening {app_name}, Boss."
    except Exception as e:
        return f"Couldn't open {app_name}, Boss: {e}"

def close_app(app_name):
    script = f'tell application "{app_name}" to quit'
    run_applescript(script)
    return f"Closing {app_name}, Boss."

# ── Volume ─────────────────────────────────────────────────────────────────────

def set_volume(level):
    level = max(0, min(100, int(level)))
    run_applescript(f"set volume output volume {level}")
    return f"Volume set to {level}%, Boss."

def mute():
    run_applescript("set volume output muted true")
    return "Muted, Boss."

def unmute():
    run_applescript("set volume output muted false")
    return "Unmuted, Boss."

def get_volume():
    vol = run_applescript("output volume of (get volume settings)")
    return f"Volume is at {vol}%, Boss."

# ── System ─────────────────────────────────────────────────────────────────────

def take_screenshot(path=None):
    if not path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/Desktop/friday_{timestamp}.png")
    result = subprocess.run(["screencapture", "-x", path])
    if result.returncode == 0:
        return f"Screenshot saved to Desktop as friday_{os.path.basename(path)}, Boss."
    return "Screenshot failed, Boss."

def lock_screen():
    run_applescript('tell application "System Events" to keystroke "q" using {command down, control down}')
    return "Locking the screen, Boss."

def sleep_mac():
    subprocess.run(["pmset", "sleepnow"])
    return "Putting the Mac to sleep, Boss."

def get_battery():
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
    for line in result.stdout.strip().split("\n"):
        if "%" in line:
            return f"Battery status: {line.strip()}, Boss."
    return "Couldn't read battery status, Boss."

def type_text(text):
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed: {text}"

def press_key(key):
    pyautogui.press(key)
    return f"Pressed {key}, Boss."

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
        return f"Not in your library, Boss. Opened Apple Music search for {song_name}."
    return f"Now playing {result}, Boss."

def pause_music():
    run_applescript('tell application "Music" to pause')
    return "Music paused, Boss."

def resume_music():
    run_applescript('tell application "Music" to play')
    return "Music resumed, Boss."

def next_track():
    run_applescript('tell application "Music" to next track')
    track = run_applescript('tell application "Music" to get name of current track')
    return f"Skipped. Now playing {track}, Boss."

def previous_track():
    run_applescript('tell application "Music" to previous track')
    track = run_applescript('tell application "Music" to get name of current track')
    return f"Going back. Now playing {track}, Boss."

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
        return "Nothing is playing right now, Boss."
    return f"Currently playing {result}, Boss."

def set_music_volume(level: int):
    level = max(0, min(100, level))
    run_applescript(f'tell application "Music" to set sound volume to {level}')
    return f"Music volume set to {level}%, Boss."

if __name__ == "__main__":
    print(get_battery())
    print(get_volume())
    print(get_current_track())