import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import ollama
from voice.listener import listen, listen_with_timeout
from voice.speaker import speak, shutdown_response
from orchestrator import process
from tools.briefing import morning_briefing
from config import OLLAMA_MODEL

def generate_followup(last_response: str) -> str:
    prompt = (
        f"You are FRIDAY, an AI assistant. You just said: '{last_response}'\n"
        f"Generate ONE short natural follow-up question in character as FRIDAY.\n"
        f"Sometimes address the user as Boss, sometimes don't. Max 8 words.\n"
        f"Examples: 'Want me to play something else?' / 'Anything else, Boss?' / 'Need anything more?'\n"
        f"Reply with ONLY the follow-up question, nothing else."
    )
    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.7}
    )
    return response["message"]["content"].strip()

def run():
    briefing = morning_briefing()
    print(f"\n{'='*50}")
    print(f"FRIDAY: {briefing}")
    print(f"{'='*50}\n")
    speak(briefing)

    while True:
        try:
            print("[ waiting for wake word or clap ]")
            user_input, lang = listen()

            if not user_input.strip() or len(user_input.strip()) < 4:
                continue

            print(f"\n{'─'*50}")
            print(f"YOU  : {user_input}")

            response = process(user_input)
            print(f"FRIDAY: {response}")
            speak(response)

            followup = generate_followup(response)
            print(f"FRIDAY: {followup}")
            print(f"{'─'*50}\n")
            speak(followup)

            followup_input = listen_with_timeout(seconds=5)
            if followup_input and len(followup_input.strip()) > 3:
                print(f"\n{'─'*50}")
                print(f"YOU  : {followup_input}")
                response2 = process(followup_input)
                print(f"FRIDAY: {response2}")
                print(f"{'─'*50}\n")
                speak(response2)

        except KeyboardInterrupt:
            print("\n[FRIDAY] Shutting down.")
            shutdown_response()
            sys.exit(0)

        except Exception as e:
            print(f"[FRIDAY] Error: {e}")
            speak("I encountered an error. Please try again.")
            time.sleep(1)

if __name__ == "__main__":
    run()
