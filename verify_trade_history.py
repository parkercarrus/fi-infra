from pathlib import Path
import sys

import duckdb

from trade_history_utils import TRADE_HISTORY_COLUMNS, load_relevant_trade_history


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "algory.duckdb"
CSV_PATH = ROOT / "trade-history.csv"
POSITIONS_TABLE = "positions"
TRADE_HISTORY_TABLE = "trade_history"


def print_header() -> None:
    print()
    print("DuckDB Verification")
    print("===================")


def format_value(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def print_table(con: duckdb.DuckDBPyConnection, table_name: str) -> None:
    rows = con.execute(f'SELECT * FROM "{table_name}" ORDER BY ALL').fetchall()
    columns = [col[0] for col in con.description]

    widths = [len(name) for name in columns]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(format_value(value)))

    separator = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    header = "| " + " | ".join(name.ljust(widths[i]) for i, name in enumerate(columns)) + " |"

    print(table_name)
    print("-" * len(table_name))
    print(separator)
    print(header)
    print(separator)
    for row in rows:
        line = "| " + " | ".join(format_value(value).ljust(widths[i]) for i, value in enumerate(row)) + " |"
        print(line)
    print(separator)
    print()


def fail(message: str) -> int:
    print()
    print("Status : FAILED")
    print(f"Reason : {message}")
    return 1


def main() -> int:
    print_header()

    if not DB_PATH.exists():
        return fail(f"database not found at {DB_PATH}")
    if not CSV_PATH.exists():
        return fail(f"CSV not found at {CSV_PATH}")

    con = duckdb.connect(str(DB_PATH), read_only=True)
    expected_trade_history = load_relevant_trade_history(CSV_PATH)

    tables = {row[0] for row in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()}
    if POSITIONS_TABLE not in tables:
        con.close()
        return fail(f"table '{POSITIONS_TABLE}' does not exist in {DB_PATH.name}")
    if TRADE_HISTORY_TABLE not in tables:
        con.close()
        return fail(f"table '{TRADE_HISTORY_TABLE}' does not exist in {DB_PATH.name}")

    actual_schema = con.execute(f'DESCRIBE "{TRADE_HISTORY_TABLE}"').fetchall()
    expected_schema = [(name, data_type) for name, data_type in TRADE_HISTORY_COLUMNS]
    schema_pairs = [(name, data_type) for name, data_type, *_ in actual_schema]
    if schema_pairs != expected_schema:
        con.close()
        return fail(f"unexpected schema for '{TRADE_HISTORY_TABLE}': {schema_pairs}")

    positions_count = con.execute(f'SELECT COUNT(*) FROM "{POSITIONS_TABLE}"').fetchone()[0]
    trade_history_count = con.execute(f'SELECT COUNT(*) FROM "{TRADE_HISTORY_TABLE}"').fetchone()[0]
    expected_count = len(expected_trade_history)

    if trade_history_count != expected_count:
        con.close()
        return fail(
            f"row count mismatch for '{TRADE_HISTORY_TABLE}': "
            f"expected={expected_count}, actual={trade_history_count}"
        )

    actual_trade_history = con.execute(
        f'SELECT timestamp, ticker, num_shares, price FROM "{TRADE_HISTORY_TABLE}" ORDER BY ALL'
    ).fetchall()
    if actual_trade_history != expected_trade_history:
        con.close()
        return fail(f"contents of '{TRADE_HISTORY_TABLE}' do not match the transformed CSV input")

    print("Status        : PASSED")
    print(f"Database      : {DB_PATH.name}")
    print(f"CSV           : {CSV_PATH.name}")
    print(f"Positions     : {positions_count} rows")
    print(f"Trade History : {trade_history_count} rows")
    print("Checks        : required tables exist, trade_history schema matches, transformed data matches")
    print()

    print_table(con, POSITIONS_TABLE)
    print_table(con, TRADE_HISTORY_TABLE)
    con.close()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        try:
            sys.stdout.close()
        finally:
            sys.exit(0)
