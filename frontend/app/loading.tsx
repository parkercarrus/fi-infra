export default function Loading() {
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[110rem] flex-col gap-6 px-6 py-8 md:px-8">
      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr_1fr]">
        <div className="h-36 animate-pulse rounded-[2rem] border border-white/8 bg-white/5" />
        <div className="h-36 animate-pulse rounded-[2rem] border border-white/8 bg-white/5" />
        <div className="h-36 animate-pulse rounded-[2rem] border border-white/8 bg-white/5" />
      </section>
      <section className="h-[30rem] animate-pulse rounded-[2rem] border border-white/8 bg-white/5" />
      <section className="h-[26rem] animate-pulse rounded-[2rem] border border-white/8 bg-white/5" />
    </main>
  );
}
