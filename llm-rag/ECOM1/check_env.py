from __future__ import annotations

from config import (
    BENCHMARK_ID,
    BITGN_API_KEY,
    MODEL_ID,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)


def mask(value: str) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def main() -> None:
    print(f"BITGN_API_KEY={mask(BITGN_API_KEY)}")
    print(f"OPENAI_API_KEY={mask(OPENAI_API_KEY)}")
    print(f"OPENAI_BASE_URL={OPENAI_BASE_URL or '<default>'}")
    print(f"BENCHMARK_ID={BENCHMARK_ID}")
    print(f"MODEL_ID={MODEL_ID}")


if __name__ == "__main__":
    main()
