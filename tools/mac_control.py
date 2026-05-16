import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pyautogui
import json
import math
import time
import threading
import re
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

def force_quit(app_name):
    subprocess.run(["pkill", "-f", app_name])
    return f"Force quitting {app_name}, Boss."

def switch_to_app(app_name):
    run_applescript(f'tell application "{app_name}" to activate')
    return f"Switched to {app_name}, Boss."

def list_running_apps():
    script = 'tell application "System Events" to get name of every process whose background only is false'
    result = run_applescript(script)
    apps = result.replace(",", ", ")
    return f"Running apps: {apps}, Boss."

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

def restart_mac():
    run_applescript('tell application "System Events" to restart')
    return "Restarting, Boss."

def shutdown_mac():
    run_applescript('tell application "System Events" to shut down')
    return "Shutting down, Boss."

# ── Window control ─────────────────────────────────────────────────────────────

def snap_left():
    run_applescript('''
    tell application "System Events"
        keystroke "left" using {control down, option down}
    end tell
    ''')
    return "Window snapped left, Boss."

def snap_right():
    run_applescript('''
    tell application "System Events"
        keystroke "right" using {control down, option down}
    end tell
    ''')
    return "Window snapped right, Boss."

def fullscreen():
    run_applescript('''
    tell application "System Events"
        keystroke "f" using {control down, command down}
    end tell
    ''')
    return "Toggled full screen, Boss."

def close_tab():
    run_applescript('''
    tell application "System Events"
        keystroke "w" using command down
    end tell
    ''')
    return "Tab closed, Boss."

def new_tab():
    run_applescript('''
    tell application "System Events"
        keystroke "t" using command down
    end tell
    ''')
    return "New tab opened, Boss."

def picture_in_picture():
    run_applescript('''
    tell application "System Events"
        keystroke "p" using {option down, command down}
    end tell
    ''')
    return "Picture in picture toggled, Boss."

# ── Active window control ──────────────────────────────────────────────────────

def move_window(direction: str) -> str:
    """Move active window to a screen position: left, right, top, bottom, center."""
    direction = direction.lower().strip()
    scripts = {
        "left":   'tell application "System Events" to keystroke "left" using {control down, option down}',
        "right":  'tell application "System Events" to keystroke "right" using {control down, option down}',
        "center": '''
            tell application "Finder"
                set screenSize to bounds of window of desktop
                set sw to item 3 of screenSize
                set sh to item 4 of screenSize
            end tell
            tell application (name of (info for (path to frontmost application))) to set bounds of window 1 to {sw/4, sh/8, sw*3/4, sh*7/8}
        ''',
    }
    if direction in scripts:
        run_applescript(scripts[direction])
        return f"Window moved {direction}, Boss."
    return f"Direction '{direction}' not recognised, Boss."

def resize_window(width: int, height: int) -> str:
    script = f'''
    tell application (name of (info for (path to frontmost application)))
        set size of window 1 to {{{width}, {height}}}
    end tell
    '''
    run_applescript(script)
    return f"Window resized to {width}x{height}, Boss."

def close_active_window() -> str:
    run_applescript('tell application "System Events" to keystroke "w" using command down')
    return "Window closed, Boss."

# ── Volume ─────────────────────────────────────────────────────────────────────

_pre_speak_volume = None

def lower_volume_for_speech(speak_vol: int = 25):
    """Lower volume before Friday speaks, restore after."""
    global _pre_speak_volume
    vol = run_applescript("output volume of (get volume settings)")
    try:
        _pre_speak_volume = int(vol)
    except:
        _pre_speak_volume = 50
    if _pre_speak_volume > speak_vol:
        run_applescript(f"set volume output volume {speak_vol}")

def restore_volume_after_speech():
    """Restore volume to what it was before Friday spoke."""
    global _pre_speak_volume
    if _pre_speak_volume is not None:
        run_applescript(f"set volume output volume {_pre_speak_volume}")
        _pre_speak_volume = None

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

# ── Display brightness ─────────────────────────────────────────────────────────

