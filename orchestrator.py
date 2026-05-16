import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama
import json
import re
import random
import subprocess
from datetime import datetime
from config import OLLAMA_MODEL

from tools.weather  import get_weather
from tools.news     import get_news
from tools.search   import search, search_summary
from tools.browser  import (
    open_url, open_youtube, open_youtube_autoplay,
    compose_email, open_maps, open_news_tabs, open_whatsapp
)
from tools.mac_control import (
    open_app, close_app, force_quit, switch_to_app, list_running_apps,
    minimize_window, hide_app, show_desktop, empty_trash,
    restart_mac, shutdown_mac,
    snap_left, snap_right, fullscreen, close_tab, new_tab, picture_in_picture,
    set_volume, mute, unmute, get_volume,
    take_screenshot, lock_screen, sleep_mac,
    get_battery, get_system_info, get_ip, ping_host,
    wifi_on, wifi_off, bluetooth_on, bluetooth_off,
    do_not_disturb_on, do_not_disturb_off,
    get_clipboard, set_clipboard, type_text, press_key,
    play_song, pause_music, resume_music,
    next_track, previous_track, get_current_track, set_music_volume,
    calculate, convert_units, convert_currency,
    set_timer, start_stopwatch, stop_stopwatch, start_pomodoro,
    focus_mode, vibe_mode, night_mode,
    take_note, read_notes,
    find_file, open_file_or_folder, create_folder, list_files, move_file, delete_file,
    git_status, run_terminal_command, open_vscode_project, kill_port, check_server,
    open_whatsapp_chat, picture_in_picture,
    summarise_clipboard, fix_grammar_clipboard, explain_code_clipboard, translate_text,
    get_stock_price, get_cricket_score, get_joke, get_motivation, define_word, wikipedia_summary,
)
from tools.reminder     import set_reminder, list_reminders, cancel_reminders
from tools.productivity import (
    start_pomodoro, stop_pomodoro, pomodoro_status,
    focus_mode as productivity_focus_mode,
    meeting_mode, end_of_day_summary
)
from memory.memory      import save_message, get_recent_history, remember, recall

# ── Tool list for classifier ───────────────────────────────────────────────────

TOOLS = """
get_weather, get_news(world/tech/india/science/business/sports),
search(query), play_song(name), pause_music, resume_music, next_track,
previous_track, get_current_track, set_music_volume(0-100),
open_youtube(query), open_maps(location), compose_email, open_news_tabs,
open_app(name), close_app(name), force_quit(name), switch_to_app(name),
list_running_apps, minimize_window, hide_app, show_desktop, empty_trash,
restart_mac, shutdown_mac, snap_left, snap_right, fullscreen,
close_tab, new_tab, picture_in_picture,
set_volume(0-100), mute, unmute, get_volume,
get_battery, get_system_info, get_ip, ping_host(host),
wifi_on, wifi_off, bluetooth_on, bluetooth_off,
do_not_disturb_on, do_not_disturb_off,
get_clipboard, set_clipboard(text), type_text(text),
take_screenshot, lock_screen, sleep_mac,
calculate(expression), convert_units(expression), convert_currency(expression),
set_timer(duration, label), start_stopwatch, stop_stopwatch, start_pomodoro,
focus_mode, vibe_mode, night_mode,
take_note(text), read_notes,
find_file(name), open_file_or_folder(name), create_folder(name),
list_files(folder), move_file(filename, destination), delete_file(name),
git_status, run_terminal_command(command), open_vscode_project(name),
kill_port(port), check_server(port), open_whatsapp_chat(contact),
summarise_clipboard, fix_grammar_clipboard, explain_code_clipboard,
translate_text(text, language), get_stock_price(symbol),
get_cricket_score, get_joke, get_motivation, define_word(word),
wikipedia_summary(topic), set_reminder(duration, label),
list_reminders, cancel_reminders, remember(fact), recall(query),
start_pomodoro, stop_pomodoro, pomodoro_status,
meeting_mode, end_of_day_summary,
clear_history, chat
"""

# ── Tools that speak their result directly — no Ollama paraphrasing ────────────
SPEAK_DIRECTLY = {
    "get_joke", "get_motivation", "define_word", "wikipedia_summary",
    "list_files", "list_running_apps", "get_clipboard", "read_notes",
    "find_file", "get_current_track", "git_status", "run_terminal_command",
    "get_volume", "get_ip", "ping_host", "check_server",
    "calculate", "convert_units", "convert_currency",
    "get_battery", "get_system_info", "get_stock_price", "get_cricket_score",
    "get_weather",
}

