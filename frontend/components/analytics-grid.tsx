import { MetricCard } from "@/components/metric-card";
import { formatPercent, formatSignedPercent } from "@/lib/format";
import { AnalyticsSnapshot } from "@/lib/types";

type AnalyticsGridProps = {
  analytics: AnalyticsSnapshot;
};

function formatRatio(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return value.toFixed(2);
}

export function AnalyticsGrid({ analytics }: AnalyticsGridProps) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <MetricCard label="Sharpe" value={formatRatio(analytics.sharpe_ratio)} />
      <MetricCard label="Sortino" value={formatRatio(analytics.sortino_ratio)} />
      <MetricCard
        label="Max Drawdown"
        value={formatSignedPercent(analytics.max_drawdown)}
        tone="negative"
      />
      <MetricCard label="CAGR" value={formatSignedPercent(analytics.cagr)} />
      <MetricCard
        label="Volatility"
        value={formatPercent(analytics.annualized_volatility)}
      />
      <MetricCard label="Win Rate" value={formatPercent(analytics.win_rate)} />
      <MetricCard
        label="Best Day"
        value={formatSignedPercent(analytics.best_day)}
        tone="positive"
      />
      <MetricCard
        label="Worst Day"
        value={formatSignedPercent(analytics.worst_day)}
        tone="negative"
      />
      <MetricCard
        label="Top 5 Weight"
        value={formatPercent(analytics.top_five_weight)}
      />
    </section>
  );
}