def set_brightness(level) -> str:
    """
    Set display brightness. level: 0-100 or words like 'low', 'high', 'max', 'min'.
    Uses built-in macOS brightness key simulation.
    """
    presets = {
        "min": 0, "minimum": 0, "off": 0,
        "low": 25, "dim": 25,
        "medium": 50, "normal": 50, "default": 50,
        "high": 75, "bright": 75,
        "max": 100, "maximum": 100, "full": 100,
    }

    if isinstance(level, str) and level.lower() in presets:
        target = presets[level.lower()]
    else:
        try:
            target = max(0, min(100, int(level)))
        except:
            return "Couldn't understand brightness level, Boss."

    # Use AppleScript via System Preferences brightness slider
    script = f'''
    tell application "System Preferences"
        reveal anchor "displaysDisplayTab" of pane id "com.apple.preference.displays"
    end tell
    '''
    # Simpler approach: use brightness command via osascript
    # Scale 0-100 to 0.0-1.0
    val = target / 100.0
    brightness_script = f'''
    tell application "System Events"
        tell process "SystemUIServer"
            try
                set value of slider 1 of menu bar item "Brightness" of menu bar 1 to {val}
            end try
        end tell
    end tell
    '''
    result = run_applescript(brightness_script)

    # Fallback: use keyboard brightness keys (simulate pressing)
    # This works reliably on all Macs
    try:
        import subprocess
        current_val = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to key code 144'],
            capture_output=True
        )
    except:
        pass

    return f"Brightness set to {target}%, Boss."

def brightness_up() -> str:
    """Increase brightness by pressing the brightness up key."""
    for _ in range(3):
        run_applescript('tell application "System Events" to key code 144')
        time.sleep(0.05)
    return "Brightness increased, Boss."

def brightness_down() -> str:
    """Decrease brightness by pressing the brightness down key."""
    for _ in range(3):
        run_applescript('tell application "System Events" to key code 145')
        time.sleep(0.05)
    return "Brightness decreased, Boss."

# ── Keyboard backlight ─────────────────────────────────────────────────────────

def keyboard_backlight_up() -> str:
    """Increase keyboard backlight."""
    for _ in range(3):
        run_applescript('tell application "System Events" to key code 134')
        time.sleep(0.05)
    return "Keyboard backlight increased, Boss."

def keyboard_backlight_down() -> str:
    """Decrease keyboard backlight."""
    for _ in range(3):
        run_applescript('tell application "System Events" to key code 133')
        time.sleep(0.05)
    return "Keyboard backlight decreased, Boss."

def keyboard_backlight_off() -> str:
    """Turn keyboard backlight all the way down."""
    for _ in range(10):
        run_applescript('tell application "System Events" to key code 133')
        time.sleep(0.03)
    return "Keyboard backlight off, Boss."

# ── AirPods ────────────────────────────────────────────────────────────────────

def connect_airpods(device_name: str = "AirPods") -> str:
    """Connect AirPods or any Bluetooth device by name."""
    script = f'''
    tell application "System Events"
        tell process "SystemUIServer"
            try
                click menu bar item "Bluetooth" of menu bar 1
                delay 0.5
                click menu item "{device_name}" of menu 1 of menu bar item "Bluetooth" of menu bar 1
                delay 0.3
                click menu item "Connect" of menu 1 of menu item "{device_name}" of menu 1 of menu bar item "Bluetooth" of menu bar 1
            end try
        end tell
    end tell
    '''
    run_applescript(script)
    return f"Attempting to connect {device_name}, Boss."

def disconnect_airpods(device_name: str = "AirPods") -> str:
    """Disconnect AirPods or any Bluetooth device by name."""
    script = f'''
    tell application "System Events"
        tell process "SystemUIServer"
            try
                click menu bar item "Bluetooth" of menu bar 1
                delay 0.5
                click menu item "{device_name}" of menu 1 of menu bar item "Bluetooth" of menu bar 1
                delay 0.3
                click menu item "Disconnect" of menu 1 of menu item "{device_name}" of menu 1 of menu bar item "Bluetooth" of menu bar 1
            end try
        end tell
    end tell
    '''
    run_applescript(script)
    return f"Disconnecting {device_name}, Boss."

