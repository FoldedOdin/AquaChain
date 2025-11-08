import { designTokens } from '@/styles/design-tokens';

/**
 * Utility functions for working with design tokens
 */

/**
 * Get a color value from the design tokens
 */
export const getColor = (
  colorName: keyof typeof designTokens.colors,
  shade?: string | number
): string => {
  const color = designTokens.colors[colorName];
  
  if (typeof color === 'string') {
    return color;
  }
  
  if (typeof color === 'object' && shade) {
    return (color as any)[shade] || (color as any)['500'] || Object.values(color)[0];
  }
  
  return typeof color === 'object' ? (color as any)['500'] || Object.values(color)[0] : color;
};

/**
 * Get a spacing value from the design tokens
 */
export const getSpacing = (size: keyof typeof designTokens.spacing): string => {
  return designTokens.spacing[size];
};

/**
 * Get a font size value from the design tokens
 */
export const getFontSize = (size: keyof typeof designTokens.typography.fontSize): string => {
  return designTokens.typography.fontSize[size];
};

/**
 * Get a border radius value from the design tokens
 */
export const getBorderRadius = (size: keyof typeof designTokens.borderRadius): string => {
  return designTokens.borderRadius[size];
};

/**
 * Get a box shadow value from the design tokens
 */
export const getBoxShadow = (size: keyof typeof designTokens.boxShadow): string => {
  return designTokens.boxShadow[size];
};

/**
 * Generate CSS custom properties from design tokens
 */
export const generateCSSCustomProperties = (): Record<string, string> => {
  const properties: Record<string, string> = {};
  
  // Colors
  Object.entries(designTokens.colors).forEach(([colorName, colorValue]) => {
    if (typeof colorValue === 'string') {
      properties[`--color-${colorName}`] = colorValue;
    } else if (typeof colorValue === 'object') {
      Object.entries(colorValue).forEach(([shade, value]) => {
        properties[`--color-${colorName}-${shade}`] = value;
      });
    }
  });
  
  // Spacing
  Object.entries(designTokens.spacing).forEach(([size, value]) => {
    properties[`--spacing-${size}`] = value;
  });
  
  // Typography
  Object.entries(designTokens.typography.fontSize).forEach(([size, value]) => {
    properties[`--font-size-${size}`] = value;
  });
  
  // Border Radius
  Object.entries(designTokens.borderRadius).forEach(([size, value]) => {
    properties[`--border-radius-${size}`] = value;
  });
  
  return properties;
};

/**
 * Create a CSS class name from design token values
 */
export const createClassName = (...parts: (string | number | undefined)[]): string => {
  return parts
    .filter(Boolean)
    .map(part => String(part).toLowerCase().replace(/[^a-z0-9]/g, '-'))
    .join('-');
};

/**
 * Get responsive breakpoint media query
 */
export const getBreakpoint = (size: keyof typeof designTokens.breakpoints): string => {
  return `@media (min-width: ${designTokens.breakpoints[size]})`;
};

/**
 * Check if user prefers reduced motion
 */
export const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Get animation duration based on user preferences
 */
export const getAnimationDuration = (
  duration: keyof typeof designTokens.animation.duration
): string => {
  if (prefersReducedMotion()) {
    return '0ms';
  }
  return designTokens.animation.duration[duration];
};

/**
 * Create a CSS-in-JS style object from design tokens
 */
export const createStyles = (styles: Record<string, any>): Record<string, any> => {
  const processedStyles: Record<string, any> = {};
  
  Object.entries(styles).forEach(([key, value]) => {
    if (typeof value === 'string' && value.startsWith('token:')) {
      const tokenPath = value.replace('token:', '').split('.');
      let tokenValue: any = designTokens;
      
      for (const path of tokenPath) {
        tokenValue = tokenValue?.[path];
      }
      
      processedStyles[key] = tokenValue || value;
    } else {
      processedStyles[key] = value;
    }
  });
  
  return processedStyles;
};

/**
 * Validate if a color meets WCAG contrast requirements
 */
export const checkColorContrast = (
  foreground: string,
  background: string,
  level: 'AA' | 'AAA' = 'AA'
): boolean => {
  // This is a simplified implementation
  // In a real application, you would use a proper color contrast library
  const requiredRatio = level === 'AA' ? 4.5 : 7;
  
  // Convert hex to RGB and calculate luminance
  const getLuminance = (hex: string): number => {
    const rgb = parseInt(hex.slice(1), 16);
    const r = (rgb >> 16) & 0xff;
    const g = (rgb >> 8) & 0xff;
    const b = (rgb >> 0) & 0xff;
    
    const [rs, gs, bs] = [r, g, b].map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  
  return ratio >= requiredRatio;
};