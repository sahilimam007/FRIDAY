import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pyautogui
import json
import math
import time
import threading
import config

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
    run_applescript(f'tell application "{app_name}" to quit')
    return f"Closing {app_name}, Boss."

def minimize_window():
    run_applescript('tell application "System Events" to keystroke "m" using command down')
    return "Minimized, Boss."

def hide_app():
    run_applescript('tell application "System Events" to keystroke "h" using command down')
    return "Hidden, Boss."

def show_desktop():
    run_applescript('tell application "System Events" to key code 103 using {command down}')
    return "Showing desktop, Boss."

def empty_trash():
    run_applescript('tell application "Finder" to empty trash')
    return "Trash emptied, Boss."

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
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/Desktop/friday_{ts}.png")
    subprocess.run(["screencapture", "-x", path])
    return f"Screenshot saved to Desktop, Boss."

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
            return f"Battery: {line.strip()}, Boss."
    return "Couldn't read battery status, Boss."

def get_system_info():
    try:
        # RAM
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
        pages_free    = int([l for l in vm.split("\n") if "Pages free" in l][0].split(":")[1].strip().rstrip("."))
        pages_active  = int([l for l in vm.split("\n") if "Pages active" in l][0].split(":")[1].strip().rstrip("."))
        pages_wired   = int([l for l in vm.split("\n") if "Pages wired" in l][0].split(":")[1].strip().rstrip("."))
        page_size     = 16384
        used_gb  = round((pages_active + pages_wired) * page_size / (1024**3), 1)
        free_gb  = round(pages_free * page_size / (1024**3), 1)
        # Disk
        df = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.split("\n")[1].split()
        disk_used = df[2]
        disk_free = df[3]
        # CPU
        cpu = subprocess.run(["top", "-l", "1", "-n", "0"], capture_output=True, text=True).stdout
        cpu_line = [l for l in cpu.split("\n") if "CPU usage" in l]
        cpu_info = cpu_line[0] if cpu_line else "CPU info unavailable"
        return f"RAM: {used_gb}GB used, {free_gb}GB free. Disk: {disk_used} used, {disk_free} free. {cpu_info}, Boss."
    except Exception as e:
        return f"Couldn't get system info, Boss: {e}"

def get_ip():
    try:
        result = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True)
        ip = result.stdout.strip()
        if not ip:
            result = subprocess.run(["ipconfig", "getifaddr", "en1"], capture_output=True, text=True)
            ip = result.stdout.strip()
        return f"Your local IP is {ip}, Boss."
    except:
        return "Couldn't get IP address, Boss."

# ── Wi-Fi & Bluetooth ──────────────────────────────────────────────────────────

def wifi_on():
    subprocess.run(["networksetup", "-setairportpower", "en0", "on"])
    return "Wi-Fi turned on, Boss."

def wifi_off():
    subprocess.run(["networksetup", "-setairportpower", "en0", "off"])
    return "Wi-Fi turned off, Boss."

def bluetooth_on():
    run_applescript('do shell script "blueutil --power 1"')
    return "Bluetooth turned on, Boss."

def bluetooth_off():
    run_applescript('do shell script "blueutil --power 0"')
    return "Bluetooth turned off, Boss."

# ── Do Not Disturb ─────────────────────────────────────────────────────────────

def do_not_disturb_on():
    script = '''
    tell application "System Events"
        tell process "Control Center"
            click menu bar item "Control Center" of menu bar 1
        end tell
    end tell
    '''
    run_applescript(script)
    return "Do Not Disturb enabled, Boss."

def do_not_disturb_off():
    return "Do Not Disturb disabled, Boss."

# ── Clipboard ─────────────────────────────────────────────────────────────────

def get_clipboard():
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    content = result.stdout.strip()
    if not content:
        return "Clipboard is empty, Boss."
    return f"Clipboard contains: {content[:200]}"

def set_clipboard(text: str):
    subprocess.run(["pbcopy"], input=text.encode())
    return f"Copied to clipboard, Boss."

def type_text(text):
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed: {text}"

def press_key(key):
    pyautogui.press(key)
    return f"Pressed {key}, Boss."

# ── Apple Music ────────────────────────────────────────────────────────────────

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

# ── Calculator ────────────────────────────────────────────────────────────────

def calculate(expression: str) -> str:
    try:
        expr = expression.lower().strip()
        expr = expr.replace('percent of', '* 0.01 *')
        expr = expr.replace('% of', '* 0.01 *')
        expr = expr.replace('%', '* 0.01')
        expr = expr.replace('x', '*').replace('×', '*').replace('÷', '/')
        expr = expr.replace('plus', '+').replace('minus', '-')
        expr = expr.replace('times', '*').replace('divided by', '/')
        expr = expr.replace('squared', '**2').replace('cubed', '**3')
        result = eval(expr, {"__builtins__": {}}, {"sqrt": math.sqrt, "pi": math.pi})
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        return f"The answer is {result}, Boss."
    except Exception as e:
        return f"Couldn't calculate that, Boss: {e}"

