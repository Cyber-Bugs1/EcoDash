"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  title: string
  value: string | number
  description: string
  trend?: "up" | "down" | "neutral"
  icon?: React.ReactNode
  className?: string
  href?: string
}

export function MetricCard({ title, value, description, trend, icon, className, href }: MetricCardProps) {
  const CardWrapper = href ? Link : 'div';
  const cardProps = href ? { href } : {};

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
        <CardContent>
          <div className="text-2xl font-bold text-foreground">{value}</div>
          <p className="text-xs text-muted-foreground mt-1">
            {description}
          </p>
        </CardContent>
      </Card>
    </CardWrapper>
  )
}
