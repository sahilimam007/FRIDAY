import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ollama
import json
import re
import random
import subprocess
from datetime import datetime
from config import OLLAMA_MODEL

# ── Core imports ───────────────────────────────────────────────────────────────
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
    set_brightness, brightness_up, brightness_down,
    keyboard_backlight_up, keyboard_backlight_down, keyboard_backlight_off,
    connect_airpods, disconnect_airpods, list_bluetooth_devices,
    read_notifications, clear_notifications,
    vpn_connect, vpn_disconnect, open_incognito,
    move_window, resize_window, close_active_window,
    take_screenshot, lock_screen, sleep_mac,
    get_battery, get_system_info, get_ip, ping_host,
    wifi_on, wifi_off, bluetooth_on, bluetooth_off,
    do_not_disturb_on, do_not_disturb_off,
    get_clipboard, set_clipboard, paste_clipboard, type_text, press_key,
    play_song, pause_music, resume_music,
    next_track, previous_track, get_current_track, set_music_volume,
    calculate, convert_units, convert_currency,
    set_timer, start_stopwatch, stop_stopwatch, start_pomodoro,
    focus_mode, vibe_mode, night_mode,
    take_note, read_notes,
    find_file, open_file_or_folder, create_folder, list_files, move_file, delete_file,
    git_status, run_terminal_command, open_vscode_project, kill_port, check_server,
    open_whatsapp_chat,
    summarise_clipboard, fix_grammar_clipboard, explain_code_clipboard, translate_text,
    get_stock_price, get_cricket_score, get_joke, get_motivation, define_word, wikipedia_summary,
)
from tools.reminder import set_reminder, list_reminders, cancel_reminders
from tools.productivity import (
    start_pomodoro as prod_start_pomodoro,
    stop_pomodoro, pomodoro_status,
    focus_mode as prod_focus_mode,
    meeting_mode, end_of_day_summary
)
from tools.alerts import (
    start_battery_monitor, stop_battery_monitor,
    check_weather_alert,
    start_weather_monitor, stop_weather_monitor,
    set_repeating_alert, stop_repeating_alert, list_repeating_alerts,
    start_news_monitor, stop_news_monitor,
    alert_status
)
from tools.clipboard import (
    get_clipboard as clip_get,
    summarise_clipboard as clip_summarise,
    fix_grammar_clipboard,
    set_clipboard as clip_set,
    paste_clipboard as clip_paste,
    copy_selection, dictate_text,
    explain_clipboard_code, debug_clipboard_error, clear_clipboard
)
from tools.security import (
    generate_password, generate_pin, generate_passphrase,
    hash_text, check_password_strength
)
from tools.calendar import (
    get_todays_events, get_tomorrows_events, get_weeks_events,
    get_next_event, create_event, delete_event,
    get_todays_reminders, add_reminder, complete_reminder,
    open_calendar, open_reminders
)
from tools.music import (
    play_playlist, play_artist, stop_music, list_playlists,
    shuffle_on, shuffle_off, repeat_on, repeat_off,
    play_radio, stop_radio, list_radio_stations,
    play_ambient, stop_ambient, stop_all_audio
)
from tools.info import (
    wikipedia_summary as info_wikipedia,
    convert_currency as info_currency,
    convert_units as info_units,
    get_flight_status, track_package,
    get_cricket_score as info_cricket,
    get_ipl_score, get_football_score, get_f1_next_race, get_f1_standings,
    get_sports_score, get_movie_info, whats_streaming,
    get_recipe, get_random_recipe,
    define_word as info_define, get_synonyms, get_antonyms,
    translate_text as info_translate
)
from tools.developer import (
    git_status as dev_git_status,
    git_add_commit_push, git_log, git_diff,
    open_vscode as dev_open_vscode,
    run_command, kill_port as dev_kill_port,
    check_server as dev_check_server,
    check_localhost, list_installed_packages,
    check_python_version, run_python_file,
    get_project_structure, count_lines_of_code
)
from memory.memory import save_message, get_recent_history, remember, recall

# ── Financial deflection ───────────────────────────────────────────────────────
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

