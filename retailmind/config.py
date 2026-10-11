from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class Settings:
    database_path: Path = PROJECT_ROOT / "data" / "retailmind.db"
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-6-astra")
    max_rows: int = _positive_int("RETAILMIND_MAX_ROWS", 500)
    query_timeout_seconds: float = _positive_float(
        "RETAILMIND_QUERY_TIMEOUT_SECONDS", 3.0
    )
    max_sql_steps: int = _positive_int("RETAILMIND_MAX_SQL_STEPS", 200_000)


settings = Settings()

