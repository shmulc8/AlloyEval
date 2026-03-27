"""
Central configuration. Edit this file before running the experiment.
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Alloy analyzer ─────────────────────────────────────────────────────────
ALLOY_PATH: str = "alloy"   # binary on PATH (installed via brew install alloy-analyzer)
ALLOY_TIMEOUT: int = 30     # seconds per check
ALLOY_SCOPE: int = 3        # scope bound — paper uses 3

# ── Experiment parameters ──────────────────────────────────────────────────
NUM_SOLUTIONS: int = 20     # trials per property per task — paper uses 20
TEMPERATURE: float = 1.0    # LLM sampling temperature

# ── Directories ────────────────────────────────────────────────────────────
DATA_DIR: Path = Path("data")
OUTPUT_DIR: Path = Path("output")

# ── LLM providers (Vertex AI REST API) ────────────────────────────────────
# Each dict: name, api_key_env, model
# Endpoint: https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent?key={key}

LLM_CONFIGS: list[dict] = [
    {
        "name": "gemini-2.5-flash-lite",
        "api_key_env": "VERTEX_API_KEY",
        "model": "gemini-2.5-flash-lite",
    },
    {
        "name": "gemini-2.5-pro",
        "api_key_env": "VERTEX_API_KEY",
        "model": "gemini-2.5-pro",
    },
]

# Config used by --fast
GEMINI_FLASH_PREVIEW_CONFIG: dict = {
    "name": "gemini-2.5-flash-lite",
    "api_key_env": "VERTEX_API_KEY",
    "model": "gemini-2.5-flash-lite",
}