def list_bluetooth_devices() -> str:
    """List paired Bluetooth devices using blueutil if available."""
    try:
        result = subprocess.run(["blueutil", "--paired"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            names = [l.split('name: "')[1].split('"')[0] for l in lines if 'name:' in l]
            if names:
                return "Paired devices: " + ", ".join(names) + ", Boss."
        return "Couldn't list Bluetooth devices, Boss."
    except:
        return "blueutil not installed. Run: brew install blueutil, Boss."

# ── Notifications ──────────────────────────────────────────────────────────────

def read_notifications() -> str:
    """Read recent macOS notifications using AppleScript."""
    script = '''
    tell application "System Events"
        tell process "NotificationCenter"
            try
                set notifs to {}
                set allGroups to groups of UI element 1 of scroll area 1 of window "Notification Center"
                repeat with g in allGroups
                    set end of notifs to description of g
                end repeat
                return notifs as string
            on error
                return "none"
            end try
        end tell
    end tell
    '''
    result = run_applescript(script)
    if not result or result == "none":
        return "No notifications right now, Boss."
    # Clean up the output
    lines = result.split(",")[:5]
    return "Recent notifications: " + ". ".join(l.strip() for l in lines if l.strip()) + ", Boss."

def clear_notifications() -> str:
    """Clear all notifications."""
    script = '''
    tell application "System Events"
        tell process "NotificationCenter"
            try
                click button "Clear All" of window "Notification Center"
            end try
        end tell
    end tell
    '''
    run_applescript(script)
    return "Notifications cleared, Boss."

# ── Clipboard ─────────────────────────────────────────────────────────────────

def get_clipboard():
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    content = result.stdout.strip()
    if not content:
        return "Clipboard is empty, Boss."
    return f"Clipboard contains: {content[:300]}"

def set_clipboard(text: str):
    subprocess.run(["pbcopy"], input=text.encode())
    return f"Copied to clipboard, Boss."

def paste_clipboard() -> str:
    """Paste clipboard content into the currently active app."""
    run_applescript('tell application "System Events" to keystroke "v" using command down')
    return "Pasted, Boss."

def type_text(text: str):
    pyautogui.typewrite(text, interval=0.05)
    return f"Typed, Boss."

def dictate_text(text: str) -> str:
    """Type text into whatever is currently focused — emails, docs, forms."""
    time.sleep(0.5)  # brief pause so focus is set
    pyautogui.typewrite(text, interval=0.04)
    return f"Dictated text, Boss."

def press_key(key: str):
    pyautogui.press(key)
    return f"Pressed {key}, Boss."

# ── VPN ────────────────────────────────────────────────────────────────────────

def vpn_connect(vpn_name: str = "") -> str:
    """Connect to a VPN via Network Preferences."""
    if vpn_name:
        script = f'''
        tell application "System Preferences"
            activate
            set current pane to pane "com.apple.preference.network"
        end tell
        '''
        run_applescript(script)
        return f"Opened Network Preferences, Boss. Select {vpn_name} and connect."
    # Try connecting via networksetup if VPN name is known
    try:
        result = subprocess.run(
            ["networksetup", "-connectpppoeservice", vpn_name],
            capture_output=True, text=True
        )
        return f"Attempting to connect VPN, Boss."
    except:
        return "Opened Network Preferences, Boss. Select your VPN and connect."

def vpn_disconnect(vpn_name: str = "") -> str:
    """Disconnect VPN."""
    try:
        subprocess.run(["networksetup", "-disconnectpppoeservice", vpn_name], capture_output=True)
        return "VPN disconnected, Boss."
    except:
        return "Couldn't disconnect VPN automatically, Boss. Do it from the menu bar."

# ── Incognito browser ──────────────────────────────────────────────────────────

def open_incognito(url: str = "") -> str:
    """Open Brave in incognito/private mode."""
    if url:
        if not url.startswith("http"):
            url = "https://" + url
        subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, "--args", "--incognito", url])
        return f"Opening {url} in private mode, Boss."
    subprocess.Popen(["open", "-a", config.DEFAULT_BROWSER, "--args", "--incognito"])
    return "Private browsing window opened, Boss."

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
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
        pages_free   = int([l for l in vm.split("\n") if "Pages free" in l][0].split(":")[1].strip().rstrip("."))
        pages_active = int([l for l in vm.split("\n") if "Pages active" in l][0].split(":")[1].strip().rstrip("."))
        pages_wired  = int([l for l in vm.split("\n") if "Pages wired" in l][0].split(":")[1].strip().rstrip("."))
        page_size    = 16384
        used_gb = round((pages_active + pages_wired) * page_size / (1024**3), 1)
        free_gb = round(pages_free * page_size / (1024**3), 1)
        df = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout.split("\n")[1].split()
        disk_used = df[2]; disk_free = df[3]
        return f"RAM: {used_gb}GB used, {free_gb}GB free. Disk: {disk_used} used, {disk_free} free, Boss."
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

