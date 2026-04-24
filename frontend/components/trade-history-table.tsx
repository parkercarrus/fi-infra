import { formatDateTime, formatNumber, formatPreciseCurrency } from "@/lib/format";
import { TradeHistoryRow } from "@/lib/types";

type TradeHistoryTableProps = {
  trades: TradeHistoryRow[];
};

export function TradeHistoryTable({ trades }: TradeHistoryTableProps) {
  return (
    <section className="rounded-[2rem] border border-white/8 bg-[linear-gradient(180deg,rgba(12,20,31,0.96),rgba(8,13,22,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-[-0.04em] text-white">
          Trade History
        </h2>
        <span className="text-xs uppercase tracking-[0.22em] text-[var(--broker-text-muted)]">
          {trades.length} records
        </span>
      </div>

      <div className="overflow-hidden rounded-[1.5rem] border border-white/8">
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse">
            <thead className="bg-white/[0.03] text-left text-[0.72rem] uppercase tracking-[0.22em] text-[var(--broker-text-muted)]">
              <tr>
                <th className="px-4 py-4 font-semibold">Time</th>
                <th className="px-4 py-4 font-semibold">Ticker</th>
                <th className="px-4 py-4 font-semibold">Side</th>
                <th className="px-4 py-4 font-semibold">Shares</th>
                <th className="px-4 py-4 font-semibold">Price</th>
                <th className="px-4 py-4 font-semibold">Notional</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/6 bg-transparent text-sm text-white">
              {trades.map((trade) => (
                <tr key={`${trade.timestamp}-${trade.ticker}-${trade.num_shares}`}>
                  <td className="px-4 py-4 text-[var(--broker-text-muted)]">
                    {formatDateTime(trade.timestamp)}
                  </td>
                  <td className="px-4 py-4 font-semibold tracking-[0.16em]">
                    {trade.ticker}
                  </td>
                  <td className="px-4 py-4">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] ${
                        trade.side === "Buy"
                          ? "bg-emerald-400/12 text-emerald-300"
                          : "bg-rose-400/12 text-rose-300"
                      }`}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-white">
                    {formatNumber(Math.abs(trade.num_shares))}
                  </td>
                  <td className="px-4 py-4 text-[var(--broker-text-muted)]">
                    {formatPreciseCurrency(trade.price)}
                  </td>
                  <td className="px-4 py-4 text-white">
                    {formatPreciseCurrency(trade.notional)}
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
