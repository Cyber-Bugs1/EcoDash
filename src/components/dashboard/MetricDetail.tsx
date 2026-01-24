"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { fetchMonthlyDataForYearAction, getAvailableYearsAction } from "@/lib/actions"
import type { MonthlyData, MetricType } from "@/lib/data-service"

interface MetricDetailProps {
  metricKey: MetricType
  metricName: string
  metricUnit: string
  metricDescription: string
  chartColor: string
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background/95 border border-border p-3 rounded-lg shadow-lg text-sm backdrop-blur-sm">
        <p className="font-bold text-foreground mb-1">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} style={{ color: entry.color }}>
            <span className="font-medium">{entry.name}:</span> {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export function MetricDetail({ metricKey, metricName, metricUnit, metricDescription, chartColor }: MetricDetailProps) {
  const searchParams = useSearchParams()
  const currentState = searchParams.get('state') || "Delhi"
  
  const [years, setYears] = useState<number[]>([])
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [currentYearData, setCurrentYearData] = useState<MonthlyData[]>([])
  const [yearAverages, setYearAverages] = useState<{year: number, average: string}[]>([])
  const [loading, setLoading] = useState(true)

  // Load available years on initial mount
  useEffect(() => {
    async function loadYears() {
      const availableYears = await getAvailableYearsAction()
      setYears(availableYears)
      if (availableYears.length > 0 && !selectedYear) {
        setSelectedYear(availableYears[0])
      }
    }
    loadYears()
  }, [])

  // Fetch data when year or state changes
  useEffect(() => {
    if (selectedYear === null) return
    
    async function loadYearData() {
      setLoading(true)
      const data = await fetchMonthlyDataForYearAction(currentState, metricKey, selectedYear as number)
      setCurrentYearData(data)
      setLoading(false)
    }
    loadYearData()
  }, [selectedYear, currentState, metricKey])

  // Load averages for year comparison chart (only once per state/metric)
  useEffect(() => {
    async function loadAverages() {
      const averages: {year: number, average: string}[] = []
      for (const year of years) {
        const data = await fetchMonthlyDataForYearAction(currentState, metricKey, year)
        if (data.length > 0) {
          const avg = data.reduce((sum, d) => sum + d.value, 0) / data.length
          averages.push({ year, average: avg.toFixed(1) })
        }
      }
      setYearAverages(averages)
    }
    if (years.length > 0) {
      loadAverages()
    }
  }, [years, currentState, metricKey])

  const currentData = currentYearData
  
  // Calculate stats
  const avgValue = currentYearData.length > 0 
    ? (currentYearData.reduce((sum, d) => sum + d.value, 0) / currentYearData.length).toFixed(1)
    : 0
  const maxValue = currentYearData.length > 0 
    ? Math.max(...currentYearData.map(d => d.value)).toFixed(1)
    : 0
  const minValue = currentYearData.length > 0 
    ? Math.min(...currentYearData.map(d => d.value)).toFixed(1)
    : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard?state=${currentState}`}>
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">{metricName}</h2>
            <p className="text-muted-foreground">{metricDescription}</p>
          </div>
        </div>
        
        {selectedYear && (
          <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v))}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select Year" />
            </SelectTrigger>
            <SelectContent>
              {years.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-primary/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Average</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgValue} {metricUnit}</div>
          </CardContent>
        </Card>
        <Card className="border-primary/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Maximum</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{maxValue} {metricUnit}</div>
          </CardContent>
        </Card>
        <Card className="border-primary/10">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Minimum</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{minValue} {metricUnit}</div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Chart */}
      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle>Monthly {metricName} for {selectedYear || "..."}</CardTitle>
          <CardDescription>
            Detailed monthly breakdown throughout the year
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading || !selectedYear ? (
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              Loading...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={currentYearData}>
                <defs>
                  <linearGradient id={`color${metricKey}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColor} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={chartColor} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke={chartColor} 
                  fillOpacity={1} 
                  fill={`url(#color${metricKey})`} 
                  name={metricName}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* All Years Comparison Bar Chart */}
      <Card className="border-primary/10">
        <CardHeader>
          <CardTitle>Year-over-Year Comparison</CardTitle>
          <CardDescription>
            Average {metricName.toLowerCase()} across all years
          </CardDescription>
        </CardHeader>
        <CardContent>
          {yearAverages.length === 0 ? (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              Loading year comparison...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={yearAverages}>
                <XAxis dataKey="year" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                <Tooltip content={<CustomTooltip />} cursor={false} />
                <Bar 
                  dataKey="average" 
                  fill={chartColor} 
                  radius={[4, 4, 0, 0]} 
                  name={`Avg ${metricName}`}
                  onClick={(data: any) => setSelectedYear(data.year)}
                  style={{ cursor: 'pointer' }}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
