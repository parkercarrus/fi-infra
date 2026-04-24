from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from backend.app.database import duckdb_connection


ZERO = Decimal("0")


@dataclass(frozen=True)
class PortfolioSnapshotRow:
    timestamp: datetime
    ticker: str
    pnl_label: str


@dataclass
class PositionLedger:
    shares: Decimal = ZERO
    cost_basis: Decimal = ZERO
    has_coverage_gap: bool = False


def ensure_portfolio_table() -> None:
    with duckdb_connection(read_only=False) as connection:
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


def _parse_pnl_percent(raw_value: str) -> Decimal:
    return Decimal(raw_value.strip().replace("%", "")) / Decimal("100")


def _load_position_snapshots() -> list[PortfolioSnapshotRow]:
    with duckdb_connection() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, "$Ticker " AS ticker, "P&L (%)" AS pnl_label
            FROM positions
            ORDER BY ticker
            """
        ).fetchall()

    return [
        PortfolioSnapshotRow(timestamp=row[0], ticker=row[1], pnl_label=row[2])
        for row in rows
    ]


def _load_trade_rows() -> list[tuple[datetime, str, Decimal, Decimal]]:
    with duckdb_connection() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }
        if "trade_history" not in tables:
            return []

        rows = connection.execute(
            """
            SELECT timestamp, ticker, num_shares, price
            FROM trade_history
            ORDER BY timestamp ASC, ticker ASC
            """
        ).fetchall()

    return [
        (row[0], row[1], Decimal(str(row[2])), Decimal(str(row[3])))
        for row in rows
    ]


def _build_ledgers() -> dict[str, PositionLedger]:
    ledgers: dict[str, PositionLedger] = {}

    for _timestamp, ticker, quantity, price in _load_trade_rows():
        ledger = ledgers.setdefault(ticker, PositionLedger())
        if quantity > ZERO:
            ledger.shares += quantity
            ledger.cost_basis += quantity * price
            continue

        sell_quantity = abs(quantity)
        if ledger.shares <= ZERO:
            ledger.has_coverage_gap = True
            continue

        modeled_sell_quantity = min(sell_quantity, ledger.shares)
        average_cost = ledger.cost_basis / ledger.shares if ledger.shares > ZERO else ZERO
        ledger.cost_basis -= average_cost * modeled_sell_quantity
        ledger.shares -= modeled_sell_quantity

        if sell_quantity > modeled_sell_quantity:
            ledger.has_coverage_gap = True

    return ledgers


def sync_portfolio_table() -> int:
    ensure_portfolio_table()
    snapshots = _load_position_snapshots()
    if not snapshots:
        with duckdb_connection() as connection:
            return connection.execute("SELECT COUNT(*) FROM portfolio").fetchone()[0]

    ledgers = _build_ledgers()

    portfolio_rows: list[tuple[datetime, str, int | None, float | None, float | None]] = []
    for snapshot in snapshots:
        ledger = ledgers.get(snapshot.ticker, PositionLedger())
        shares: int | None = None
        avg_cost: float | None = None
        price: float | None = None

        if ledger.shares > ZERO and ledger.cost_basis > ZERO and not ledger.has_coverage_gap:
            integral_shares = ledger.shares.to_integral_value()
            if ledger.shares == integral_shares:
                average_cost = ledger.cost_basis / ledger.shares
                market_price = average_cost * (Decimal("1") + _parse_pnl_percent(snapshot.pnl_label))
                shares = int(integral_shares)
                avg_cost = float(average_cost)
                price = float(market_price)

        portfolio_rows.append(
            (snapshot.timestamp, snapshot.ticker, shares, avg_cost, price)
        )

    with duckdb_connection(read_only=False) as connection:
        connection.execute("DELETE FROM portfolio")
        if portfolio_rows:
            connection.executemany(
                """
                INSERT INTO portfolio (timestamp, ticker, num_shares, avg_cost, price)
                VALUES (?, ?, ?, ?, ?)
                """,
                portfolio_rows,
            )

    return len(portfolio_rows)
