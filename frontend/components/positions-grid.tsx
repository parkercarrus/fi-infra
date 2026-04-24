import {
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
  formatSignedCurrency,
} from "@/lib/format";
import { PositionSnapshot } from "@/lib/types";

type PositionsGridProps = {
  positions: PositionSnapshot[];
};

export function PositionsGrid({ positions }: PositionsGridProps) {
  return (
    <section className="rounded-[2rem] border border-white/8 bg-[linear-gradient(180deg,rgba(12,20,31,0.96),rgba(8,13,22,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-[-0.04em] text-white">
          Positions
        </h2>
        <span className="text-xs uppercase tracking-[0.22em] text-[var(--broker-text-muted)]">
          {positions.length} holdings
        </span>
      </div>

      <div className="overflow-hidden rounded-[1.5rem] border border-white/8">
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead className="bg-white/[0.03] text-left text-[0.72rem] uppercase tracking-[0.22em] text-[var(--broker-text-muted)]">
              <tr>
                <th className="px-4 py-4 font-semibold">Ticker</th>
                <th className="px-4 py-4 font-semibold">Sector</th>
                <th className="px-4 py-4 font-semibold">Weight</th>
                <th className="px-4 py-4 font-semibold">Shares</th>
                <th className="px-4 py-4 font-semibold">Avg Cost</th>
                <th className="px-4 py-4 font-semibold">Price</th>
                <th className="px-4 py-4 font-semibold">Value</th>
                <th className="px-4 py-4 font-semibold">P&amp;L</th>
                <th className="px-4 py-4 font-semibold">Last Trade</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/6 bg-transparent text-sm text-white">
              {positions.map((position) => (
                <tr key={position.ticker}>
                  <td className="px-4 py-4 font-semibold tracking-[0.16em]">
                    {position.ticker}
                  </td>
                  <td className="px-4 py-4 text-[var(--broker-text-muted)]">
                    {position.sector}
                  </td>
                  <td className="px-4 py-4 text-white">
                    {formatPercent(position.weight)}
                  </td>
                  <td className="px-4 py-4 text-white">
                    {formatNumber(position.shares)}
                  </td>
                  <td className="px-4 py-4 text-[var(--broker-text-muted)]">
                    {formatCurrency(position.average_cost)}
                  </td>
                  <td className="px-4 py-4 text-[var(--broker-text-muted)]">
                    {formatCurrency(position.market_price)}
                  </td>
                  <td className="px-4 py-4 text-white">
                    {formatCurrency(position.market_value)}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex flex-col gap-1">
                      <span
                        className={
                          position.unrealized_pnl !== null && position.unrealized_pnl >= 0
                            ? "text-emerald-300"
                            : "text-rose-300"
                        }
                      >
                        {formatSignedCurrency(position.unrealized_pnl)}
                      </span>
                      <span className="text-xs text-[var(--broker-text-muted)]">
                        {position.pnl_label}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-4 text-[var(--broker-text-muted)]">
                    {formatDateTime(position.last_trade_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
