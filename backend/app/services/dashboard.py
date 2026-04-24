from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
import math
import statistics

from backend.app.database import duckdb_connection
from backend.app.models import (
    AnalyticsSnapshot,
    CurvePoint,
    ExposureSlice,
    PlatformResponse,
    PlatformSummary,
    PositionSnapshot,
    TradeHistoryRow,
)


ZERO = Decimal("0")
NAV_START = Decimal("100")

SECTOR_MAP = {
    "APO": "Financials",
    "BRK.B": "Financials",
    "BROS": "Consumer",
    "BWXT": "Industrials",
    "BX": "Financials",
    "CAT": "Industrials",
    "CC": "Materials",
    "COIN": "Financials",
    "GEV": "Industrials",
    "GOOG": "Communication",
    "HOOD": "Financials",
    "JPM": "Financials",
    "KKR": "Financials",
    "KRO": "Materials",
    "META": "Communication",
    "MSFT": "Technology",
    "MU": "Technology",
    "NE": "Energy",
    "NU": "Financials",
    "NVDA": "Technology",
    "PVH": "Consumer",
    "RL": "Consumer",
    "SGI": "Consumer",
    "SPY": "Index ETF",
    "TDW": "Energy",
    "TSLA": "Consumer",
    "WWD": "Industrials",
}

RISK_BUCKET_MAP = {
    "APO": "Private Capital",
    "BRK.B": "Financials",
    "BROS": "Consumer Cyclical",
    "BWXT": "Industrials & Defense",
    "BX": "Private Capital",
    "CAT": "Industrials & Defense",
    "CC": "Materials & Chemicals",
    "COIN": "Financials",
    "GEV": "Industrials & Defense",
    "GOOG": "Platform Tech",
    "HOOD": "Financials",
    "JPM": "Financials",
    "KKR": "Private Capital",
    "KRO": "Materials & Chemicals",
    "META": "Platform Tech",
    "MSFT": "Platform Tech",
    "MU": "Semiconductors",
    "NE": "Energy",
    "NU": "Financials",
    "NVDA": "Semiconductors",
    "PVH": "Consumer Cyclical",
    "RL": "Consumer Cyclical",
    "SGI": "Consumer Cyclical",
    "SPY": "Broad Market Beta",
    "TDW": "Energy",
    "TSLA": "Consumer Cyclical",
    "WWD": "Industrials & Defense",
}


@dataclass
class PositionRow:
    as_of: datetime
    ticker: str
    pnl_label: str
    shares: Decimal | None = None
    average_cost: Decimal | None = None
    market_price: Decimal | None = None


@dataclass
class PositionLedger:
    modeled_shares: Decimal = ZERO
    modeled_cost_basis: Decimal = ZERO
    last_trade_at: datetime | None = None
    last_trade_price: Decimal | None = None
    has_coverage_gap: bool = False


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _parse_pnl_percent(raw_value: str) -> Decimal:
    cleaned = raw_value.strip().replace("%", "")
    return Decimal(cleaned) / Decimal("100")


def _format_pnl_label_from_prices(
    average_cost: Decimal | None,
    market_price: Decimal | None,
) -> str:
    if not average_cost or average_cost <= ZERO or market_price is None:
        return "0.00%"
    pnl_percent = ((market_price / average_cost) - Decimal("1")) * Decimal("100")
    return f"{pnl_percent.quantize(Decimal('0.01'))}%"