# ── Unit converter ────────────────────────────────────────────────────────────

def convert_units(expression: str) -> str:
    try:
        expr = expression.lower()
        conversions = {
            ("miles", "km"):        lambda x: x * 1.60934,
            ("km", "miles"):        lambda x: x * 0.621371,
            ("kg", "pounds"):       lambda x: x * 2.20462,
            ("pounds", "kg"):       lambda x: x * 0.453592,
            ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
            ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
            ("meters", "feet"):     lambda x: x * 3.28084,
            ("feet", "meters"):     lambda x: x * 0.3048,
            ("liters", "gallons"):  lambda x: x * 0.264172,
            ("gallons", "liters"):  lambda x: x * 3.78541,
            ("inches", "cm"):       lambda x: x * 2.54,
            ("cm", "inches"):       lambda x: x * 0.393701,
        }
        import re
        match = re.search(r'([\d.]+)', expr)
        if not match:
            return "Couldn't find a number to convert, Boss."
        value = float(match.group(1))
        for (from_u, to_u), fn in conversions.items():
            if from_u in expr and to_u in expr:
                result = round(fn(value), 4)
                return f"{value} {from_u} = {result} {to_u}, Boss."
        return "Conversion not recognised, Boss."
    except Exception as e:
        return f"Conversion failed, Boss: {e}"

# ── Currency converter ────────────────────────────────────────────────────────

def convert_currency(expression: str) -> str:
    try:
        import re, requests
        match = re.search(r'([\d.]+)', expression)
        if not match:
            return "Couldn't find an amount, Boss."
        amount = float(match.group(1))
        expr = expression.lower()
        currencies = {
            "dollar": "USD", "dollars": "USD", "usd": "USD",
            "euro": "EUR", "euros": "EUR", "eur": "EUR",
            "pound": "GBP", "pounds": "GBP", "gbp": "GBP",
            "rupee": "INR", "rupees": "INR", "inr": "INR",
            "yen": "JPY", "jpy": "JPY",
            "yuan": "CNY", "cny": "CNY",
        }
        from_cur = to_cur = None
        words = expr.split()
        found = []
        for word in words:
            if word in currencies:
                found.append(currencies[word])
        if len(found) >= 2:
            from_cur, to_cur = found[0], found[1]
        else:
            return "Couldn't understand the currencies, Boss."
        url = f"https://open.er-api.com/v6/latest/{from_cur}"
        resp = requests.get(url, timeout=5).json()
        rate = resp["rates"][to_cur]
        result = round(amount * rate, 2)
        return f"{amount} {from_cur} = {result} {to_cur}, Boss."
    except Exception as e:
        return f"Currency conversion failed, Boss: {e}"

# ── Timer & Stopwatch ─────────────────────────────────────────────────────────

_stopwatch_start = None

def start_stopwatch():
    global _stopwatch_start
    _stopwatch_start = time.time()
    return "Stopwatch started, Boss."

def stop_stopwatch():
    global _stopwatch_start
    if _stopwatch_start is None:
        return "No stopwatch running, Boss."
    elapsed = time.time() - _stopwatch_start
    _stopwatch_start = None
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    return f"Stopwatch stopped. Elapsed: {mins}m {secs}s, Boss."

def set_timer(duration_str: str, label: str = "Timer") -> str:
    import re
    total_seconds = 0
    patterns = [
        (r'(\d+)\s*hour', 3600),
        (r'(\d+)\s*minute', 60),
        (r'(\d+)\s*second', 1),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, duration_str.lower())
        if match:
            total_seconds += int(match.group(1)) * multiplier
    if total_seconds == 0:
        match = re.search(r'(\d+)', duration_str)
        if match:
            total_seconds = int(match.group(1)) * 60
    if total_seconds == 0:
        return "Couldn't understand the duration, Boss."

    def fire():
        time.sleep(total_seconds)
        subprocess.run(["osascript", "-e",
            f'display notification "{label}" with title "FRIDAY" sound name "Glass"'])
        subprocess.Popen(["say", "-v", "Samantha", f"Boss, your timer is done. {label}. [[slnc 1000]]"])

    threading.Thread(target=fire, daemon=True).start()
    mins = total_seconds // 60
    secs = total_seconds % 60
    time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
    return f"Timer set for {time_str}, Boss."

# ── Pomodoro ──────────────────────────────────────────────────────────────────

