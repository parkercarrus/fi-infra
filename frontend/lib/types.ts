export type PlatformSummary = {
  portfolio_value: number;
  recent_pnl: number;
  recent_pnl_percent: number;
  unrealized_pnl: number;
  latest_trade_at: string | null;
  latest_trade_label: string | null;
  coverage_ratio: number;
};

export type CurvePoint = {
  date: string;
  portfolio_value: number;
  nav: number;
  drawdown: number;
  net_flow: number;
};

export type PositionSnapshot = {
  ticker: string;
  sector: string;
  risk_bucket: string;
  pnl_percent: number;
  pnl_label: string;
  coverage_status: "modeled" | "partial";
  shares: number | null;
  average_cost: number | null;
  market_price: number | null;
  market_value: number | null;
  unrealized_pnl: number | null;
  weight: number | null;
  last_trade_at: string | null;
};

export type TradeHistoryRow = {
  timestamp: string;
  ticker: string;
  num_shares: number;
  price: number;
  side: "Buy" | "Sell";
  notional: number;
};

export type AnalyticsSnapshot = {
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown: number;
  cagr: number;
  annualized_volatility: number;
  win_rate: number;
  best_day: number;
  worst_day: number;
  top_position_weight: number;
  top_five_weight: number;
};

export type ExposureSlice = {
  label: string;
  value: number;
  weight: number;
};

export type PlatformData = {
  summary: PlatformSummary;
  curve: CurvePoint[];
  positions: PositionSnapshot[];
  trades: TradeHistoryRow[];
  analytics: AnalyticsSnapshot;
  sector_exposure: ExposureSlice[];
  risk_exposure: ExposureSlice[];
};
