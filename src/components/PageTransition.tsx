"use client";

import { useEffect, useState, useRef, useTransition } from "react";
import { usePathname, useSearchParams } from "next/navigation";

export function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showParticles, setShowParticles] = useState(false);
  const previousPathRef = useRef(pathname + searchParams.toString());

  useEffect(() => {
    const currentPath = pathname + searchParams.toString();
    
    // Only trigger transition if path actually changed
    if (previousPathRef.current !== currentPath) {
      previousPathRef.current = currentPath;
      
      // Start the transition animation
      setIsTransitioning(true);
      setShowParticles(true);
      
      // End transition after animation completes
      const timer = setTimeout(() => {
        setIsTransitioning(false);
      }, 500);

      // Hide particles after they've animated
      const particleTimer = setTimeout(() => {
        setShowParticles(false);
      }, 800);

      return () => {
        clearTimeout(timer);
        clearTimeout(particleTimer);
      };
    }
  }, [pathname, searchParams]);

  return (
    <div className="relative min-h-screen">
      {/* Smoke/Water Transition Overlay - Always in DOM but visibility controlled */}
      <div
        className={`fixed inset-0 z-[100] pointer-events-none`}
        style={{ opacity: showParticles ? 1 : 0 }}
      >
        {/* Smoke particles */}
        {showParticles && (
          <div className="absolute inset-0 overflow-hidden">
            <div className="smoke-particle smoke-1" />
            <div className="smoke-particle smoke-2" />
            <div className="smoke-particle smoke-3" />
            <div className="smoke-particle smoke-4" />
            <div className="smoke-particle smoke-5" />
            <div className="water-ripple" />
            <div className="water-ripple water-ripple-2" />
            <div className="water-ripple water-ripple-3" />
          </div>
        )}
      </div>

      {/* Main content with fade animation */}
      <div
        className={`transition-all duration-300 ease-out ${
          isTransitioning 
            ? "opacity-0 scale-[0.98]" 
            : "opacity-100 scale-100"
        }`}
      >
        {children}
      </div>
    </div>
  );
}