def start_pomodoro():
    def run():
        subprocess.Popen(["say", "-v", "Samantha", "Pomodoro started. 25 minutes of focus, Boss. [[slnc 1000]]"])
        time.sleep(25 * 60)
        subprocess.run(["osascript", "-e",
            'display notification "Take a 5 minute break!" with title "FRIDAY" sound name "Glass"'])
        subprocess.Popen(["say", "-v", "Samantha", "Pomodoro complete, Boss. Take a 5 minute break. [[slnc 1000]]"])
    threading.Thread(target=run, daemon=True).start()
    return "Pomodoro started. 25 minutes on the clock, Boss."

# ── Focus / Vibe / Night modes ────────────────────────────────────────────────

def focus_mode():
    run_applescript('tell application "Music" to pause')
    run_applescript("set volume output volume 30")
    return "Focus mode on. Music paused, volume lowered, Boss."

def vibe_mode():
    run_applescript('tell application "Music" to play')
    run_applescript("set volume output volume 60")
    return "Vibe mode on. Music playing, volume set to 60, Boss."

def night_mode():
    run_applescript("set volume output volume 20")
    subprocess.run(["brightness", "0.1"], capture_output=True)
    return "Night mode on. Volume lowered, Boss."

# ── Notes ─────────────────────────────────────────────────────────────────────

NOTES_PATH = os.path.expanduser("~/Developer/friday/memory/notes.txt")

def take_note(note: str) -> str:
    ts = time.strftime("%Y-%m-%d %H:%M")
    with open(NOTES_PATH, "a") as f:
        f.write(f"[{ts}] {note}\n")
    return f"Note saved, Boss."

def read_notes() -> str:
    if not os.path.exists(NOTES_PATH):
        return "No notes yet, Boss."
    with open(NOTES_PATH, "r") as f:
        content = f.read().strip()
    if not content:
        return "No notes yet, Boss."
    lines = content.split("\n")[-5:]
    return "Your last notes: " + ". ".join(lines)

# ── File finder ───────────────────────────────────────────────────────────────

def find_file(filename: str) -> str:
    try:
        result = subprocess.run(
            ["mdfind", "-name", filename],
            capture_output=True, text=True, timeout=10
        )
        paths = result.stdout.strip().split("\n")
        paths = [p for p in paths if p and ".Trash" not in p][:5]
        if not paths:
            return f"Couldn't find any file named {filename}, Boss."
        return f"Found {len(paths)} file(s): " + ", ".join(paths)
    except Exception as e:
        return f"File search failed, Boss: {e}"

# ── Developer tools ───────────────────────────────────────────────────────────

def git_status(path: str = None) -> str:
    try:
        cwd = path or os.path.expanduser("~/Developer")
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=cwd
        )
        if result.returncode != 0:
            return "Not a git repo or git error, Boss."
        output = result.stdout.strip()
        if not output:
            return "All clean — nothing to commit, Boss."
        return f"Git status: {output}"
    except Exception as e:
        return f"Git status failed, Boss: {e}"

def run_terminal_command(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=15
        )
        output = (result.stdout + result.stderr).strip()
        return output[:300] if output else "Command ran with no output, Boss."
    except subprocess.TimeoutExpired:
        return "Command timed out, Boss."
    except Exception as e:
        return f"Command failed, Boss: {e}"

def open_vscode_project(project: str) -> str:
    path = os.path.expanduser(f"~/Developer/{project}")
    if not os.path.exists(path):
        path = os.path.expanduser(f"~/{project}")
    if os.path.exists(path):
        subprocess.Popen(["code", path])
        return f"Opening {project} in VS Code, Boss."
    return f"Couldn't find project {project}, Boss."

def kill_port(port: str) -> str:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split("\n")
        pids = [p for p in pids if p]
        if not pids:
            return f"Nothing running on port {port}, Boss."
        for pid in pids:
            subprocess.run(["kill", "-9", pid])
        return f"Killed process on port {port}, Boss."
    except Exception as e:
        return f"Couldn't kill port {port}, Boss: {e}"

def check_server(port: str = "8000") -> str:
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip()
        if pids:
            return f"Yes, something is running on port {port}, Boss."
        return f"Nothing running on port {port}, Boss."
    except Exception as e:
        return f"Couldn't check port, Boss: {e}"

# ── WhatsApp ──────────────────────────────────────────────────────────────────

def open_whatsapp_chat(contact: str = "") -> str:
    subprocess.Popen(["open", "-a", "WhatsApp"])
    return f"Opening WhatsApp, Boss. You'll need to select {contact} manually."

# ── Picture in picture ────────────────────────────────────────────────────────

def picture_in_picture():
    run_applescript('''
    tell application "System Events"
        keystroke "p" using {option down, command down}
    end tell
    ''')
    return "Picture in picture toggled, Boss."

if __name__ == "__main__":
    print(get_battery())
    print(get_system_info())
    print(calculate("15 percent of 8500"))
    print(convert_units("5 miles to km"))
    print(find_file("resume"))
    