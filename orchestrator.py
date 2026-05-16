import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama
import json
from datetime import datetime
from config import OLLAMA_MODEL

from tools.weather     import get_weather
from tools.news        import get_news
from tools.search      import search, search_summary
from tools.browser     import (
    open_url, open_youtube, open_youtube_autoplay,
    compose_email, open_maps, open_news_tabs
)
from tools.mac_control import (
    set_volume, get_battery, open_app, close_app,
    take_screenshot, sleep_mac, lock_screen,
    play_song, pause_music, resume_music,
    next_track, previous_track, get_current_track
)
from memory.memory import save_message, get_recent_history, remember, recall

# ── Tool definitions (Ollama reads these to decide what to call) ───────────────

TOOLS = [
    {"name": "get_weather",        "description": "Get current weather and temperature"},
    {"name": "get_news",           "description": "Get latest news headlines. Param: category (world/tech/india/science/business/sports)"},
    {"name": "search",             "description": "Search the web for any information. Param: query"},
    {"name": "play_song",          "description": "Play a song on Apple Music. Param: song name and artist"},
    {"name": "pause_music",        "description": "Pause the currently playing music"},
    {"name": "resume_music",       "description": "Resume paused music"},
    {"name": "next_track",         "description": "Skip to next song"},
    {"name": "previous_track",     "description": "Go back to previous song"},
    {"name": "get_current_track",  "description": "Get the name of the currently playing song"},
    {"name": "open_youtube",       "description": "Open and play a video on YouTube. Param: search query"},
    {"name": "open_maps",          "description": "Open Google Maps for a location. Param: place name"},
    {"name": "compose_email",      "description": "Open Gmail to compose an email"},
    {"name": "open_news_tabs",     "description": "Open news websites in browser tabs"},
    {"name": "open_app",           "description": "Open any Mac application. Param: app name"},
    {"name": "close_app",          "description": "Close a Mac application. Param: app name"},
    {"name": "set_volume",         "description": "Set Mac volume. Param: number 0-100"},
    {"name": "get_battery",        "description": "Check Mac battery level"},
    {"name": "take_screenshot",    "description": "Take a screenshot of the screen. Triggered by: screenshot, ss, snap, capture, grab screen"},
    {"name": "sleep_mac",          "description": "Put the Mac to sleep"},
    {"name": "lock_screen",        "description": "Lock the Mac screen"},
    {"name": "remember",           "description": "Save a fact to memory. Param: the fact to remember"},
    {"name": "recall",             "description": "Recall something from memory. Param: what to look up"},
    {"name": "none",               "description": "No tool needed — just answer conversationally"},
]

TOOL_LIST_STR = "\n".join(
    f"- {t['name']}: {t['description']}" for t in TOOLS
)


# ── Step 1: Ask Ollama which tool to call ─────────────────────────────────────

def classify_intent(user_input: str) -> dict:
    """
    Ask Ollama to read the user input and return which tool to call
    and what parameter to pass. Returns a dict like:
    {"tool": "take_screenshot", "param": ""}
    {"tool": "play_song", "param": "Blinding Lights"}
    {"tool": "none", "param": ""}
    """
    prompt = f"""You are a command classifier for an AI assistant called Friday.

Available tools:
{TOOL_LIST_STR}

User said: "{user_input}"

Reply with ONLY a JSON object like this:
{{"tool": "tool_name", "param": "parameter or empty string"}}

Rules:
- Pick the single best tool
- If no tool fits, use "none"
- For take_screenshot: any mention of ss, snap, screenshot, capture, grab screen → take_screenshot
- For play_song: extract just the song/artist name as param
- For open_youtube: extract just the search query as param
- For set_volume: extract just the number as param
- For open_app / close_app: extract just the app name as param
- Return ONLY the JSON, no other text"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    raw = response["message"]["content"].strip()

    # Clean up in case Ollama adds markdown
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        return {"tool": "none", "param": ""}


# ── Step 2: Execute the tool ───────────────────────────────────────────────────

def execute_tool(tool: str, param: str) -> str | None:
    if tool == "get_weather":         return get_weather()
    if tool == "get_news":
        cat = param.lower() if param else "world"
        return get_news(cat)
    if tool == "search":              return search(param) if param else None
    if tool == "play_song":           return play_song(param) if param else None
    if tool == "pause_music":         return pause_music()
    if tool == "resume_music":        return resume_music()
    if tool == "next_track":          return next_track()
    if tool == "previous_track":      return previous_track()
    if tool == "get_current_track":   return get_current_track()
    if tool == "open_youtube":        return open_youtube_autoplay(param) if param else open_youtube()
    if tool == "open_maps":           return open_maps(param) if param else None
    if tool == "compose_email":       return compose_email()
    if tool == "open_news_tabs":      return open_news_tabs()
    if tool == "open_app":            return open_app(param.title()) if param else None
    if tool == "close_app":           return close_app(param.title()) if param else None
    if tool == "set_volume":
        try:    return set_volume(int(param))
        except: return set_volume(50)
    if tool == "get_battery":         return get_battery()
    if tool == "take_screenshot":     return take_screenshot()
    if tool == "sleep_mac":           return sleep_mac()
    if tool == "lock_screen":         return lock_screen()
    if tool == "remember":            return remember(param) if param else None
    if tool == "recall":              return recall(param) if param else None
    if tool == "clear_history":
        from memory.memory import clear_history
        return clear_history()
    return None


# ── Step 3: Ask Ollama to respond naturally ───────────────────────────────────

def ask_ollama(user_input: str, tool_result: str | None = None) -> str:
    memory_context = recall(user_input)
    history = get_recent_history(limit=10)
    now = datetime.now()

    system_prompt = (
        "You are FRIDAY, the personal AI assistant of Sahil. "
        "You are modelled after FRIDAY from the Marvel Cinematic Universe. "
        "ALWAYS address Sahil as Boss. Never say Sir. Never say his name. "
        "Reply in English only. No Hindi. No other language. Ever. "
        "Be direct, tactical, concise — 1 to 2 sentences maximum unless asked for more. "
        "Never offer unsolicited suggestions. "
        "Never mention Ollama, Llama, or that you are an AI. "
        "Never repeat the same opening phrase twice in a row. "
        "CRITICAL: If a tool result is provided, base your response ONLY on that result. "
        "Never claim an action was done if no tool result was given. "
        f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}. "
        "Location: Kolkata, India."
    )

    if memory_context:
        system_prompt += f"\n\nWhat you know about Boss:\n{memory_context}"

    messages = [{"role": "system", "content": system_prompt}]
    messages += history

    if tool_result:
        messages.append({
            "role": "user",
            "content": (
                f"SYSTEM RESULT: {tool_result}\n"
                f"Repeat this result back to Boss in 1 sentence. "
                f"Do NOT add any extra information. "
                f"Do NOT mention what was on screen. "
                f"Just confirm exactly what the system result says."
            )
        })
    else:
        messages.append({"role": "user", "content": user_input})

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"]


# ── Main entry point ───────────────────────────────────────────────────────────

def process(user_input: str) -> str:
    save_message("user", user_input)

    # Step 1 — classify intent
    intent     = classify_intent(user_input)
    tool       = intent.get("tool", "none")
    param      = intent.get("param", "")

    print(f"[FRIDAY] Intent: {tool} | Param: {param}")

    # Step 2 — execute tool
    tool_result = execute_tool(tool, param) if tool != "none" else None

    # Step 3 — respond naturally
    result = ask_ollama(user_input, tool_result)

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
