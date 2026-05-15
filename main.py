import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
from voice.listener import listen
from voice.speaker import speak
from orchestrator import process

def run():
    speak("Jarvis online, Sir. All systems are operational and standing by.")
    print("[Jarvis] Listening for wake word or double clap...")

    while True:
        try:
            # ── Step 1: Wait for wake + record command ────────────────────
            user_input, lang = listen()

            if not user_input.strip():
                continue

            print(f"[Jarvis] Heard ({lang}): {user_input}")

            # ── Step 2: Process through orchestrator ─────────────────────
            response = process(user_input, lang)
            print(f"[Jarvis] Response: {response}")

            # ── Step 3: Speak the response ────────────────────────────────
            speak(response)

        except KeyboardInterrupt:
            print("\n[Jarvis] Shutting down. Goodbye, Sir.")
            speak("Shutting down. Goodbye, Sir. See you soon.")
            sys.exit(0)

        except Exception as e:
            print(f"[Jarvis] Error: {e}")
            speak("I encountered an error, Sir. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    run()