"use client"

import { useRef, ReactNode, useEffect, useState } from 'react';
import { motion, useInView } from 'framer-motion';

interface ScrollFloatProps {
  children: ReactNode;
  direction?: 'up' | 'down';
  offset?: number;
  className?: string;
  delay?: number;
}

export default function ScrollFloat({
  children,
  direction = 'up',
  offset = 50,
  className = '',
  delay = 0,
}: ScrollFloatProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { 
    once: true, 
    margin: "-50px",
    amount: 0.1 
  });
  
  const [hasLoaded, setHasLoaded] = useState(false);
  
  useEffect(() => {
    // Small delay to allow initial render
    const timer = setTimeout(() => setHasLoaded(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const initialY = direction === 'up' ? offset : -offset;
  
  // Show immediately if in view, otherwise animate
  const shouldAnimate = hasLoaded && isInView;

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: initialY, filter: 'blur(8px)' }}
      animate={shouldAnimate ? { 
        opacity: 1, 
        y: 0, 
        filter: 'blur(0px)' 
      } : { 
        opacity: 0, 
        y: initialY, 
        filter: 'blur(8px)' 
      }}
      transition={{ 
        duration: 0.8, 
        delay,
        ease: [0.21, 0.47, 0.32, 0.98] 
      }}
    >
      {children}
    </motion.div>
  );
}

// Simple fade in on scroll variant
export function ScrollFadeIn({
  children,
  className = '',
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{ 
        duration: 0.8, 
        delay,
        ease: [0.21, 0.47, 0.32, 0.98] 
      }}
    >
      {children}
    </motion.div>
  );
}
