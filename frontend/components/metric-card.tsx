type MetricCardProps = {
  label: string;
  value: string;
  tone?: "default" | "positive" | "negative";
};

export function MetricCard({
  label,
  value,
  tone = "default",
}: MetricCardProps) {
  const toneClass =
    tone === "positive"
      ? "border-emerald-400/18 bg-emerald-400/8 text-emerald-300"
      : tone === "negative"
        ? "border-rose-400/18 bg-rose-400/8 text-rose-300"
        : "border-white/8 bg-white/4 text-white";

  return (
    <article
      className={`rounded-[1.7rem] border px-5 py-5 shadow-[0_18px_40px_rgba(0,0,0,0.2)] ${toneClass}`}
    >
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.26em] text-[var(--broker-text-muted)]">
        {label}
      </p>
      <p className="mt-4 text-3xl font-semibold tracking-[-0.06em]">
        {value}
      </p>
    </article>
  );
}
