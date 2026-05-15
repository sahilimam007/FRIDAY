import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
import json
import chromadb
from datetime import datetime
from config import BASE_DIR

# ── Paths ──────────────────────────────────────────────────────────────────────
MEMORY_DIR   = os.path.join(BASE_DIR, "memory")
DB_PATH      = os.path.join(MEMORY_DIR, "friday.db")
CHROMA_PATH  = os.path.join(MEMORY_DIR, "chroma_store")

# ── ChromaDB client (long-term semantic memory) ────────────────────────────────
chroma_client    = chromadb.PersistentClient(path=CHROMA_PATH)
long_term_memory = chroma_client.get_or_create_collection(name="friday_memory")

# ── SQLite setup (short-term conversation history) ────────────────────────────
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
# SHORT-TERM MEMORY  (SQLite — last N conversation turns)
# ══════════════════════════════════════════════════════════════════════════════

def save_message(role: str, content: str):
    """Save a single conversation turn."""
    conn = _get_conn()
    conn.execute(
        "INSERT INTO conversations (role, content, timestamp) VALUES (?, ?, ?)",
        (role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 10) -> list[dict]:
    """Return the last N conversation turns."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


def clear_history():
    """Wipe the short-term conversation history."""
    conn = _get_conn()
    conn.execute("DELETE FROM conversations")
    conn.commit()
    conn.close()
    return "Conversation history cleared, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# LONG-TERM MEMORY  (ChromaDB — semantic facts & notes)
# ══════════════════════════════════════════════════════════════════════════════

def remember(fact: str, tags: list[str] | None = None):
    """Store a fact in long-term memory."""
    doc_id   = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "tags": json.dumps(tags or [])
    }
    long_term_memory.add(
        documents=[fact],
        metadatas=[metadata],
        ids=[doc_id]
    )
    return "Noted, Boss. I'll remember that."


def recall(query: str, top_k: int = 3) -> str:
    """Retrieve relevant facts from long-term memory."""
    count = long_term_memory.count()
    if count == 0:
        return ""
    results = long_term_memory.query(
        query_texts=[query],
        n_results=min(top_k, count)
    )
    docs = results.get("documents", [[]])[0]
    if not docs:
        return ""
    return "Relevant memory:\n" + "\n".join(f"- {d}" for d in docs)


def forget_all():
    """Wipe all long-term memories."""
    ids = long_term_memory.get()["ids"]
    if ids:
        long_term_memory.delete(ids=ids)
    return "All long-term memories erased, Boss."


# ══════════════════════════════════════════════════════════════════════════════
# QUICK TEST
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    save_message("user", "What is the weather today?")
    save_message("assistant", "It is 31 degrees and humid in Kolkata, Boss.")
    print("Recent history:", get_recent_history())
    print(remember("Boss prefers dark mode on all apps", tags=["preference"]))
    print(remember("Boss is building Friday on a MacBook Pro M1 Pro", tags=["about"]))
    print(recall("what machine does Boss use"))