import requests
import json
import sqlite3
import os
from datetime import datetime
import config

# ── Database setup ────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(config.SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            role      TEXT NOT NULL,
            content   TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_message(role: str, content: str):
    conn = sqlite3.connect(config.SQLITE_PATH)
    conn.execute(
        "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def load_recent_history(limit: int = 10) -> list:
    conn = sqlite3.connect(config.SQLITE_PATH)
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    # return in chronological order
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

# ── Ollama chat ───────────────────────────────────────────────────────────────
def ask_ollama(user_input: str, extra_context: str = "") -> str:
    history = load_recent_history()

    # build system prompt with current time + date
    now = datetime.now()
    system = (
        f"You are JARVIS, the personal AI assistant of Sahil. "
        f"Always address him as Sir. Be concise, witty, and British. "
        f"Never mention Ollama or that you are an AI. "
        f"Current time is {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}. "
        f"Location: Kolkata, India."
    )

    if extra_context:
        system += f"\n\nReal-time data for this query:\n{extra_context}"

    messages = [{"role": "system", "content": system}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    # pick model — try jarvis first, fall back to llama3.2
    for model in [config.OLLAMA_MODEL, config.OLLAMA_FALLBACK]:
        try:
            response = requests.post(
                f"{config.OLLAMA_URL}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
                timeout=config.LLM_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                reply = data["message"]["content"].strip()
                save_message("user", user_input)
                save_message("assistant", reply)
                return reply
        except Exception as e:
            if config.DEBUG:
                print(f"[Orchestrator] Model {model} failed: {e}")
            continue

    return "I'm having trouble connecting to my brain, Sir. Please ensure Ollama is running."

# ── Intent detection ──────────────────────────────────────────────────────────
def detect_intent(text: str) -> str:
    text = text.lower().strip()

    if any(w in text for w in ["weather", "temperature", "forecast", "rain", "hot", "cold"]):
        return "weather"
    if any(w in text for w in ["news", "headline", "what's happening", "today", "world"]):
        return "news"
    if any(w in text for w in ["open", "launch", "start", "go to", "show me", "browse"]):
        return "browser"
    if any(w in text for w in ["search", "look up", "find", "google", "what is", "who is"]):
        return "search"
    if any(w in text for w in ["volume", "brightness", "mute", "screenshot", "close", "quit"]):
        return "mac_control"
    if any(w in text for w in ["remember", "forget", "what do you know about me"]):
        return "memory"
    if any(w in text for w in ["time", "date", "day"]):
        return "time"

    return "chat"

# ── Time handler ─────────────────────────────────────────────────────────────
def handle_time() -> str:
    now = datetime.now()
    return (
        f"It is {now.strftime('%I:%M %p')} on {now.strftime('%A, %d %B %Y')}, Sir."
    )

# ── Main process function ─────────────────────────────────────────────────────
def process(user_input: str) -> str:
    if not user_input.strip():
        return ""

    intent = detect_intent(user_input)

    if config.DEBUG:
        print(f"[Orchestrator] Intent: {intent}")

    # time — no need to call LLM
    if intent == "time":
        return handle_time()

    # for everything else, call LLM (tools will add context in later phases)
    return ask_ollama(user_input)

# ── Terminal test loop ────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  JARVIS — Terminal Mode")
    print("  Type 'quit' to exit")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["quit", "exit", "bye"]:
                print("Jarvis: Goodbye, Sir. Always a pleasure.")
                break
            if not user_input:
                continue
            print("Jarvis: thinking...", end="\r")
            response = process(user_input)
            print(f"Jarvis: {response}          ")
        except KeyboardInterrupt:
            print("\nJarvis: Shutting down, Sir.")
            break
        