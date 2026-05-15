import os

# ── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.expanduser("~/Developer/friday")
MEMORY_DIR      = os.path.join(BASE_DIR, "memory")
MODELS_DIR      = os.path.join(BASE_DIR, "models")
VOICE_DIR       = os.path.join(BASE_DIR, "voice")
TOOLS_DIR       = os.path.join(BASE_DIR, "tools")
UI_DIR          = os.path.join(BASE_DIR, "ui")

# ── Ollama / LLM ─────────────────────────────────────────────────────────────
OLLAMA_MODEL    = "friday"
OLLAMA_FALLBACK = "llama3.2"
OLLAMA_URL      = "http://localhost:11434"
LLM_TIMEOUT     = 60

# ── Whisper STT ───────────────────────────────────────────────────────────────
WHISPER_MODEL   = "small"
WHISPER_LANG    = "en"
WHISPER_DEVICE  = "auto"

# ── Text to Speech ────────────────────────────────────────────────────────────
TTS_ENGINE      = "say"
SAY_VOICE       = "Samantha"
PIPER_MODEL     = os.path.join(MODELS_DIR, "piper", "en_US-lessac-medium.onnx")

# ── Wake Word (clap detection) ────────────────────────────────────────────────
CLAP_THRESHOLD  = 3500
CLAP_COOLDOWN   = 0.5
CLAP_WINDOW     = 1.0
SAMPLE_RATE     = 16000
CHUNK_SIZE      = 1024

# ── Memory (ChromaDB) ────────────────────────────────────────────────────────
CHROMA_PATH     = os.path.join(MEMORY_DIR, "chroma")
SQLITE_PATH     = os.path.join(MEMORY_DIR, "friday.db")
MEMORY_RESULTS  = 5

# ── News / Web ───────────────────────────────────────────────────────────────
NEWS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://feeds.feedburner.com/ndtvnews-top-stories",
]
NEWS_MAX_ARTICLES = 5

# ── Weather ──────────────────────────────────────────────────────────────────
WEATHER_LAT     = 22.5726
WEATHER_LON     = 88.3639
WEATHER_URL     = "https://api.open-meteo.com/v1/forecast"

# ── Browser ──────────────────────────────────────────────────────────────────
DEFAULT_BROWSER = "Brave Browser"

# ── UI ────────────────────────────────────────────────────────────────────────
ORB_WIDTH       = 500
ORB_HEIGHT      = 500
ORB_FPS         = 60
ACCENT_COLOR    = "#00d4ff"

# ── User ─────────────────────────────────────────────────────────────────────
USER_NAME       = "Sir"
FRIDAY_NAME     = "Friday"

# ── System ───────────────────────────────────────────────────────────────────
DEBUG           = False
LOG_PATH        = os.path.join(BASE_DIR, "friday.log")

# ── Auto-create directories on import ────────────────────────────────────────
for _dir in [MEMORY_DIR, MODELS_DIR, CHROMA_PATH]:
    os.makedirs(_dir, exist_ok=True)