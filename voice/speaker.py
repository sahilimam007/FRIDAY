import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import random
from config import SAY_VOICE

_current_process = None
_last_wake = None

WAKE_RESPONSES = [
    "Yes Sir, how may I assist you?",
    "At your service, Sir.",
    "Good to hear from you, Sir. What do you need?",
    "Online and ready, Sir.",
    "How can I help you, Sir?",
    "Always here, Sir. What do you need?",
    "Awaiting your orders, Sir.",
    "Right here, Sir. Go ahead.",
    "Standing by, Sir. What is it?",
    "Ready when you are, Sir.",
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
    _current_process = subprocess.Popen(["say", "-v", SAY_VOICE, text.strip() + " [[slnc 500]]"])
    _current_process.wait()

def wake_response():
    """Jarvis greets Sir after being woken up."""
    global _last_wake
    choices = [w for w in WAKE_RESPONSES if w != _last_wake]
    phrase = random.choice(choices)
    _last_wake = phrase
    speak(phrase)
    return phrase

if __name__ == "__main__":
    speak("Jarvis online, Sir. All systems are operational and standing by.")
    import time
    time.sleep(2)
    wake_response()

def wake_response():
    """Jarvis greets Sir after being woken up."""
    global _last_wake
    choices = [w for w in WAKE_RESPONSES if w != _last_wake]
    phrase = random.choice(choices)
    _last_wake = phrase
    speak(phrase)
    return phrase

if __name__ == "__main__":
    speak("Jarvis online, Sir. All systems are operational and standing by.")
    import time
    time.sleep(2)
    wake_response()