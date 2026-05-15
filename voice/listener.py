import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyaudio
import wave
import tempfile
import audioop
import time
from faster_whisper import WhisperModel
from config import WHISPER_MODEL

# ── Whisper model (loads once) ─────────────────────────────────────────────────
print("Loading Whisper model...")
whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
print("Whisper ready.")

# ── Audio settings ─────────────────────────────────────────────────────────────
FORMAT            = pyaudio.paInt16
CHANNELS          = 1
RATE              = 16000
CHUNK             = 1024
CLAP_THRESHOLD    = 3000
CLAP_COOLDOWN     = 0.3
CLAP_WINDOW       = 1.5
RECORD_SECONDS    = 6


# ── Clap detection ─────────────────────────────────────────────────────────────

def wait_for_double_clap():
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    print("Listening for double clap...")
    clap_times = []
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            amplitude = audioop.rms(data, 2)
            if amplitude > CLAP_THRESHOLD:
                now = time.time()
                if clap_times and (now - clap_times[-1]) < CLAP_COOLDOWN:
                    continue
                clap_times.append(now)
                print(f"  Clap {len(clap_times)} detected (amplitude {amplitude})")
                clap_times = [t for t in clap_times if now - t <= CLAP_WINDOW]
                if len(clap_times) >= 2:
                    print("Double clap detected! Waking up...")
                    clap_times = []
                    return True
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


# ── Voice recording ────────────────────────────────────────────────────────────

def record_audio(seconds: int = RECORD_SECONDS) -> str:
    pa     = pyaudio.PyAudio()
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    print(f"Recording for {seconds} seconds... speak now!")
    frames = []
    for _ in range(0, int(RATE / CHUNK * seconds)):
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


# ── Transcribe ────────────────────────────────────────────────────────────────

def transcribe(audio_path: str) -> tuple:
    segments, info = whisper.transcribe(audio_path)
    detected_lang  = info.language
    text = " ".join(s.text.strip() for s in segments).strip()
    os.unlink(audio_path)
    print(f"Detected language: {detected_lang}")
    return text, detected_lang


# ── Full listen cycle ──────────────────────────────────────────────────────────

def listen() -> tuple:
    wait_for_double_clap()
    audio_path = record_audio()
    text, lang = transcribe(audio_path)
    print(f"Heard ({lang}): {text}")
    return text, lang


# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Double clap to test. Ctrl+C to quit.\n")
    while True:
        result, lang = listen()
        if result:
            print(f"Transcribed ({lang}): {result}\n")
            