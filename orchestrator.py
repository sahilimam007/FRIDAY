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
    next_track, previous_track, get_current_track,
    picture_in_picture, minimize_window, hide_app,
    get_system_info, calculate, get_clipboard, set_clipboard,
    focus_mode, vibe_mode, night_mode, type_text
)
from tools.reminder import set_reminder, list_reminders, cancel_reminders
from memory.memory import save_message, get_recent_history, remember, recall

# ── Tool definitions ───────────────────────────────────────────────────────────

TOOLS = [
    {"name": "get_weather",        "description": "Get current weather and temperature"},
    {"name": "get_news",           "description": "Get latest news. Param: category (world/tech/india/science/business/sports)"},
    {"name": "search",             "description": "Search the web. Param: search query"},
    {"name": "play_song",          "description": "Play a song on Apple Music. Param: song name and artist"},
    {"name": "pause_music",        "description": "Pause music"},
    {"name": "resume_music",       "description": "Resume music"},
    {"name": "next_track",         "description": "Skip to next song"},
    {"name": "previous_track",     "description": "Go to previous song"},
    {"name": "get_current_track",  "description": "What song is playing right now"},
    {"name": "open_youtube",       "description": "Open and play a YouTube video. Param: search query"},
    {"name": "open_maps",          "description": "Open Google Maps. Param: place name"},
    {"name": "compose_email",      "description": "Open Gmail compose window"},
    {"name": "open_news_tabs",     "description": "Open news websites in browser"},
    {"name": "open_app",           "description": "Open a Mac app. Param: app name"},
    {"name": "close_app",          "description": "Close a Mac app. Param: app name"},
    {"name": "minimize_window",    "description": "Minimize current window. Param: app name (optional)"},
    {"name": "hide_app",           "description": "Hide an app. Param: app name (optional)"},
    {"name": "picture_in_picture", "description": "Float video in small window. Triggered by: pip, smaller screen, mini player, float video, picture in picture"},
    {"name": "set_volume",         "description": "Set volume. Param: number 0-100"},
    {"name": "get_battery",        "description": "Check battery level"},
    {"name": "get_system_info",    "description": "Check RAM, CPU, storage usage. Triggered by: system info, how much ram, storage, cpu usage"},
    {"name": "take_screenshot",    "description": "Take a screenshot. Triggered by: ss, snap, screenshot, capture, grab screen"},
    {"name": "sleep_mac",          "description": "Put Mac to sleep"},
    {"name": "lock_screen",        "description": "Lock the screen"},
    {"name": "calculate",          "description": "Calculate a math expression. Param: the math expression. Triggered by: calculate, what is X plus Y, percentage, multiply"},
    {"name": "get_clipboard",      "description": "Read what is in the clipboard"},
    {"name": "set_clipboard",      "description": "Copy something to clipboard. Param: text to copy"},
    {"name": "type_text",          "description": "Type text at cursor position. Param: text to type"},
    {"name": "focus_mode",         "description": "Activate focus mode — closes distracting apps, lowers volume"},
    {"name": "vibe_mode",          "description": "Activate vibe mode — opens music, sets good volume"},
    {"name": "night_mode",         "description": "Activate night mode — lowers volume and dims screen"},
    {"name": "set_reminder",       "description": "Set a reminder. Param format: 'TIME|MESSAGE' e.g. '20 minutes|drink water'"},
    {"name": "list_reminders",     "description": "List all active reminders"},
    {"name": "cancel_reminders",   "description": "Cancel all active reminders"},
    {"name": "remember",           "description": "Save something to memory. Param: the fact"},
    {"name": "recall",             "description": "Recall something from memory. Param: what to look up"},
    {"name": "clear_history",      "description": "Clear conversation history"},
    {"name": "none",               "description": "No tool needed — answer conversationally"},
]

TOOL_LIST_STR = "\n".join(
    f"- {t['name']}: {t['description']}" for t in TOOLS
)


# ── Step 1: Classify intent ────────────────────────────────────────────────────

def classify_intent(user_input: str) -> dict:
    prompt = f"""You are a command classifier for an AI assistant called Friday.

Available tools:
{TOOL_LIST_STR}

User said: "{user_input}"

Reply with ONLY a JSON object like this:
{{"tool": "tool_name", "param": "parameter or empty string"}}

Rules:
- Pick the single best tool
- If no tool fits, use "none"
- For take_screenshot: ss, snap, screenshot, capture, grab screen → take_screenshot
- For picture_in_picture: smaller screen, pip, float, mini player → picture_in_picture
- For calculate: any math, percentage, multiplication → calculate
- For play_song: extract just the song/artist name
- For open_youtube: extract just the search query
- For set_volume: extract just the number
- For open_app / close_app: extract just the app name
- For get_system_info: ram, memory, storage, cpu, system info → get_system_info
- For set_reminder: format param as 'TIME|MESSAGE' e.g. '20 minutes|drink water'
- Return ONLY the JSON, no other text"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    raw = response["message"]["content"].strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except Exception:
        return {"tool": "none", "param": ""}


# ── Step 2: Execute tool ───────────────────────────────────────────────────────

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
    if tool == "minimize_window":     return minimize_window(param)
    if tool == "hide_app":            return hide_app(param)
    if tool == "picture_in_picture":  return picture_in_picture()
    if tool == "set_volume":
        try:    return set_volume(int(param))
        except: return set_volume(50)
    if tool == "get_battery":         return get_battery()
    if tool == "get_system_info":     return get_system_info()
    if tool == "take_screenshot":     return take_screenshot()
    if tool == "sleep_mac":           return sleep_mac()
    if tool == "lock_screen":         return lock_screen()
    if tool == "calculate":           return calculate(param) if param else None
    if tool == "get_clipboard":       return get_clipboard()
    if tool == "set_clipboard":       return set_clipboard(param) if param else None
    if tool == "type_text":           return type_text(param) if param else None
    if tool == "focus_mode":          return focus_mode()
    if tool == "vibe_mode":           return vibe_mode()
    if tool == "night_mode":          return night_mode()
    if tool == "set_reminder":
        if param and "|" in param:
            time_str, message = param.split("|", 1)
            return set_reminder(time_str.strip(), message.strip())
        return "Please specify a time and what to remind you about."
    if tool == "list_reminders":      return list_reminders()
    if tool == "cancel_reminders":    return cancel_reminders()
    if tool == "remember":            return remember(param) if param else None
    if tool == "recall":              return recall(param) if param else None
    if tool == "clear_history":
        from memory.memory import clear_history
        return clear_history()
    return None


# ── Step 3: Respond naturally ──────────────────────────────────────────────────

def ask_ollama(user_input: str, tool_result: str | None = None) -> str:
    memory_context = recall(user_input)
    history = get_recent_history(limit=10)
    now = datetime.now()

    system_prompt = (
        "You are FRIDAY, the personal AI assistant of Sahil. "
        "You are modelled after FRIDAY from the Marvel Cinematic Universe. "
        "Usually address Sahil as Boss but sometimes omit it for natural flow. Never say Sir or his name. "
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
                f"Repeat this result back in 1 sentence. "
                f"Do NOT add extra information. "
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

    intent = classify_intent(user_input)
    tool   = intent.get("tool", "none")
    param  = intent.get("param", "")

    print(f"[FRIDAY] Intent: {tool} | Param: {param}")

    tool_result = execute_tool(tool, param) if tool != "none" else None
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