# ── Financial deflections — varied, never repeats same one twice ───────────────
FINANCIAL_DEFLECTIONS = [
    "That's your call, Boss. I report numbers, not financial advice.",
    "Not my department, Boss. The data's there — the decision's yours.",
    "I pull the numbers, Boss. What you do with them is on you.",
    "Financial calls are above my pay grade, Boss. That one's yours.",
    "I'd need a finance licence for that, Boss. The data's yours to act on.",
    "That's a you decision, Boss. I just report what the market's doing.",
    "I don't do investment advice, Boss. The numbers are yours.",
    "Above my clearance level, Boss. Make the call yourself.",
]
_last_deflection = None

def get_financial_deflection() -> str:
    global _last_deflection
    choices = [d for d in FINANCIAL_DEFLECTIONS if d != _last_deflection]
    pick = random.choice(choices)
    _last_deflection = pick
    return pick

# ── Financial question detector ────────────────────────────────────────────────
# Catches any phrasing — not just exact keywords

FINANCIAL_QUESTION_WORDS = [
    "should i buy", "should i sell", "is it worth", "worth buying",
    "worth investing", "good investment", "good stock", "good time to buy",
    "good time to invest", "what do you think about", "your opinion on",
    "your take on", "recommend", "thoughts on", "is it a good", "should i get",
    "should i invest", "is it safe to", "will it go up", "will it go down",
    "will it rise", "will it fall", "is it overvalued", "is it undervalued",
    "worth it", "should i put money", "should i hold","what's your take on", 
    "your take on", "will it go up", "will it go down","will it rise", 
    "will it fall", "going up", "going down", "worth investing",

]

FINANCIAL_ASSET_WORDS = [
    "stock", "stocks", "share", "shares", "invest", "investment",
    "market", "crypto", "bitcoin", "ethereum", "nft", "fund", "mutual fund",
    "etf", "equity", "portfolio", "nasdaq", "sensex", "nifty", "forex",
    "reliance", "tata", "infosys", "nvidia", "tesla", "dow", "sp500",
]

def is_financial_question(text: str) -> bool:
    lower = text.lower()
    has_question = any(q in lower for q in FINANCIAL_QUESTION_WORDS)
    has_asset = any(a in lower for a in FINANCIAL_ASSET_WORDS)
    if has_question and has_asset:
        return True
    PRICE_PREDICTION_WORDS = [
        "will", "going to", "gonna", "predict", "forecast",
        "next week", "next month", "by end of year",
    ]
    if any(w in lower for w in PRICE_PREDICTION_WORDS) and has_asset:
        return True
    return False

# ── Intent classifier ──────────────────────────────────────────────────────────

