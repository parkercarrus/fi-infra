from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.app.database import duckdb_connection


ZERO = Decimal("0")


@dataclass(frozen=True)
class TradeEvent:
    trade_date: date
    ticker: str
    quantity: Decimal
    price: Decimal


def ensure_portfolio_history_tables() -> None:
    with duckdb_connection(read_only=False) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS market_price_history (
                as_of_date DATE,
                ticker VARCHAR,
                close_price DOUBLE,
                source VARCHAR,
                fetched_at TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_history (
                as_of_date DATE,
                ticker VARCHAR,
                shares DOUBLE,
                avg_cost DOUBLE,
                close_price DOUBLE,
                market_value DOUBLE,
                cost_basis DOUBLE,
                unrealized_pnl DOUBLE,
                price_source VARCHAR,
                is_price_forward_filled BOOLEAN
            )
            """
        )


def _load_trade_events() -> list[TradeEvent]:
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
            SELECT CAST(timestamp AS DATE), ticker, num_shares, price
            FROM trade_history
            ORDER BY timestamp ASC, ticker ASC
            """
        ).fetchall()

    return [
        TradeEvent(
            trade_date=row[0],
            ticker=row[1],
            quantity=Decimal(str(row[2])),
            price=Decimal(str(row[3])),
        )
        for row in rows
    ]


def _date_range(start_date: date, end_date: date) -> list[date]:
    current_date = start_date
    values: list[date] = []
    while current_date <= end_date:
        values.append(current_date)
        current_date += timedelta(days=1)
    return values


def _tickers_for_history(trades: list[TradeEvent]) -> list[str]:
    return sorted({trade.ticker for trade in trades if trade.quantity != ZERO})


def _yahoo_period_timestamp(value: date) -> int:
    return int(datetime(value.year, value.month, value.day).timestamp())


def _fetch_yahoo_close_history(
    ticker: str,
    start_date: date,
    end_date: date,
) -> list[tuple[date, float]]:
    period1 = _yahoo_period_timestamp(start_date)
    period2 = _yahoo_period_timestamp(end_date + timedelta(days=1))
    encoded_ticker = quote(ticker, safe="")
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_ticker}"
        f"?period1={period1}&period2={period2}&interval=1d&includeAdjustedClose=true"
    )
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=30) as response:
        payload = json.load(response)

    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return []

    timestamps = result[0].get("timestamp") or []
    quote_payload = ((result[0].get("indicators") or {}).get("quote") or [{}])[0]
    close_values = quote_payload.get("close") or []
    rows: list[tuple[date, float]] = []

    for raw_timestamp, close_price in zip(timestamps, close_values):
        if close_price is None:
            continue
        rows.append((datetime.utcfromtimestamp(raw_timestamp).date(), float(close_price)))

    return rows


