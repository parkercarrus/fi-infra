import { PerformanceChart } from "@/components/performance-chart";
import { PageEmptyState } from "@/components/page-empty-state";
import { SummaryStrip } from "@/components/summary-strip";
import { TradeHistoryTable } from "@/components/trade-history-table";
import { getPlatformData } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  const platform = await getPlatformData();

  if (!platform) {
    return <PageEmptyState title="Overview" />;
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-[110rem] flex-col gap-6 px-6 py-8 md:px-8">
      <SummaryStrip summary={platform.summary} />
      <PerformanceChart points={platform.curve} title="Total Value" />
      <TradeHistoryTable trades={platform.trades} />
    </main>
  );
}
