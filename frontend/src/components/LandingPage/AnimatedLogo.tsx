import React, { useEffect, useState } from 'react';

/**
 * Animated AquaChain Logo Component
 * Features floating droplet icon with pulsing and floating animations
 * Responsive scaling and accessibility support
 */
const AnimatedLogo: React.FC = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return (
    <div className="flex flex-col items-center">
      {/* Animated Droplet Icon */}
      <div 
        className={`relative mb-4 ${
          prefersReducedMotion 
            ? '' 
            : 'animate-gentle-wave'
        }`}
        style={{
          animationDelay: '0.5s',
          animationDuration: '4s'
        }}
      >
        {/* Outer Glow Ring */}
        <div 
          className={`absolute inset-0 rounded-full ${
            prefersReducedMotion 
              ? 'bg-aqua-500/20' 
              : 'bg-aqua-500/20 animate-ping'
          }`}
          style={{
            width: '120px',
            height: '120px',
            animationDuration: '3s',
            animationDelay: '1s'
          }}
        />
        
        {/* Middle Glow Ring */}
        <div 
          className={`absolute inset-2 rounded-full ${
            prefersReducedMotion 
              ? 'bg-aqua-400/30' 
              : 'bg-aqua-400/30 animate-pulse'
          }`}
          style={{
            animationDuration: '2s',
            animationDelay: '0.5s'
          }}
        />
        
        {/* Main Droplet Icon */}
        <div className="relative w-24 h-24 lg:w-28 lg:h-28">
          <svg
            viewBox="0 0 100 100"
            className="w-full h-full drop-shadow-lg"
            role="img"
            aria-label="AquaChain water droplet logo"
          >
            {/* Gradient Definitions */}
            <defs>
              <linearGradient id="dropletGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4" />
                <stop offset="50%" stopColor="#0891b2" />
                <stop offset="100%" stopColor="#0e7490" />
              </linearGradient>
              <radialGradient id="highlightGradient" cx="30%" cy="30%">
                <stop offset="0%" stopColor="#ffffff" stopOpacity="0.8" />
                <stop offset="50%" stopColor="#ffffff" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
              </radialGradient>
              <filter id="dropShadow">
                <feDropShadow dx="0" dy="4" stdDeviation="3" floodColor="#000000" floodOpacity="0.3"/>
              </filter>
            </defs>
            
            {/* Main Droplet Shape */}
            <path
              d="M50 10 C30 30, 20 50, 20 65 C20 80, 32.5 90, 50 90 C67.5 90, 80 80, 80 65 C80 50, 70 30, 50 10 Z"
              fill="url(#dropletGradient)"
              filter="url(#dropShadow)"
              className={prefersReducedMotion ? '' : 'animate-pulse'}
              style={{
                animationDuration: '3s',
                animationDelay: '1.5s'
              }}
            />
            
            {/* Highlight */}
            <ellipse
              cx="42"
              cy="35"
              rx="8"
              ry="12"
              fill="url(#highlightGradient)"
              className={prefersReducedMotion ? '' : 'animate-pulse'}
              style={{
                animationDuration: '2.5s',
                animationDelay: '2s'
              }}
            />
            
            {/* Small Bubbles */}
            {!prefersReducedMotion && (
              <>
                <circle
                  cx="35"
                  cy="60"
                  r="2"
                  fill="#ffffff"
                  opacity="0.6"
                  className="animate-bounce"
                  style={{
                    animationDuration: '2s',
                    animationDelay: '3s'
                  }}
                />
                <circle
                  cx="65"
                  cy="55"
                  r="1.5"
                  fill="#ffffff"
                  opacity="0.4"
                  className="animate-bounce"
                  style={{
                    animationDuration: '2.5s',
                    animationDelay: '3.5s'
                  }}
                />
                <circle
                  cx="50"
                  cy="70"
                  r="1"
                  fill="#ffffff"
                  opacity="0.3"
                  className="animate-bounce"
                  style={{
                    animationDuration: '3s',
                    animationDelay: '4s'
                  }}
                />
              </>
            )}
          </svg>
        </div>
      </div>
      
      {/* AquaChain Text Logo */}
      <div className="text-center">
        <h2 className="text-3xl lg:text-4xl xl:text-5xl font-display font-bold text-white mb-2">
          <span className="text-aqua-400">Aqua</span>
          <span className="text-white">Chain</span>
        </h2>
        <div className="text-sm lg:text-base text-aqua-300 font-medium tracking-wider uppercase">
          Water Quality Monitoring
        </div>
      </div>
      
      {/* Floating Particles (only if motion is allowed) */}
      {!prefersReducedMotion && (
        <div className="absolute inset-0 pointer-events-none">
          {/* Floating Particle 1 */}
          <div 
            className="absolute w-1 h-1 bg-aqua-400 rounded-full opacity-60 animate-bounce"
            style={{
              top: '20%',
              left: '15%',
              animationDuration: '3s',
              animationDelay: '2s'
            }}
          />
          
          {/* Floating Particle 2 */}
          <div 
            className="absolute w-1.5 h-1.5 bg-aqua-300 rounded-full opacity-40 animate-bounce"
            style={{
              top: '30%',
              right: '20%',
              animationDuration: '4s',
              animationDelay: '1s'
            }}
          />
          
          {/* Floating Particle 3 */}
          <div 
            className="absolute w-0.5 h-0.5 bg-white rounded-full opacity-80 animate-bounce"
            style={{
              bottom: '25%',
              left: '25%',
              animationDuration: '2.5s',
              animationDelay: '3s'
            }}
          />
          
          {/* Floating Particle 4 */}
          <div 
            className="absolute w-1 h-1 bg-emerald-400 rounded-full opacity-50 animate-bounce"
            style={{
              bottom: '35%',
              right: '15%',
              animationDuration: '3.5s',
              animationDelay: '0.5s'
            }}
          />
        </div>
      )}
    </div>
  );
};

export default AnimatedLogo;