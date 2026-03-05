"""
Central configuration. Edit this file before running the experiment.
"""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Alloy analyzer ─────────────────────────────────────────────────────────
ALLOY_PATH: str = "alloy"   # binary on PATH (installed via brew install alloy-analyzer)
ALLOY_TIMEOUT: int = 30     # seconds per check
ALLOY_SCOPE: int = 4        # scope bound

# ── Experiment parameters ──────────────────────────────────────────────────
NUM_SOLUTIONS: int = 10     # trials per property per task
TEMPERATURE: float = 1.0    # LLM sampling temperature

# ── Directories ────────────────────────────────────────────────────────────
DATA_DIR: Path = Path("data")
OUTPUT_DIR: Path = Path("output")

# ── LLM providers (OpenAI-compatible API) ─────────────────────────────────
# Each dict: name, base_url (None = OpenAI default), api_key_env, model
LLM_CONFIGS: list[dict] = [
    {
        "name": "o3-mini",
        "base_url": None,
        "api_key_env": "OPENAI_API_KEY",
        "model": "o3-mini",
    },
    {
        "name": "deepseek-r1",
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-reasoner",
    },
]
