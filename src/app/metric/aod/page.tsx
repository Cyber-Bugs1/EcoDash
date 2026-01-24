import { fetchStatesAction } from "@/lib/actions";
import { Header } from "@/components/dashboard/Header";
import { MetricDetail } from "@/components/dashboard/MetricDetail";

export default async function AODPage({
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
          metricKey="aod"
          metricName="Aerosol Optical Depth (AOD)"
          metricUnit=""
          metricDescription="Detailed monthly breakdown of Aerosol measurements"
          chartColor="var(--color-chart-2)"
        />
      </main>
    </div>
  );
}
