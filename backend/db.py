from __future__ import annotations

from pathlib import Path

from backend.app.config import get_settings
from backend.app.services.google_sheet import ensure_position_tables


def get_database_path() -> Path:
    return get_settings().database_path


def initialize_duckdb() -> Path:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if not database_path.exists():
        raise FileNotFoundError(
            f"DuckDB file does not exist at '{database_path}'. "
            "Load the portfolio data before starting the API."
        )
    ensure_position_tables()
    print(f"DuckDB is available at '{database_path}'")
    return database_path


if __name__ == "__main__":
    initialize_duckdb()
