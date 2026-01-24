"use client"

import { useRouter, usePathname, useSearchParams } from "next/navigation"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { MapPin } from "lucide-react"

interface StateSelectorProps {
  states: string[]
  currentState: string
}

export function StateSelector({ states, currentState }: StateSelectorProps) {
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()

  const handleStateChange = (state: string) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('state', state)
    router.push(`/dashboard?${params.toString()}`)
  }

  return (
    <div className="flex items-center gap-2">
      <MapPin className="h-4 w-4 text-primary" />
      <Select value={currentState} onValueChange={handleStateChange}>
        <SelectTrigger className="w-[180px] border-primary/20 bg-background focus:ring-primary/20">
          <SelectValue placeholder="Select State" />
        </SelectTrigger>
        <SelectContent>
          {states.map((state) => (
            <SelectItem key={state} value={state}>
              {state}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
