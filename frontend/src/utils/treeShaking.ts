/**
 * Tree Shaking Optimization Utilities
 * Provides optimized imports and bundle size reduction techniques
 */

// Optimized imports for common libraries

// Lodash alternatives - Use native implementations for better tree shaking
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

export const merge = (target: any, ...sources: any[]): any => {
  return Object.assign(target, ...sources);
};

export const cloneDeep = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

// Date utilities - Native implementations
export const format = (date: Date, formatStr: string): string => {
  // Simple format implementation - extend as needed
  const options: Intl.DateTimeFormatOptions = {};
  if (formatStr.includes('yyyy')) options.year = 'numeric';
  if (formatStr.includes('MM')) options.month = '2-digit';
  if (formatStr.includes('dd')) options.day = '2-digit';
  return date.toLocaleDateString('en-US', options);
};

export const parseISO = (dateString: string): Date => {
  return new Date(dateString);
};

export const isValid = (date: Date): boolean => {
  return !isNaN(date.getTime());
};

export const differenceInMinutes = (dateLeft: Date, dateRight: Date): number => {
  return Math.floor((dateLeft.getTime() - dateRight.getTime()) / (1000 * 60));
};

export const addDays = (date: Date, amount: number): Date => {
  const result = new Date(date);
  result.setDate(result.getDate() + amount);
  return result;
};

export const startOfDay = (date: Date): Date => {
  const result = new Date(date);
  result.setHours(0, 0, 0, 0);
  return result;
};

export const endOfDay = (date: Date): Date => {
  const result = new Date(date);
  result.setHours(23, 59, 59, 999);
  return result;
};

// Recharts - Import only required components
export {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';

// Framer Motion - Import only what's needed
export {
  motion,
  AnimatePresence,
  useAnimation,
  useInView
} from 'framer-motion';

// Lucide React - Import individual icons
export {
  Activity,
  Shield,
  Brain,
  Home,
  Wrench,
  Mail,
  Phone,
  MapPin,
  ChevronDown,
  Menu,
  X,
  Eye,
  EyeOff,
  Check,
  AlertCircle,
  Loader2
} from 'lucide-react';

/**
 * Dynamic import utilities for better code splitting
 */
export const dynamicImports = {
  // Chart components
  loadCharts: () => import('recharts'),
  
  // Animation library
  loadAnimations: () => import('framer-motion'),
  
  // Date utilities - using native implementations
  loadDateUtils: () => Promise.resolve({
    format, parseISO, isValid, differenceInMinutes, addDays, startOfDay, endOfDay
  }),
  
  // AWS SDK components (load only when needed)
  loadAWSAuth: () => import('aws-amplify/auth'),
  loadAWSAPI: () => import('aws-amplify/api'),
  
  // Heavy UI components
  loadRichTextEditor: () => import('@headlessui/react'),
};

/**
 * Conditional loading based on feature flags
 */
interface FeatureFlags {
  enableCharts: boolean;
  enableAnimations: boolean;
  enableRichText: boolean;
  enableAdvancedAuth: boolean;
}

export const conditionalImports = {
  async loadFeatures(flags: FeatureFlags) {
    const imports: Record<string, any> = {};
    
    if (flags.enableCharts) {
      imports.charts = await dynamicImports.loadCharts();
    }
    
    if (flags.enableAnimations) {
      imports.animations = await dynamicImports.loadAnimations();
    }
    
    if (flags.enableAdvancedAuth) {
      imports.auth = await dynamicImports.loadAWSAuth();
    }
    
    return imports;
  }
};

/**
 * Bundle size monitoring
 */
export const bundleMonitor = {
  // Track component render performance with proper feature detection
  trackComponentSize: (componentName: string) => {
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined' && 'performance' in window) {
      try {
        const startTime = performance.now();
        
        return () => {
          try {
            const endTime = performance.now();
            const renderTime = endTime - startTime;
            
            if (renderTime > 16) { // > 1 frame at 60fps
              console.warn(`${componentName} render took ${renderTime.toFixed(2)}ms`);
            }
          } catch (error) {
            console.warn('Error measuring component render time:', error);
          }
        };
      } catch (error) {
        console.warn('Performance.now() not available:', error);
        return () => {}; // Return no-op function
      }
    }
    
    return () => {}; // No-op in production or unsupported browsers
  },
  
  // Monitor bundle loading with proper feature detection
  trackBundleLoad: (bundleName: string) => {
    if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined' && 'performance' in window) {
      try {
        const startTime = performance.now();
        
        return () => {
          try {
            const endTime = performance.now();
            const loadTime = endTime - startTime;
            
            console.log(`${bundleName} bundle loaded in ${loadTime.toFixed(2)}ms`);
          } catch (error) {
            console.warn('Error measuring bundle load time:', error);
          }
        };
      } catch (error) {
        console.warn('Performance.now() not available:', error);
        return () => {}; // Return no-op function
      }
    }
    
    return () => {}; // No-op in production or unsupported browsers
  }
};

/**
 * Webpack chunk optimization hints
 */
export const chunkOptimization = {
  // Vendor chunk - Third party libraries
  vendor: [
    'react',
    'react-dom',
    'react-router-dom',
    'framer-motion',
    'aws-amplify'
  ],
  
  // Common chunk - Shared utilities
  common: [
    './src/utils',
    './src/hooks',
    './src/contexts'
  ],
  
  // Landing page chunk
  landing: [
    './src/components/LandingPage'
  ],
  
  // Dashboard chunk
  dashboard: [
    './src/pages/Dashboard',
    './src/components/Dashboard'
  ]
};

/**
 * CSS optimization utilities
 */
export const cssOptimization = {
  // Critical CSS classes that should be inlined
  criticalClasses: [
    'font-sans',
    'font-display',
    'text-aqua-500',
    'bg-gradient-to-b',
    'min-h-screen',
    'flex',
    'items-center',
    'justify-center'
  ],
  
  // Non-critical CSS that can be loaded asynchronously
  nonCriticalClasses: [
    'animate-bubble-rise',
    'animate-caustics',
    'animate-shimmer',
    'shadow-underwater',
    'shadow-glow'
  ]
};

/**
 * Image optimization for bundle size
 */
export const imageOptimization = {
  // Recommended image formats by use case
  formats: {
    hero: ['avif', 'webp', 'jpg'],
    icons: ['svg', 'webp', 'png'],
    thumbnails: ['webp', 'jpg'],
    backgrounds: ['avif', 'webp', 'jpg']
  },
  
  // Responsive breakpoints
  breakpoints: [320, 640, 768, 1024, 1280, 1920],
  
  // Quality settings
  quality: {
    avif: 0.8,
    webp: 0.85,
    jpg: 0.9
  }
};