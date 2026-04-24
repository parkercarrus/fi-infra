import { formatCurrency, formatDateTime, formatSignedCurrency } from "@/lib/format";
import { PlatformSummary } from "@/lib/types";

type SummaryStripProps = {
  summary: PlatformSummary;
};

export function SummaryStrip({ summary }: SummaryStripProps) {
  const recentPnlTone =
    summary.recent_pnl > 0
      ? "text-emerald-400"
      : summary.recent_pnl < 0
        ? "text-rose-400"
        : "text-[var(--broker-text)]";

  return (
    <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr_1fr]">
      <article className="rounded-[2rem] border border-white/8 bg-[linear-gradient(135deg,rgba(27,45,67,0.96),rgba(10,17,27,0.98))] p-6 shadow-[0_18px_60px_rgba(0,0,0,0.25)]">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-cyan-300">
          Portfolio Value
        </p>
        <p className="mt-4 text-5xl font-semibold tracking-[-0.08em] text-white md:text-6xl">
          {formatCurrency(summary.portfolio_value, true)}
        </p>
      </article>

      <article className="rounded-[2rem] border border-emerald-400/15 bg-[linear-gradient(135deg,rgba(16,36,31,0.95),rgba(9,16,26,0.98))] p-6 shadow-[0_18px_60px_rgba(0,0,0,0.25)]">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-emerald-300">
          Recent P&amp;L
        </p>
        <p className={`mt-4 text-3xl font-semibold tracking-[-0.06em] ${recentPnlTone}`}>
          {formatSignedCurrency(summary.recent_pnl)}
        </p>
      </article>

      <article className="rounded-[2rem] border border-white/8 bg-[linear-gradient(135deg,rgba(24,31,48,0.95),rgba(9,16,26,0.98))] p-6 shadow-[0_18px_60px_rgba(0,0,0,0.25)]">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-amber-300">
          Most Recent Trade
        </p>
        <p className="mt-4 text-2xl font-semibold tracking-[-0.05em] text-white">
          {summary.latest_trade_label ?? "--"}
        </p>
        <p className="mt-2 text-sm text-[var(--broker-text-muted)]">
          {formatDateTime(summary.latest_trade_at)}
        </p>
      </article>
    </section>
  );
}
