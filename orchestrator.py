import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama
import json
import re
from datetime import datetime
from config import OLLAMA_MODEL

from tools.weather     import get_weather
from tools.news        import get_news
from tools.search      import search, search_summary
from tools.browser     import (
    open_url, open_youtube, open_youtube_autoplay,
    compose_email, open_maps, open_news_tabs, open_whatsapp
)
from tools.mac_control import (
    # app control
    open_app, close_app, minimize_window, hide_app,
    show_desktop, empty_trash,
    # volume
    set_volume, mute, unmute, get_volume,
    # system
    take_screenshot, lock_screen, sleep_mac,
    get_battery, get_system_info, get_ip,
    # wifi & bluetooth
    wifi_on, wifi_off, bluetooth_on, bluetooth_off,
    do_not_disturb_on, do_not_disturb_off,
    # clipboard
    get_clipboard, set_clipboard, type_text, press_key,
    # music
    play_song, pause_music, resume_music,
    next_track, previous_track, get_current_track, set_music_volume,
    # calculator & converter
    calculate, convert_units, convert_currency,
    # timer & stopwatch
    set_timer, start_stopwatch, stop_stopwatch, start_pomodoro,
    # modes
    focus_mode, vibe_mode, night_mode,
    # notes
    take_note, read_notes,
    # file finder
    find_file,
    # developer
    git_status, run_terminal_command, open_vscode_project,
    kill_port, check_server,
    # whatsapp & pip
    open_whatsapp_chat, picture_in_picture,
)
from tools.reminder import set_reminder, list_reminders, cancel_reminders
from memory.memory import save_message, get_recent_history, remember, recall

# ── Tool definitions for Ollama intent classifier ─────────────────────────────

TOOLS = """
get_weather, get_news(category: world/tech/india/science/business/sports),
search(query), play_song(name), pause_music, resume_music, next_track,
previous_track, get_current_track, set_music_volume(level),
open_youtube(query), open_maps(location), compose_email,
open_news_tabs, open_app(name), close_app(name), minimize_window,
hide_app, show_desktop, empty_trash, set_volume(0-100), mute, unmute,
get_volume, get_battery, get_system_info, get_ip, wifi_on, wifi_off,
bluetooth_on, bluetooth_off, do_not_disturb_on, do_not_disturb_off,
get_clipboard, set_clipboard(text), take_screenshot, lock_screen,
sleep_mac, calculate(expression), convert_units(expression),
convert_currency(expression), set_timer(duration, label),
start_stopwatch, stop_stopwatch, start_pomodoro, focus_mode,
vibe_mode, night_mode, take_note(text), read_notes, find_file(name),
git_status, run_terminal_command(command), open_vscode_project(name),
kill_port(port), check_server(port), open_whatsapp_chat(contact),
picture_in_picture, set_reminder(duration, label), list_reminders,
cancel_reminders, remember(fact), recall(query), clear_history, chat
"""

# ── Intent classifier ─────────────────────────────────────────────────────────

