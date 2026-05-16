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

# Clap settings
CLAP_THRESHOLD = 3500
CLAP_COOLDOWN  = 0.5
CLAP_WINDOW    = 1.0

# Silence detection settings
SILENCE_THRESHOLD  = 200
SILENCE_SECONDS    = 1.5
MAX_RECORD_SECONDS = 15

# ── Wake words — any of these trigger Friday ───────────────────────────────────
WAKE_WORDS = [
    "friday",
    "hey friday",
    "friday wake up",
    "wake up friday",
    "yo friday",
    "okay friday",
    "hi friday",
]


# ── Noise floor calibration ────────────────────────────────────────────────────
def calibrate_noise_floor(seconds: float = 1.5) -> int:
    """
    Sample ambient noise for a short period and return a dynamic
    silence threshold slightly above the noise floor.
    """
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
    # Set threshold 40% above noise floor, minimum 200
    dynamic = max(200, int(noise_floor * 1.4))
    print(f"Noise floor: {int(noise_floor)} → silence threshold: {dynamic}")
    return dynamic


# ── Check if text contains any wake word ──────────────────────────────────────
def _is_wake_word(text: str) -> bool:
    text = text.lower().strip()
    for wake in WAKE_WORDS:
        if wake in text:
            return True
    return False


# ── Transcribe any WAV file ────────────────────────────────────────────────────
def transcribe(audio_path: str) -> tuple:
    segments, info = whisper.transcribe(audio_path, language="en")
    detected_lang  = info.language
    text = " ".join(s.text.strip() for s in segments).strip()
    os.unlink(audio_path)
    return text, detected_lang


# ── Quick transcribe to check for wake word ───────────────────────────────────
def _quick_transcribe(audio_path: str) -> str:
    segments, _ = whisper.transcribe(audio_path, language="en")
    text = " ".join(s.text.strip() for s in segments).strip().lower()
    os.unlink(audio_path)
    return text


# ── Record with silence detection ─────────────────────────────────────────────
def record_until_silence(silence_threshold: int = None) -> str:
    """Record until silence is detected. Returns path to WAV file."""
    threshold = silence_threshold or SILENCE_THRESHOLD

    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)

    print("Listening... (speak now, will stop when you stop talking)")
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
    Waits for either:
    - Double clap         → wake up
    - Any wake word       → wake up (friday, hey friday, wake up friday, etc.)
    Then records until silence and returns (text, language).
    Also stops Friday mid-speech if a clap or wake word is detected.
    """
    from voice.speaker import stop_speaking, wake_response

    # Calibrate noise floor before listening
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
                    # Interrupt Friday if she's speaking
                    stop_speaking()
                    wake_triggered = True
                    clap_times = []
                    break

            # ── Wake word detection (check every 3 seconds) ────────────────
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
                        # Interrupt Friday if she's speaking
                        stop_speaking()
                        wake_triggered = True

                t = threading.Thread(target=check_wake, args=(tmp.name,), daemon=True)
                t.start()

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    # Give audio device time to fully release
    time.sleep(2.0)
    wake_response()
    time.sleep(0.5)

    # Record actual command using dynamic noise threshold
    audio_path = record_until_silence(silence_threshold=dynamic_threshold)
    text, lang = transcribe(audio_path)
    print(f"Heard ({lang}): {text}")
    return text, lang


# ── Listen with timeout (for follow-up) ───────────────────────────────────────
def listen_with_timeout(seconds: int = 5) -> str | None:
    """Listen for a short period, return text or None if silent."""
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
        return None

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
    print("Say 'Friday', 'Hey Friday', 'Wake up Friday' or double clap.")
    print("Ctrl+C to quit.\n")
    while True:
        text, lang = listen()
        if text:
            print(f"Transcribed ({lang}): {text}\n")