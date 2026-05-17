import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyaudio
import wave
import tempfile
import audioop
import time
import threading
from faster_whisper import WhisperModel
from config import WHISPER_MODEL

# ── Whisper model (loads once) ─────────────────────────────────────────────────
print("Loading Whisper model...")
whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
print("Whisper ready.")

# ── Audio settings ─────────────────────────────────────────────────────────────
FORMAT         = pyaudio.paInt16
CHANNELS       = 1
RATE           = 16000
CHUNK          = 1024

CLAP_THRESHOLD     = 3500
CLAP_COOLDOWN      = 0.5
CLAP_WINDOW        = 1.0
SILENCE_THRESHOLD  = 200
SILENCE_SECONDS    = 1.5
MAX_RECORD_SECONDS = 15

WAKE_WORDS = [
    "friday", "hey friday", "friday wake up",
    "wake up friday", "yo friday", "okay friday", "hi friday",
]

# ── Orb state helper (safe — works even if orb not running) ───────────────────
def _set_orb(state: str):
    try:
        from ui_preview import set_orb_state
        set_orb_state(state)
    except Exception:
        pass

# ── Noise floor calibration ────────────────────────────────────────────────────
def calibrate_noise_floor(seconds: float = 1.5) -> int:
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    levels = []
    for _ in range(int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        levels.append(audioop.rms(data, 2))
    stream.stop_stream()
    stream.close()
    pa.terminate()
    noise_floor = sum(levels) / len(levels)
    dynamic = max(200, int(noise_floor * 1.4))
    print(f"Noise floor: {int(noise_floor)} → silence threshold: {dynamic}")
    return dynamic

# ── Wake word check ────────────────────────────────────────────────────────────
def _is_wake_word(text: str) -> bool:
    text = text.lower().strip()
    for wake in WAKE_WORDS:
        if wake in text:
            return True
    return False

# ── Transcribe ────────────────────────────────────────────────────────────────
def transcribe(audio_path: str) -> tuple:
    segments, info = whisper.transcribe(audio_path, language="en")
    detected_lang  = info.language
    text = " ".join(s.text.strip() for s in segments).strip()
    os.unlink(audio_path)
    return text, detected_lang

def _quick_transcribe(audio_path: str) -> str:
    segments, _ = whisper.transcribe(audio_path, language="en")
    text = " ".join(s.text.strip() for s in segments).strip().lower()
    os.unlink(audio_path)
    return text

# ── Record with silence detection ─────────────────────────────────────────────
def record_until_silence(silence_threshold: int = None) -> str:
    threshold = silence_threshold or SILENCE_THRESHOLD
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    print("Listening... (speak now)")
    frames        = []
    silent_chunks = 0
    max_chunks    = int(RATE / CHUNK * MAX_RECORD_SECONDS)
    silence_limit = int(RATE / CHUNK * SILENCE_SECONDS)

    for _ in range(max_chunks):
        data      = stream.read(CHUNK, exception_on_overflow=False)
        amplitude = audioop.rms(data, 2)
        frames.append(data)
        if amplitude < threshold:
            silent_chunks += 1
        else:
            silent_chunks = 0
        if silent_chunks >= silence_limit:
            print("Silence detected, processing...")
            break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wf  = wave.open(tmp.name, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()
    return tmp.name

# ── Main listen function ───────────────────────────────────────────────────────
def listen() -> tuple:
    """
    Full orb state flow:
    idle → (wake detected) → listening → (wake phrase) → speaking
    → (recording command) → listening → (thinking) → processing
    Returns (text, language) for orchestrator to process.
    """
    from voice.speaker import stop_speaking, wake_response

    # Step 1: idle — waiting for wake
    _set_orb("idle")

    print("Calibrating noise floor...")
    dynamic_threshold = calibrate_noise_floor(1.5)

    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)

    print(f"\nReady — double clap or say {' / '.join(WAKE_WORDS[:3])}...")

    clap_times      = []
    wake_word_buf   = []
    wake_triggered  = False
    WAKE_BUF_CHUNKS = int(RATE / CHUNK * 3.0)

    try:
        while not wake_triggered:
            data      = stream.read(CHUNK, exception_on_overflow=False)
            amplitude = audioop.rms(data, 2)
            wake_word_buf.append(data)

            if len(wake_word_buf) > WAKE_BUF_CHUNKS:
                wake_word_buf.pop(0)

            # ── Clap detection ─────────────────────────────────────────────
            if amplitude > CLAP_THRESHOLD:
                now = time.time()
                if clap_times and (now - clap_times[-1]) < CLAP_COOLDOWN:
                    continue
                clap_times.append(now)
                print(f"  Clap {len(clap_times)} detected")
                clap_times = [t for t in clap_times if now - t <= CLAP_WINDOW]
                if len(clap_times) >= 2:
                    print("Double clap! Waking up...")
                    stop_speaking()
                    wake_triggered = True
                    clap_times = []
                    break

            # ── Wake word detection ────────────────────────────────────────
            if len(wake_word_buf) >= WAKE_BUF_CHUNKS:
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                wf  = wave.open(tmp.name, "wb")
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(wake_word_buf))
                wf.close()
                wake_word_buf = []

                def check_wake(path):
                    nonlocal wake_triggered
                    text = _quick_transcribe(path)
                    if _is_wake_word(text):
                        print(f"Wake word detected: '{text}'")
                        stop_speaking()
                        wake_triggered = True

                t = threading.Thread(target=check_wake, args=(tmp.name,), daemon=True)
                t.start()

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    # Step 2: wake detected → orb goes green (listening)
    _set_orb("listening")
    time.sleep(2.0)

    # Step 3: Friday speaks wake phrase → orb goes blue (speaking)
    _set_orb("speaking")
    wake_response()
    time.sleep(0.5)

    # Step 4: recording command → orb goes green (listening)
    _set_orb("listening")
    audio_path = record_until_silence(silence_threshold=dynamic_threshold)

    # Step 5: processing → orb goes orange
    _set_orb("processing")
    text, lang = transcribe(audio_path)
    print(f"Heard ({lang}): {text}")

    # Return text — orchestrator will set speaking when Friday responds
    return text, lang

# ── Listen with timeout (follow-up) ───────────────────────────────────────────
def listen_with_timeout(seconds: int = 5) -> str | None:
    """Listen briefly for follow-up. Orb goes green during this."""
    _set_orb("listening")

    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    frames        = []
    max_chunks    = int(RATE / CHUNK * seconds)
    silence_limit = int(RATE / CHUNK * SILENCE_SECONDS)
    silent_chunks = 0
    got_speech    = False

    for _ in range(max_chunks):
        data      = stream.read(CHUNK, exception_on_overflow=False)
        amplitude = audioop.rms(data, 2)
        frames.append(data)
        if amplitude > SILENCE_THRESHOLD * 3:
            got_speech    = True
            silent_chunks = 0
        elif got_speech:
            silent_chunks += 1
            if silent_chunks >= silence_limit:
                break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    if not got_speech:
        _set_orb("idle")
        return None

    _set_orb("processing")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wf  = wave.open(tmp.name, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()
    text, _ = transcribe(tmp.name)
    return text if text.strip() else None

# ── Test ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Say 'Friday' or double clap. Ctrl+C to quit.\n")
    while True:
        text, lang = listen()
        if text:
            print(f"Transcribed ({lang}): {text}\n")