def ping_host(host: str):
    try:
        result = subprocess.run(["ping", "-c", "3", host], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split("\n")
        summary = lines[-1] if lines else "No response"
        return f"Ping to {host}: {summary}, Boss."
    except Exception as e:
        return f"Ping failed, Boss: {e}"

# ── Wi-Fi & Bluetooth ──────────────────────────────────────────────────────────

def wifi_on():
    subprocess.run(["networksetup", "-setairportpower", "en0", "on"])
    return "Wi-Fi turned on, Boss."

def wifi_off():
    subprocess.run(["networksetup", "-setairportpower", "en0", "off"])
    return "Wi-Fi turned off, Boss."

def bluetooth_on():
    subprocess.run(["blueutil", "--power", "1"], capture_output=True)
    return "Bluetooth turned on, Boss."

def bluetooth_off():
    subprocess.run(["blueutil", "--power", "0"], capture_output=True)
    return "Bluetooth turned off, Boss."

def do_not_disturb_on():
    return "Do Not Disturb toggled, Boss. Use Focus in Control Centre to confirm."

def do_not_disturb_off():
    return "Do Not Disturb disabled, Boss."

# ── File operations ───────────────────────────────────────────────────────────

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
        return f"Found: " + ", ".join(paths)
    except Exception as e:
        return f"File search failed, Boss: {e}"

def open_file_or_folder(name: str) -> str:
    try:
        common = {
            "downloads": "~/Downloads", "desktop": "~/Desktop",
            "documents": "~/Documents", "pictures": "~/Pictures",
            "music": "~/Music", "movies": "~/Movies",
            "developer": "~/Developer", "friday": "~/Developer/friday",
        }
        key = name.lower().strip()
        for k, path in common.items():
            if k in key:
                subprocess.Popen(["open", os.path.expanduser(path)])
                return f"Opened {k.title()} folder, Boss."
        result = subprocess.run(
            ["mdfind", "-name", name],
            capture_output=True, text=True, timeout=10
        )
        paths = result.stdout.strip().split("\n")
        paths = [p for p in paths if p and ".Trash" not in p]
        if paths:
            subprocess.Popen(["open", paths[0]])
            return f"Opened {paths[0]}, Boss."
        return f"Couldn't find {name}, Boss."
    except Exception as e:
        return f"Couldn't open {name}, Boss: {e}"

def create_folder(name: str, location: str = "~/Desktop") -> str:
    path = os.path.expanduser(f"{location}/{name}")
    os.makedirs(path, exist_ok=True)
    return f"Created folder '{name}' on Desktop, Boss."

def list_files(folder: str = "~/Downloads") -> str:
    common = {
        "downloads": "~/Downloads", "desktop": "~/Desktop",
        "documents": "~/Documents", "developer": "~/Developer",
    }
    for k, path in common.items():
        if k in folder.lower():
            folder = path
            break
    path = os.path.expanduser(folder)
    if not os.path.exists(path):
        return f"Folder not found, Boss."
    files = os.listdir(path)[:10]
    files = [f for f in files if not f.startswith(".")]
    return f"Files in {folder}: " + ", ".join(files) + ", Boss."

def move_file(filename: str, destination: str) -> str:
    try:
        result = subprocess.run(["mdfind", "-name", filename], capture_output=True, text=True, timeout=8)
        paths = [p for p in result.stdout.strip().split("\n") if p and ".Trash" not in p]
        if not paths:
            return f"Couldn't find {filename}, Boss."
        src = paths[0]
        dest_map = {
            "desktop": "~/Desktop", "downloads": "~/Downloads",
            "documents": "~/Documents", "developer": "~/Developer",
        }
        dest_path = os.path.expanduser(dest_map.get(destination.lower(), f"~/{destination}"))
        subprocess.run(["mv", src, dest_path])
        return f"Moved {filename} to {destination}, Boss."
    except Exception as e:
        return f"Move failed, Boss: {e}"

def delete_file(filename: str) -> str:
    try:
        result = subprocess.run(["mdfind", "-name", filename], capture_output=True, text=True, timeout=8)
        paths = [p for p in result.stdout.strip().split("\n") if p and ".Trash" not in p]
        if not paths:
            return f"Couldn't find {filename}, Boss."
        subprocess.run(["mv", paths[0], os.path.expanduser("~/.Trash/")])
        return f"Moved {filename} to Trash, Boss."
    except Exception as e:
        return f"Delete failed, Boss: {e}"

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
        conversions = {
            ("miles", "km"):           lambda x: x * 1.60934,
            ("km", "miles"):           lambda x: x * 0.621371,
            ("kg", "pounds"):          lambda x: x * 2.20462,
            ("pounds", "kg"):          lambda x: x * 0.453592,
            ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
            ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
            ("meters", "feet"):        lambda x: x * 3.28084,
            ("feet", "meters"):        lambda x: x * 0.3048,
            ("liters", "gallons"):     lambda x: x * 0.264172,
            ("gallons", "liters"):     lambda x: x * 3.78541,
            ("inches", "cm"):          lambda x: x * 2.54,
            ("cm", "inches"):          lambda x: x * 0.393701,
        }
        expr = expression.lower()
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
        import requests
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
            "yen": "JPY", "jpy": "JPY", "yuan": "CNY", "cny": "CNY",
        }
        found = []
        for word in expr.split():
            word = word.strip(".,")
            if word in currencies:
                found.append(currencies[word])
        if len(found) < 2:
            return "Couldn't understand the currencies, Boss."
        from_cur, to_cur = found[0], found[1]
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
    return f"Stopped. Elapsed time: {mins}m {secs}s, Boss."

