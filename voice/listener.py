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
CLAP_THRESHOLD = 3000
CLAP_COOLDOWN  = 0.3
CLAP_WINDOW    = 1.5

# Silence detection settings
SILENCE_THRESHOLD  = 200   # below this = silence
SILENCE_SECONDS    = 1.5   # stop after 1.5s of silence
MAX_RECORD_SECONDS = 15    # hard cap


# ── Transcribe any WAV file ────────────────────────────────────────────────────

def transcribe(audio_path: str) -> tuple:
    segments, info = whisper.transcribe(audio_path)
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

def record_until_silence() -> str:
    """Record until silence is detected. Returns path to WAV file."""
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

        if amplitude < SILENCE_THRESHOLD:
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


# ── Continuous background listening for "Jarvis" wake word ────────────────────

def _record_chunk(seconds: float = 2.0) -> str:
    """Record a short chunk for wake word detection."""
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    frames = []
    for _ in range(int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
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
    - Double clap  → wake up
    - "Jarvis"     → wake up
    Then records until silence and returns (text, language).
    """
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)

    print("\nReady — double clap or say 'Jarvis'...")

    clap_times      = []
    wake_word_buf   = []   # raw frames for wake word detection
    wake_triggered  = False
    WAKE_BUF_CHUNKS = int(RATE / CHUNK * 2.0)  # 2 second rolling buffer

    try:
        while not wake_triggered:
            data      = stream.read(CHUNK, exception_on_overflow=False)
            amplitude = audioop.rms(data, 2)
            wake_word_buf.append(data)

            # Keep rolling 2-second buffer for wake word
            if len(wake_word_buf) > WAKE_BUF_CHUNKS:
                wake_word_buf.pop(0)

            # ── Clap detection ────────────────────────────────────────────
            if amplitude > CLAP_THRESHOLD:
                now = time.time()
                if clap_times and (now - clap_times[-1]) < CLAP_COOLDOWN:
                    continue
                clap_times.append(now)
                print(f"  Clap {len(clap_times)} detected")
                clap_times = [t for t in clap_times if now - t <= CLAP_WINDOW]
                if len(clap_times) >= 2:
                    print("Double clap! Waking up...")
                    wake_triggered = True
                    clap_times = []

            # ── Wake word detection (check every 2 seconds) ───────────────
            if len(wake_word_buf) >= WAKE_BUF_CHUNKS:
                # Save buffer to temp file and transcribe quickly
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                wf  = wave.open(tmp.name, "wb")
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(wake_word_buf))
                wf.close()
                wake_word_buf = []  # reset buffer

                # Run transcription in background thread so audio doesn't skip
                def check_wake(path):
                    nonlocal wake_triggered
                    text = _quick_transcribe(path)
                    if "jarvis" in text:
                        print(f"Wake word detected: '{text}'")
                        wake_triggered = True

                t = threading.Thread(target=check_wake, args=(tmp.name,), daemon=True)
                t.start()

    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

   # Say wake phrase before recording
    from voice.speaker import wake_response
    wake_response()

    # Now record the actual command
    audio_path = record_until_silence()
    text, lang = transcribe(audio_path)
    print(f"Heard ({lang}): {text}")
    return text, lang


# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Say 'Jarvis' or double clap. Ctrl+C to quit.\n")
    while True:
        text, lang = listen()
        if text:
            print(f"Transcribed ({lang}): {text}\n")
