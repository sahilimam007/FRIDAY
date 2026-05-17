import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import random
import json
from PyQt6.QtWidgets      import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel   import QWebChannel
from PyQt6.QtCore         import QObject, pyqtSlot, pyqtSignal, QUrl, Qt

# ── Bridge: Python ↔ JavaScript ───────────────────────────────────────────────
class Bridge(QObject):
    state_update = pyqtSignal(str, str)
    tool_count_updated = pyqtSignal(int)
    pending_tools_ready = pyqtSignal(str)
    tool_code_ready = pyqtSignal(str)
    tools_list_updated = pyqtSignal()

    def __init__(self):
        super().__init__()

    @pyqtSlot(str)
    def on_chat(self, text: str):
        print(f"[UI] Chat: {text}")
        if text == "__minimise__":
            _window.showMinimized(); return
        if text == "__maximise__":
            _window.showNormal() if _window.isFullScreen() else _window.showFullScreen(); return
        if text == "__close__":
            _window.close(); return
        threading.Thread(target=handle_chat, args=(text,), daemon=True).start()

    @pyqtSlot()
    def on_ready(self):
        print("[UI] HTML UI ready.")
        _bridge.state_update.emit("idle", "")
        from sie.approval_manager import get_pending_count
        count = get_pending_count()
        self.tool_count_updated.emit(count)

    @pyqtSlot()
    def request_pending_tools(self):
        from sie.approval_manager import get_pending_tools
        tools = get_pending_tools()
        self.pending_tools_ready.emit(json.dumps(tools))
        self.tool_count_updated.emit(len(tools))

    @pyqtSlot(int)
    def approve_tool(self, tool_id: int):
        from sie.approval_manager import approve_tool, get_pending_count
        approve_tool(tool_id)
        self.tools_list_updated.emit()
        self.tool_count_updated.emit(get_pending_count())

    @pyqtSlot(int)
    def reject_tool(self, tool_id: int):
        from sie.approval_manager import reject_tool, get_pending_count
        reject_tool(tool_id)
        self.tools_list_updated.emit()
        self.tool_count_updated.emit(get_pending_count())

    @pyqtSlot(int)
    def get_tool_code(self, tool_id: int):
        from sie.approval_manager import _get_conn
        conn = _get_conn()
        row = conn.execute("SELECT code FROM pending_tools WHERE id = ?", (tool_id,)).fetchone()
        conn.close()
        code = row["code"] if row else ""
        self.tool_code_ready.emit(code)

    @pyqtSlot()
    def approve_all_tools(self):
        from sie.approval_manager import get_pending_tools, approve_tool, get_pending_count
        for tool in get_pending_tools():
            approve_tool(tool["id"])
        self.tools_list_updated.emit()
        self.tool_count_updated.emit(0)

    @pyqtSlot()
    def reject_all_tools(self):
        from sie.approval_manager import get_pending_tools, reject_tool, get_pending_count
        for tool in get_pending_tools():
            reject_tool(tool["id"])
        self.tools_list_updated.emit()
        self.tool_count_updated.emit(0)

# ── Globals ────────────────────────────────────────────────────────────────────
_bridge = None
_window = None

def set_ui_state(state: str, message: str = ""):
    if _bridge:
        _bridge.state_update.emit(state, message)

# ── Chat handler ───────────────────────────────────────────────────────────────
def handle_chat(text: str):
    from orchestrator  import process
    from voice.speaker import speak
    set_ui_state("processing", f'Processing: "{text}"')
    response = process(text)
    set_ui_state("speaking", response)
    speak(response)
    set_ui_state("idle", "")

# ── Voice loop ─────────────────────────────────────────────────────────────────
FOLLOWUPS = [
    "Anything else, Boss?",
    "Can I help with anything else, Boss?",
    "What else do you need, Boss?",
    "Shall I do anything else, Boss?",
]

def friday_voice_loop():
    from voice.listener  import listen, listen_with_timeout
    from voice.speaker   import speak
    from orchestrator    import process

    speak("Friday online, Boss. All systems operational.")
    set_ui_state("idle", "")

    while True:
        try:
            set_ui_state("idle", "")
            user_input, lang = listen()
            if not user_input.strip():
                continue

            print(f"[FRIDAY] Heard: {user_input}")
            set_ui_state("processing", f'"{user_input}"')

            response = process(user_input)
            print(f"[FRIDAY] Response: {response}")

            set_ui_state("speaking", response)
            speak(response)

            followup_phrase = random.choice(FOLLOWUPS)
            set_ui_state("speaking", followup_phrase)
            speak(followup_phrase)

            set_ui_state("listening", "")
            followup = listen_with_timeout(seconds=5)
            if followup and followup.strip():
                set_ui_state("processing", f'"{followup}"')
                resp2 = process(followup)
                set_ui_state("speaking", resp2)
                speak(resp2)

            set_ui_state("idle", "")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[FRIDAY] Error: {e}")
            import traceback; traceback.print_exc()
            set_ui_state("idle", "")

# ── Main window ────────────────────────────────────────────────────────────────
class FridayWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FRIDAY")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("background:#0a0c10;")
        self.setWindowFlags(Qt.WindowType.Window)

        self.view = QWebEngineView()
        self.view.setStyleSheet("background:#0a0c10;")
        self.setCentralWidget(self.view)

        global _bridge
        _bridge = Bridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", _bridge)
        self.view.page().setWebChannel(self.channel)
        _bridge.state_update.connect(self._send_state)

        html_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "friday_display.html"
        )
        self.view.setUrl(QUrl.fromLocalFile(html_path))
        self.showMaximized()

    def _send_state(self, state: str, message: str):
        data = json.dumps({"state": state, "message": message})
        self.view.page().runJavaScript(
            f"window.fridayUpdate && window.fridayUpdate({data})"
        )

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.showNormal() if self.isFullScreen() else self.showMinimized()
        elif e.key() == Qt.Key.Key_F11:
            self.showNormal() if self.isFullScreen() else self.showFullScreen()

# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FRIDAY")

    _window = FridayWindow()

    voice_thread = threading.Thread(target=friday_voice_loop, daemon=True)
    voice_thread.start()

    sys.exit(app.exec())
