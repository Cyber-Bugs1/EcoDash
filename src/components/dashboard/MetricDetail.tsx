"use client"

import { useState, useEffect } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"
import {
  Area,
  AreaChart,
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
import { fetchMetricDetailAction, getAvailableYearsAction } from "@/lib/actions"
import type { MonthlyData, MetricType, MetricDetailResponse } from "@/lib/data-service"
import { MetricNavbar } from "./MetricNavbar"

interface MetricDetailProps {
  metricKey: MetricType
  metricName: string
  metricUnit: string
  metricDescription: string
  chartColor: string
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const currentState = searchParams.get('state') || "Delhi"
  const urlYear = searchParams.get('year')
  
  const [years, setYears] = useState<number[]>([])
  const [selectedYear, setSelectedYear] = useState<number | null>(urlYear ? parseInt(urlYear) : null)
  const [currentYearData, setCurrentYearData] = useState<MonthlyData[]>([])
  const [annualStats, setAnnualStats] = useState<{ mean: number; max: number; min: number } | null>(null)
  const [loading, setLoading] = useState(true)

  // Update URL when year changes
  const handleYearChange = (year: number) => {
    setSelectedYear(year)
    const params = new URLSearchParams(searchParams.toString())
    params.set('year', year.toString())
    router.push(`${pathname}?${params.toString()}`, { scroll: false })
  }

  // Load available years on initial mount
  useEffect(() => {
    async function loadYears() {
      const availableYears = await getAvailableYearsAction()
      setYears(availableYears)
      // If no year in URL, set the first available year
      if (availableYears.length > 0 && !selectedYear) {
        handleYearChange(availableYears[0])
      }
    }
    loadYears()
  }, [])

  // Fetch data when year or state changes
  useEffect(() => {
    if (selectedYear === null) return
    
    async function loadYearData() {
      setLoading(true)
      const response = await fetchMetricDetailAction(currentState, metricKey, selectedYear as number)
      
      if (response) {
        // Convert monthly_averages to MonthlyData format
        const monthlyData: MonthlyData[] = MONTHS.map((month, index) => ({
          month,
          value: parseFloat(response.monthly_averages[index]?.toFixed(2) || '0'),
        }));
        setCurrentYearData(monthlyData)
        
        // Set annual stats from API response
        setAnnualStats({
          mean: response.annual_mean,
          max: response.annual_max,
          min: response.annual_min,
        })
      } else {
        setCurrentYearData([])
        setAnnualStats(null)
      }
      
      setLoading(false)
    }
    loadYearData()
  }, [selectedYear, currentState, metricKey])

  // Use API stats or fallback to calculated values
  const avgValue = annualStats ? annualStats.mean.toFixed(1) : '0'
  const maxValue = annualStats ? annualStats.max.toFixed(1) : '0'
  const minValue = annualStats ? annualStats.min.toFixed(1) : '0'

  return (
    <div className="space-y-6">
      {/* Metric Navigation Bar */}
      <MetricNavbar />
      
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
          <Select value={selectedYear.toString()} onValueChange={(v) => handleYearChange(parseInt(v))}>
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
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={currentYearData.length > 0 ? currentYearData : MONTHS.map(m => ({ month: m, value: 0 }))}>
              <defs>
                <linearGradient id={`color${metricKey}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={chartColor} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={chartColor} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="month" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickCount={8} />
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
                isAnimationActive={true}
                animationDuration={600}
                animationEasing="ease-in-out"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>


    </div>
  )
}
