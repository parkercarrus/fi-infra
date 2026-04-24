from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database_path: str


class PlatformSummary(BaseModel):
    portfolio_value: float
    recent_pnl: float
    recent_pnl_percent: float
    unrealized_pnl: float
    latest_trade_at: datetime | None
    latest_trade_label: str | None
    coverage_ratio: float


class CurvePoint(BaseModel):
    date: date
    portfolio_value: float
    nav: float
    drawdown: float
    net_flow: float


class PositionSnapshot(BaseModel):
    ticker: str
    sector: str
    risk_bucket: str
    pnl_percent: float
    pnl_label: str
    coverage_status: str
    shares: float | None
    average_cost: float | None
    market_price: float | None
    market_value: float | None
    unrealized_pnl: float | None
    weight: float | None
    last_trade_at: datetime | None


class TradeHistoryRow(BaseModel):
    timestamp: datetime
    ticker: str
    num_shares: float
    price: float
    side: str
    notional: float


class AnalyticsSnapshot(BaseModel):
    sharpe_ratio: float | None
    sortino_ratio: float | None
    max_drawdown: float
    cagr: float
    annualized_volatility: float
    win_rate: float
    best_day: float
    worst_day: float
    top_position_weight: float
    top_five_weight: float


class ExposureSlice(BaseModel):
    label: str
    value: float
    weight: float


class PlatformResponse(BaseModel):
    summary: PlatformSummary
    curve: list[CurvePoint]
    positions: list[PositionSnapshot]
    trades: list[TradeHistoryRow]
    analytics: AnalyticsSnapshot
    sector_exposure: list[ExposureSlice]
    risk_exposure: list[ExposureSlice]