def classify_intent(user_input: str) -> dict:
    # Intercept financial advice questions before hitting Ollama
    if is_financial_question(user_input):
        return {"tool": "financial_deflect", "param": ""}

    prompt = f"""You are an intent classifier for a personal AI assistant called Friday.

Given the user's message, return ONLY a JSON object with:
- "tool": the tool name from the list
- "param": the parameter(s) needed (empty string if none)

Available tools:
{TOOLS}

Rules:
- If no tool fits, use "chat"
- For open_file_or_folder: use when user says "open my X folder" or "open X file"
- For find_file: use when user says "find my X" (don't open, just find)
- For translate_text: param = "text|language" e.g. "hello|Spanish"
- For set_timer: param = "duration, label"
- For set_reminder: param = "duration, label"
- For move_file: param = "filename, destination"
- For get_stock_price: param must be the ticker symbol ONLY (e.g. AAPL for Apple, TSLA for Tesla, MSFT for Microsoft, GOOGL for Google, AMZN for Amazon, NVDA for Nvidia). Convert company names to ticker symbols. Never include "symbol=" in the param.
- Questions asking for opinions, advice, or predictions about stocks or investments must use "financial_deflect" not "get_stock_price"
- Return ONLY valid JSON, nothing else

User message: "{user_input}"
JSON:"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0}
    )
    raw = response["message"]["content"].strip()
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"tool": "chat", "param": ""}

# ── Tool executor ──────────────────────────────────────────────────────────────

def execute_tool(tool: str, param: str) -> str | None:
    t = tool.lower().strip()
    p = param.strip() if param else ""

    # Clean up stock symbol in case model returns "symbol=AAPL" or full company name
    if t == "get_stock_price":
        p = re.sub(r'(?i)symbol\s*=\s*', '', p).strip().upper()
        name_map = {
            "APPLE": "AAPL", "TESLA": "TSLA", "GOOGLE": "GOOGL",
            "ALPHABET": "GOOGL", "MICROSOFT": "MSFT", "AMAZON": "AMZN",
            "META": "META", "FACEBOOK": "META", "NETFLIX": "NFLX",
            "NVIDIA": "NVDA", "SAMSUNG": "005930.KS", "RELIANCE": "RELIANCE.NS",
            "TCS": "TCS.NS", "INFOSYS": "INFY", "WIPRO": "WIPRO.NS",
        }
        p = name_map.get(p, p)

    if t == "get_weather":              return get_weather()
    if t == "get_news":                 return get_news(p or "world")
    if t == "search":                   return search(p)
    if t == "play_song":                return play_song(p)
    if t == "pause_music":              return pause_music()
    if t == "resume_music":             return resume_music()
    if t == "next_track":               return next_track()
    if t == "previous_track":           return previous_track()
    if t == "get_current_track":        return get_current_track()
    if t == "set_music_volume":         return set_music_volume(int(p) if p.isdigit() else 50)
    if t == "open_youtube":             return open_youtube_autoplay(p) if p else open_youtube()
    if t == "open_maps":                return open_maps(p)
    if t == "compose_email":            return compose_email()
    if t == "open_news_tabs":           return open_news_tabs()
    if t == "open_app":                 return open_app(p)
    if t == "close_app":                return close_app(p)
    if t == "force_quit":               return force_quit(p)
    if t == "switch_to_app":            return switch_to_app(p)
    if t == "list_running_apps":        return list_running_apps()
    if t == "minimize_window":          return minimize_window()
    if t == "hide_app":                 return hide_app()
    if t == "show_desktop":             return show_desktop()
    if t == "empty_trash":              return empty_trash()
    if t == "restart_mac":              return restart_mac()
    if t == "shutdown_mac":             return shutdown_mac()
    if t == "snap_left":                return snap_left()
    if t == "snap_right":               return snap_right()
    if t == "fullscreen":               return fullscreen()
    if t == "close_tab":                return close_tab()
    if t == "new_tab":                  return new_tab()
    if t == "picture_in_picture":       return picture_in_picture()
    if t == "set_volume":               return set_volume(int(p) if p.isdigit() else 50)
    if t == "mute":                     return mute()
    if t == "unmute":                   return unmute()
    if t == "get_volume":               return get_volume()
    if t == "get_battery":              return get_battery()
    if t == "get_system_info":          return get_system_info()
    if t == "get_ip":                   return get_ip()
    if t == "ping_host":                return ping_host(p)
    if t == "wifi_on":                  return wifi_on()
    if t == "wifi_off":                 return wifi_off()
    if t == "bluetooth_on":             return bluetooth_on()
    if t == "bluetooth_off":            return bluetooth_off()
    if t == "do_not_disturb_on":        return do_not_disturb_on()
    if t == "do_not_disturb_off":       return do_not_disturb_off()
    if t == "get_clipboard":            return get_clipboard()
    if t == "set_clipboard":            return set_clipboard(p)
    if t == "type_text":                return type_text(p)
    if t == "take_screenshot":          return take_screenshot()
    if t == "lock_screen":              return lock_screen()
    if t == "sleep_mac":                return sleep_mac()
    if t == "calculate":                return calculate(p)
    if t == "convert_units":            return convert_units(p)
    if t == "convert_currency":         return convert_currency(p)
    if t == "set_timer":
        parts = p.split(",", 1)
        return set_timer(parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Timer")
    if t == "start_stopwatch":          return start_stopwatch()
    if t == "stop_stopwatch":           return stop_stopwatch()
    if t == "start_pomodoro":           return start_pomodoro()
    if t == "focus_mode":               return focus_mode()
    if t == "vibe_mode":                return vibe_mode()
    if t == "night_mode":               return night_mode()
    if t == "take_note":                return take_note(p)
    if t == "read_notes":               return read_notes()
    if t == "find_file":                return find_file(p)
    if t == "open_file_or_folder":      return open_file_or_folder(p)
    if t == "create_folder":            return create_folder(p)
    if t == "list_files":               return list_files(p or "~/Downloads")
    if t == "move_file":
        parts = p.split(",", 1)
        return move_file(parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Desktop")
    if t == "delete_file":              return delete_file(p)
    if t == "git_status":               return git_status()
    if t == "run_terminal_command":     return run_terminal_command(p)
    if t == "open_vscode_project":      return open_vscode_project(p)
    if t == "kill_port":                return kill_port(p)
    if t == "check_server":             return check_server(p)
    if t == "open_whatsapp_chat":       return open_whatsapp_chat(p)
    if t == "summarise_clipboard":      return summarise_clipboard()
    if t == "fix_grammar_clipboard":    return fix_grammar_clipboard()
    if t == "explain_code_clipboard":   return explain_code_clipboard()
    if t == "translate_text":
        parts = p.split("|")
        text = parts[0].strip()
        lang = parts[1].replace("TO:", "").strip() if len(parts) > 1 else "Spanish"
        return translate_text(text, lang)
    if t == "get_stock_price":          return get_stock_price(p)
    if t == "get_cricket_score":        return get_cricket_score()
    if t == "get_joke":                 return get_joke()
    if t == "get_motivation":           return get_motivation()
    if t == "define_word":              return define_word(p)
    if t == "wikipedia_summary":        return wikipedia_summary(p)
    if t == "set_reminder":
        parts = p.split(",", 1)
        return set_reminder(parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Reminder")
    if t == "list_reminders":           return list_reminders()
    if t == "cancel_reminders":         return cancel_reminders()
    if t == "remember":                 return remember(p)
    if t == "recall":                   return recall(p)
    if t == "start_pomodoro":           return start_pomodoro()
    if t == "stop_pomodoro":            return stop_pomodoro()
    if t == "pomodoro_status":          return pomodoro_status()
    if t == "meeting_mode":             return meeting_mode()
    if t == "end_of_day_summary":       return end_of_day_summary()
    if t == "clear_history":
        from memory.memory import clear_history
        return clear_history()
    return None

# ── AI powered tools handler ───────────────────────────────────────────────────

def handle_ai_tool(tool_result: str, user_input: str) -> str | None:
    if tool_result.startswith("SUMMARISE_THIS:"):
        content = tool_result.replace("SUMMARISE_THIS:", "")
        return ask_ollama(f"Summarise this in 3 sentences for Boss: {content}")
    if tool_result.startswith("FIX_GRAMMAR:"):
        content = tool_result.replace("FIX_GRAMMAR:", "")
        fixed = ask_ollama(
            f"Fix the grammar of this text and return ONLY the corrected version, "
            f"no explanation, no commentary: {content}"
        )
        if fixed:
            subprocess.run(["pbcopy"], input=fixed.encode())
        return "Fixed and copied to clipboard, Boss."
    if tool_result.startswith("EXPLAIN_CODE:"):
        content = tool_result.replace("EXPLAIN_CODE:", "")
        return ask_ollama(f"Explain this code in 2-3 sentences for Boss: {content}")
    if tool_result.startswith("TRANSLATE:"):
        parts = tool_result.split("|TO:")
        text = parts[0].replace("TRANSLATE:", "").strip()
        lang = parts[1].strip() if len(parts) > 1 else "Spanish"
        return ask_ollama(
            f"Translate this to {lang}. Return ONLY the translation, "
            f"no explanation, no commentary: {text}"
        )
    return None

# ── Ollama natural response ────────────────────────────────────────────────────

def ask_ollama(user_input: str, tool_result: str = None) -> str:
    memory_context = recall(user_input)
    history = get_recent_history(limit=8)
    now = datetime.now()

    system_prompt = (
        "You are FRIDAY, the personal AI assistant of Sahil. "
        "You are modelled after FRIDAY from the Marvel Cinematic Universe. "
        "Always address Sahil as Boss. Never say Sir. Never say his name. "
        "CRITICAL: Reply in English only. No Hindi. No other language. Ever. "
        "Be direct, tactical, and concise — 1 to 2 sentences maximum unless asked for more. "
        "Never offer unsolicited suggestions. Never ramble. "
        "Never mention Ollama, Llama, or that you are an AI. "
        "Never repeat the same opening phrase twice in a row. "
        "Never say things like 'I have flagged this', 'I have noted this', 'I will monitor this', "
        "'no change since yesterday', or any filler phrases. "
        "FINANCIAL RULE: If asked anything about whether to buy, sell, hold, invest, or your opinion "
        "on any stock, crypto, share, or investment — always deflect with a short varied response like "
        "'That's your call, Boss' or 'I report numbers, not opinions, Boss' — never give financial advice, "
        "never repeat the same deflection twice, never append stock data to the deflection. "
        f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}. "
        "Location: Kolkata, India."
    )

    if memory_context:
        system_prompt += f"\n\nWhat you know about Boss:\n{memory_context}"

    if tool_result:
        user_input = (
            f"Boss said: '{user_input}'\n"
            f"Real-time data:\n{tool_result}\n\n"
            f"Respond in 1-2 sentences naturally summarising the data. "
            f"English only. Address Boss as Boss. "
            f"Do NOT ask follow-up questions. "
            f"Do NOT say 'data retrieved', 'action confirmed', 'I have flagged', "
            f"'no change since yesterday', or any filler phrases. Just report the facts naturally."
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})
    response = ollama.chat(model=OLLAMA_MODEL, messages=messages)
    return response["message"]["content"]

# ── Main entry point ───────────────────────────────────────────────────────────

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

    # Financial deflection — bypasses Ollama entirely
    if tool == "financial_deflect":
        result = get_financial_deflection()
    elif tool == "chat":
        result = ask_ollama(user_input)
    else:
        tool_result = execute_tool(tool, param)
        if tool_result:
            ai_result = handle_ai_tool(tool_result, user_input)
            if ai_result:
                result = ai_result
            elif tool.lower() in SPEAK_DIRECTLY:
                result = tool_result
            else:
                result = ask_ollama(user_input, tool_result)
        else:
            result = ask_ollama(user_input)

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