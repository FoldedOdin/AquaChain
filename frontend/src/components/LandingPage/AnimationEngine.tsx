import React, { useEffect, useRef, useState } from 'react';
import { AnimationEngine, AnimationSettings } from '../../utils/animationEngine';
import { PerformanceMonitor } from '../../utils/performanceMonitor';

interface AnimationEngineProps {
  settings: AnimationSettings;
  onRippleClick?: (x: number, y: number) => void;
  className?: string;
  children?: React.ReactNode;
}

/**
 * Animation Engine Component for AquaChain Landing Page
 * Manages bubble system, ripple effects, and parallax scrolling
 */
const AnimationEngineComponent: React.FC<AnimationEngineProps> = ({
  settings,
  onRippleClick,
  className = '',
  children
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<AnimationEngine | null>(null);
  const performanceMonitorRef = useRef<PerformanceMonitor | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize animation engine
  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize performance monitor
    performanceMonitorRef.current = new PerformanceMonitor();
    performanceMonitorRef.current.start();

    // Initialize animation engine
    engineRef.current = new AnimationEngine(
      containerRef.current,
      settings,
      performanceMonitorRef.current
    );

    engineRef.current.start();
    setIsInitialized(true);

    // Cleanup on unmount
    return () => {
      if (engineRef.current) {
        engineRef.current.stop();
      }
      if (performanceMonitorRef.current) {
        performanceMonitorRef.current.stop();
      }
    };
  }, [settings]);

  // Update settings when they change
  useEffect(() => {
    if (engineRef.current && isInitialized) {
      engineRef.current.updateSettings(settings);
    }
  }, [settings, isInitialized]);

  // Handle click events for ripple effects
  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (!engineRef.current || !settings.enableRipples) return;

    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    engineRef.current.createRipple(x, y);
    
    if (onRippleClick) {
      onRippleClick(x, y);
    }
  };

  // Parallax management functions (available for future use)
  // const addParallaxElement = React.useCallback((element: HTMLElement, speed: number = 0.5) => {
  //   if (engineRef.current && settings.enableParallax) {
  //     engineRef.current.parallaxController.addElement(element, speed);
  //   }
  // }, [settings.enableParallax]);

  // const removeParallaxElement = React.useCallback((element: HTMLElement) => {
  //   if (engineRef.current) {
  //     engineRef.current.parallaxController.removeElement(element);
  //   }
  // }, []);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${className}`}
      onClick={handleClick}
      style={{
        cursor: settings.enableRipples ? 'pointer' : 'default'
      }}
    >
      {/* Background layers for underwater effect */}
      {settings.enableBubbles && (
        <>
          <div 
            className="absolute inset-0 bg-gradient-to-b from-aqua-900/20 via-aqua-800/30 to-aqua-700/40"
            style={{
              background: `
                radial-gradient(ellipse at 20% 50%, rgba(6, 182, 212, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 20%, rgba(6, 182, 212, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at 40% 80%, rgba(6, 182, 212, 0.08) 0%, transparent 50%)
              `
            }}
          />
          
          {/* Caustics effect */}
          <div 
            className="absolute inset-0 opacity-30"
            style={{
              background: `
                radial-gradient(ellipse 800px 400px at 50% 0%, rgba(6, 182, 212, 0.1) 0%, transparent 70%)
              `,
              animation: 'caustics-flow 15s ease-in-out infinite'
            }}
          />
        </>
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
};

export default AnimationEngineComponent;