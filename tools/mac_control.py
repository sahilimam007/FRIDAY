import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pyautogui
import config

def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def open_app(app_name):
    try:
        subprocess.Popen(["open", "-a", app_name])
        return f"Opening {app_name}, Sir."
    except Exception as e:
        return f"Couldn't open {app_name}, Sir: {e}"

def close_app(app_name):
    script = f'tell application "{app_name}" to quit'
    run_applescript(script)
    return f"Closing {app_name}, Sir."

def set_volume(level):
    """level: 0-100"""
    level = max(0, min(100, int(level)))
    script = f"set volume output volume {level}"
    run_applescript(script)
    return f"Volume set to {level}%, Sir."

def mute():
    run_applescript("set volume output muted true")
    return "Muted, Sir."

def unmute():
    run_applescript("set volume output muted false")
    return "Unmuted, Sir."

def get_volume():
    script = "output volume of (get volume settings)"
    vol = run_applescript(script)
    return f"Volume is at {vol}%, Sir."

def take_screenshot(path=None):
    if not path:
        path = os.path.expanduser("~/Desktop/jarvis_screenshot.png")
    subprocess.run(["screencapture", "-x", path])
    return f"Screenshot saved to {path}, Sir."

def lock_screen():
    script = 'tell application "System Events" to keystroke "q" using {command down, control down}'
    run_applescript(script)
    return "Locking the screen, Sir."

def sleep_mac():
    subprocess.run(["pmset", "sleepnow"])
    return "Putting the Mac to sleep, Sir."

def get_battery():
    result = subprocess.run(
        ["pmset", "-g", "batt"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if "%" in line:
            return f"Battery status: {line.strip()}, Sir."
    return "Couldn't read battery status, Sir."

def type_text(text):
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed: {text}"

def press_key(key):
    pyautogui.press(key)
    return f"Pressed {key}, Sir."

if __name__ == "__main__":
    print(get_battery())
    print(get_volume())
    print(open_app("Calculator"))
    