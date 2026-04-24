import { AnalyticsGrid } from "@/components/analytics-grid";
import { ExposurePanel } from "@/components/exposure-panel";
import { PageEmptyState } from "@/components/page-empty-state";
import { PerformanceChart } from "@/components/performance-chart";
import { getPlatformData } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage() {
  const platform = await getPlatformData();

  if (!platform) {
    return <PageEmptyState title="Analytics" />;
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[110rem] flex-col gap-6 px-6 py-8 md:px-8">
      <AnalyticsGrid analytics={platform.analytics} />
      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.95fr]">
        <PerformanceChart points={platform.curve} title="Portfolio Curve" />
        <PerformanceChart
          points={platform.curve}
          title="Drawdown"
          mode="drawdown"
        />
      </section>
      <section className="grid gap-6 xl:grid-cols-2">
        <ExposurePanel title="Sector Risk" items={platform.sector_exposure} />
        <ExposurePanel title="Common Risk Exposure" items={platform.risk_exposure} />
      </section>
    </main>
  );
}
