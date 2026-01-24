"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string | number
  description: React.ReactNode
  trend?: "up" | "down" | "neutral"
  icon?: React.ReactNode
  className?: string
  href?: string
  percentage?: number
}

export function MetricCard({ title, value, description, trend, icon, className, href, percentage }: MetricCardProps) {
  const CardWrapper = href ? Link : 'div';
  const cardProps = href ? { href } : {};

  // Determine percentage bar color based on value
  const getPercentageColor = (pct: number) => {
    if (pct <= 33) return 'bg-green-500';
    if (pct <= 66) return 'bg-yellow-500';
    if (pct <= 100) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <CardWrapper {...cardProps as any} className={cn("block", href && "cursor-pointer")}>
      <Card className={cn(
        "overflow-hidden border-primary/10 shadow-sm transition-all hover:shadow-md hover:border-primary/30",
        href && "hover:scale-[1.02] active:scale-[0.98]",
        className
      )}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          {icon && <div className="text-primary opacity-80">{icon}</div>}
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="text-2xl font-bold text-foreground">{value}</div>
          <div className="text-xs text-muted-foreground">
            {description}
          </div>
          {percentage !== undefined && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>of max threshold</span>
                <span>{percentage.toFixed(1)}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                <div 
                  className={cn("h-full rounded-full transition-all", getPercentageColor(percentage))}
                  style={{ width: `${Math.min(percentage, 100)}%` }}
                />
              </div>
            </div>
          )}
          {href && (
            <div className="text-xs text-primary/70 mt-3 flex items-center gap-1">
              <span>Click to explore details</span>
              <span className="text-primary">→</span>
            </div>
          )}
        </CardContent>
      </Card>
    </CardWrapper>
  )
}
