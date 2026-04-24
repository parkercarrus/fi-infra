import { formatCurrency, formatPercent } from "@/lib/format";
import { ExposureSlice } from "@/lib/types";

type ExposurePanelProps = {
  title: string;
  items: ExposureSlice[];
};

export function ExposurePanel({ title, items }: ExposurePanelProps) {
  const largestValue = items[0]?.value ?? 1;

  return (
    <section className="rounded-[2rem] border border-white/8 bg-[linear-gradient(180deg,rgba(12,20,31,0.96),rgba(8,13,22,0.98))] p-6 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
      <h2 className="text-lg font-semibold tracking-[-0.04em] text-white">
        {title}
      </h2>

      <div className="mt-6 flex flex-col gap-4">
        {items.map((item) => {
          const width = Math.max(
            12,
            (item.value / largestValue) * 100,
          );

          return (
            <div key={item.label} className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-white">{item.label}</span>
                </div>
                <span className="text-sm font-medium text-[var(--broker-text-muted)]">
                  {formatCurrency(item.value)} · {formatPercent(item.weight)}
                </span>
              </div>

              <div className="h-2 overflow-hidden rounded-full bg-white/8">
                <div
                  className="h-full rounded-full bg-[linear-gradient(90deg,#22d3ee,#38bdf8)]"
                  style={{ width: `${width}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
