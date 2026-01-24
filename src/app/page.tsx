"use client"
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-black text-white">
      {/* Animated Gradient Background */}
      <div className="absolute inset-0 z-0">
         <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-black to-green-900 animate-gradient-slow opacity-80" />
         <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(16,185,129,0.1),transparent_50%)] animate-pulse-slow" />
      </div>
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 text-center space-y-8">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60 animate-fade-in-up">
          The Pulse of Our Planet.
        </h1>
        
        <p className="text-lg md:text-xl text-white/70 max-w-2xl mx-auto font-light leading-relaxed animate-fade-in-up delay-100">
          Monitoring 5 vital environmental metrics across India. 
          <br className="hidden md:block" />
          Real-time data. Actionable insights. A sustainable future.
        </p>

        <div className="animate-fade-in-up delay-200">
          <Link href="/dashboard">
            <Button size="lg" className="rounded-full text-lg px-8 py-6 bg-white text-black hover:bg-white/90 hover:scale-105 transition-all duration-300 group">
              Explore Data
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
          </Link>
        </div>
      </div>

      {/* Footer / Abstract Elements */}
      <div className="absolute bottom-0 w-full p-6 text-center text-white/20 text-sm">
        <p>© 2024 EcoDash Initiative</p>
      </div>
    </div>
  );
}