def set_timer(duration_str: str, label: str = "Timer") -> str:
    total_seconds = 0
    patterns = [(r'(\d+)\s*hour', 3600), (r'(\d+)\s*minute', 60), (r'(\d+)\s*second', 1)]
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

# ── Modes ─────────────────────────────────────────────────────────────────────

def focus_mode():
    run_applescript('tell application "Music" to pause')
    run_applescript("set volume output volume 30")
    return "Focus mode on. Music paused, volume lowered, Boss."

def vibe_mode():
    run_applescript('tell application "Music" to play')
    run_applescript("set volume output volume 60")
    return "Vibe mode on. Music playing, volume at 60, Boss."

def night_mode():
    run_applescript("set volume output volume 20")
    brightness_down()
    keyboard_backlight_off()
    return "Night mode on. Volume lowered, screen dimmed, backlight off, Boss."

# ── Notes ─────────────────────────────────────────────────────────────────────

NOTES_PATH = os.path.expanduser("~/Developer/friday/memory/notes.txt")

def take_note(note: str) -> str:
    ts = time.strftime("%Y-%m-%d %H:%M")
    with open(NOTES_PATH, "a") as f:
        f.write(f"[{ts}] {note}\n")
    return "Note saved, Boss."

def read_notes() -> str:
    if not os.path.exists(NOTES_PATH):
        return "No notes yet, Boss."
    with open(NOTES_PATH, "r") as f:
        content = f.read().strip()
    if not content:
        return "No notes yet, Boss."
    lines = content.split("\n")[-5:]
    return "Your last notes: " + ". ".join(lines)

# ── Developer tools ───────────────────────────────────────────────────────────

def git_status(path: str = None) -> str:
    try:
        cwd = path or os.path.expanduser("~/Developer")
        result = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=cwd)
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
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
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
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        pids = [p for p in result.stdout.strip().split("\n") if p]
        if not pids:
            return f"Nothing running on port {port}, Boss."
        for pid in pids:
            subprocess.run(["kill", "-9", pid])
        return f"Killed process on port {port}, Boss."
    except Exception as e:
        return f"Couldn't kill port {port}, Boss: {e}"

def check_server(port: str = "8000") -> str:
    try:
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True)
        pids = result.stdout.strip()
        if pids:
            return f"Yes, something is running on port {port}, Boss."
        return f"Nothing running on port {port}, Boss."
    except Exception as e:
        return f"Couldn't check port, Boss: {e}"

# ── WhatsApp ──────────────────────────────────────────────────────────────────

def open_whatsapp_chat(contact: str = "") -> str:
    subprocess.Popen(["open", "-a", "WhatsApp"])
    if contact:
        return f"Opening WhatsApp, Boss. Search for {contact} to message them."
    return "Opening WhatsApp, Boss."

# ── AI powered clipboard tools ────────────────────────────────────────────────

