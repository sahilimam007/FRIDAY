import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama
from config import OLLAMA_MODEL

from tools.weather   import get_weather
from tools.news      import get_news
from tools.search    import search, search_summary
from tools.browser   import open_url, open_youtube, compose_email, open_maps
from tools.mac_control import (
    set_volume, get_battery, open_app, close_app,
    take_screenshot, sleep_mac, lock_screen
)
from memory.memory import save_message, get_recent_history, remember, recall

# ── Keyword router ─────────────────────────────────────────────────────────────

def route(user_input: str) -> str | None:
    """
    Check if the input matches a tool keyword.
    Returns a string response if a tool handles it, else None (falls through to Ollama).
    """
    text = user_input.lower().strip()

    # ── Weather ──────────────────────────────────────────────────────────────
    if any(w in text for w in ["weather", "temperature", "humid", "rain", "forecast"]):
        return get_weather()

    # ── News ─────────────────────────────────────────────────────────────────
    if any(w in text for w in ["news", "headlines", "what's happening"]):
        if "tech"     in text: return get_news("tech")
        if "india"    in text: return get_news("india")
        if "science"  in text: return get_news("science")
        if "business" in text: return get_news("business")
        if "sport"    in text: return get_news("sports")
        return get_news("world")

    # ── YouTube ───────────────────────────────────────────────────────────────
    if "youtube" in text or "play" in text:
        # extract what comes after "play" or "youtube"
        for trigger in ["play on youtube", "youtube", "play"]:
            if trigger in text:
                query = text.split(trigger, 1)[-1].strip()
                if query:
                    return open_youtube(query)

    # ── Maps ──────────────────────────────────────────────────────────────────
    if any(w in text for w in ["maps", "directions", "navigate to", "where is"]):
        for trigger in ["navigate to", "directions to", "where is", "maps"]:
            if trigger in text:
                place = text.split(trigger, 1)[-1].strip()
                if place:
                    return open_maps(place)

    # ── Email ─────────────────────────────────────────────────────────────────
    if any(w in text for w in ["email", "gmail", "compose", "send mail"]):
        return compose_email(to="", subject="", body="")

    # ── Volume ────────────────────────────────────────────────────────────────
    if "volume" in text:
        for n in range(101):
            if str(n) in text:
                return set_volume(n)
        if "mute" in text:   return set_volume(0)
        if "max"  in text:   return set_volume(100)
        if "half" in text:   return set_volume(50)

    # ── Battery ───────────────────────────────────────────────────────────────
    if any(w in text for w in ["battery", "charge", "power level"]):
        return get_battery()

    # ── Screenshot ────────────────────────────────────────────────────────────
    if any(w in text for w in ["screenshot", "screen capture", "capture screen"]):
        return take_screenshot()

    # ── Sleep / Lock ──────────────────────────────────────────────────────────
    if "sleep"      in text: return sleep_mac()
    if "lock"       in text: return lock_screen()

    # ── Open app ──────────────────────────────────────────────────────────────
    if text.startswith("open "):
        app = text.replace("open ", "").strip().title()
        return open_app(app)

    # ── Close app ─────────────────────────────────────────────────────────────
    if text.startswith("close ") or text.startswith("quit "):
        app = text.replace("close ", "").replace("quit ", "").strip().title()
        return close_app(app)

    # ── Web search ────────────────────────────────────────────────────────────
    if any(w in text for w in ["search", "google", "look up", "find"]):
        for trigger in ["search for", "search", "google", "look up", "find"]:
            if trigger in text:
                query = text.split(trigger, 1)[-1].strip()
                if query:
                    return search(query)

    # ── Memory — remember ─────────────────────────────────────────────────────
    if any(w in text for w in ["remember that", "note that", "don't forget"]):
        for trigger in ["remember that", "note that", "don't forget"]:
            if trigger in text:
                fact = text.split(trigger, 1)[-1].strip()
                if fact:
                    return remember(fact)

    # ── Memory — recall ───────────────────────────────────────────────────────
    if any(w in text for w in ["do you remember", "what do you know about", "recall"]):
        return recall(text)

    # ── Clear history ─────────────────────────────────────────────────────────
    if any(w in text for w in ["clear history", "forget conversation", "reset chat"]):
        from memory.memory import clear_history
        return clear_history()

    return None  # nothing matched — send to Ollama


# ── Ollama call with memory context ───────────────────────────────────────────

def ask_ollama(user_input: str) -> str:
    # Pull relevant long-term memories
    memory_context = recall(user_input)

    # Build message list — system + recent history + memory + current input
    history = get_recent_history(limit=10)

    system_prompt = (
        "You are Jarvis, a highly intelligent British AI assistant. "
        "You are witty, precise, and always address the user as Sir. "
        "Keep responses concise and useful."
    )
    if memory_context:
        system_prompt += f"\n\n{memory_context}"

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"]


# ── Main entry point ───────────────────────────────────────────────────────────

def process(user_input: str) -> str:
    # Save what the user said
    save_message("user", user_input)

    # Try tools first
    result = route(user_input)

    # Fall through to Ollama if no tool matched
    if result is None:
        result = ask_ollama(user_input)

    # Save Jarvis's response
    save_message("assistant", result)

    return result


# ── Terminal test loop ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Jarvis online. Type 'quit' to exit.\n")
    while True:
        try:
            user = input("You: ").strip()
            if not user:
                continue
            if user.lower() in ["quit", "exit"]:
                print("Jarvis: Goodbye, Sir.")
                break
            response = process(user)
            print(f"Jarvis: {response}\n")
        except KeyboardInterrupt:
            print("\nJarvis: Shutting down, Sir.")
            break
        