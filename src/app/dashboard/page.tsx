import { Header } from "@/components/dashboard/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { OverviewCharts } from "@/components/dashboard/OverviewCharts";
import { Wind, Factory, AlertTriangle, Leaf, Wheat, Droplets } from "lucide-react";

import { fetchPollutionDataAction, fetchStatesAction, checkBackendHealthAction } from "@/lib/actions";

export default async function Dashboard({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const resolvedParams = await searchParams;
  const currentState = (resolvedParams.state as string) || "Delhi";
  
  // Check backend health first
  const health = await checkBackendHealthAction();
  
  const [data, allStates] = await Promise.all([
    fetchPollutionDataAction(currentState),
    fetchStatesAction()
  ]);
  
  const latestData = data[data.length - 1];

  return (
    <div className="min-h-screen bg-background">
      <Header states={allStates} currentState={currentState} />
      <main className="container mx-auto p-4 space-y-8">
        {/* Backend Status Alert */}
        {!health.online && (
          <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-500">Backend Server Offline</h3>
              <p className="text-sm text-muted-foreground">
                {health.message}. Please ensure the API server is running.
              </p>
            </div>
          </div>
        )}

        <section>
          <h2 className="text-3xl font-bold tracking-tight mb-4">Dashboard Overview</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {/* Pollution Metrics */}
            <MetricCard
              title="PM 2.5"
              value={latestData ? `${latestData.pm25} µg/m³` : "N/A"}
              description="Particulate Matter < 2.5µm"
              icon={<Factory className="h-4 w-4" />}
              href={`/metric/pm25?state=${currentState}`}
            />
            <MetricCard
              title="AOD"
              value={latestData ? latestData.aod : "N/A"}
              description="Aerosol Optical Depth"
              icon={<Wind className="h-4 w-4" />}
              href={`/metric/aod?state=${currentState}`}
            />
            
            {/* New Metrics */}
            <MetricCard
              title="Vegetation"
              value="View Data"
              description="Vegetation Index & Health"
              icon={<Leaf className="h-4 w-4" />}
              href={`/metric/vegetation?state=${currentState}`}
            />
            <MetricCard
              title="Crop Yield"
              value="View Data"
              description="Agricultural Predictions"
              icon={<Wheat className="h-4 w-4" />}
              href={`/metric/crop-yield?state=${currentState}`}
            />
            <MetricCard
              title="Water Levels"
              value="View Data"
              description="Water Level Monitoring"
              icon={<Droplets className="h-4 w-4" />}
              href={`/metric/water-level?state=${currentState}`}
            />
          </div>
        </section>

        {latestData && (
          <section>
             <OverviewCharts data={data} />
          </section>
        )}
      </main>
    </div>
  );
}
