from __future__ import annotations

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
