from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BITGN_API_KEY = os.getenv("BITGN_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
BENCHMARK_ID = os.getenv("BENCHMARK_ID", "bitgn/ecom1-dev")
MODEL_ID = os.getenv("MODEL_ID", "gpt-4.1-2025-04-14")


def require_env(name: str, value: str) -> str:
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
