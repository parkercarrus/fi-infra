from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

from backend.app.database import duckdb_connection


DEFAULT_SHEET_ID = "1JOmzegYf0kGxDcjej0Fx_RCuFVoaOxobEnDsptjTJA8"
DEFAULT_GID = "595987006"


@dataclass(frozen=True)
class SheetPosition:
    timestamp: datetime
    ticker: str
    pnl_label: str
    pnl_percent: float


def build_google_sheet_csv_url(
    sheet_id: str = DEFAULT_SHEET_ID,
    gid: str = DEFAULT_GID,
) -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def ensure_position_tables() -> None:
    with duckdb_connection(read_only=False) as connection:
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
            CREATE TABLE IF NOT EXISTS position_snapshots (
                snapshot_time TIMESTAMP,
                ticker VARCHAR,
                pnl_label VARCHAR,
                pnl_percent DOUBLE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS position_history (
                as_of_date DATE,
                ticker VARCHAR,
                pnl_label VARCHAR,
                pnl_percent DOUBLE,
                source_snapshot_time TIMESTAMP,
                is_forward_filled BOOLEAN
            )
            """
        )

        snapshot_count = connection.execute(
            "SELECT COUNT(*) FROM position_snapshots"
        ).fetchone()[0]
        current_position_count = connection.execute(
            'SELECT COUNT(*) FROM positions'
        ).fetchone()[0]

        if snapshot_count == 0 and current_position_count > 0:
            rows = connection.execute(
                'SELECT timestamp, "$Ticker ", "P&L (%)" FROM positions'
            ).fetchall()
            snapshot_rows = [
                (timestamp, ticker, pnl_label, _parse_percent(pnl_label))
                for timestamp, ticker, pnl_label in rows
            ]
            connection.executemany(
                """
                INSERT INTO position_snapshots (snapshot_time, ticker, pnl_label, pnl_percent)
                VALUES (?, ?, ?, ?)
                """,
                snapshot_rows,
            )
            connection.executemany(
                """
                INSERT INTO position_history (
                    as_of_date,
                    ticker,
                    pnl_label,
                    pnl_percent,
                    source_snapshot_time,
                    is_forward_filled
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        timestamp.date(),
                        ticker,
                        pnl_label,
                        pnl_percent,
                        timestamp,
                        False,
                    )
                    for timestamp, ticker, pnl_label, pnl_percent in snapshot_rows
                ],
            )


def _parse_percent(raw_value: str) -> float:
    return float(raw_value.strip().replace("%", "")) / 100


def _select_relevant_columns(raw_rows: list[list[str]]) -> list[list[str]]:
    selected_rows: list[list[str]] = []
    for row in raw_rows:
        ticker_value = row[4].strip() if len(row) > 4 else ""
        pnl_value = row[10].strip() if len(row) > 10 else ""
        if ticker_value and pnl_value:
            selected_rows.append([ticker_value, pnl_value])
    return selected_rows


def _extract_positions(rows: list[list[str]], fetched_at: datetime) -> list[SheetPosition]:
    selected_rows = _select_relevant_columns(rows)
    if not selected_rows:
        return []

    header = selected_rows[0]
    if len(header) != 2:
        return []

    positions: list[SheetPosition] = []
    for ticker, pnl_label in selected_rows[1:]:
        if ticker == header[0] and pnl_label == header[1]:
            continue
        positions.append(
            SheetPosition(
                timestamp=fetched_at,
                ticker=ticker,
                pnl_label=pnl_label,
                pnl_percent=_parse_percent(pnl_label),
            )
        )

    return positions


def fetch_google_sheet_positions(
    csv_url: str | None = None,
    fetched_at: datetime | None = None,
) -> list[SheetPosition]:
    target_url = csv_url or build_google_sheet_csv_url()
    timestamp = fetched_at or datetime.now()

    with urlopen(target_url) as response:
        payload = response.read().decode("utf-8-sig")

    reader = csv.reader(io.StringIO(payload))
    return _extract_positions(list(reader), timestamp)


def load_google_sheet_positions_from_file(
    csv_path: str | Path,
    fetched_at: datetime | None = None,
) -> list[SheetPosition]:
    timestamp = fetched_at or datetime.now()
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return _extract_positions(list(reader), timestamp)


def rebuild_position_history() -> int:
    ensure_position_tables()

    with duckdb_connection(read_only=False) as connection:
        snapshot_rows = connection.execute(
            """
            SELECT snapshot_time, ticker, pnl_label, pnl_percent
            FROM position_snapshots
            ORDER BY snapshot_time ASC, ticker ASC
            """
        ).fetchall()

        if not snapshot_rows:
            connection.execute("DELETE FROM position_history")
            return 0

        per_ticker: dict[str, list[tuple[datetime, str, float]]] = {}
        for snapshot_time, ticker, pnl_label, pnl_percent in snapshot_rows:
            per_ticker.setdefault(ticker, []).append((snapshot_time, pnl_label, pnl_percent))

        start_date = min(snapshot_time.date() for snapshot_time, *_ in snapshot_rows)
        end_date = max(snapshot_time.date() for snapshot_time, *_ in snapshot_rows)
        rows_to_insert: list[tuple[date, str, str, float, datetime, bool]] = []

        for ticker, entries in per_ticker.items():
            current_index = 0
            last_snapshot: tuple[datetime, str, float] | None = None
            current_date = start_date

            while current_date <= end_date:
                while current_index < len(entries) and entries[current_index][0].date() <= current_date:
                    last_snapshot = entries[current_index]
                    current_index += 1

                if last_snapshot is not None:
                    snapshot_time, pnl_label, pnl_percent = last_snapshot
                    rows_to_insert.append(
                        (
                            current_date,
                            ticker,
                            pnl_label,
                            pnl_percent,
                            snapshot_time,
                            snapshot_time.date() != current_date,
                        )
                    )

                current_date += timedelta(days=1)

        connection.execute("DELETE FROM position_history")
        connection.executemany(
            """
            INSERT INTO position_history (
                as_of_date,
                ticker,
                pnl_label,
                pnl_percent,
                source_snapshot_time,
                is_forward_filled
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )

    return len(rows_to_insert)


def refresh_positions_from_sheet(
    csv_url: str | None = None,
    fetched_at: datetime | None = None,
) -> int:
    positions = fetch_google_sheet_positions(csv_url=csv_url, fetched_at=fetched_at)
    if not positions:
        return 0

    ensure_position_tables()
    snapshot_time = positions[0].timestamp

    with duckdb_connection(read_only=False) as connection:
        connection.execute("DELETE FROM positions")
        connection.executemany(
            """
            INSERT INTO positions (timestamp, "$Ticker ", "P&L (%)")
            VALUES (?, ?, ?)
            """,
            [(position.timestamp, position.ticker, position.pnl_label) for position in positions],
        )
        connection.execute(
            "DELETE FROM position_snapshots WHERE snapshot_time = ?",
            [snapshot_time],
        )
        connection.executemany(
            """
            INSERT INTO position_snapshots (snapshot_time, ticker, pnl_label, pnl_percent)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    position.timestamp,
                    position.ticker,
                    position.pnl_label,
                    position.pnl_percent,
                )
                for position in positions
            ],
        )

    rebuild_position_history()
    return len(positions)
