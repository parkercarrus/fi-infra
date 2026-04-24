type PageEmptyStateProps = {
  title: string;
};

export function PageEmptyState({ title }: PageEmptyStateProps) {
  return (
    <main className="mx-auto flex min-h-[70vh] w-full max-w-[110rem] items-center px-6 py-10 md:px-8">
      <section className="w-full rounded-[2.2rem] border border-white/8 bg-[linear-gradient(180deg,rgba(12,20,31,0.96),rgba(8,13,22,0.98))] p-8 shadow-[0_20px_80px_rgba(0,0,0,0.28)]">
        <p className="text-sm uppercase tracking-[0.28em] text-[var(--broker-text-muted)]">
          {title}
        </p>
        <p className="mt-4 text-3xl font-semibold tracking-[-0.06em] text-white">
          Backend connection required
        </p>
      </section>
    </main>
  );
}
