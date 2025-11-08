/**
 * Lazy Loading Utilities
 * Provides image lazy loading and component code splitting functionality
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';

// Intersection Observer options for lazy loading
const LAZY_LOADING_OPTIONS: IntersectionObserverInit = {
  root: null,
  rootMargin: '50px',
  threshold: 0.1,
};

/**
 * Hook for lazy loading images using Intersection Observer
 */
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState<string>(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const imgElement = imgRef.current;
    if (!imgElement) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Start loading the actual image
            const img = new Image();
            img.onload = () => {
              setImageSrc(src);
              setIsLoaded(true);
              observer.unobserve(imgElement);
            };
            img.onerror = () => {
              setIsError(true);
              observer.unobserve(imgElement);
            };
            img.src = src;
          }
        });
      },
      LAZY_LOADING_OPTIONS
    );

    observer.observe(imgElement);

    return () => {
      observer.unobserve(imgElement);
    };
  }, [src]);

  return { imgRef, imageSrc, isLoaded, isError };
};

/**
 * Hook for lazy loading any element using Intersection Observer
 */
export const useLazyElement = (threshold = 0.1, rootMargin = '50px') => {
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            observer.unobserve(element);
          }
        });
      },
      {
        root: null,
        rootMargin,
        threshold,
      }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [threshold, rootMargin]);

  return { elementRef, isVisible };
};

/**
 * Preload critical resources
 */
export const preloadResource = (href: string, as: string, type?: string) => {
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = href;
  link.as = as;
  if (type) link.type = type;
  
  document.head.appendChild(link);
  
  return () => {
    document.head.removeChild(link);
  };
};

/**
 * Preload fonts with font-display: swap
 */
export const preloadFonts = (fonts: Array<{ href: string; type?: string }>) => {
  const cleanupFunctions: Array<() => void> = [];
  
  fonts.forEach(({ href, type = 'font/woff2' }) => {
    const cleanup = preloadResource(href, 'font', type);
    cleanupFunctions.push(cleanup);
  });
  
  return () => {
    cleanupFunctions.forEach(cleanup => cleanup());
  };
};

/**
 * Image component with lazy loading
 */
interface LazyImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string;
  placeholder?: string;
  fallback?: string;
}

export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  placeholder,
  fallback,
  className = '',
  alt = '',
  ...props
}) => {
  const { imgRef, imageSrc, isLoaded, isError } = useLazyImage(src, placeholder);

  if (isError && fallback) {
    return React.createElement('img', {
      src: fallback,
      alt: alt,
      className: `${className} lazy-image-error`,
      ...props
    });
  }

  return React.createElement('img', {
    ref: imgRef,
    src: imageSrc,
    alt: alt,
    className: `${className} ${isLoaded ? 'lazy-image-loaded' : 'lazy-image-loading'}`,
    loading: 'lazy',
    ...props
  });
};

/**
 * Component wrapper for lazy loading content
 */
interface LazyContentProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
  className?: string;
}

export const LazyContent: React.FC<LazyContentProps> = ({
  children,
  fallback,
  threshold = 0.1,
  rootMargin = '50px',
  className = '',
}) => {
  const { elementRef, isVisible } = useLazyElement(threshold, rootMargin);

  return React.createElement('div', {
    ref: elementRef,
    className: className
  }, isVisible ? children : fallback);
};

/**
 * Hook for code splitting with loading states
 */
export const useCodeSplitting = <T extends React.ComponentType<any>>(
  importFunction: () => Promise<{ default: T }>
) => {
  const [Component, setComponent] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const loadComponent = useCallback(async () => {
    try {
      setIsLoading(true);
      const module = await importFunction();
      setComponent(() => module.default);
    } catch (err) {
      setError(err as Error);
    } finally {
      setIsLoading(false);
    }
  }, [importFunction]);

  useEffect(() => {
    loadComponent();
  }, [loadComponent]);

  return { Component, isLoading, error, reload: loadComponent };
};