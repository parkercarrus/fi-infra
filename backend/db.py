from __future__ import annotations

from pathlib import Path

import duckdb

from backend.app.config import get_settings
from backend.app.services.google_sheet import ensure_position_tables
from backend.app.services.portfolio_history import ensure_portfolio_history_tables
from backend.app.services.portfolio import ensure_portfolio_table, sync_portfolio_table


def get_database_path() -> Path:
    return get_settings().database_path


def initialize_duckdb() -> Path:
    database_path = get_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(database_path))
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS trade_history (
                timestamp TIMESTAMP,
                ticker VARCHAR,
                num_shares DECIMAL(18,4),
                price DECIMAL(18,6)
            )
            """
        )
    finally:
        connection.close()

    ensure_position_tables()
    ensure_portfolio_table()
    ensure_portfolio_history_tables()
    sync_portfolio_table()
    print(f"DuckDB is available at '{database_path}'")
    return database_path


if __name__ == "__main__":
    initialize_duckdb()
