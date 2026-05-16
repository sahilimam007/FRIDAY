import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
import re
import chromadb
from datetime import datetime, timedelta
from config import BASE_DIR, OLLAMA_MODEL

# ── Paths ──────────────────────────────────────────────────────────────────────
MEMORY_DIR   = os.path.join(BASE_DIR, "memory")
DB_PATH      = os.path.join(MEMORY_DIR, "friday.db")
CHROMA_PATH  = os.path.join(MEMORY_DIR, "chroma_store")

# ── ChromaDB client ────────────────────────────────────────────────────────────
chroma_client    = chromadb.PersistentClient(path=CHROMA_PATH)
long_term_memory = chroma_client.get_or_create_collection(name="friday_memory")

# ── SQLite setup ───────────────────────────────────────────────────────────────
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            role      TEXT    NOT NULL,
            content   TEXT    NOT NULL,
            timestamp TEXT    NOT NULL
        )
    """)
    conn.commit()
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# DATE RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

def resolve_dates(fact: str) -> str:
    today = datetime.now()
    text  = fact.lower()

    if "today" in text:
        fact = re.sub(r'\btoday\b', today.strftime("%A %d %B %Y"), fact, flags=re.IGNORECASE)

    if "tomorrow" in text:
        tomorrow = today + timedelta(days=1)
        fact = re.sub(r'\btomorrow\b', tomorrow.strftime("%A %d %B %Y"), fact, flags=re.IGNORECASE)

    if "day after tomorrow" in text:
        dat = today + timedelta(days=2)
        fact = re.sub(r'\bday after tomorrow\b', dat.strftime("%A %d %B %Y"), fact, flags=re.IGNORECASE)

    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for i, day in enumerate(days):
        if f"next {day}" in text:
            days_ahead = (i - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = today + timedelta(days=days_ahead)
            fact = re.sub(
                rf'\bnext {day}\b',
                target.strftime("%A %d %B %Y"),
                fact, flags=re.IGNORECASE
            )

    for i, day in enumerate(days):
        if f"this {day}" in text:
            days_ahead = (i - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            target = today + timedelta(days=days_ahead)
            fact = re.sub(
                rf'\bthis {day}\b',
                target.strftime("%A %d %B %Y"),
                fact, flags=re.IGNORECASE
            )

    return fact


# ══════════════════════════════════════════════════════════════════════════════
# SHORT-TERM MEMORY  (SQLite)
# ══════════════════════════════════════════════════════════════════════════════

def save_message(role: str, content: str):
    conn = _get_conn()
    conn.execute(
        "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def clear_history():
    conn = _get_conn()
    conn.execute("DELETE FROM conversations")
    conn.commit()
    conn.close()
    return "Conversation history cleared, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# LONG-TERM MEMORY  (ChromaDB)
# ══════════════════════════════════════════════════════════════════════════════

def remember(fact: str, tags: list[str] | None = None):
    resolved = resolve_dates(fact)
    doc_id   = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "saved_on":  datetime.now().strftime("%A %d %B %Y"),
        "tags":      json.dumps(tags or [])
    }
    long_term_memory.add(
        documents=[resolved],
        metadatas=[metadata],
        ids=[doc_id]
    )
    return "Noted, Boss. I'll remember that."


def recall(query: str, top_k: int = 3) -> str:
    count = long_term_memory.count()
    if count == 0:
        return ""
    results = long_term_memory.query(
        query_texts=[query],
        n_results=min(top_k, count)
    )
    docs      = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    if not docs:
        return ""

    lines = []
    for doc, meta in zip(docs, metadatas):
        saved_on = meta.get("saved_on", "")
        lines.append(f"- {doc} (saved: {saved_on})")

    return "Relevant memory:\n" + "\n".join(lines)


def forget_all():
    ids = long_term_memory.get()["ids"]
    if ids:
        long_term_memory.delete(ids=ids)
    return "All long-term memories erased, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# STARTUP CHECK — events today or tomorrow
# ══════════════════════════════════════════════════════════════════════════════

def check_upcoming_events() -> str | None:
    count = long_term_memory.count()
    if count == 0:
        return None

    today    = datetime.now()
    tomorrow = today + timedelta(days=1)

    today_str    = today.strftime("%A %d %B %Y")
    tomorrow_str = tomorrow.strftime("%A %d %B %Y")

    results_today = long_term_memory.query(
        query_texts=[f"event on {today_str}"],
        n_results=min(5, count)
    )
    results_tomorrow = long_term_memory.query(
        query_texts=[f"event on {tomorrow_str}"],
        n_results=min(5, count)
    )

    reminders = []

    for doc in results_today.get("documents", [[]])[0]:
        if today_str in doc:
            reminders.append(f"Today: {doc}")

    for doc in results_tomorrow.get("documents", [[]])[0]:
        if tomorrow_str in doc:
            reminders.append(f"Tomorrow: {doc}")

    if not reminders:
        return None

    return "Heads up, Boss — " + " | ".join(reminders)


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing date resolver:")
    print(resolve_dates("I have a meeting tomorrow"))
    print(resolve_dates("exam on next monday"))

    print("\nTesting remember + recall:")
    print(remember("Boss has a meeting tomorrow at 3pm"))
    print(recall("meeting"))

    print("\nTesting startup check:")
    print(check_upcoming_events())
    