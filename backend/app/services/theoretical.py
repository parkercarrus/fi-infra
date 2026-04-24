from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb


THEORETICAL_DB_PATH = Path(__file__).resolve().parents[3] / "Theoretical.duckdb"


def ensure_theoretical_tables() -> None:
    THEORETICAL_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(THEORETICAL_DB_PATH))
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio (
                timestamp TIMESTAMP,
                ticker VARCHAR,
                num_shares INTEGER,
                avg_cost DOUBLE,
                price DOUBLE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                timestamp TIMESTAMP,
                "$Ticker " VARCHAR,
                "P&L (%)" VARCHAR
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS theoretical_positions (
                timestamp TIMESTAMP,
                ticker VARCHAR,
                num_shares DOUBLE,
                price DOUBLE
            )
            """
        )
    finally:
        connection.close()


def reset_theoretical_db(source_db_path: str | Path | None = None) -> None:
    import duckdb

    ensure_theoretical_tables()
    source_path = Path(source_db_path) if source_db_path else Path(__file__).resolve().parents[3] / "algory.duckdb"

    source = duckdb.connect(str(source_path), read_only=True)
    target = duckdb.connect(str(THEORETICAL_DB_PATH))
    try:
        tables = {
            row[0]
            for row in source.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }
        portfolio_rows = []
        if "portfolio" in tables:
            portfolio_rows = source.execute(
                """
                SELECT timestamp, ticker, num_shares, avg_cost, price
                FROM portfolio
                """
            ).fetchall()
        rows = source.execute('SELECT timestamp, "$Ticker ", "P&L (%)" FROM positions').fetchall()
        target.execute("DELETE FROM portfolio")
        target.execute("DELETE FROM positions")
        if portfolio_rows:
            target.executemany(
                """
                INSERT INTO portfolio (timestamp, ticker, num_shares, avg_cost, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                portfolio_rows,
            )
        if rows:
            target.executemany(
                'INSERT INTO positions (timestamp, "$Ticker ", "P&L (%)") VALUES (?, ?, ?)',
                rows,
            )
    finally:
        source.close()
        target.close()


def add_theoretical_position(
    ticker: str,
    entrance: str,
    exit: str,
    num_shares: float = 1,
) -> int:
    import yfinance as yf

    ensure_theoretical_tables()
    data = yf.download(ticker, start=entrance, end=exit, auto_adjust=False, progress=False)
    if data.empty:
        return 0

    rows: list[tuple[datetime, str, float, float]] = []
    for index, row in data.iterrows():
        close_price = float(row["Close"])
        timestamp = index.to_pydatetime() if hasattr(index, "to_pydatetime") else datetime.fromisoformat(str(index))
        rows.append((timestamp, ticker, float(num_shares), close_price))

    connection = duckdb.connect(str(THEORETICAL_DB_PATH))
    try:
        connection.executemany(
            """
            INSERT INTO theoretical_positions (timestamp, ticker, num_shares, price)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
    finally:
        connection.close()

    return len(rows)