def classify_intent(user_input: str) -> dict:
    prompt = f"""You are an intent classifier for a personal AI assistant called Friday.

Given the user's message, return ONLY a JSON object with:
- "tool": the tool name from the list
- "param": the parameter(s) needed (empty string if none)

Available tools:
{TOOLS}

Rules:
- If the user wants to chat or ask a question with no tool needed, use "chat"
- For news, detect category from context (tech, india, science, business, sports, world)
- For YouTube, extract the search query
- For timers/reminders, extract duration and label
- For calculations, extract the full math expression
- For conversions, extract the full expression including units
- For find file, extract the filename
- For terminal commands, extract the exact command
- For VS Code projects, extract the project name
- For port operations, extract the port number
- Return ONLY valid JSON, nothing else

User message: "{user_input}"

JSON:"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0}
    )
    raw = response["message"]["content"].strip()
    # extract JSON
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"tool": "chat", "param": ""}

# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(tool: str, param: str) -> str | None:
    t = tool.lower().strip()
    p = param.strip() if param else ""

    if t == "get_weather":            return get_weather()
    if t == "get_news":               return get_news(p or "world")
    if t == "search":                 return search(p)
    if t == "play_song":              return play_song(p)
    if t == "pause_music":            return pause_music()
    if t == "resume_music":           return resume_music()
    if t == "next_track":             return next_track()
    if t == "previous_track":         return previous_track()
    if t == "get_current_track":      return get_current_track()
    if t == "set_music_volume":       return set_music_volume(int(p) if p.isdigit() else 50)
    if t == "open_youtube":           return open_youtube_autoplay(p) if p else open_youtube()
    if t == "open_maps":              return open_maps(p)
    if t == "compose_email":          return compose_email()
    if t == "open_news_tabs":         return open_news_tabs()
    if t == "open_app":               return open_app(p)
    if t == "close_app":              return close_app(p)
    if t == "minimize_window":        return minimize_window()
    if t == "hide_app":               return hide_app()
    if t == "show_desktop":           return show_desktop()
    if t == "empty_trash":            return empty_trash()
    if t == "set_volume":             return set_volume(int(p) if p.isdigit() else 50)
    if t == "mute":                   return mute()
    if t == "unmute":                 return unmute()
    if t == "get_volume":             return get_volume()
    if t == "get_battery":            return get_battery()
    if t == "get_system_info":        return get_system_info()
    if t == "get_ip":                 return get_ip()
    if t == "wifi_on":                return wifi_on()
    if t == "wifi_off":               return wifi_off()
    if t == "bluetooth_on":           return bluetooth_on()
    if t == "bluetooth_off":          return bluetooth_off()
    if t == "do_not_disturb_on":      return do_not_disturb_on()
    if t == "do_not_disturb_off":     return do_not_disturb_off()
    if t == "get_clipboard":          return get_clipboard()
    if t == "set_clipboard":          return set_clipboard(p)
    if t == "take_screenshot":        return take_screenshot()
    if t == "lock_screen":            return lock_screen()
    if t == "sleep_mac":              return sleep_mac()
    if t == "calculate":              return calculate(p)
    if t == "convert_units":          return convert_units(p)
    if t == "convert_currency":       return convert_currency(p)
    if t == "set_timer":
        parts = p.split(",", 1)
        duration = parts[0].strip()
        label    = parts[1].strip() if len(parts) > 1 else "Timer"
        return set_timer(duration, label)
    if t == "start_stopwatch":        return start_stopwatch()
    if t == "stop_stopwatch":         return stop_stopwatch()
    if t == "start_pomodoro":         return start_pomodoro()
    if t == "focus_mode":             return focus_mode()
    if t == "vibe_mode":              return vibe_mode()
    if t == "night_mode":             return night_mode()
    if t == "take_note":              return take_note(p)
    if t == "read_notes":             return read_notes()
    if t == "find_file":              return find_file(p)
    if t == "git_status":             return git_status()
    if t == "run_terminal_command":   return run_terminal_command(p)
    if t == "open_vscode_project":    return open_vscode_project(p)
    if t == "kill_port":              return kill_port(p)
    if t == "check_server":           return check_server(p)
    if t == "open_whatsapp_chat":     return open_whatsapp_chat(p)
    if t == "picture_in_picture":     return picture_in_picture()
    if t == "set_reminder":
        parts = p.split(",", 1)
        duration = parts[0].strip()
        label    = parts[1].strip() if len(parts) > 1 else "Reminder"
        return set_reminder(duration, label)
    if t == "list_reminders":         return list_reminders()
    if t == "cancel_reminders":       return cancel_reminders()
    if t == "remember":               return remember(p)
    if t == "recall":                 return recall(p)
    if t == "clear_history":
        from memory.memory import clear_history
        return clear_history()
    return None

# ── Ollama natural response ───────────────────────────────────────────────────

def ask_ollama(user_input: str, tool_result: str = None) -> str:
    memory_context = recall(user_input)
    history = get_recent_history(limit=8)
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

    if tool_result:
        user_input = (
            f"Boss said: '{user_input}'\n"
            f"Real-time data:\n{tool_result}\n\n"
            f"Respond in 1 sentence confirming the action or summarising the data. "
            f"English only. Address Boss as Boss. Do NOT ask follow up questions."
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"]

# ── Main entry point ──────────────────────────────────────────────────────────

def process(user_input: str) -> str:
    save_message("user", user_input)

    try:
        intent = classify_intent(user_input)
        tool   = intent.get("tool", "chat")
        param  = intent.get("param", "")
        print(f"[FRIDAY] Intent: {tool} | Param: {param}")
    except Exception as e:
        print(f"[FRIDAY] Intent classification failed: {e}")
        tool, param = "chat", ""

    if tool == "chat":
        result = ask_ollama(user_input)
    else:
        tool_result = execute_tool(tool, param)
        if tool_result:
            result = ask_ollama(user_input, tool_result)
        else:
            result = ask_ollama(user_input)

    save_message("assistant", result)
    return result

# ── Terminal test loop ────────────────────────────────────────────────────────

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
        