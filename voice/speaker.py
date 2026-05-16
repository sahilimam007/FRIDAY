import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import random
import time
from config import SAY_VOICE

_current_process = None
_last_wake = None

# Voice settings — adjust with "speak faster", "speak slower" etc.
_speed = 175      # words per minute (default: 175, range: 100-300)
_pitch = 50       # pitch (default: 50, range: 1-100)

WAKE_RESPONSES = [
    "Yes Boss, how may I assist you?",
    "At your service.",
    "Go ahead, Boss.",
    "Online and ready.",
    "How can I help?",
    "Always here. What do you need?",
    "Awaiting your orders, Boss.",
    "Right here. Go ahead.",
    "Standing by. What is it?",
    "Ready when you are, Boss.",
]

SHUTDOWN_RESPONSES = [
    "Shutting down. Goodbye, Boss.",
    "Going offline. Do try not to break anything while I'm gone.",
    "Signing off. It's been a pleasure, Boss.",
    "Powering down. Take care.",
    "Going offline now. Until next time, Boss.",
    "Shutting down systems. Farewell.",
    "Going dark, Boss. Don't hesitate to call.",
    "Systems offline. Rest well.",
]

def stop_speaking():
    """Kill current speech immediately."""
    global _current_process
    if _current_process and _current_process.poll() is None:
        _current_process.kill()
        _current_process = None

def speak(text: str):
    """Speak text out loud using macOS say command."""
    global _current_process
    stop_speaking()
    # [[slnc 1000]] adds 1 second silence at end to prevent cutoff
    # [[pbas N]] sets pitch, [[rate N]] sets speed inline
    ssml = f"[[pbas {_pitch}]][[rate {_speed}]]{text.strip()} [[slnc 1000]]"
    _current_process = subprocess.Popen(
        ["say", "-v", SAY_VOICE, ssml]
    )
    _current_process.wait()
    time.sleep(0.3)

def set_speed(level: str) -> str:
    """
    Set voice speed. level can be:
    - 'faster', 'fast', 'slower', 'slow', 'normal', 'default'
    - A number string like '200'
    """
    global _speed
    level = level.strip().lower()

    presets = {
        "slowest":  120,
        "slow":     145,
        "normal":   175,
        "default":  175,
        "fast":     210,
        "faster":   210,
        "fastest":  260,
        "very fast": 260,
        "very slow": 120,
    }

    if level in presets:
        _speed = presets[level]
    else:
        try:
            val = int(level)
            _speed = max(100, min(300, val))
        except ValueError:
            return "I didn't catch that speed setting, Boss."

    return f"Voice speed set to {_speed} words per minute, Boss."

def set_pitch(level: str) -> str:
    """
    Set voice pitch. level can be:
    - 'higher', 'high', 'lower', 'low', 'normal', 'default'
    - A number string like '60'
    """
    global _pitch
    level = level.strip().lower()

    presets = {
        "lowest":  20,
        "low":     35,
        "normal":  50,
        "default": 50,
        "high":    65,
        "higher":  65,
        "highest": 80,
        "very high": 80,
        "very low":  20,
    }

    if level in presets:
        _pitch = presets[level]
    else:
        try:
            val = int(level)
            _pitch = max(1, min(100, val))
        except ValueError:
            return "I didn't catch that pitch setting, Boss."

    return f"Voice pitch set to {_pitch}, Boss."

def get_voice_settings() -> str:
    return f"Currently running at {_speed} words per minute, pitch {_pitch}, Boss."

def wake_response():
    """Friday greets Boss after being woken up."""
    global _last_wake
    choices = [w for w in WAKE_RESPONSES if w != _last_wake]
    phrase = random.choice(choices)
    _last_wake = phrase
    speak(phrase)
    return phrase

def shutdown_response():
    """Random shutdown phrase."""
    phrase = random.choice(SHUTDOWN_RESPONSES)
    speak(phrase)
    return phrase

if __name__ == "__main__":
    speak("Friday online, Boss. All systems are operational and standing by.")
    time.sleep(1)

    print(set_speed("fast"))
    speak("This is fast mode, Boss.")
    time.sleep(1)

    print(set_speed("slow"))
    speak("This is slow mode, Boss.")
    time.sleep(1)

    print(set_speed("normal"))
    print(set_pitch("high"))
    speak("This is high pitch, Boss.")
    time.sleep(1)

    print(set_pitch("normal"))
    speak("Back to normal. How does that sound, Boss?")