FINANCIAL_QUESTION_WORDS = [
    "should i buy", "should i sell", "is it worth", "worth buying",
    "worth investing", "good investment", "good stock", "good time to buy",
    "good time to invest", "what do you think about", "your opinion on",
    "your take on", "recommend", "thoughts on", "is it a good", "should i get",
    "should i invest", "is it safe to", "will it go up", "will it go down",
    "will it rise", "will it fall", "is it overvalued", "is it undervalued",
    "worth it", "should i put money", "should i hold",
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
    has_asset    = any(a in lower for a in FINANCIAL_ASSET_WORDS)
    if has_question and has_asset:
        return True
    PRICE_PREDICTION_WORDS = ["will", "going to", "gonna", "predict", "forecast"]
    if any(w in lower for w in PRICE_PREDICTION_WORDS) and has_asset:
        return True
    return False

# ── Battery output cleaner ─────────────────────────────────────────────────────
def clean_battery_output(raw: str) -> str:
    """Parse raw pmset battery output into a clean readable string."""
    try:
        percent_match = re.search(r'(\d+)%', raw)
        time_match    = re.search(r'(\d+:\d+) remaining', raw)
        charging      = "charging" in raw.lower()
        charged       = "charged" in raw.lower()

        percent = percent_match.group(1) if percent_match else "?"
        time_str = time_match.group(1) if time_match else None

        if charged:
            return f"Battery at {percent}%, fully charged, Boss."
        elif charging:
            if time_str:
                return f"Battery at {percent}%, charging. Full in {time_str}, Boss."
            return f"Battery at {percent}%, charging, Boss."
        else:
            if time_str:
                return f"Battery at {percent}%, {time_str} remaining, Boss."
            return f"Battery at {percent}%, discharging, Boss."
    except Exception:
        return raw  # fallback to raw if parsing fails

# ── Tool list ──────────────────────────────────────────────────────────────────
TOOLS = """
get_weather, get_news(world/tech/india/science/business/sports),
search(query), play_song(name), play_playlist(name), play_artist(name),
play_radio(station), play_ambient(sound), stop_music, stop_radio, stop_ambient,
stop_all_audio, list_playlists, list_radio_stations,
shuffle_on, shuffle_off, repeat_on, repeat_off,
pause_music, resume_music, next_track, previous_track,
get_current_track, set_music_volume(0-100),
open_youtube(query), open_maps(location), compose_email, open_news_tabs,
open_app(name), close_app(name), force_quit(name), switch_to_app(name),
list_running_apps, minimize_window, hide_app, show_desktop, empty_trash,
restart_mac, shutdown_mac, snap_left, snap_right, fullscreen,
close_tab, new_tab, picture_in_picture,
set_volume(0-100), mute, unmute, get_volume,
set_brightness(level), brightness_up, brightness_down,
keyboard_backlight_up, keyboard_backlight_down, keyboard_backlight_off,
connect_airpods, disconnect_airpods, list_bluetooth_devices,
read_notifications, clear_notifications,
vpn_connect, vpn_disconnect, open_incognito(url),
get_battery, get_system_info, get_ip, ping_host(host),
wifi_on, wifi_off, bluetooth_on, bluetooth_off,
do_not_disturb_on, do_not_disturb_off,
get_clipboard, set_clipboard(text), paste_clipboard, type_text(text),
take_screenshot, lock_screen, sleep_mac,
calculate(expression), convert_units(expression), convert_currency(expression),
set_timer(duration, label), start_stopwatch, stop_stopwatch,
start_pomodoro, stop_pomodoro, pomodoro_status,
focus_mode, vibe_mode, night_mode, meeting_mode, end_of_day_summary,
take_note(text), read_notes,
find_file(name), open_file_or_folder(name), create_folder(name),
list_files(folder), move_file(filename|destination), delete_file(name),
git_status, git_commit(message), git_log, run_command(command),
open_vscode(project), kill_port(port), check_server(port),
count_lines_of_code, get_project_structure,
open_whatsapp_chat(contact),
summarise_clipboard, fix_grammar_clipboard, explain_code_clipboard,
dictate_text(text), generate_password, generate_pin, generate_passphrase,
check_password_strength(password), hash_text(text),
get_todays_events, get_tomorrows_events, get_weeks_events,
get_next_event, create_event(title|date|time), delete_event(title),
get_todays_reminders, add_reminder(task), complete_reminder(task),
open_calendar, open_reminders,
translate_text(text|language),
get_flight_status(flight), track_package(tracking_number),
get_sports_score(sport), get_ipl_score, get_cricket_score,
get_football_score, get_f1_next_race, get_f1_standings,
get_movie_info(title), whats_streaming(service),
get_recipe(dish), get_random_recipe,
define_word(word), get_synonyms(word), get_antonyms(word),
wikipedia_summary(topic), get_stock_price(symbol),
get_joke, get_motivation,
start_battery_monitor, stop_battery_monitor,
start_weather_monitor, stop_weather_monitor, check_weather_alert,
start_news_monitor, stop_news_monitor,
set_repeating_alert(label|interval_mins), stop_repeating_alert(label),
list_repeating_alerts, alert_status,
set_reminder(duration|label), list_reminders, cancel_reminders,
remember(fact), recall(query), clear_history, chat
"""

# ── SPEAK_DIRECTLY — results spoken as-is, never re-processed by Ollama ───────
SPEAK_DIRECTLY = {
    # Search & News
    "search",
    "get_news",

    # Info lookups
    "get_joke", "get_motivation", "define_word", "wikipedia_summary",
    "get_synonyms", "get_antonyms",
    "get_movie_info", "get_recipe", "get_random_recipe",
    "get_flight_status", "track_package",

    # System
    "get_battery", "get_system_info", "get_ip", "ping_host",
    "list_files", "list_running_apps", "get_clipboard", "read_notes",
    "find_file", "get_volume",

    # Developer
    "git_status", "run_command", "check_server",
    "count_lines_of_code", "get_project_structure",

    # Math & conversion
    "calculate", "convert_units", "convert_currency",

    # Stocks & sports
    "get_stock_price", "get_weather",
    "get_sports_score", "get_ipl_score",
    "get_cricket_score", "get_football_score",
    "get_f1_next_race", "get_f1_standings",

    # Calendar & reminders
    "get_todays_events", "get_tomorrows_events", "get_weeks_events",
    "get_next_event", "get_todays_reminders", "list_reminders",
    "list_repeating_alerts", "alert_status", "pomodoro_status",

    # Music state
    "get_current_track", "list_playlists", "list_radio_stations",
    "list_bluetooth_devices",

    # Clipboard AI tools — fix_grammar runs Ollama internally, speak directly
    # summarise_clipboard and explain_code_clipboard use SUMMARISE:/EXPLAIN_CODE: prefix
    # so they must go through handle_ai_tool — do NOT add them here
    "fix_grammar_clipboard", "translate_text", "word_count_clipboard",

    # Security
    "generate_password", "generate_pin", "generate_passphrase",
    "check_password_strength", "hash_text",

    # Memory
    "recall",
}

# ── Intent classifier ──────────────────────────────────────────────────────────
def classify_intent(user_input: str) -> dict:
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
- For translate_text: param = "text|language"
- For create_event: param = "title|date|time"
- For set_reminder: param = "duration|label"
- For set_repeating_alert: param = "label|interval_mins"
- For move_file: param = "filename|destination"
- For get_stock_price: param must be ticker symbol only (e.g. AAPL, TSLA, RELIANCE.NS)
- For wikipedia_summary: param must be the topic only (e.g. Nikola Tesla) — no prefix words
- For get_news: param must be ONE word only: world, tech, india, science, business, or sports
- Questions asking opinions about stocks/crypto = financial_deflect
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

    # Clean common classifier prefixes from params
    def clean_param(val, *prefixes):
        for prefix in prefixes:
            val = re.sub(rf'(?i){re.escape(prefix)}\s*=\s*', '', val).strip()
        return val

    # Weather & News
    if t == "get_weather":             return get_weather()
    if t == "get_news":                return get_news(p or "world")
    if t == "search":                  return search(p)

    # Music
    if t == "play_song":
        if not p:
            return "What would you like me to play, Boss?"
        return play_song(p)
    if t == "play_playlist":           return play_playlist(p)
    if t == "play_artist":             return play_artist(p)
    if t == "play_radio":              return play_radio(p)
    if t == "play_ambient":            return play_ambient(p)
    if t == "stop_music":              return stop_music()
    if t == "stop_radio":              return stop_radio()
    if t == "stop_ambient":            return stop_ambient()
    if t == "stop_all_audio":          return stop_all_audio()
    if t == "list_playlists":          return list_playlists()
    if t == "list_radio_stations":     return list_radio_stations()
    if t == "shuffle_on":              return shuffle_on()
    if t == "shuffle_off":             return shuffle_off()
    if t == "repeat_on":               return repeat_on()
    if t == "repeat_off":              return repeat_off()
    if t == "pause_music":             return pause_music()
    if t == "resume_music":            return resume_music()
    if t == "next_track":              return next_track()
    if t == "play_next_track":         return next_track()   # alias
    if t == "previous_track":          return previous_track()
    if t == "get_current_track":       return get_current_track()
    if t == "set_music_volume":        return set_music_volume(int(p) if p.isdigit() else 50)

    # Browser
    if t == "open_youtube":            return open_youtube_autoplay(p) if p else open_youtube()
    if t == "open_maps":               return open_maps(p)
    if t == "compose_email":           return compose_email()
    if t == "open_news_tabs":          return open_news_tabs()
    if t == "open_whatsapp_chat":      return open_whatsapp_chat(p)

    # App control
    if t == "open_app":                return open_app(p)
    if t == "close_app":               return close_app(p)
    if t == "force_quit":              return force_quit(p)
    if t == "switch_to_app":           return switch_to_app(p)
    if t == "list_running_apps":       return list_running_apps()
    if t == "minimize_window":         return minimize_window()
    if t == "hide_app":                return hide_app()
    if t == "show_desktop":            return show_desktop()
    if t == "empty_trash":             return empty_trash()
    if t == "restart_mac":             return restart_mac()
    if t == "shutdown_mac":            return shutdown_mac()
    if t == "snap_left":               return snap_left()
    if t == "snap_right":              return snap_right()
    if t == "fullscreen":              return fullscreen()
    if t == "close_tab":               return close_tab()
    if t == "new_tab":                 return new_tab()
    if t == "picture_in_picture":      return picture_in_picture()

    # Volume & Display
    if t == "set_volume":              return set_volume(int(p) if p.isdigit() else 50)
    if t == "mute":                    return mute()
    if t == "unmute":                  return unmute()
    if t == "get_volume":              return get_volume()
    if t == "set_brightness":
        p = clean_param(p, "level")
        return set_brightness(p)
    if t == "brightness_up":           return brightness_up()
    if t == "brightness_down":         return brightness_down()
    if t == "keyboard_backlight_up":   return keyboard_backlight_up()
    if t == "keyboard_backlight_down": return keyboard_backlight_down()
    if t == "keyboard_backlight_off":  return keyboard_backlight_off()

    # Connectivity
    if t == "connect_airpods":         return connect_airpods(p or "AirPods")
    if t == "disconnect_airpods":      return disconnect_airpods(p or "AirPods")
    if t == "list_bluetooth_devices":  return list_bluetooth_devices()
    if t == "vpn_connect":             return vpn_connect(p)
    if t == "vpn_disconnect":          return vpn_disconnect(p)
    if t == "open_incognito":          return open_incognito(p)
    if t == "wifi_on":                 return wifi_on()
    if t == "wifi_off":                return wifi_off()
    if t == "bluetooth_on":            return bluetooth_on()
    if t == "bluetooth_off":           return bluetooth_off()
    if t == "do_not_disturb_on":       return do_not_disturb_on()
    if t == "do_not_disturb_off":      return do_not_disturb_off()
    if t == "read_notifications":      return read_notifications()
    if t == "clear_notifications":     return clear_notifications()

    # System
    if t == "get_battery":
        raw = get_battery()
        return clean_battery_output(raw)
    if t == "get_system_info":         return get_system_info()
    if t == "get_ip":                  return get_ip()
    if t == "ping_host":               return ping_host(p)
    if t == "take_screenshot":         return take_screenshot()
    if t == "lock_screen":             return lock_screen()
    if t == "sleep_mac":               return sleep_mac()

    # Clipboard
    if t == "get_clipboard":           return clip_get()
    if t == "set_clipboard":           return clip_set(p)
    if t == "paste_clipboard":         return clip_paste()
    if t == "summarise_clipboard":     return clip_summarise()
    if t == "fix_grammar_clipboard":   return fix_grammar_clipboard()
    if t == "explain_code_clipboard":  return explain_clipboard_code()
    if t == "type_text":               return type_text(p)
    if t == "dictate_text":            return dictate_text(p)

    # Security
    if t == "generate_password":       return generate_password()
    if t == "generate_pin":            return generate_pin()
    if t == "generate_passphrase":     return generate_passphrase()
    if t == "hash_text":               return hash_text(p)
    if t == "check_password_strength": return check_password_strength(p)

    # Math
    if t == "calculate":               return calculate(p)
    if t == "convert_units":           return info_units(p)
    if t == "convert_currency":        return info_currency(p)

    # Timer
    if t == "set_timer":
        parts = p.split("|", 1)
        return set_timer(parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Timer")
    if t == "start_stopwatch":         return start_stopwatch()
    if t == "stop_stopwatch":          return stop_stopwatch()

    # Productivity
    if t == "start_pomodoro":          return prod_start_pomodoro()
    if t == "stop_pomodoro":           return stop_pomodoro()
    if t == "pomodoro_status":         return pomodoro_status()
    if t == "focus_mode":              return prod_focus_mode()
    if t == "vibe_mode":               return vibe_mode()
    if t == "night_mode":              return night_mode()
    if t == "meeting_mode":            return meeting_mode()
    if t == "end_of_day_summary":      return end_of_day_summary()

    # Notes
    if t == "take_note":               return take_note(p)
    if t == "read_notes":              return read_notes()

    # Files
    if t == "find_file":               return find_file(p)
    if t == "open_file_or_folder":     return open_file_or_folder(p)
    if t == "create_folder":           return create_folder(p)
    if t == "list_files":              return list_files(p or "~/Downloads")
    if t == "move_file":
        parts = p.split("|", 1)
        return move_file(parts[0].strip(), parts[1].strip() if len(parts) > 1 else "Desktop")
    if t == "delete_file":             return delete_file(p)

    # Developer
    if t == "git_status":              return dev_git_status()
    if t == "git_commit":              return git_add_commit_push(p)
    if t == "git_log":                 return git_log()
    if t == "run_command":             return run_command(p)
    if t == "open_vscode":             return dev_open_vscode(p or "friday")
    if t == "kill_port":               return dev_kill_port(p)
    if t == "check_server":            return dev_check_server(p)
    if t == "count_lines_of_code":     return count_lines_of_code()
    if t == "get_project_structure":   return get_project_structure()

    # Calendar
    if t == "get_todays_events":       return get_todays_events()
    if t == "get_tomorrows_events":    return get_tomorrows_events()
    if t == "get_weeks_events":        return get_weeks_events()
    if t == "get_next_event":          return get_next_event()
    if t == "create_event":
        parts = p.split("|")
        title = parts[0].strip() if parts else p
        date  = parts[1].strip() if len(parts) > 1 else "today"
        time  = parts[2].strip() if len(parts) > 2 else "9am"
        return create_event(title, date, time)
    if t == "delete_event":            return delete_event(p)
    if t == "get_todays_reminders":    return get_todays_reminders()
    if t == "add_reminder":            return add_reminder(p)
    if t == "complete_reminder":       return complete_reminder(p)
    if t == "open_calendar":           return open_calendar()
    if t == "open_reminders":          return open_reminders()

    # Info
    if t == "wikipedia_summary":
        p = clean_param(p, "topic", "query", "subject")
        return info_wikipedia(p)
    if t == "define_word":             return info_define(p)
    if t == "get_synonyms":            return get_synonyms(p)
    if t == "get_antonyms":            return get_antonyms(p)
    if t == "translate_text":
        parts = p.split("|")
        text = parts[0].strip()
        lang = parts[1].strip() if len(parts) > 1 else "hindi"
        return info_translate(text, lang)
    if t == "get_flight_status":       return get_flight_status(p)
    if t == "track_package":           return track_package(p)
    if t == "get_sports_score":        return get_sports_score(p)
    if t == "get_ipl_score":           return get_ipl_score()
    if t == "get_cricket_score":       return info_cricket()
    if t == "get_football_score":      return get_football_score()
    if t == "get_f1_next_race":        return get_f1_next_race()
    if t == "get_f1_standings":        return get_f1_standings()
    if t == "get_movie_info":          return get_movie_info(p)
    if t == "whats_streaming":         return whats_streaming(p)
    if t == "get_recipe":              return get_recipe(p)
    if t == "get_random_recipe":       return get_random_recipe()
    if t == "get_stock_price":
        p = clean_param(p, "symbol", "ticker")
        return get_stock_price(p.upper())
    if t == "get_joke":                return get_joke()
    if t == "get_motivation":          return get_motivation()

    # Alerts
    if t == "start_battery_monitor":   return start_battery_monitor()
    if t == "stop_battery_monitor":    return stop_battery_monitor()
    if t == "check_weather_alert":     return check_weather_alert()
    if t == "start_weather_monitor":   return start_weather_monitor()
    if t == "stop_weather_monitor":    return stop_weather_monitor()
    if t == "start_news_monitor":      return start_news_monitor()
    if t == "stop_news_monitor":       return stop_news_monitor()
    if t == "set_repeating_alert":
        parts = p.split("|", 1)
        label = parts[0].strip()
        mins  = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else 30
        return set_repeating_alert(label, mins)
    if t == "stop_repeating_alert":    return stop_repeating_alert(p)
    if t == "list_repeating_alerts":   return list_repeating_alerts()
    if t == "alert_status":            return alert_status()

    # Reminders & Memory
    if t == "set_reminder":
        parts = p.split("|", 1)
        duration = parts[0].strip()
        label    = parts[1].strip() if len(parts) > 1 else "Reminder"
        return set_reminder(duration, label)
    if t == "list_reminders":          return list_reminders()
    if t == "cancel_reminders":        return cancel_reminders()
    if t == "remember":
        p = clean_param(p, "fact")
        return remember(p)
    if t == "recall":
        p = clean_param(p, "query", "topic")
        return recall(p)
    if t == "clear_history":
        from memory.memory import clear_history
        return clear_history()

    return None

# ── AI powered clipboard handler ───────────────────────────────────────────────
def handle_ai_tool(tool_result: str, user_input: str) -> str | None:
    if tool_result.startswith("SUMMARISE:"):
        content = tool_result.replace("SUMMARISE:", "")
        return ask_ollama(f"Summarise this in 3 sentences for Boss: {content}")
    if tool_result.startswith("EXPLAIN_CODE:"):
        content = tool_result.replace("EXPLAIN_CODE:", "")
        return ask_ollama(f"Explain this code in 2-3 sentences for Boss: {content}")
    if tool_result.startswith("DEBUG_ERROR:"):
        content = tool_result.replace("DEBUG_ERROR:", "")
        return ask_ollama(f"Explain this error and suggest a fix in 2-3 sentences for Boss: {content}")
    return None

# ── Ollama natural response ────────────────────────────────────────────────────
def ask_ollama(user_input: str, tool_result: str = None) -> str:
    memory_context = recall(user_input)
    history = get_recent_history(limit=8)
    now = datetime.now()

    system_prompt = (
        "You are FRIDAY, the personal AI assistant of Sahil. "
        "Modelled after FRIDAY from the Marvel Cinematic Universe. "
        "Address Sahil as Boss — sometimes omit for natural flow. Never say Sir or his name. "
        "Reply in English only. No Hindi. No other language. Ever. "
        "Be direct, tactical, concise — 1 to 2 sentences maximum unless asked for more. "
        "Never offer unsolicited suggestions. Never ramble. "
        "Never mention Ollama, Llama, or that you are an AI. "
        "Never repeat the same opening phrase twice in a row. "
        "CRITICAL: If tool result is provided, base response ONLY on that result. "
        "Never claim an action was done if no tool result was given. "
        f"Current time: {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}. "
        "Location: Kolkata, India."
    )

    if memory_context:
        system_prompt += f"\n\nWhat you know about Boss:\n{memory_context}"

    if tool_result:
        user_input = (
            f"Boss said: '{user_input}'\n"
            f"System result: {tool_result}\n\n"
            f"Respond in 1-2 sentences confirming the action. "
            f"Base your response ONLY on the system result. "
            f"Do NOT add extra information or hallucinate."
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