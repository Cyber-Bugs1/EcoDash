"use client"
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { Button } from '@/components/ui/button';
import { ArrowRight, Github, Leaf, AlertTriangle, Lightbulb } from 'lucide-react';
import ScrollFloat from '@/components/ui/ScrollFloat';
import Magnet from '@/components/ui/Magnet';

// Dynamic import to avoid SSR issues with WebGL
const Orb = dynamic(() => import('@/components/ui/Orb'), { ssr: false });

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-white">
      {/* Animated Orb Background */}
      <div className="absolute inset-0 z-0 flex items-center justify-center">
        <div className="w-[800px] h-[800px] md:w-[1000px] md:h-[1000px] opacity-60">
          <Orb
            hue={120}
            hoverIntensity={0.3}
            rotateOnHover={true}
            forceHoverState={false}
            backgroundColor="#000000"
          />
        </div>
      </div>
      
      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 py-16">
        {/* Hero Section */}
        <section className="text-center space-y-8 min-h-[80vh] flex flex-col items-center justify-center">
          <ScrollFloat direction="up" offset={40}>
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
              The Pulse of Our Planet.
            </h1>
          </ScrollFloat>
          
          <ScrollFloat direction="up" offset={30}>
            <p className="text-lg md:text-xl text-white/70 max-w-2xl mx-auto font-light leading-relaxed">
              <span className="text-emerald-400 font-medium">&quot;What we do to the environment, we do to ourselves.&quot;</span>
              <br className="hidden md:block" />
              Monitoring 5 vital environmental metrics across India for a sustainable future.
            </p>
          </ScrollFloat>

          <ScrollFloat direction="up" offset={20}>
            <Link href="/dashboard">
              <Button size="lg" className="rounded-full text-lg px-8 py-6 bg-white text-black hover:bg-white/90 hover:scale-105 transition-all duration-300 group">
                Explore Data
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </ScrollFloat>
        </section>

        {/* Problem & Solution Section */}
        <section className="grid md:grid-cols-2 gap-8 py-20 max-w-5xl mx-auto">
          {/* Problem Statement */}
          <ScrollFloat direction="up" offset={50}>
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-4 h-full">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-8 w-8 text-red-400" />
                <h2 className="text-2xl font-bold text-white">The Problem</h2>
              </div>
              <p className="text-white/70 leading-relaxed">
                India faces severe environmental challenges - rising air pollution, depleting water resources, 
                declining agricultural yields, and degrading ecosystems. Without unified, real-time environmental 
                monitoring, policy-makers and citizens remain in the dark about the true state of our environment 
                until it&apos;s too late.
              </p>
            </div>
          </ScrollFloat>

          {/* Solution */}
          <ScrollFloat direction="up" offset={50}>
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 space-y-4 h-full">
              <div className="flex items-center gap-3">
                <Lightbulb className="h-8 w-8 text-yellow-400" />
                <h2 className="text-2xl font-bold text-white">Our Solution</h2>
              </div>
              <p className="text-white/70 leading-relaxed">
                EcoDash aggregates satellite data and predictive analytics to track PM2.5, Aerosol Optical Depth, 
                Water Levels, Crop Yield, and Vegetation indices across all Indian states. We transform complex 
                environmental data into actionable insights, enabling proactive environmental stewardship.
              </p>
            </div>
          </ScrollFloat>
        </section>

        {/* Mission Statement */}
        <section className="text-center py-16 max-w-3xl mx-auto">
          <ScrollFloat direction="up" offset={40}>
            <Leaf className="h-12 w-12 text-emerald-400 mx-auto mb-6" />
            <h2 className="text-3xl font-bold text-white mb-4">Our Mission</h2>
            <p className="text-xl text-white/70 leading-relaxed">
              To democratize environmental awareness by making satellite-powered environmental data accessible to everyone - 
              from researchers to farmers, policy-makers to citizens - fostering collective action for a healthier planet.
            </p>
          </ScrollFloat>
        </section>

        {/* Developers Section */}
        <section className="py-16 max-w-2xl mx-auto">
          <ScrollFloat direction="up" offset={30}>
            <h2 className="text-2xl font-bold text-white text-center mb-8">Built With 💚 By</h2>
          </ScrollFloat>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Developer 1 */}
            <ScrollFloat direction="up" offset={40}>
              <Magnet padding={80} magnetStrength={3}>
                <a 
                  href="https://github.com/rexcode0" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-5 hover:bg-white/10 hover:border-white/20 transition-all duration-300 group"
                >
                  <Github className="h-10 w-10 text-white/70 group-hover:text-white transition-colors" />
                  <div>
                    <h3 className="text-lg font-semibold text-white">Ashish Sharma</h3>
                    <p className="text-white/50 text-sm">@rexcode0</p>
                  </div>
                </a>
              </Magnet>
            </ScrollFloat>

            {/* Developer 2 */}
            <ScrollFloat direction="up" offset={40}>
              <Magnet padding={80} magnetStrength={3}>
                <a 
                  href="https://github.com/RatandeepOO" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-5 hover:bg-white/10 hover:border-white/20 transition-all duration-300 group"
                >
                  <Github className="h-10 w-10 text-white/70 group-hover:text-white transition-colors" />
                  <div>
                    <h3 className="text-lg font-semibold text-white">Ratandeep Arora</h3>
                    <p className="text-white/50 text-sm">@RatandeepOO</p>
                  </div>
                </a>
              </Magnet>
            </ScrollFloat>
          </div>
        </section>
      </div>

      {/* Footer */}
      <div className="relative z-10 w-full p-6 text-center text-white/20 text-sm border-t border-white/5">
        <p>From team coding turtle</p>
      </div>
    </div>
  );
}

