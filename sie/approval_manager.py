import os, sys, sqlite3, importlib, shutil
from datetime import datetime

# ─── configuration ────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sie.db")
APPROVED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "approved")

# ensure the approved tools directory exists
os.makedirs(APPROVED_DIR, exist_ok=True)

# ─── database helpers ─────────────────────────────────────────────────
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def _init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pending_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS approved_tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            file_path TEXT NOT NULL,
            approved_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

_init_db()

# ─── pending queue functions ──────────────────────────────────────────
def add_pending_tool(name: str, description: str, code: str) -> int:
    """Add a new tool to the pending queue. Returns the tool id."""
    conn = _get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO pending_tools (name, description, code) VALUES (?, ?, ?)",
            (name, description, code)
        )
        tool_id = cursor.lastrowid
        conn.commit()
        return tool_id
    except sqlite3.IntegrityError:
        # tool with this name already exists
        return 0
    finally:
        conn.close()

def get_pending_tools() -> list[dict]:
    """Return all tools waiting for approval."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM pending_tools ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pending_count() -> int:
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM pending_tools").fetchone()[0]
    conn.close()
    return count

def reject_tool(tool_id: int) -> bool:
    """Delete a tool from the pending queue."""
    conn = _get_conn()
    conn.execute("DELETE FROM pending_tools WHERE id = ?", (tool_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0

# ─── approval & dynamic loading ───────────────────────────────────────
def approve_tool(tool_id: int) -> str | None:
    """
    Approve a pending tool:
    - move its code into tools/approved/<tool_name>.py
    - save to approved_tools table
    - delete from pending queue
    - reload registered tools
    Returns the tool name if successful, else None.
    """
    conn = _get_conn()
    row = conn.execute("SELECT * FROM pending_tools WHERE id = ?", (tool_id,)).fetchone()
    if not row:
        conn.close()
        return None

    name, code = row["name"], row["code"]
    # sanitise filename
    safe_name = name.lower().replace(" ", "_").replace("-", "_")
    file_path = os.path.join(APPROVED_DIR, f"{safe_name}.py")

    # write the code (with necessary imports if missing)
    try:
        with open(file_path, "w") as f:
            f.write(code)
    except Exception:
        conn.close()
        return None

    # remove from pending, add to approved
    conn.execute("DELETE FROM pending_tools WHERE id = ?", (tool_id,))
    conn.execute("INSERT INTO approved_tools (name, file_path) VALUES (?, ?)", (name, file_path))
    conn.commit()
    conn.close()

    # reload approved tools into memory
    reload_approved_tools()
    return name

# ─── runtime execution of approved tools ──────────────────────────────
# In-memory cache: tool_name -> callable (function)
_approved_functions = {}

def reload_approved_tools():
    """Import all approved tools from the tools/approved/ directory."""
    global _approved_functions
    _approved_functions.clear()

    # Ensure the approved directory is in sys.path (already added by orchestrator)
    if APPROVED_DIR not in sys.path:
        sys.path.insert(0, os.path.dirname(APPROVED_DIR))

    for filename in os.listdir(APPROVED_DIR):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]  # strip .py
            # import the module dynamically
            try:
                # Remove any previously loaded module
                if module_name in sys.modules:
                    del sys.modules[module_name]
                module = importlib.import_module(f"approved.{module_name}")
                # The tool module must provide a function named 'run'
                if hasattr(module, "run"):
                    _approved_functions[module_name] = module.run
                else:
                    print(f"[SIE] Warning: {filename} has no 'run' function – skipped")
            except Exception as e:
                print(f"[SIE] Failed to load approved tool {filename}: {e}")

def execute_approved_tool(tool_name: str, param: str = "") -> str | None:
    """
    Execute an approved tool by its name.
    The tool's module must have a 'run(param)' function.
    """
    # try to match by name (case insensitive, underscore/space normalisation)
    key = tool_name.lower().replace(" ", "_").replace("-", "_")
    func = _approved_functions.get(key)
    if not func:
        # try original name
        func = _approved_functions.get(tool_name)
    if not func:
        # reload in case a tool was approved while running
        reload_approved_tools()
        func = _approved_functions.get(key) or _approved_functions.get(tool_name)
    if not func:
        return None
    try:
        result = func(param)
        return str(result) if result is not None else "Tool executed."
    except Exception as e:
        return f"Tool execution error: {e}"

# ─── startup initialisation ───────────────────────────────────────────
reload_approved_tools()
