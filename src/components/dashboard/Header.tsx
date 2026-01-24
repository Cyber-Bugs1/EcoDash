"use client"

import Link from "next/link"
import Image from "next/image"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import { StateSelector } from "./StateSelector"

interface HeaderProps {
  states?: string[]
  currentState?: string
}

export function Header({ states = [], currentState = "Delhi" }: HeaderProps) {
  const { setTheme } = useTheme()

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link 
            href="/" 
            className="flex items-center gap-2 group cursor-pointer transition-all duration-300 hover:scale-105"
          >
            <Image 
              src="/logo.png?v=2" 
              alt="EcoDash Logo" 
              width={32} 
              height={32} 
              className="transition-all duration-300 group-hover:drop-shadow-[0_0_8px_hsl(var(--primary))]" 
            />
            <h1 className="text-xl font-bold tracking-tight text-foreground transition-all duration-300 group-hover:text-primary">
              Eco<span className="text-primary transition-all duration-300 group-hover:drop-shadow-[0_0_12px_hsl(var(--primary))]">Dash</span>
            </h1>
          </Link>
          
          <StateSelector states={states} currentState={currentState} />
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" className="h-9 w-9 border-primary/20 hover:bg-primary/10 hover:text-primary">
              <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme("light")}>
              Light
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("dark")}>
              Dark
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme("system")}>
              System
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
