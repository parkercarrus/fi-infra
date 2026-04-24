import { ExposurePanel } from "@/components/exposure-panel";
import { PageEmptyState } from "@/components/page-empty-state";
import { PositionsGrid } from "@/components/positions-grid";
import { SummaryStrip } from "@/components/summary-strip";
import { getPlatformData } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function PortfolioPage() {
  const platform = await getPlatformData();

  if (!platform) {
    return <PageEmptyState title="Portfolio" />;
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[110rem] flex-col gap-6 px-6 py-8 md:px-8">
      <SummaryStrip summary={platform.summary} />
      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <PositionsGrid positions={platform.positions} />
        <div className="flex flex-col gap-6">
          <ExposurePanel title="Sector Exposure" items={platform.sector_exposure} />
          <ExposurePanel title="Risk Buckets" items={platform.risk_exposure} />
        </div>
      </section>
    </main>
  );
}