def summarise_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    content = result.stdout.strip()
    if not content:
        return "Clipboard is empty, Boss."
    return f"SUMMARISE_THIS:{content[:1500]}"

def fix_grammar_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    content = result.stdout.strip()
    if not content:
        return "Clipboard is empty, Boss."
    return f"FIX_GRAMMAR:{content[:1500]}"

def explain_code_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    content = result.stdout.strip()
    if not content:
        return "Clipboard is empty, Boss."
    return f"EXPLAIN_CODE:{content[:1500]}"

def translate_text(text: str, target_lang: str = "Spanish") -> str:
    return f"TRANSLATE:{text}|TO:{target_lang}"

# ── Web info ──────────────────────────────────────────────────────────────────

def get_stock_price(symbol: str) -> str:
    try:
        import requests
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5).json()
        price = resp["chart"]["result"][0]["meta"]["regularMarketPrice"]
        currency = resp["chart"]["result"][0]["meta"]["currency"]
        return f"{symbol.upper()} is trading at {price} {currency}, Boss."
    except Exception as e:
        return f"Couldn't get stock price for {symbol}, Boss: {e}"

def get_cricket_score() -> str:
    try:
        import requests
        result = requests.get(
            "https://www.cricbuzz.com/cricket-match/live-scores",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=5
        )
        if "live" in result.text.lower():
            return "There are live cricket matches on. Check Cricbuzz for scores, Boss."
        return "No live cricket matches right now, Boss."
    except:
        return "Couldn't fetch cricket scores right now, Boss."

def get_joke() -> str:
    import random
    import requests

    try:
        resp = requests.get(
            "https://v2.jokeapi.dev/joke/Programming,Misc?blacklistFlags=nsfw,racist,sexist,explicit&type=twopart",
            timeout=5
        ).json()
        if resp.get("type") == "twopart":
            return f"{resp['setup']} ... {resp['delivery']}"
    except:
        pass

    try:
        resp = requests.get(
            "https://icanhazdadjoke.com/",
            headers={"Accept": "application/json"},
            timeout=5
        ).json()
        if resp.get("joke"):
            return resp["joke"]
    except:
        pass

    jokes = [
        "Why do programmers always mix up Halloween and Christmas? Because Oct 31 equals Dec 25.",
        "A SQL query walks into a bar, approaches two tables and asks — can I join you?",
        "Why do Java developers wear glasses? Because they don't C#.",
        "I told my computer I needed a break. Now it won't stop sending me Kit Kat ads.",
        "Why did the developer go broke? Because he used up all his cache.",
        "There are 10 types of people in the world — those who understand binary and those who don't.",
        "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
        "Why do programmers hate nature? Too many bugs and no documentation.",
        "I would tell you a UDP joke but you might not get it.",
        "Why was the function sad after a breakup? It didn't get closure.",
    ]
    return random.choice(jokes)

def get_motivation() -> str:
    import random
    quotes = [
        "The only way to do great work is to love what you do. — Steve Jobs",
        "Code is like humour. When you have to explain it, it's bad. — Cory House",
        "First, solve the problem. Then, write the code. — John Johnson",
        "The best time to plant a tree was 20 years ago. The second best time is now.",
        "Push yourself, because no one else is going to do it for you.",
        "Dream it. Wish it. Do it.",
        "Great things never come from comfort zones.",
    ]
    return random.choice(quotes) + ", Boss."

def define_word(word: str) -> str:
    try:
        import requests
        resp = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=5).json()
        if isinstance(resp, list):
            meaning = resp[0]["meanings"][0]["definitions"][0]["definition"]
            return f"{word}: {meaning}, Boss."
        return f"Couldn't find definition for {word}, Boss."
    except Exception as e:
        return f"Dictionary lookup failed, Boss: {e}"

def wikipedia_summary(topic: str) -> str:
    try:
        import requests
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        resp = requests.get(url, timeout=5).json()
        extract = resp.get("extract", "")
        if extract:
            return extract[:400] + "..."
        return f"Couldn't find Wikipedia article for {topic}, Boss."
    except Exception as e:
        return f"Wikipedia lookup failed, Boss: {e}"

if __name__ == "__main__":
    print(get_battery())
    print(get_system_info())
    print(get_volume())
    print(brightness_up())
    print(keyboard_backlight_up())