"use client"

import Link from "next/link"
import { usePathname, useSearchParams } from "next/navigation"
import { cn } from "@/lib/utils"
import { Factory, Wind, Droplets, Wheat, Leaf } from "lucide-react"

const METRICS = [
  { key: "pm25", name: "PM 2.5", href: "/metric/pm25", icon: Factory, color: "#94a3b8" },
  { key: "aod", name: "AOD", href: "/metric/aod", icon: Wind, color: "#14b8a6" },
  { key: "water-level", name: "Water", href: "/metric/water-level", icon: Droplets, color: "#0ea5e9" },
  { key: "crop-yield", name: "Crop Yield", href: "/metric/crop-yield", icon: Wheat, color: "#eab308" },
  { key: "vegetation", name: "Vegetation", href: "/metric/vegetation", icon: Leaf, color: "#22c55e" },
]

export function MetricNavbar() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const stateParam = searchParams.get('state')
  const yearParam = searchParams.get('year')
  
  // Build URL with state and year parameters preserved
  const getHref = (baseHref: string) => {
    const params = new URLSearchParams()
    if (stateParam) params.set('state', stateParam)
    if (yearParam) params.set('year', yearParam)
    const queryString = params.toString()
    return queryString ? `${baseHref}?${queryString}` : baseHref
  }

  return (
    <nav className="mb-6 overflow-hidden">
      <div className="flex gap-2 min-w-max py-1 px-1">
        {METRICS.map((metric) => {
          const isActive = pathname.includes(metric.key)
          const Icon = metric.icon
          
          return (
            <Link
              key={metric.key}
              href={getHref(metric.href)}
              className={cn(
                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300",
                "border hover:scale-105",
                isActive 
                  ? "border-transparent text-white shadow-lg" 
                  : "border-border/50 bg-background hover:bg-muted text-muted-foreground hover:text-foreground"
              )}
              style={isActive ? { backgroundColor: metric.color, boxShadow: `0 4px 14px ${metric.color}50` } : {}}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{metric.name}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
