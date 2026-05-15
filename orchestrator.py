import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama
from datetime import datetime
from config import OLLAMA_MODEL

from tools.weather     import get_weather
from tools.news        import get_news
from tools.search      import search, search_summary
from tools.browser     import open_url, open_youtube, compose_email, open_maps
from tools.mac_control import (
    set_volume, get_battery, open_app, close_app,
    take_screenshot, sleep_mac, lock_screen
)
from memory.memory import save_message, get_recent_history, remember, recall

# ── Keyword router ─────────────────────────────────────────────────────────────

def route(user_input: str) -> str | None:
    text = user_input.lower().strip()

    if any(w in text for w in ["weather", "temperature", "humid", "rain", "forecast"]):
        return get_weather()

    if any(w in text for w in ["news", "headlines", "what's happening"]):
        if "tech"     in text: return get_news("tech")
        if "india"    in text: return get_news("india")
        if "science"  in text: return get_news("science")
        if "business" in text: return get_news("business")
        if "sport"    in text: return get_news("sports")
        return get_news("world")

    if "youtube" in text or "play" in text:
        for trigger in ["play on youtube", "youtube", "play"]:
            if trigger in text:
                query = text.split(trigger, 1)[-1].strip()
                if query:
                    return open_youtube(query)

    if any(w in text for w in ["maps", "directions", "navigate to", "where is"]):
        for trigger in ["navigate to", "directions to", "where is", "maps"]:
            if trigger in text:
                place = text.split(trigger, 1)[-1].strip()
                if place:
                    return open_maps(place)

    if any(w in text for w in ["email", "gmail", "compose", "send mail"]):
        return compose_email(to="", subject="", body="")

    if "volume" in text:
        for n in range(101):
            if str(n) in text:
                return set_volume(n)
        if "mute" in text:   return set_volume(0)
        if "max"  in text:   return set_volume(100)
        if "half" in text:   return set_volume(50)

    if any(w in text for w in ["battery", "charge", "power level"]):
        return get_battery()

    if any(w in text for w in ["screenshot", "screen capture", "capture screen"]):
        return take_screenshot()

    if "sleep"      in text: return sleep_mac()
    if "lock"       in text: return lock_screen()

    if text.startswith("open "):
        app = text.replace("open ", "").strip().title()
        return open_app(app)

    if text.startswith("close ") or text.startswith("quit "):
        app = text.replace("close ", "").replace("quit ", "").strip().title()
        return close_app(app)

    if any(w in text for w in ["search", "google", "look up", "find"]):
        for trigger in ["search for", "search", "google", "look up", "find"]:
            if trigger in text:
                query = text.split(trigger, 1)[-1].strip()
                if query:
                    return search(query)

    if any(w in text for w in ["remember that", "note that", "don't forget"]):
        for trigger in ["remember that", "note that", "don't forget"]:
            if trigger in text:
                fact = text.split(trigger, 1)[-1].strip()
                if fact:
                    return remember(fact)

    if any(w in text for w in ["do you remember", "what do you know about", "recall"]):
        return recall(text)

    if any(w in text for w in ["clear history", "forget conversation", "reset chat"]):
        from memory.memory import clear_history
        return clear_history()

    return None


# ── Ollama call with memory context ───────────────────────────────────────────

def ask_ollama(user_input: str) -> str:
    memory_context = recall(user_input)
    history = get_recent_history(limit=10)
    now = datetime.now()

    system_prompt = (
        "You are FRIDAY, the personal AI assistant of Sahil. "
        "You are modelled after FRIDAY from the Marvel Cinematic Universe. "
        "You MUST always address Sahil as Boss. Never say Sir. Never say his name. "
        "CRITICAL: Reply in English only. No Hindi. No other language. Ever. "
        "Be direct, tactical, and concise — 1 to 2 sentences maximum unless asked for more. "
        "Never offer unsolicited suggestions. "
        "Never mention Ollama, Llama, or that you are an AI. "
        "Never repeat the same opening phrase twice in a row. "
        f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}. "
        "Location: Kolkata, India."
    )

    if memory_context:
        system_prompt += f"\n\nWhat you know about Boss:\n{memory_context}"

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"]


# ── Main entry point ───────────────────────────────────────────────────────────

def process(user_input: str) -> str:
    save_message("user", user_input)

    memory_context = recall(user_input)
    tool_result = route(user_input)

    if tool_result is None:
        result = ask_ollama(user_input)
    else:
        memory_note = f"\nContext about Boss:\n{memory_context}\n" if memory_context else ""
        result = ask_ollama(
            f"{memory_note}Boss asked: '{user_input}'\n"
            f"Real-time data:\n{tool_result}\n\n"
            f"Respond naturally in 1-2 sentences based on this data. "
            f"English only. Address Boss as Boss."
        )

    save_message("assistant", result)
    return result


# ── Terminal test loop ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Friday online. Type 'quit' to exit.\n")
    while True:
        try:
            user = input("You: ").strip()
            if not user:
                continue
            if user.lower() in ["quit", "exit"]:
                print("Friday: Goodbye, Boss.")
                break
            response = process(user)
            print(f"Friday: {response}\n")
        except KeyboardInterrupt:
            print("\nFriday: Shutting down, Boss.")
            break