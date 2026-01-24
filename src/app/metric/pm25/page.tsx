import { fetchStatesAction } from "@/lib/actions";
import { Header } from "@/components/dashboard/Header";
import { MetricDetail } from "@/components/dashboard/MetricDetail";

export default async function PM25Page({
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
          metricKey="pm25"
          metricName="PM 2.5"
          metricUnit="µg/m³"
          metricDescription="Detailed monthly breakdown of Particulate Matter < 2.5µm"
          chartColor="#94a3b8"
        />
      </main>
    </div>
  );
}