def _load_position_rows() -> list[PositionRow]:
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

        if "portfolio" in tables:
            rows = connection.execute(
                """
                SELECT
                    COALESCE(portfolio.timestamp, positions.timestamp) AS as_of,
                    COALESCE(portfolio.ticker, positions."$Ticker ") AS ticker,
                    positions."P&L (%)" AS pnl_label,
                    portfolio.num_shares,
                    portfolio.avg_cost,
                    portfolio.price
                FROM positions
                FULL OUTER JOIN portfolio
                    ON portfolio.ticker = positions."$Ticker "
                ORDER BY ticker
                """
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT
                    timestamp,
                    "$Ticker " AS ticker,
                    "P&L (%)" AS pnl_label,
                    NULL AS num_shares,
                    NULL AS avg_cost,
                    NULL AS price
                FROM positions
                ORDER BY ticker
                """
            ).fetchall()

    return [
        PositionRow(
            as_of=row[0],
            ticker=row[1],
            pnl_label=row[2] or _format_pnl_label_from_prices(
                Decimal(str(row[4])) if row[4] is not None else None,
                Decimal(str(row[5])) if row[5] is not None else None,
            ),
            shares=Decimal(str(row[3])) if row[3] is not None else None,
            average_cost=Decimal(str(row[4])) if row[4] is not None else None,
            market_price=Decimal(str(row[5])) if row[5] is not None else None,
        )
        for row in rows
        if row[0] is not None and row[1] is not None
    ]


def _load_trade_rows() -> list[TradeHistoryRow]:
    with duckdb_connection() as connection:
        rows = connection.execute(
            """
            SELECT timestamp, ticker, num_shares, price
            FROM trade_history
            ORDER BY timestamp ASC, ticker ASC
            """
        ).fetchall()

    return [
        TradeHistoryRow(
            timestamp=row[0],
            ticker=row[1],
            num_shares=float(row[2]),
            price=float(row[3]),
            side="Buy" if row[2] > 0 else "Sell",
            notional=float(abs(row[2] * row[3])),
        )
        for row in rows
    ]


def _load_position_history() -> dict[str, dict[date, float]]:
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
        if "position_history" not in tables:
            return {}

        rows = connection.execute(
            """
            SELECT as_of_date, ticker, pnl_percent
            FROM position_history
            ORDER BY as_of_date ASC, ticker ASC
            """
        ).fetchall()

    history: dict[str, dict[date, float]] = defaultdict(dict)
    for as_of_date, ticker, pnl_percent in rows:
        history[ticker][as_of_date] = float(pnl_percent)
    return history


def _load_trade_flows() -> dict[date, Decimal]:
    with duckdb_connection() as connection:
        rows = connection.execute(
            """
            SELECT CAST(timestamp AS DATE) AS as_of_date, SUM(num_shares * price) AS net_flow
            FROM trade_history
            GROUP BY 1
            ORDER BY 1
            """
        ).fetchall()

    return {
        row[0]: Decimal(str(row[1]))
        for row in rows
        if row[1] is not None
    }


def _load_curve_from_portfolio_history() -> list[tuple[date, Decimal]]:
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
        if "portfolio_history" not in tables:
            return []

        rows = connection.execute(
            """
            SELECT as_of_date, SUM(market_value) AS portfolio_value
            FROM portfolio_history
            GROUP BY 1
            ORDER BY 1
            """
        ).fetchall()

    return [(row[0], Decimal(str(row[1]))) for row in rows if row[1] is not None]


def _build_ledgers(trades: list[TradeHistoryRow]) -> dict[str, PositionLedger]:
    ledgers: dict[str, PositionLedger] = {}

    for trade in trades:
        ledger = ledgers.setdefault(trade.ticker, PositionLedger())
        quantity = Decimal(str(trade.num_shares))
        price = Decimal(str(trade.price))
        ledger.last_trade_at = trade.timestamp
        ledger.last_trade_price = price

        if quantity > ZERO:
            ledger.modeled_shares += quantity
            ledger.modeled_cost_basis += quantity * price
            continue

        sell_quantity = abs(quantity)
        if ledger.modeled_shares <= ZERO:
            ledger.has_coverage_gap = True
            continue

        modeled_sell_quantity = min(sell_quantity, ledger.modeled_shares)
        average_cost = (
            ledger.modeled_cost_basis / ledger.modeled_shares
            if ledger.modeled_shares > ZERO
            else ZERO
        )
        ledger.modeled_cost_basis -= average_cost * modeled_sell_quantity
        ledger.modeled_shares -= modeled_sell_quantity
        if sell_quantity > modeled_sell_quantity:
            ledger.has_coverage_gap = True

    return ledgers


def _append_anchor(
    anchors: dict[str, list[tuple[int, Decimal]]],
    ticker: str,
    point_date: date,
    price: Decimal,
) -> None:
    series = anchors.setdefault(ticker, [])
    ordinal = point_date.toordinal()
    if series and series[-1][0] == ordinal:
        series[-1] = (ordinal, price)
        return
    series.append((ordinal, price))


def _interpolate_price(anchors: list[tuple[int, Decimal]], ordinal: int) -> Decimal:
    if not anchors:
        return ZERO
    if ordinal <= anchors[0][0]:
        return anchors[0][1]
    if ordinal >= anchors[-1][0]:
        return anchors[-1][1]

    for index in range(1, len(anchors)):
        left_ordinal, left_price = anchors[index - 1]
        right_ordinal, right_price = anchors[index]
        if ordinal > right_ordinal:
            continue
        if right_ordinal == left_ordinal:
            return right_price
        fraction = Decimal(ordinal - left_ordinal) / Decimal(right_ordinal - left_ordinal)
        return left_price + ((right_price - left_price) * fraction)

    return anchors[-1][1]


def _date_range(start: date, end: date) -> list[date]:
    current = start
    dates: list[date] = []
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def _build_current_positions(
    position_rows: list[PositionRow],
    ledgers: dict[str, PositionLedger],
) -> tuple[list[PositionSnapshot], dict[str, Decimal], Decimal, Decimal]:
    positions: list[PositionSnapshot] = []
    current_price_map: dict[str, Decimal] = {}
    portfolio_value = ZERO
    total_unrealized = ZERO

    for row in position_rows:
        pnl_percent = _parse_pnl_percent(row.pnl_label)
        ledger = ledgers.get(row.ticker, PositionLedger())
        average_cost = None
        market_price = None
        market_value = None
        unrealized_pnl = None
        shares = row.shares

        if (
            row.shares is not None
            and row.average_cost is not None
            and row.market_price is not None
            and row.shares > ZERO
        ):
            average_cost = row.average_cost
            market_price = row.market_price
            market_value = market_price * row.shares
            unrealized_pnl = market_value - (average_cost * row.shares)
            current_price_map[row.ticker] = market_price
            portfolio_value += market_value
            total_unrealized += unrealized_pnl
        elif ledger.modeled_shares > ZERO and ledger.modeled_cost_basis > ZERO:
            shares = ledger.modeled_shares
            average_cost = ledger.modeled_cost_basis / ledger.modeled_shares
            market_price = average_cost * (Decimal("1") + pnl_percent)
            market_value = market_price * ledger.modeled_shares
            unrealized_pnl = market_value - ledger.modeled_cost_basis
            current_price_map[row.ticker] = market_price
            portfolio_value += market_value
            total_unrealized += unrealized_pnl

        coverage_status = "modeled"
        if market_value is None or (row.shares is None and ledger.has_coverage_gap):
            coverage_status = "partial"

        positions.append(
            PositionSnapshot(
                ticker=row.ticker,
                sector=SECTOR_MAP.get(row.ticker, "Other"),
                risk_bucket=RISK_BUCKET_MAP.get(row.ticker, "Other"),
                pnl_percent=float(pnl_percent),
                pnl_label=row.pnl_label,
                coverage_status=coverage_status,
                shares=_decimal_to_float(shares if shares and shares > ZERO else None),
                average_cost=_decimal_to_float(average_cost),
                market_price=_decimal_to_float(market_price),
                market_value=_decimal_to_float(market_value),
                unrealized_pnl=_decimal_to_float(unrealized_pnl),
                weight=None,
                last_trade_at=ledger.last_trade_at,
            )
        )

    for position in positions:
        if position.market_value is not None and portfolio_value > ZERO:
            position.weight = float(Decimal(str(position.market_value)) / portfolio_value)

    positions.sort(key=lambda item: item.market_value or 0.0, reverse=True)
    return positions, current_price_map, portfolio_value, total_unrealized


def _build_price_anchors(
    trades: list[TradeHistoryRow],
    current_price_map: dict[str, Decimal],
    snapshot_date: date,
) -> dict[str, list[tuple[int, Decimal]]]:
    anchors: dict[str, list[tuple[int, Decimal]]] = {}

    for trade in trades:
        _append_anchor(
            anchors,
            trade.ticker,
            trade.timestamp.date(),
            Decimal(str(trade.price)),
        )

    for ticker, current_price in current_price_map.items():
        _append_anchor(anchors, ticker, snapshot_date, current_price)

    return anchors


def _historical_market_price(
    ticker: str,
    current_date: date,
    average_cost: Decimal,
    price_anchors: dict[str, list[tuple[int, Decimal]]],
    position_history: dict[str, dict[date, float]],
) -> Decimal:
    pnl_history = position_history.get(ticker)
    if pnl_history and current_date in pnl_history:
        return average_cost * (Decimal("1") + Decimal(str(pnl_history[current_date])))
    return _interpolate_price(price_anchors.get(ticker, []), current_date.toordinal())


def _build_curve(
    trades: list[TradeHistoryRow],
    price_anchors: dict[str, list[tuple[int, Decimal]]],
    snapshot_date: date,
    position_history: dict[str, dict[date, float]],
) -> tuple[list[CurvePoint], list[float]]:
    if not trades:
        return [], []

    start_date = min(trade.timestamp.date() for trade in trades)
    trades_by_day: dict[date, list[TradeHistoryRow]] = defaultdict(list)
    for trade in trades:
        trades_by_day[trade.timestamp.date()].append(trade)

    holdings: dict[str, Decimal] = defaultdict(lambda: ZERO)
    cost_basis: dict[str, Decimal] = defaultdict(lambda: ZERO)
    points: list[CurvePoint] = []
    daily_returns: list[float] = []
    nav = NAV_START
    peak_nav = NAV_START
    previous_value = ZERO

    for current_date in _date_range(start_date, snapshot_date):
        net_flow = ZERO
        for trade in trades_by_day.get(current_date, []):
            quantity = Decimal(str(trade.num_shares))
            price = Decimal(str(trade.price))
            holdings[trade.ticker] += quantity
            net_flow += quantity * price
            if quantity > ZERO:
                cost_basis[trade.ticker] += quantity * price
            else:
                sell_quantity = abs(quantity)
                existing_shares = holdings[trade.ticker] - quantity
                if existing_shares > ZERO and cost_basis[trade.ticker] > ZERO:
                    average_cost = cost_basis[trade.ticker] / existing_shares
                    cost_basis[trade.ticker] -= average_cost * min(sell_quantity, existing_shares)
            if holdings[trade.ticker] <= ZERO:
                holdings.pop(trade.ticker, None)
                cost_basis.pop(trade.ticker, None)

        portfolio_value = ZERO
        ordinal = current_date.toordinal()
        for ticker, shares in holdings.items():
            if shares <= ZERO:
                continue
            average_cost = (
                cost_basis[ticker] / shares
                if shares > ZERO and ticker in cost_basis and cost_basis[ticker] > ZERO
                else _interpolate_price(price_anchors.get(ticker, []), ordinal)
            )
            market_price = _historical_market_price(
                ticker,
                current_date,
                average_cost,
                price_anchors,
                position_history,
            )
            portfolio_value += shares * market_price

        if previous_value > ZERO:
            denominator = previous_value + (net_flow / Decimal("2"))
            if denominator > ZERO:
                daily_return = (portfolio_value - previous_value - net_flow) / denominator
            else:
                daily_return = ZERO
            nav *= Decimal("1") + daily_return
            daily_returns.append(float(daily_return))
        else:
            daily_return = ZERO

        if nav > peak_nav:
            peak_nav = nav
        drawdown = (nav / peak_nav) - Decimal("1") if peak_nav > ZERO else ZERO
        points.append(
            CurvePoint(
                date=current_date,
                portfolio_value=float(portfolio_value),
                nav=float(nav),
                drawdown=float(drawdown),
                net_flow=float(net_flow),
            )
        )
        previous_value = portfolio_value

    return points, daily_returns


def _build_curve_from_history(
    history_points: list[tuple[date, Decimal]],
    trade_flows: dict[date, Decimal],
) -> tuple[list[CurvePoint], list[float]]:
    if not history_points:
        return [], []

    points: list[CurvePoint] = []
    daily_returns: list[float] = []
    nav = NAV_START
    peak_nav = NAV_START
    previous_value = ZERO

    for current_date, portfolio_value in history_points:
        net_flow = trade_flows.get(current_date, ZERO)

        if previous_value > ZERO:
            denominator = previous_value + (net_flow / Decimal("2"))
            if denominator > ZERO:
                daily_return = (portfolio_value - previous_value - net_flow) / denominator
            else:
                daily_return = ZERO
            nav *= Decimal("1") + daily_return
            daily_returns.append(float(daily_return))
        else:
            daily_return = ZERO

        if nav > peak_nav:
            peak_nav = nav
        drawdown = (nav / peak_nav) - Decimal("1") if peak_nav > ZERO else ZERO
        points.append(
            CurvePoint(
                date=current_date,
                portfolio_value=float(portfolio_value),
                nav=float(nav),
                drawdown=float(drawdown),
                net_flow=float(net_flow),
            )
        )
        previous_value = portfolio_value

    return points, daily_returns


def _recent_pnl(curve: list[CurvePoint]) -> tuple[float, float]:
    if not curve:
        return 0.0, 0.0

    latest_point = curve[-1]
    target_date = latest_point.date - timedelta(days=30)
    base_point = curve[0]
    for point in curve:
        if point.date >= target_date:
            base_point = point
            break

    pnl_value = latest_point.portfolio_value - base_point.portfolio_value
    pnl_percent = (pnl_value / base_point.portfolio_value) if base_point.portfolio_value else 0.0
    return pnl_value, pnl_percent


def _build_exposure(
    positions: list[PositionSnapshot],
    attribute: str,
) -> list[ExposureSlice]:
    grouped: dict[str, Decimal] = defaultdict(lambda: ZERO)
    total_value = sum((Decimal(str(position.market_value)) for position in positions if position.market_value), ZERO)

    for position in positions:
        if position.market_value is None:
            continue
        label = getattr(position, attribute)
        grouped[label] += Decimal(str(position.market_value))

    slices = [
        ExposureSlice(
            label=label,
            value=float(value),
            weight=float(value / total_value) if total_value > ZERO else 0.0,
        )
        for label, value in grouped.items()
    ]
    slices.sort(key=lambda item: item.value, reverse=True)
    return slices


def _build_analytics(curve: list[CurvePoint], daily_returns: list[float], positions: list[PositionSnapshot]) -> AnalyticsSnapshot:
    if not curve or not daily_returns:
        return AnalyticsSnapshot(
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown=0.0,
            cagr=0.0,
            annualized_volatility=0.0,
            win_rate=0.0,
            best_day=0.0,
            worst_day=0.0,
            top_position_weight=0.0,
            top_five_weight=0.0,
        )

    mean_return = statistics.fmean(daily_returns)
    volatility = statistics.stdev(daily_returns) if len(daily_returns) > 1 else 0.0
    downside_returns = [value for value in daily_returns if value < 0]
    downside_deviation = statistics.stdev(downside_returns) if len(downside_returns) > 1 else 0.0

    annualized_volatility = volatility * math.sqrt(252) if volatility else 0.0
    sharpe_ratio = (mean_return / volatility) * math.sqrt(252) if volatility else None
    sortino_ratio = (
        (mean_return / downside_deviation) * math.sqrt(252)
        if downside_deviation and downside_deviation >= 0.001 and len(downside_returns) >= 10
        else None
    )

    starting_nav = curve[0].nav or 100.0
    ending_nav = curve[-1].nav or starting_nav
    total_days = max((curve[-1].date - curve[0].date).days, 1)
    years = total_days / 365.25
    cagr = ((ending_nav / starting_nav) ** (1 / years) - 1) if years > 0 else 0.0

    max_drawdown = min(point.drawdown for point in curve)
    best_day = max(daily_returns)
    worst_day = min(daily_returns)
    positive_days = sum(1 for value in daily_returns if value > 0)
    win_rate = positive_days / len(daily_returns) if daily_returns else 0.0

    weighted_positions = [position.weight or 0.0 for position in positions if position.weight is not None]
    weighted_positions.sort(reverse=True)
    top_position_weight = weighted_positions[0] if weighted_positions else 0.0
    top_five_weight = sum(weighted_positions[:5]) if weighted_positions else 0.0

    return AnalyticsSnapshot(
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        cagr=cagr,
        annualized_volatility=annualized_volatility,
        win_rate=win_rate,
        best_day=best_day,
        worst_day=worst_day,
        top_position_weight=top_position_weight,
        top_five_weight=top_five_weight,
    )


def get_platform_data() -> PlatformResponse:
    position_rows = _load_position_rows()
    trades = _load_trade_rows()
    position_history = _load_position_history()
    trade_flows = _load_trade_flows()
    portfolio_history_curve = _load_curve_from_portfolio_history()
    ledgers = _build_ledgers(trades)

    snapshot_date = max((row.as_of.date() for row in position_rows), default=date.today())
    positions, current_price_map, portfolio_value, total_unrealized = _build_current_positions(
        position_rows,
        ledgers,
    )
    if portfolio_history_curve:
        curve, daily_returns = _build_curve_from_history(
            portfolio_history_curve,
            trade_flows,
        )
    else:
        price_anchors = _build_price_anchors(trades, current_price_map, snapshot_date)
        curve, daily_returns = _build_curve(
            trades,
            price_anchors,
            snapshot_date,
            position_history,
        )
    recent_pnl, recent_pnl_percent = _recent_pnl(curve)
    sector_exposure = _build_exposure(positions, "sector")
    risk_exposure = _build_exposure(positions, "risk_bucket")
    analytics = _build_analytics(curve, daily_returns, positions)

    latest_trade = trades[-1] if trades else None
    summary = PlatformSummary(
        portfolio_value=float(portfolio_value),
        recent_pnl=recent_pnl,
        recent_pnl_percent=recent_pnl_percent,
        unrealized_pnl=float(total_unrealized),
        latest_trade_at=latest_trade.timestamp if latest_trade else None,
        latest_trade_label=f"{latest_trade.ticker} {latest_trade.side}" if latest_trade else None,
        coverage_ratio=(
            sum(1 for position in positions if position.coverage_status == "modeled") / len(positions)
            if positions
            else 0.0
        ),
    )

    trades_desc = sorted(trades, key=lambda trade: (trade.timestamp, trade.ticker), reverse=True)
    return PlatformResponse(
        summary=summary,
        curve=curve,
        positions=positions,
        trades=trades_desc,
        analytics=analytics,
        sector_exposure=sector_exposure,
        risk_exposure=risk_exposure,
    )


def get_dashboard_data() -> PlatformResponse:
    return get_platform_data()
