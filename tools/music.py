import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import threading
import time
import random

def run_applescript(script):
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True
    )
    return result.stdout.strip()

# ── Current state ──────────────────────────────────────────────────────────────
_ambient_process = None
_radio_process   = None

# ── Apple Music ────────────────────────────────────────────────────────────────

def play_song(song_name: str) -> str:
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

def play_playlist(playlist_name: str) -> str:
    script = f'''
    tell application "Music"
        activate
        try
            play playlist "{playlist_name}"
            return "playing"
        on error
            return "not found"
        end try
    end tell
    '''
    result = run_applescript(script)
    if result == "not found":
        return f"Couldn't find playlist '{playlist_name}', Boss."
    return f"Playing playlist {playlist_name}, Boss."

def play_artist(artist_name: str) -> str:
    script = f'''
    tell application "Music"
        activate
        set searchResults to search playlist "Library" for "{artist_name}"
        if (count of searchResults) > 0 then
            play first item of searchResults
            return "playing"
        else
            return "not found"
        end if
    end tell
    '''
    result = run_applescript(script)
    if result == "not found":
        query = artist_name.replace(" ", "+")
        subprocess.Popen(["open", f"https://music.apple.com/search?term={query}"])
        return f"No tracks by {artist_name} in library, Boss. Opened Apple Music search."
    return f"Playing {artist_name}, Boss."

def pause_music() -> str:
    run_applescript('tell application "Music" to pause')
    return "Music paused, Boss."

def resume_music() -> str:
    run_applescript('tell application "Music" to play')
    return "Music resumed, Boss."

def next_track() -> str:
    run_applescript('tell application "Music" to next track')
    time.sleep(0.5)
    track = run_applescript('tell application "Music" to get name of current track')
    return f"Skipped. Now playing {track}, Boss."

def previous_track() -> str:
    run_applescript('tell application "Music" to previous track')
    time.sleep(0.5)
    track = run_applescript('tell application "Music" to get name of current track')
    return f"Going back. Now playing {track}, Boss."

def get_current_track() -> str:
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

def set_music_volume(level: int) -> str:
    level = max(0, min(100, int(level)))
    run_applescript(f'tell application "Music" to set sound volume to {level}')
    return f"Music volume set to {level}%, Boss."

def shuffle_on() -> str:
    run_applescript('tell application "Music" to set shuffle enabled to true')
    return "Shuffle on, Boss."

def shuffle_off() -> str:
    run_applescript('tell application "Music" to set shuffle enabled to false')
    return "Shuffle off, Boss."

def repeat_on() -> str:
    run_applescript('tell application "Music" to set song repeat to one')
    return "Repeat on, Boss."

def repeat_off() -> str:
    run_applescript('tell application "Music" to set song repeat to off')
    return "Repeat off, Boss."

def stop_music() -> str:
    run_applescript('tell application "Music" to stop')
    return "Music stopped, Boss."

def list_playlists() -> str:
    script = '''
    tell application "Music"
        set pnames to {}
        repeat with p in playlists
            set end of pnames to name of p
        end repeat
        return pnames
    end tell
    '''
    result = run_applescript(script)
    if not result:
        return "Couldn't fetch playlists, Boss."
    playlists = result.split(", ")[:10]
    return "Your playlists: " + ", ".join(playlists) + ", Boss."

# ── Local music files ──────────────────────────────────────────────────────────

