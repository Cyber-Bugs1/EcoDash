"use client"

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  Area,
  AreaChart
} from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendData } from "@/lib/data-service"

interface OverviewChartsProps {
  trend: TrendData;
}

interface ChartDataPoint {
  year: number;
  pm25: number;
  aod: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background/95 border border-border p-3 rounded-lg shadow-lg text-sm transition-all animate-in fade-in-0 zoom-in-95 backdrop-blur-sm">
        <p className="font-bold text-foreground mb-1">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="flex items-center gap-2" style={{ color: entry.color }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="font-medium">{entry.name}:</span>
            <span>{typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function OverviewCharts({ trend }: OverviewChartsProps) {
  // Convert trend data to chart format
  // trend.years, trend.pm25, trend.aod are parallel arrays
  const chartData: ChartDataPoint[] = trend.years.map((year, index) => ({
    year,
    pm25: trend.pm25[index],
    aod: trend.aod[index],
  }));

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        {/* PM 2.5 Chart */}
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle>PM 2.5 Trend</CardTitle>
            <CardDescription>
              Historical & Predicted PM2.5 Levels (µg/m³)
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPm25" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="year" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickCount={8} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="pm25" 
                  stroke="var(--color-primary)" 
                  fillOpacity={1} 
                  fill="url(#colorPm25)" 
                  name="PM 2.5" 
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* AOD Chart */}
        <Card className="border-primary/10">
          <CardHeader>
            <CardTitle>Aerosol Optical Depth (AOD) Trends</CardTitle>
            <CardDescription>
              Historical & Predicted AOD Levels
            </CardDescription>
          </CardHeader>
          <CardContent className="pl-2">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={chartData}>
                <XAxis dataKey="year" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} domain={['auto', 'auto']} tickCount={8} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="aod" 
                  stroke="var(--color-chart-2)" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: "var(--color-background)", strokeWidth: 2 }}
                  activeDot={{ r: 6, strokeWidth: 0 }}
                  name="AOD"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
