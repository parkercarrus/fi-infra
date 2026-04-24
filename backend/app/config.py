from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    allowed_origins: tuple[str, ...]
    database_path: Path


def _split_origins(raw_value: str) -> tuple[str, ...]:
    origins = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    return tuple(origins)


def get_settings() -> Settings:
    root = Path(__file__).resolve().parents[2]
    return Settings(
        app_name="FI Infra Portfolio API",
        app_env=os.getenv("PORTFOLIO_API_ENV", "development"),
        app_host=os.getenv("PORTFOLIO_API_HOST", "127.0.0.1"),
        app_port=int(os.getenv("PORTFOLIO_API_PORT", "8000")),
        allowed_origins=_split_origins(
            os.getenv("PORTFOLIO_API_ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
        ),
        database_path=Path(os.getenv("PORTFOLIO_DB_PATH", root / "algory.duckdb")).resolve(),
    )
