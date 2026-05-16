import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import random
import time
from config import SAY_VOICE

_current_process = None
_last_wake = None

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
    _current_process = subprocess.Popen(
        ["say", "-v", SAY_VOICE, text.strip() + " [[slnc 1000]]"]
    )
    _current_process.wait()
    # Extra buffer after speech finishes
    time.sleep(0.3)

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
    time.sleep(2)
    wake_response()