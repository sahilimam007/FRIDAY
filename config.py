import os

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.expanduser("~/Developer/jarvis")
MEMORY_DIR      = os.path.join(BASE_DIR, "memory")
MODELS_DIR      = os.path.join(BASE_DIR, "models")
VOICE_DIR       = os.path.join(BASE_DIR, "voice")
TOOLS_DIR       = os.path.join(BASE_DIR, "tools")
UI_DIR          = os.path.join(BASE_DIR, "ui")

# ── Ollama / LLM ─────────────────────────────────────────────────────────────
OLLAMA_MODEL    = "jarvis"          # custom model name from Modelfile
OLLAMA_FALLBACK = "llama3.2"       # fallback if jarvis model not created yet
OLLAMA_URL      = "http://localhost:11434"
LLM_TIMEOUT     = 60               # seconds before giving up on a response

# ── Whisper STT ───────────────────────────────────────────────────────────────
WHISPER_MODEL   = "small"          # tiny / base / small / medium (small = best balance)
WHISPER_LANG    = "en"             # language code
WHISPER_DEVICE  = "auto"          # auto detects CPU/GPU

# ── Text to Speech ────────────────────────────────────────────────────────────
TTS_ENGINE      = "say"            # "say" = macOS built-in | "piper" = offline neural TTS
SAY_VOICE       = "Daniel"         # macOS voice (Daniel = British, sounds good for Jarvis)
PIPER_MODEL     = os.path.join(MODELS_DIR, "piper", "en_US-lessac-medium.onnx")

# ── Wake Word (clap detection) ────────────────────────────────────────────────
CLAP_THRESHOLD  = 2500             # amplitude threshold (tune if too sensitive)
CLAP_COOLDOWN   = 0.4              # seconds between claps
CLAP_WINDOW     = 1.2              # seconds to wait for second clap
SAMPLE_RATE     = 16000            # audio sample rate
CHUNK_SIZE      = 1024             # audio chunk size

# ── Memory (ChromaDB) ────────────────────────────────────────────────────────
CHROMA_PATH     = os.path.join(MEMORY_DIR, "chroma")
SQLITE_PATH     = os.path.join(MEMORY_DIR, "jarvis.db")
MEMORY_RESULTS  = 5                # how many memories to retrieve per query

# ── News / Web ───────────────────────────────────────────────────────────────
NEWS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",           # BBC News
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",  # Times of India
    "https://feeds.feedburner.com/ndtvnews-top-stories", # NDTV
]
NEWS_MAX_ARTICLES = 5              # how many articles to summarise

# ── Weather ──────────────────────────────────────────────────────────────────
WEATHER_LAT     = 22.5726          # Kolkata latitude
WEATHER_LON     = 88.3639          # Kolkata longitude
WEATHER_URL     = "https://api.open-meteo.com/v1/forecast"

# ── Browser ──────────────────────────────────────────────────────────────────
DEFAULT_BROWSER = "Brave Browser"  # name as it appears in /Applications

# ── UI ────────────────────────────────────────────────────────────────────────
ORB_WIDTH       = 500
ORB_HEIGHT      = 500
ORB_FPS         = 60
ACCENT_COLOR    = "#00d4ff"        # Jarvis blue

# ── User ─────────────────────────────────────────────────────────────────────
USER_NAME       = "Sir"            # how Jarvis addresses you
JARVIS_NAME     = "Jarvis"

# ── System ───────────────────────────────────────────────────────────────────
DEBUG           = False            # set True to print extra logs
LOG_PATH        = os.path.join(BASE_DIR, "jarvis.log")

# ── Auto-create directories on import ────────────────────────────────────────
for _dir in [MEMORY_DIR, MODELS_DIR, CHROMA_PATH]:
    os.makedirs(_dir, exist_ok=True)
    