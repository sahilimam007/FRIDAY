import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import subprocess
import pyautogui
import requests
import time

# ── Helpers ────────────────────────────────────────────────────────────────────

def _read_clipboard() -> str:
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return result.stdout.strip()

def _ask_ollama(prompt: str) -> str:
    try:
        payload = {
            "model": "friday",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=60)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"Error contacting Ollama: {e}"

# ── Clipboard tools ────────────────────────────────────────────────────────────

def get_clipboard() -> str:
    text = _read_clipboard()
    if not text:
        return "Clipboard is empty, Boss."
    return f"Clipboard contains: {text[:500]}"

def summarise_clipboard() -> str:
    text = _read_clipboard()
    if not text:
        return "Clipboard is empty, Boss."
    if len(text) < 100:
        return f"Clipboard contains: {text}"
    # Return SUMMARISE: prefix so handle_ai_tool in orchestrator processes it
    return f"SUMMARISE:{text[:2000]}"

def fix_grammar_clipboard() -> str:
    text = _read_clipboard()
    if not text:
        return "Clipboard is empty, Boss."
    prompt = (
        "Fix the grammar, spelling, and punctuation of the following text. "
        "Return ONLY the corrected text with no explanation, no preamble, no quotes:\n\n"
        f"{text}"
    )
    fixed = _ask_ollama(prompt)
    if fixed:
        subprocess.run(["pbcopy"], input=fixed.encode())
        return "Grammar fixed and copied back to clipboard, Boss."
    return "Could not fix grammar, Boss."

def explain_clipboard_code() -> str:
    text = _read_clipboard()
    if not text:
        return "Clipboard is empty, Boss."
    # Return EXPLAIN_CODE: prefix so handle_ai_tool in orchestrator processes it
    return f"EXPLAIN_CODE:{text[:2000]}"

def debug_clipboard_error() -> str:
    text = _read_clipboard()
    if not text:
        return "Clipboard is empty, Boss."
    return f"DEBUG_ERROR:{text[:2000]}"

def set_clipboard(text: str) -> str:
    subprocess.run(["pbcopy"], input=text.encode())
    return "Copied to clipboard, Boss."

def paste_clipboard() -> str:
    time.sleep(0.3)
    pyautogui.hotkey("command", "v")
    return "Pasted from clipboard, Boss."

def copy_selection() -> str:
    pyautogui.hotkey("command", "c")
    time.sleep(0.3)
    result = subprocess.run(["pbpaste"], capture_output=True, text=True)
    return f"Copied: {result.stdout.strip()[:100]}, Boss."

def dictate_text(text: str) -> str:
    time.sleep(0.5)
    pyautogui.typewrite(text, interval=0.04)
    return f"Typed: {text[:50]}..., Boss." if len(text) > 50 else f"Typed: {text}, Boss."

def clear_clipboard() -> str:
    subprocess.run(["pbcopy"], input=b"")
    return "Clipboard cleared, Boss."

if __name__ == "__main__":
    set_clipboard("Hello from Friday!")
    print(get_clipboard())
    print(summarise_clipboard())