import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import random
from voice.listener import listen, listen_with_timeout
from voice.speaker import speak, shutdown_response
from orchestrator import process

FOLLOWUPS = [
    "Anything else, Sir?",
    "Can I help with anything else, Sir?",
    "What else can I do for you, Sir?",
    "Is there anything more you need, Sir?",
    "Shall I do anything else, Sir?",
]

def run():
    speak("Friday online, Sir. All systems are operational and standing by.")
    print("[FRIDAY] Listening for wake word or double clap...")

    while True:
        try:
            user_input, lang = listen()

            if not user_input.strip():
                continue

            print(f"[FRIDAY] Heard ({lang}): {user_input}")
            response = process(user_input)
            print(f"[FRIDAY] Response: {response}")
            speak(response)

            # ── Follow up ─────────────────────────────────────────────────
            speak(random.choice(FOLLOWUPS))
            followup_input = listen_with_timeout(seconds=5)
            if followup_input:
                response2 = process(followup_input)
                print(f"[FRIDAY] Response: {response2}")
                speak(response2)

        except KeyboardInterrupt:
            print("\n[FRIDAY] Shutting down.")
            shutdown_response()
            sys.exit(0)

        except Exception as e:
            print(f"[FRIDAY] Error: {e}")
            speak("I encountered an error, Sir. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    run()