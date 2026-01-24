import { Header } from "@/components/dashboard/Header";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { OverviewCharts } from "@/components/dashboard/OverviewCharts";
import { Wind, Factory, AlertTriangle, Leaf, Wheat, Droplets, TrendingUp } from "lucide-react";

import { fetchPollutionDataAction, fetchStatesAction, checkBackendHealthAction, fetchStateSummaryAction } from "@/lib/actions";
import { getCategoryBgColor } from "@/lib/data-service";

// Disable caching - always fetch fresh data
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default async function Dashboard({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const resolvedParams = await searchParams;
  const currentState = (resolvedParams.state as string) || "Delhi";
  
  // Check backend health first
  const health = await checkBackendHealthAction();
  
  // Fetch state summary using new API format
  const [summary, allStates] = await Promise.all([
    fetchStateSummaryAction(currentState),
    fetchStatesAction(),
  ]);

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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
            {summary && (
              <span className="text-sm text-muted-foreground">
                Data for {summary.year}
              </span>
            )}
          </div>
          
          {summary ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {/* PM2.5 */}
              <MetricCard
                title="PM 2.5"
                value={`${summary.summary['PM2.5'].mean_value.toFixed(1)} µg/m³`}
                description={
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryBgColor(summary.summary['PM2.5'].category)}`}>
                      {summary.summary['PM2.5'].category}
                    </span>
                    {summary.summary['PM2.5'].spike_detected_next_10_months && (
                      <span className="text-xs text-red-500 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Spike Alert
                      </span>
                    )}
                  </div>
                }
                icon={<Factory className="h-4 w-4" />}
                href={`/metric/pm25?state=${currentState}`}
                percentage={summary.summary['PM2.5'].mean_percentage_of_max}
              />
              
              {/* AOD */}
              <MetricCard
                title="AOD"
                value={summary.summary.AOD.mean_value.toFixed(3)}
                description={
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryBgColor(summary.summary.AOD.category)}`}>
                      {summary.summary.AOD.category}
                    </span>
                    {summary.summary.AOD.spike_detected_next_10_months && (
                      <span className="text-xs text-red-500 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Spike Alert
                      </span>
                    )}
                  </div>
                }
                icon={<Wind className="h-4 w-4" />}
                href={`/metric/aod?state=${currentState}`}
                percentage={summary.summary.AOD.mean_percentage_of_max}
              />
              
              {/* Vegetation */}
              <MetricCard
                title="Vegetation"
                value={`${(summary.summary.Vegetation.mean_value * 100).toFixed(1)}%`}
                description={
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryBgColor(summary.summary.Vegetation.category)}`}>
                      {summary.summary.Vegetation.category}
                    </span>
                    {summary.summary.Vegetation.spike_detected_next_10_months && (
                      <span className="text-xs text-red-500 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Spike Alert
                      </span>
                    )}
                  </div>
                }
                icon={<Leaf className="h-4 w-4" />}
                href={`/metric/vegetation?state=${currentState}`}
                percentage={summary.summary.Vegetation.mean_percentage_of_max}
              />
              
              {/* Crop Yield */}
              <MetricCard
                title="Crop Yield"
                value={`${(summary.summary['Crop Yield'].mean_value * 100).toFixed(1)}%`}
                description={
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryBgColor(summary.summary['Crop Yield'].category)}`}>
                      {summary.summary['Crop Yield'].category}
                    </span>
                    {summary.summary['Crop Yield'].spike_detected_next_10_months && (
                      <span className="text-xs text-red-500 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Spike Alert
                      </span>
                    )}
                  </div>
                }
                icon={<Wheat className="h-4 w-4" />}
                href={`/metric/crop-yield?state=${currentState}`}
                percentage={summary.summary['Crop Yield'].mean_percentage_of_max}
              />
              
              {/* Water Level */}
              <MetricCard
                title="Water Level"
                value={`${(summary.summary['Water Level'].mean_value * 100).toFixed(1)}% stress`}
                description={
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCategoryBgColor(summary.summary['Water Level'].category)}`}>
                      {summary.summary['Water Level'].category}
                    </span>
                    {summary.summary['Water Level'].spike_detected_next_10_months && (
                      <span className="text-xs text-red-500 flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" /> Spike Alert
                      </span>
                    )}
                  </div>
                }
                icon={<Droplets className="h-4 w-4" />}
                href={`/metric/water-level?state=${currentState}`}
                percentage={summary.summary['Water Level'].mean_percentage_of_max}
              />
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No data available for {currentState}
            </div>
          )}
        </section>

        {summary?.trend && (
          <section>
             <OverviewCharts trend={summary.trend} />
          </section>
        )}
      </main>
    </div>
  );
}
