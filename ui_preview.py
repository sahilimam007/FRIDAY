import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math, random, threading
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore    import Qt, QTimer, QPointF, QRectF, pyqtSignal, QObject
from PyQt6.QtGui     import QPainter, QBrush, QColor, QRadialGradient, QPen

# ── Signal bridge (thread-safe comms from voice thread → UI thread) ────────────
class Bridge(QObject):
    state_changed = pyqtSignal(str)   # idle / listening / processing / speaking

_bridge = Bridge()

def set_orb_state(state: str):
    """Call this from any thread to update the orb."""
    _bridge.state_changed.emit(state)

# ── Orb widget ─────────────────────────────────────────────────────────────────
class FridayOrb(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(260, 260)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - 290, screen.bottom() - 290)

        self.center       = QPointF(130, 130)
        self.base_radius  = 65
        self.radius       = 28
        self.target_radius = 28
        self.phase        = 0.0
        self.state        = "idle"
        self._drag_pos    = None

        # rings
        self.rings = []
        for i in range(10):
            tilt      = (i / 10) * 90 + 10
            rad_ratio = 0.32 + i * 0.075
            speed     = 0.25 + i * 0.10
            opacity   = 80 + i * 14
            self.rings.append({
                'tilt':      math.radians(tilt),
                'azimuth':   random.uniform(0, 2 * math.pi),
                'rad_ratio': rad_ratio,
                'speed':     speed,
                'opacity':   opacity
            })

        self.data_points = []
        for _ in range(60):
            self.data_points.append([
                random.uniform(-math.pi / 2, math.pi / 2),
                random.uniform(0, 2 * math.pi),
                random.uniform(0.002, 0.014),
                random.uniform(1.0, 3.0)
            ])

        self.particles = []
        for _ in range(80):
            factor = random.uniform(1.1, 1.7)
            speed  = random.uniform(0.003, 0.012) * random.choice([1, -1])
            tilt   = random.uniform(-0.7, 0.7)
            phase  = random.uniform(0, math.pi * 2)
            size   = random.uniform(0.8, 2.2)
            alpha  = random.uniform(0.3, 0.9)
            self.particles.append([factor, speed, tilt, phase, size, alpha])

        self.ripples     = []
        self.last_ripple = 0

        # connect bridge signal
        _bridge.state_changed.connect(self.set_state)

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)
        self.show()
        self.setFocus()

    def animate(self):
        sm = {"idle": 0.8, "listening": 1.8, "processing": 4.0, "speaking": 1.5}.get(self.state, 1.0)
        self.phase += 0.022 * sm

        if self.state == "idle":
            self.target_radius = 28 + 2 * math.sin(self.phase * 1.2)
        else:
            self.target_radius = self.base_radius

        self.radius += (self.target_radius - self.radius) * 0.12

        for ring in self.rings:
            ring['azimuth'] = (ring['azimuth'] + ring['speed'] * 0.01 * sm) % (2 * math.pi)
        for pt in self.data_points:
            pt[1] = (pt[1] + pt[2] * sm) % (2 * math.pi)
        for pt in self.particles:
            pt[3] += pt[1] * sm

        if self.state == "speaking":
            self.last_ripple += 1
            if self.last_ripple > 20:
                self.ripples.append([self.radius + 5, 1.0])
                self.last_ripple = 0
        self.ripples = [[r + 2.5, a - 0.035] for r, a in self.ripples if a > 0]

        self.update()

    def set_state(self, state: str):
        if state in ("idle", "listening", "processing", "speaking"):
            self.state = state

    def keyPressEvent(self, event):
        key = event.text().lower()
        if key == 'i':   self.set_state("idle")
        elif key == 'l': self.set_state("listening")
        elif key == 'p': self.set_state("processing")
        elif key == 't': self.set_state("speaking")
        elif key == 'q': QApplication.quit()
        self.setFocus()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            delta = e.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = e.globalPosition().toPoint()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.center.x(), self.center.y()
        idle = self.state == "idle"

        # colour palette per state
        colours = {
            "idle":       (30, 100, 255),
            "listening":  (0,  220, 120),
            "processing": (255, 160, 0),
            "speaking":   (30,  180, 255),
        }
        r, g, b = colours.get(self.state, (30, 100, 255))

        # outer aura
        glow = QRadialGradient(self.center, self.radius + 50)
        glow.setColorAt(0,   QColor(r, g, b, 45))
        glow.setColorAt(0.5, QColor(r//2, g//2, b//2, 15))
        glow.setColorAt(1,   QColor(0, 0, 0, 0))
        p.setBrush(QBrush(glow))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.center, self.radius + 50, self.radius + 50)

        # back particles
        if not idle:
            p.setPen(Qt.PenStyle.NoPen)
            for factor, sp, tilt, ph, sz, al in self.particles:
                orbit = factor * self.radius
                x = cx + math.cos(ph) * orbit
                y = cy + math.sin(ph) * orbit * math.cos(tilt)
                z = math.sin(ph) * math.sin(tilt)
                if z < 0:
                    a = int(al * (0.4 + (z + 1) * 0.3) * 180)
                    p.setBrush(QBrush(QColor(r//2, g//2, b, max(0, a))))
                    p.drawEllipse(QPointF(x, y), sz * 0.7, sz * 0.7)

        # rings
        p.setBrush(Qt.BrushStyle.NoBrush)
        for ring in self.rings:
            major = self.radius * ring['rad_ratio']
            minor = major * abs(math.cos(ring['tilt']))
            if minor < 1: continue
            p.save()
            p.translate(self.center)
            p.rotate(math.degrees(ring['azimuth']))
            p.setPen(QPen(QColor(r, g, b, int(ring['opacity'] * 0.75)), 1.0))
            p.drawEllipse(QRectF(-major, -minor, 2 * major, 2 * minor))
            p.restore()

        # data points
        p.setPen(Qt.PenStyle.NoPen)
        for lat, lon, _, sz in self.data_points:
            x3    = self.radius * math.cos(lat) * math.cos(lon)
            y3    = self.radius * math.sin(lat)
            z3    = self.radius * math.cos(lat) * math.sin(lon)
            depth = (z3 + self.radius) / (2 * self.radius)
            alpha = int(60 + depth * 160)
            dot_sz = sz * (0.5 + depth * 0.8)
            p.setBrush(QBrush(QColor(r, g, b, alpha)))
            p.drawEllipse(QPointF(cx + x3, cy - y3), dot_sz, dot_sz)

        # core sphere
        core = QRadialGradient(
            QPointF(cx - self.radius * 0.28, cy - self.radius * 0.28),
            self.radius * 0.12, self.center, self.radius
        )
        core.setColorAt(0,    QColor(210, 235, 255, 250))
        core.setColorAt(0.2,  QColor(r, g, b, 230))
        core.setColorAt(0.55, QColor(r//3, g//3, b//3+40, 180))
        core.setColorAt(0.82, QColor(8, 25, 130, 140))
        core.setColorAt(1,    QColor(0, 6, 40, 60))
        p.setBrush(QBrush(core))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(self.center, self.radius, self.radius)

        # specular highlight
        spec = QRadialGradient(
            QPointF(cx - self.radius * 0.35, cy - self.radius * 0.38),
            self.radius * 0.6
        )
        spec.setColorAt(0, QColor(255, 255, 255, 90))
        spec.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(spec))
        p.drawEllipse(self.center, self.radius, self.radius)

        # bright inner core
        cg = QRadialGradient(self.center, 0.4 * self.radius)
        cg.setColorAt(0,   QColor(220, 238, 255, 255))
        cg.setColorAt(0.4, QColor(r, g, b, 230))
        cg.setColorAt(0.8, QColor(15, 70, 200, 110))
        cg.setColorAt(1,   QColor(0, 0, 0, 0))
        p.setBrush(QBrush(cg))
        p.drawEllipse(self.center, 0.4 * self.radius, 0.4 * self.radius)

        inner = QRadialGradient(self.center, 0.12 * self.radius)
        inner.setColorAt(0, QColor(255, 255, 255, 255))
        inner.setColorAt(1, QColor(200, 225, 255, 0))
        p.setBrush(QBrush(inner))
        p.drawEllipse(self.center, 0.12 * self.radius, 0.12 * self.radius)

        # front particles
        if not idle:
            for factor, sp, tilt, ph, sz, al in self.particles:
                orbit = factor * self.radius
                x = cx + math.cos(ph) * orbit
                y = cy + math.sin(ph) * orbit * math.cos(tilt)
                z = math.sin(ph) * math.sin(tilt)
                if z >= 0:
                    a = int(al * (0.5 + z * 0.5) * 220)
                    pg = QRadialGradient(QPointF(x, y), sz * 4)
                    pg.setColorAt(0, QColor(r, g, b, min(255, int(a * 0.8))))
                    pg.setColorAt(1, QColor(0, 0, 0, 0))
                    p.setBrush(QBrush(pg))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawEllipse(QPointF(x, y), sz * 4, sz * 4)
                    p.setBrush(QBrush(QColor(200, 220, 255, min(255, a))))
                    p.drawEllipse(QPointF(x, y), sz, sz)

        # speaking ripples
        p.setBrush(Qt.BrushStyle.NoBrush)
        for rv, a in self.ripples:
            p.setPen(QPen(QColor(r, g, b, int(a * 160)), 1.5))
            p.drawEllipse(self.center, rv, rv)

        p.end()


# ── Friday voice loop (runs in background thread) ─────────────────────────────
def friday_loop():
    from voice.listener  import listen, listen_with_timeout
    from voice.speaker   import speak, shutdown_response, wake_response
    from orchestrator    import process

    speak("Friday online, Boss. All systems operational.")
    set_orb_state("idle")

    import random
    FOLLOWUPS = [
        "Anything else, Boss?",
        "Can I help with anything else, Boss?",
        "What else do you need, Boss?",
        "Shall I do anything else, Boss?",
    ]

    while True:
        try:
            # listener handles idle→listening→speaking→listening→processing internally
            user_input, lang = listen()

            if not user_input.strip():
                set_orb_state("idle")
                continue

            print(f"[FRIDAY] Heard: {user_input}")

            # still processing (ollama thinking)
            set_orb_state("processing")
            response = process(user_input)
            print(f"[FRIDAY] Response: {response}")

            # speaking response
            set_orb_state("speaking")
            speak(response)

            # follow-up — listener_with_timeout handles orb states internally
            set_orb_state("speaking")
            speak(random.choice(FOLLOWUPS))

            followup = listen_with_timeout(seconds=5)
            if followup and followup.strip():
                set_orb_state("processing")
                resp2 = process(followup)
                set_orb_state("speaking")
                speak(resp2)

            set_orb_state("idle")

        except KeyboardInterrupt:
            shutdown_response()
            QApplication.quit()
            break
        except Exception as e:
            print(f"[FRIDAY] Error: {e}")
            set_orb_state("idle")

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    orb = FridayOrb()

    # start voice loop in background thread
    voice_thread = threading.Thread(target=friday_loop, daemon=True)
    voice_thread.start()

    sys.exit(app.exec())