MUSIC_DIRS = [
    os.path.expanduser("~/Music"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Desktop"),
]
MUSIC_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg"}

def find_local_track(name: str) -> str | None:
    """Search local folders for a music file matching name."""
    name_lower = name.lower()
    for folder in MUSIC_DIRS:
        if not os.path.exists(folder):
            continue
        for root, _, files in os.walk(folder):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in MUSIC_EXTENSIONS and name_lower in f.lower():
                    return os.path.join(root, f)
    return None

def play_local_file(name: str) -> str:
    """Find and play a local music file."""
    path = find_local_track(name)
    if path:
        subprocess.Popen(["open", path])
        return f"Playing {os.path.basename(path)}, Boss."
    # Fall back to Apple Music search
    return play_song(name)

def list_local_music(folder: str = "~/Music") -> str:
    path = os.path.expanduser(folder)
    if not os.path.exists(path):
        return f"Folder {folder} not found, Boss."
    files = []
    for f in os.listdir(path):
        if os.path.splitext(f)[1].lower() in MUSIC_EXTENSIONS:
            files.append(f)
    if not files:
        return f"No music files found in {folder}, Boss."
    return "Local tracks: " + ", ".join(files[:10]) + ", Boss."

# ── Radio streams ──────────────────────────────────────────────────────────────

RADIO_STATIONS = {
    "lofi":         "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "lofi hip hop": "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "jazz":         "https://stream.zeno.fm/0r0xa792kwzuv",
    "classical":    "https://stream.zeno.fm/yn65qm8qasquv",
    "rock":         "https://stream.zeno.fm/yzvb3vhkqhquv",
    "pop":          "https://stream.zeno.fm/f3wvbbqmdg8uv",
    "news":         "https://stream.zeno.fm/wrk7bqdygp8uv",
    "chill":        "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "hip hop":      "https://stream.zeno.fm/0r0xa792kwzuv",
    "bollywood":    "https://stream.zeno.fm/wrk7bqdygp8uv",
}

def play_radio(station: str = "lofi") -> str:
    global _radio_process
    stop_radio()

    station_key = station.lower().strip()
    url = RADIO_STATIONS.get(station_key)

    if not url:
        # Try partial match
        for k, v in RADIO_STATIONS.items():
            if station_key in k or k in station_key:
                url = v
                station_key = k
                break

    if not url:
        available = ", ".join(RADIO_STATIONS.keys())
        return f"Station '{station}' not found, Boss. Available: {available}."

    try:
        # Use ffplay if available, else open in browser
        result = subprocess.run(["which", "ffplay"], capture_output=True)
        if result.returncode == 0:
            _radio_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return f"Playing {station_key} radio, Boss."
        else:
            subprocess.Popen(["open", url])
            return f"Opening {station_key} radio in browser, Boss."
    except Exception as e:
        subprocess.Popen(["open", url])
        return f"Opening {station_key} radio in browser, Boss."

def stop_radio() -> str:
    global _radio_process
    if _radio_process and _radio_process.poll() is None:
        _radio_process.terminate()
        _radio_process = None
        return "Radio stopped, Boss."
    return "No radio playing, Boss."

def list_radio_stations() -> str:
    stations = ", ".join(RADIO_STATIONS.keys())
    return f"Available stations: {stations}, Boss."

# ── Ambient sounds ─────────────────────────────────────────────────────────────

AMBIENT_STREAMS = {
    "rain":        "https://stream.zeno.fm/yn65qm8qasquv",
    "rain sounds": "https://stream.zeno.fm/yn65qm8qasquv",
    "white noise": "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "nature":      "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "ocean":       "https://stream.zeno.fm/yn65qm8qasquv",
    "fire":        "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "lofi":        "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "study":       "https://stream.zeno.fm/fyn8eh3h5f8uv",
    "sleep":       "https://stream.zeno.fm/yn65qm8qasquv",
    "focus":       "https://stream.zeno.fm/fyn8eh3h5f8uv",
}

def play_ambient(sound: str = "rain") -> str:
    global _ambient_process
    stop_ambient()

    sound_key = sound.lower().strip()
    url = AMBIENT_STREAMS.get(sound_key)

    if not url:
        for k, v in AMBIENT_STREAMS.items():
            if sound_key in k or k in sound_key:
                url = v
                sound_key = k
                break

    if not url:
        available = ", ".join(AMBIENT_STREAMS.keys())
        return f"Sound '{sound}' not found, Boss. Available: {available}."

    try:
        result = subprocess.run(["which", "ffplay"], capture_output=True)
        if result.returncode == 0:
            _ambient_process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", url],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return f"Playing {sound_key} sounds, Boss."
        else:
            subprocess.Popen(["open", url])
            return f"Opening {sound_key} sounds in browser, Boss."
    except Exception as e:
        subprocess.Popen(["open", url])
        return f"Opening {sound_key} in browser, Boss."

def stop_ambient() -> str:
    global _ambient_process
    if _ambient_process and _ambient_process.poll() is None:
        _ambient_process.terminate()
        _ambient_process = None
        return "Ambient sound stopped, Boss."
    return "No ambient sound playing, Boss."

def stop_all_audio() -> str:
    stop_radio()
    stop_ambient()
    run_applescript('tell application "Music" to pause')
    return "All audio stopped, Boss."

if __name__ == "__main__":
    print(get_current_track())
    print(list_playlists())
    print(list_radio_stations())