def rebuild_market_price_history(end_date: date | None = None) -> int:
    trades = _load_trade_events()
    if not trades:
        ensure_portfolio_history_tables()
        with duckdb_connection(read_only=False) as connection:
            connection.execute("DELETE FROM market_price_history")
        return 0

    ensure_portfolio_history_tables()

    start_date = min(trade.trade_date for trade in trades)
    target_end_date = end_date or date.today()
    fetched_at = datetime.now()
    rows_to_insert: list[tuple[date, str, float, str, datetime]] = []

    for ticker in _tickers_for_history(trades):
        try:
            history_rows = _fetch_yahoo_close_history(
                ticker=ticker,
                start_date=start_date,
                end_date=target_end_date,
            )
        except Exception:
            continue
        for as_of_date, close_price in history_rows:
            rows_to_insert.append(
                (
                    as_of_date,
                    ticker,
                    close_price,
                    "yahoo_chart",
                    fetched_at,
                )
            )

    with duckdb_connection(read_only=False) as connection:
        connection.execute("DELETE FROM market_price_history")
        if rows_to_insert:
            connection.executemany(
                """
                INSERT INTO market_price_history (as_of_date, ticker, close_price, source, fetched_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows_to_insert,
            )

    return len(rows_to_insert)


def _load_price_history() -> tuple[dict[str, dict[date, Decimal]], date | None]:
    ensure_portfolio_history_tables()
    with duckdb_connection() as connection:
        rows = connection.execute(
            """
            SELECT as_of_date, ticker, close_price
            FROM market_price_history
            ORDER BY as_of_date ASC, ticker ASC
            """
        ).fetchall()

    price_history: dict[str, dict[date, Decimal]] = defaultdict(dict)
    last_date: date | None = None
    for as_of_date, ticker, close_price in rows:
        price_history[ticker][as_of_date] = Decimal(str(close_price))
        if last_date is None or as_of_date > last_date:
            last_date = as_of_date
    return price_history, last_date


def rebuild_portfolio_history(end_date: date | None = None) -> int:
    trades = _load_trade_events()
    ensure_portfolio_history_tables()
    if not trades:
        with duckdb_connection(read_only=False) as connection:
            connection.execute("DELETE FROM portfolio_history")
        return 0

    price_history, last_price_date = _load_price_history()
    if not price_history:
        rebuild_market_price_history(end_date=end_date)
        price_history, last_price_date = _load_price_history()
    if not price_history:
        raise RuntimeError(
            "market_price_history is empty; fetch market prices before rebuilding portfolio_history"
        )

    start_date = min(trade.trade_date for trade in trades)
    target_end_date = end_date or last_price_date or date.today()

    trades_by_date: dict[date, list[TradeEvent]] = defaultdict(list)
    for trade in trades:
        trades_by_date[trade.trade_date].append(trade)

    holdings: dict[str, Decimal] = defaultdict(lambda: ZERO)
    cost_basis: dict[str, Decimal] = defaultdict(lambda: ZERO)
    last_trade_price: dict[str, Decimal] = {}
    last_market_price: dict[str, Decimal] = {}
    rows_to_insert: list[tuple[date, str, float, float, float, float, float, float, str, bool]] = []

    for current_date in _date_range(start_date, target_end_date):
        for trade in trades_by_date.get(current_date, []):
            shares_before = holdings[trade.ticker]
            last_trade_price[trade.ticker] = trade.price

            if trade.quantity > ZERO:
                new_shares = shares_before + trade.quantity
                if shares_before < ZERO and new_shares <= ZERO:
                    holdings[trade.ticker] = new_shares
                    cost_basis[trade.ticker] = ZERO
                elif shares_before < ZERO < new_shares:
                    holdings[trade.ticker] = new_shares
                    cost_basis[trade.ticker] = new_shares * trade.price
                else:
                    holdings[trade.ticker] = new_shares
                    cost_basis[trade.ticker] += trade.quantity * trade.price
                continue

            sell_quantity = abs(trade.quantity)
            if shares_before > ZERO:
                average_cost = cost_basis[trade.ticker] / shares_before
                new_shares = shares_before - sell_quantity
                holdings[trade.ticker] = new_shares
                cost_basis[trade.ticker] = average_cost * new_shares if new_shares > ZERO else ZERO
            else:
                holdings[trade.ticker] = shares_before - sell_quantity
                cost_basis[trade.ticker] = ZERO

        for ticker, prices in price_history.items():
            if current_date in prices:
                last_market_price[ticker] = prices[current_date]

        for ticker, shares in holdings.items():
            if shares <= ZERO:
                continue

            close_price = price_history.get(ticker, {}).get(current_date)
            price_source = "yfinance"
            is_forward_filled = False

            if close_price is not None:
                last_market_price[ticker] = close_price
            elif ticker in last_market_price:
                close_price = last_market_price[ticker]
                price_source = "forward_fill"
                is_forward_filled = True
            elif ticker in last_trade_price:
                close_price = last_trade_price[ticker]
                last_market_price[ticker] = close_price
                price_source = "trade_price"
                is_forward_filled = True
            else:
                continue

            ticker_cost_basis = cost_basis[ticker]
            average_cost = ticker_cost_basis / shares if shares > ZERO else ZERO
            market_value = shares * close_price
            unrealized_pnl = market_value - ticker_cost_basis
            rows_to_insert.append(
                (
                    current_date,
                    ticker,
                    float(shares),
                    float(average_cost),
                    float(close_price),
                    float(market_value),
                    float(ticker_cost_basis),
                    float(unrealized_pnl),
                    price_source,
                    is_forward_filled,
                )
            )

    with duckdb_connection(read_only=False) as connection:
        connection.execute("DELETE FROM portfolio_history")
        if rows_to_insert:
            connection.executemany(
                """
                INSERT INTO portfolio_history (
                    as_of_date,
                    ticker,
                    shares,
                    avg_cost,
                    close_price,
                    market_value,
                    cost_basis,
                    unrealized_pnl,
                    price_source,
                    is_price_forward_filled
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows_to_insert,
            )

    return len(rows_to_insert)


def sync_portfolio_history(end_date: date | None = None) -> tuple[int, int]:
    market_price_rows = rebuild_market_price_history(end_date=end_date)
    portfolio_rows = rebuild_portfolio_history(end_date=end_date)
    return market_price_rows, portfolio_rows
