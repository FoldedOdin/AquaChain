import React, { useEffect, useState, useRef } from 'react';

interface Bubble {
  id: number;
  x: number;
  y: number;
  size: number;
  speed: number;
  drift: number;
  opacity: number;
}

/**
 * Underwater Background Animation Component
 * Features animated background layers, floating bubbles, and water caustics
 * Optimized for 60fps performance with reduced motion support
 */
const UnderwaterBackground: React.FC = () => {
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const animationFrameRef = useRef<number | null>(null);
  const bubblesRef = useRef<Bubble[]>([]);
  const lastTimeRef = useRef<number>(0);

  // Check for reduced motion preference
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Initialize bubbles
  useEffect(() => {
    if (prefersReducedMotion) return;

    const initializeBubbles = () => {
      const newBubbles: Bubble[] = [];
      const maxBubbles = window.innerWidth < 768 ? 8 : 15; // Fewer bubbles on mobile

      for (let i = 0; i < maxBubbles; i++) {
        newBubbles.push(createBubble(i));
      }

      setBubbles(newBubbles);
      bubblesRef.current = newBubbles;
    };

    initializeBubbles();

    // Reinitialize on window resize
    const handleResize = () => {
      initializeBubbles();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [prefersReducedMotion]);

  // Create a new bubble
  const createBubble = (id: number): Bubble => {
    return {
      id,
      x: Math.random() * window.innerWidth,
      y: window.innerHeight + Math.random() * 200,
      size: Math.random() * 20 + 5, // 5-25px
      speed: Math.random() * 2 + 0.5, // 0.5-2.5px per frame
      drift: Math.random() * 0.5 + 0.1, // Horizontal drift
      opacity: Math.random() * 0.6 + 0.2, // 0.2-0.8
    };
  };

  // Recycle bubble when it goes off screen
  const recycleBubble = (bubble: Bubble): Bubble => {
    return {
      ...bubble,
      x: Math.random() * window.innerWidth,
      y: window.innerHeight + Math.random() * 100,
      size: Math.random() * 20 + 5,
      speed: Math.random() * 2 + 0.5,
      drift: Math.random() * 0.5 + 0.1,
      opacity: Math.random() * 0.6 + 0.2,
    };
  };

  // Animation loop
  useEffect(() => {
    if (prefersReducedMotion) return;

    const animate = (currentTime: number) => {
      // Throttle to ~60fps
      if (currentTime - lastTimeRef.current < 16) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      lastTimeRef.current = currentTime;

      // Update bubbles
      const updatedBubbles = bubblesRef.current.map(bubble => {
        const newY = bubble.y - bubble.speed;
        const newX = bubble.x + Math.sin(newY * 0.01) * bubble.drift;

        // Recycle bubble if it's off screen
        if (newY < -50) {
          return recycleBubble(bubble);
        }

        return {
          ...bubble,
          x: newX,
          y: newY,
        };
      });

      bubblesRef.current = updatedBubbles;
      setBubbles([...updatedBubbles]);

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [prefersReducedMotion]);

  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Deep Water Background Gradient */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900"
        style={{
          background: 'linear-gradient(180deg, #001f2e 0%, #003d5b 30%, #01579b 70%, #0e4d64 100%)'
        }}
      />

      {/* Animated Water Layers */}
      <div className="absolute inset-0">
        {/* Layer 1 - Deep water movement */}
        <div
          className={`absolute inset-0 opacity-30 ${prefersReducedMotion ? '' : 'animate-gentle-wave'
            }`}
          style={{
            background: 'radial-gradient(ellipse 100% 50% at 50% 100%, rgba(6, 182, 212, 0.1) 0%, transparent 70%)',
            animationDuration: '20s',
            animationDelay: '0s'
          }}
        />

        {/* Layer 2 - Mid water movement */}
        <div
          className={`absolute inset-0 opacity-20 ${prefersReducedMotion ? '' : 'animate-gentle-wave'
            }`}
          style={{
            background: 'radial-gradient(ellipse 80% 60% at 30% 80%, rgba(8, 131, 149, 0.15) 0%, transparent 60%)',
            animationDuration: '25s',
            animationDelay: '5s'
          }}
        />

        {/* Layer 3 - Surface water movement */}
        <div
          className={`absolute inset-0 opacity-10 ${prefersReducedMotion ? '' : 'animate-gentle-wave'
            }`}
          style={{
            background: 'radial-gradient(ellipse 120% 40% at 70% 90%, rgba(29, 233, 182, 0.1) 0%, transparent 80%)',
            animationDuration: '30s',
            animationDelay: '10s'
          }}
        />
      </div>

      {/* Water Caustics Effect */}
      {!prefersReducedMotion && (
        <div className="absolute inset-0 opacity-20">
          {/* Caustic Pattern 1 */}
          <div
            className="absolute inset-0 animate-caustics"
            style={{
              background: `
                radial-gradient(ellipse 200px 100px at 20% 30%, rgba(6, 182, 212, 0.3) 0%, transparent 50%),
                radial-gradient(ellipse 150px 80px at 80% 60%, rgba(6, 182, 212, 0.2) 0%, transparent 50%),
                radial-gradient(ellipse 100px 60px at 50% 80%, rgba(29, 233, 182, 0.25) 0%, transparent 50%)
              `,
              animationDuration: '15s',
              animationDelay: '0s'
            }}
          />

          {/* Caustic Pattern 2 */}
          <div
            className="absolute inset-0 animate-caustics"
            style={{
              background: `
                radial-gradient(ellipse 180px 90px at 60% 20%, rgba(8, 131, 149, 0.2) 0%, transparent 50%),
                radial-gradient(ellipse 120px 70px at 30% 70%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse 80px 50px at 90% 40%, rgba(29, 233, 182, 0.2) 0%, transparent 50%)
              `,
              animationDuration: '18s',
              animationDelay: '3s'
            }}
          />
        </div>
      )}

      {/* Floating Bubbles */}
      {!prefersReducedMotion && (
        <div className="absolute inset-0 pointer-events-none">
          {bubbles.map(bubble => (
            <div
              key={bubble.id}
              className="absolute rounded-full bg-white/20 backdrop-blur-sm"
              style={{
                left: `${bubble.x}px`,
                top: `${bubble.y}px`,
                width: `${bubble.size}px`,
                height: `${bubble.size}px`,
                opacity: bubble.opacity,
                boxShadow: `
                  inset 0 0 ${bubble.size * 0.3}px rgba(255, 255, 255, 0.5),
                  0 0 ${bubble.size * 0.5}px rgba(6, 182, 212, 0.3)
                `,
                transform: 'translate3d(0, 0, 0)', // Force GPU acceleration
              }}
            />
          ))}
        </div>
      )}

      {/* Light Rays Effect */}
      {!prefersReducedMotion && (
        <div className="absolute inset-0 opacity-10">
          {/* Ray 1 */}
          <div
            className="absolute top-0 left-1/4 w-1 h-full bg-gradient-to-b from-aqua-400 to-transparent animate-pulse"
            style={{
              animationDuration: '4s',
              animationDelay: '1s',
              transform: 'rotate(5deg) translateX(-50%)'
            }}
          />

          {/* Ray 2 */}
          <div
            className="absolute top-0 right-1/3 w-0.5 h-full bg-gradient-to-b from-emerald-400 to-transparent animate-pulse"
            style={{
              animationDuration: '5s',
              animationDelay: '2s',
              transform: 'rotate(-3deg) translateX(50%)'
            }}
          />

          {/* Ray 3 */}
          <div
            className="absolute top-0 left-2/3 w-0.5 h-full bg-gradient-to-b from-aqua-300 to-transparent animate-pulse"
            style={{
              animationDuration: '6s',
              animationDelay: '0.5s',
              transform: 'rotate(2deg) translateX(-50%)'
            }}
          />
        </div>
      )}

      {/* Depth Gradient Overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'linear-gradient(to bottom, transparent 0%, rgba(0, 31, 46, 0.3) 70%, rgba(0, 31, 46, 0.6) 100%)'
        }}
      />
    </div>
  );
};

export default UnderwaterBackground;