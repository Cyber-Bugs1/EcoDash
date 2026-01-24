import { fetchStatesAction } from "@/lib/actions";
import { Header } from "@/components/dashboard/Header";
import { MetricDetail } from "@/components/dashboard/MetricDetail";

export default async function WaterLevelPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const resolvedParams = await searchParams;
  const currentState = (resolvedParams.state as string) || "Delhi";
  const allStates = await fetchStatesAction();

  return (
    <div className="min-h-screen bg-background">
      <Header states={allStates} currentState={currentState} />
      <main className="container mx-auto p-4">
        <MetricDetail
          metricKey="water_levels"
          metricName="Water Levels"
          metricUnit="m"
          metricDescription="Detailed monthly breakdown of water level measurements"
          chartColor="var(--color-chart-5)"
        />
      </main>
    </div>
  );
}
