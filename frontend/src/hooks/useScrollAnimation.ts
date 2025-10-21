import { useRef, useEffect, useState } from 'react';
import { useAnimation, useReducedMotion } from 'framer-motion';

export interface ScrollAnimationOptions {
  threshold?: number;
  rootMargin?: string;
  triggerOnce?: boolean;
  staggerDelay?: number;
  enableReducedMotion?: boolean;
}

export interface ScrollAnimationReturn {
  ref: React.RefObject<any>;
  isInView: boolean;
  controls: ReturnType<typeof useAnimation>;
  shouldReduceMotion: boolean;
}

/**
 * Custom hook for scroll-triggered animations with Intersection Observer
 * Provides enhanced control over animation timing and reduced motion support
 */
export const useScrollAnimation = (
  options: ScrollAnimationOptions = {}
): ScrollAnimationReturn => {
  const {
    threshold = 0.1,
    rootMargin = '-50px',
    triggerOnce = true,
    enableReducedMotion = true
  } = options;

  const ref = useRef<any>(null);
  const [isInView, setIsInView] = useState(false);
  const controls = useAnimation();
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        const inView = entry.isIntersecting;
        
        if (inView && (!triggerOnce || !isInView)) {
          setIsInView(true);
          controls.start('visible');
        } else if (!triggerOnce && !inView) {
          setIsInView(false);
          controls.start('hidden');
        }
      },
      {
        threshold,
        rootMargin
      }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [threshold, rootMargin, triggerOnce, isInView, controls]);

  return {
    ref,
    isInView,
    controls,
    shouldReduceMotion: enableReducedMotion ? shouldReduceMotion || false : false
  };
};

/**
 * Hook for staggered animations of multiple elements
 */
export const useStaggeredAnimation = (
  itemCount: number,
  options: ScrollAnimationOptions & { staggerDelay?: number } = {}
) => {
  const { staggerDelay = 0.1, ...scrollOptions } = options;
  const { ref, isInView, controls, shouldReduceMotion } = useScrollAnimation(scrollOptions);
  const [animatedItems, setAnimatedItems] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isInView && !shouldReduceMotion) {
      // Animate items with stagger delay
      for (let i = 0; i < itemCount; i++) {
        setTimeout(() => {
          setAnimatedItems(prev => new Set(Array.from(prev).concat(i)));
        }, i * staggerDelay * 1000);
      }
    } else if (isInView && shouldReduceMotion) {
      // Show all items immediately if reduced motion is preferred
      const itemIndices: number[] = [];
      for (let i = 0; i < itemCount; i++) {
        itemIndices.push(i);
      }
      setAnimatedItems(new Set(itemIndices));
    }
  }, [isInView, itemCount, staggerDelay, shouldReduceMotion]);

  const getItemVariants = (index: number) => ({
    hidden: {
      opacity: shouldReduceMotion ? 1 : 0,
      y: shouldReduceMotion ? 0 : 30,
      scale: shouldReduceMotion ? 1 : 0.95
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: shouldReduceMotion ? {} : {
        duration: 0.5,
        ease: [0.25, 0.46, 0.45, 0.94]
      }
    }
  });

  const isItemVisible = (index: number) => animatedItems.has(index);

  return {
    ref,
    isInView,
    controls,
    shouldReduceMotion,
    getItemVariants,
    isItemVisible
  };
};

/**
 * Hook for parallax scroll effects
 */
export const useParallaxScroll = (speed: number = 0.5) => {
  const [offset, setOffset] = useState(0);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion) return;

    const handleScroll = () => {
      setOffset(window.pageYOffset * speed);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [speed, shouldReduceMotion]);

  return shouldReduceMotion ? 0 : offset;
};

/**
 * Hook for scroll progress tracking
 */
export const useScrollProgress = () => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const scrollPercent = scrollTop / docHeight;
      setProgress(Math.min(Math.max(scrollPercent, 0), 1));
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll(); // Initial calculation

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return progress;
};

/**
 * Animation variants for common scroll animations
 */
export const scrollAnimationVariants = {
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.6, ease: 'easeOut' }
    }
  },
  
  slideUp: {
    hidden: { opacity: 0, y: 50 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
    }
  },
  
  slideDown: {
    hidden: { opacity: 0, y: -50 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
    }
  },
  
  slideLeft: {
    hidden: { opacity: 0, x: 50 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
    }
  },
  
  slideRight: {
    hidden: { opacity: 0, x: -50 },
    visible: { 
      opacity: 1, 
      x: 0,
      transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
    }
  },
  
  scale: {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { 
      opacity: 1, 
      scale: 1,
      transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
    }
  },
  
  stagger: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  }
};

/**
 * Utility function to create responsive animation variants
 */
export const createResponsiveVariants = (
  mobileVariant: any,
  desktopVariant: any,
  breakpoint: number = 768
) => {
  const isMobile = typeof window !== 'undefined' && window.innerWidth < breakpoint;
  return isMobile ? mobileVariant : desktopVariant;
};