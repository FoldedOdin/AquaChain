/**
 * Image Optimization Utilities
 * Handles WebP conversion, compression, and responsive images
 */

import React from 'react';

/**
 * Check if browser supports WebP format
 */
export const supportsWebP = (): Promise<boolean> => {
  return new Promise((resolve) => {
    const webP = new Image();
    webP.onload = webP.onerror = () => {
      resolve(webP.height === 2);
    };
    webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
  });
};

/**
 * Check if browser supports AVIF format
 */
export const supportsAVIF = (): Promise<boolean> => {
  return new Promise((resolve) => {
    const avif = new Image();
    avif.onload = avif.onerror = () => {
      resolve(avif.height === 2);
    };
    avif.src = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A=';
  });
};

/**
 * Generate responsive image sources with different formats
 */
export interface ResponsiveImageSource {
  src: string;
  srcSet?: string;
  type?: string;
  sizes?: string;
}

export const generateResponsiveImageSources = (
  basePath: string,
  filename: string,
  sizes: number[] = [320, 640, 768, 1024, 1280, 1920]
): ResponsiveImageSource[] => {
  const name = filename.split('.')[0];
  const sources: ResponsiveImageSource[] = [];

  // AVIF sources (best compression)
  const avifSrcSet = sizes
    .map(size => `${basePath}/${name}-${size}w.avif ${size}w`)
    .join(', ');
  
  sources.push({
    src: `${basePath}/${name}-1024w.avif`,
    srcSet: avifSrcSet,
    type: 'image/avif',
    sizes: '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw'
  });

  // WebP sources (good compression, wide support)
  const webpSrcSet = sizes
    .map(size => `${basePath}/${name}-${size}w.webp ${size}w`)
    .join(', ');
  
  sources.push({
    src: `${basePath}/${name}-1024w.webp`,
    srcSet: webpSrcSet,
    type: 'image/webp',
    sizes: '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw'
  });

  // JPEG fallback (universal support)
  const jpegSrcSet = sizes
    .map(size => `${basePath}/${name}-${size}w.jpg ${size}w`)
    .join(', ');
  
  sources.push({
    src: `${basePath}/${name}-1024w.jpg`,
    srcSet: jpegSrcSet,
    type: 'image/jpeg',
    sizes: '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw'
  });

  return sources;
};

/**
 * Optimized Picture component with multiple formats
 */
interface OptimizedPictureProps {
  basePath: string;
  filename: string;
  alt: string;
  className?: string;
  sizes?: number[];
  loading?: 'lazy' | 'eager';
  priority?: boolean;
}

export const OptimizedPicture: React.FC<OptimizedPictureProps> = ({
  basePath,
  filename,
  alt,
  className = '',
  sizes = [320, 640, 768, 1024, 1280, 1920],
  loading = 'lazy',
  priority = false
}) => {
  const sources = generateResponsiveImageSources(basePath, filename, sizes);
  const fallbackSrc = sources[sources.length - 1].src;

  return React.createElement('picture', { className },
    ...sources.slice(0, -1).map((source, index) =>
      React.createElement('source', {
        key: index,
        srcSet: source.srcSet,
        type: source.type,
        sizes: source.sizes
      })
    ),
    React.createElement('img', {
      src: fallbackSrc,
      alt: alt,
      loading: priority ? 'eager' : loading,
      decoding: 'async',
      className: 'w-full h-full object-cover'
    })
  );
};

/**
 * Preload critical images
 */
export const preloadCriticalImages = (images: Array<{ src: string; type?: string }>) => {
  images.forEach(({ src, type = 'image/webp' }) => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.href = src;
    link.as = 'image';
    link.type = type;
    document.head.appendChild(link);
  });
};

/**
 * Lazy load background images
 */
export const useLazyBackgroundImage = (imageUrl: string, placeholder?: string) => {
  const [backgroundImage, setBackgroundImage] = React.useState(placeholder || 'none');
  const [isLoaded, setIsLoaded] = React.useState(false);
  const elementRef = React.useRef<HTMLElement>(null);

  React.useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = new Image();
            img.onload = () => {
              setBackgroundImage(`url(${imageUrl})`);
              setIsLoaded(true);
              observer.unobserve(element);
            };
            img.src = imageUrl;
          }
        });
      },
      { threshold: 0.1, rootMargin: '50px' }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [imageUrl]);

  return { elementRef, backgroundImage, isLoaded };
};

/**
 * Image compression utility (client-side)
 */
export const compressImage = (
  file: File,
  maxWidth: number = 1920,
  maxHeight: number = 1080,
  quality: number = 0.8
): Promise<Blob> => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();

    img.onload = () => {
      // Calculate new dimensions
      let { width, height } = img;
      
      if (width > height) {
        if (width > maxWidth) {
          height = (height * maxWidth) / width;
          width = maxWidth;
        }
      } else {
        if (height > maxHeight) {
          width = (width * maxHeight) / height;
          height = maxHeight;
        }
      }

      canvas.width = width;
      canvas.height = height;

      // Draw and compress
      ctx?.drawImage(img, 0, 0, width, height);
      
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Canvas to Blob conversion failed'));
          }
        },
        'image/webp',
        quality
      );
    };

    img.onerror = () => reject(new Error('Image loading failed'));
    img.src = URL.createObjectURL(file);
  });
};

/**
 * Generate blur placeholder for images
 */
export const generateBlurPlaceholder = (width: number = 40, height: number = 40): string => {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  
  canvas.width = width;
  canvas.height = height;
  
  if (ctx) {
    // Create a simple gradient placeholder
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, '#e5e7eb');
    gradient.addColorStop(1, '#f3f4f6');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
  }
  
  return canvas.toDataURL('image/jpeg', 0.1);
};