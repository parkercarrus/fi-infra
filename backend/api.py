from __future__ import annotations
# Access Google Sheets API / BNY Mellon API and return information
from pathlib import Path
import duckdb
import yfinance as yf
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from main import portfolio

import argparse

from backend.main import app, main
from backend.app.services.google_sheet import rebuild_position_history, refresh_positions_from_sheet
from backend.app.services.portfolio_history import sync_portfolio_history
from backend.app.services.portfolio import sync_portfolio_table
from backend.app.services.theoretical import add_theoretical_position, reset_theoretical_db


def refresh_google_sheet_snapshot() -> int:
    return refresh_positions_from_sheet()


def rebuild_history() -> int:
    return rebuild_position_history()


def sync_portfolio_snapshot() -> int:
    return sync_portfolio_table()


def sync_daily_portfolio_history() -> tuple[int, int]:
    return sync_portfolio_history()
def fetchData(Timestamp):
    df = portfolio()
    con = duckdb.connect(str(Parent_Path))

    rows = [
        (Timestamp, df.iloc[i][0], df.iloc[i][3], df.iloc[i][6] / df.iloc[i][3])
        for i in range(df.shape[0])
    ]

    con.executemany("""
        INSERT INTO positions (timestamp, ticker, num_shares, price)
        VALUES (?, ?, ?, ?)
    """, rows)

    con.close()

def ResetTheoreticalDB():
    con = duckdb.connect(str(Parent_Path))
    df = con.sql("SELECT * FROM positions").df()
    con.close()
    
    Theoretical_db_path.unlink(missing_ok=True)
    
    new_con = duckdb.connect(str(Theoretical_db_path))
    new_con.execute("""
        CREATE TABLE positions (
            timestamp TIMESTAMP,
            ticker VARCHAR,
            num_shares INTEGER,
            price FLOAT
        )
    """)

    if not df.empty:
        rows = [
            (row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
             row[1], row[2], row[3])
            for row in df.itertuples(index=False)
        ]
        new_con.executemany("""
            INSERT INTO positions (timestamp, ticker, num_shares, price)
            VALUES (?, ?, ?, ?)
        """, rows)

    new_con.close()
    print("Theoretical database created from dataframe.")

def addTheoreticalPosition(TICKER, ENTRANCE, EXIT, numShares=1):
    data = yf.download(TICKER, start=ENTRANCE, end=EXIT)
    con = duckdb.connect(str(Theoretical_db_path))

    for i in range(len(data)):
        price = float(data.iloc[i]["Close"])
        con.execute("""
            INSERT INTO positions (timestamp, ticker, num_shares, price)
            VALUES (?, ?, ?, ?)
        """, [data.index[i].isoformat(), TICKER, numShares, price])  # isoformat() here too

    con.close() 


def reset_theoretical_positions() -> None:
    reset_theoretical_db()


def add_theoretical_positions(
    ticker: str,
    entrance: str,
    exit: str,
    num_shares: float = 1,
) -> int:
    return add_theoretical_position(
        ticker=ticker,
        entrance=entrance,
        exit=exit,
        num_shares=num_shares,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Portfolio maintenance commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve", help="Run the API server")
    subparsers.add_parser("refresh-sheet", help="Pull the latest Google Sheet snapshot into DuckDB")
    subparsers.add_parser("rebuild-history", help="Rebuild the forward-filled daily position history table")
    subparsers.add_parser("sync-portfolio", help="Rebuild the canonical portfolio table from positions and trade history")
    subparsers.add_parser(
        "rebuild-portfolio-history",
        help="Fetch daily closes and rebuild the day-by-day portfolio history table",
    )
    subparsers.add_parser("daily-refresh", help="Refresh the Google Sheet snapshot and rebuild history")
    subparsers.add_parser("reset-theoretical", help="Reset the theoretical database from the current positions table")

    add_theoretical_parser = subparsers.add_parser(
        "add-theoretical",
        help="Append a theoretical position price path from Yahoo Finance",
    )
    add_theoretical_parser.add_argument("ticker")
    add_theoretical_parser.add_argument("entrance")
    add_theoretical_parser.add_argument("exit")
    add_theoretical_parser.add_argument("--num-shares", type=float, default=1)

    return parser


def cli() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "serve":
        main()
        return

    if args.command in {"refresh-sheet", "daily-refresh"}:
        count = refresh_google_sheet_snapshot()
        history_message = ""
        if args.command == "daily-refresh":
            market_rows, portfolio_history_rows = sync_daily_portfolio_history()
            history_message = (
                f" fetched {market_rows} market price rows and rebuilt "
                f"{portfolio_history_rows} portfolio_history rows."
            )
        print(
            f"Loaded {count} rows from Google Sheets into positions and position_snapshots, "
            f"rebuilt position_history, and synced portfolio.{history_message}"
        )
        return

    if args.command == "rebuild-history":
        count = rebuild_history()
        print(f"Rebuilt position_history with {count} rows.")
        return

    if args.command == "sync-portfolio":
        count = sync_portfolio_snapshot()
        print(f"Synced portfolio with {count} rows.")
        return

    if args.command == "rebuild-portfolio-history":
        market_rows, portfolio_history_rows = sync_daily_portfolio_history()
        print(
            f"Fetched {market_rows} market price rows and rebuilt "
            f"portfolio_history with {portfolio_history_rows} rows."
        )
        return

    if args.command == "reset-theoretical":
        reset_theoretical_positions()
        print("Theoretical database reset from current positions.")
        return

    if args.command == "add-theoretical":
        count = add_theoretical_positions(
            ticker=args.ticker,
            entrance=args.entrance,
            exit=args.exit,
            num_shares=args.num_shares,
        )
        print(f"Added {count} theoretical rows for {args.ticker}.")
        return


__all__ = [
    "app",
    "main",
    "refresh_google_sheet_snapshot",
    "rebuild_history",
    "sync_portfolio_snapshot",
    "sync_daily_portfolio_history",
    "reset_theoretical_positions",
    "add_theoretical_positions",
    "cli",
]


if __name__ == "__main__":
    cli()
