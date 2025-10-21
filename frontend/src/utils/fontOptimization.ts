/**
 * Font Optimization Utilities
 * Handles font preloading and optimization for performance
 */

/**
 * Font configuration for AquaChain
 */
export const FONT_CONFIG = {
  // Primary fonts
  inter: {
    family: 'Inter',
    weights: [400, 500, 600, 700],
    display: 'swap' as const,
    preload: true,
  },
  poppins: {
    family: 'Poppins',
    weights: [400, 500, 600, 700],
    display: 'swap' as const,
    preload: true,
  },
};

/**
 * Generate Google Fonts URL with optimization
 */
export const generateGoogleFontsUrl = () => {
  const fonts = Object.values(FONT_CONFIG)
    .filter(font => font.preload)
    .map(font => {
      const weights = font.weights.join(',');
      return `${font.family.replace(' ', '+')}:wght@${weights}`;
    })
    .join('&family=');

  return `https://fonts.googleapis.com/css2?family=${fonts}&display=swap`;
};

/**
 * Preload critical fonts
 */
export const preloadFonts = () => {
  const fontsUrl = generateGoogleFontsUrl();
  
  // Preload the CSS file
  const link = document.createElement('link');
  link.rel = 'preload';
  link.href = fontsUrl;
  link.as = 'style';
  link.onload = () => {
    // Convert to stylesheet after loading
    link.rel = 'stylesheet';
  };
  
  document.head.appendChild(link);
  
  // Preconnect to Google Fonts domains
  const preconnectGstatic = document.createElement('link');
  preconnectGstatic.rel = 'preconnect';
  preconnectGstatic.href = 'https://fonts.gstatic.com';
  preconnectGstatic.crossOrigin = 'anonymous';
  document.head.appendChild(preconnectGstatic);
  
  const preconnectGoogleapis = document.createElement('link');
  preconnectGoogleapis.rel = 'preconnect';
  preconnectGoogleapis.href = 'https://fonts.googleapis.com';
  document.head.appendChild(preconnectGoogleapis);
};

/**
 * Add font-display: swap CSS for better performance
 */
export const addFontDisplaySwap = () => {
  const style = document.createElement('style');
  style.textContent = `
    @font-face {
      font-family: 'Inter';
      font-display: swap;
    }
    
    @font-face {
      font-family: 'Poppins';
      font-display: swap;
    }
    
    /* Fallback fonts for better FOUT handling */
    .font-sans {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    }
    
    .font-display {
      font-family: 'Poppins', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    }
  `;
  
  document.head.appendChild(style);
};

/**
 * Initialize font optimization
 */
export const initializeFontOptimization = () => {
  // Only run in browser
  if (typeof window === 'undefined') return;
  
  // Preload fonts
  preloadFonts();
  
  // Add font-display: swap
  addFontDisplaySwap();
  
  // Add font loading class to body for CSS targeting
  document.body.classList.add('fonts-loading');
  
  // Remove loading class when fonts are loaded
  if ('fonts' in document) {
    document.fonts.ready.then(() => {
      document.body.classList.remove('fonts-loading');
      document.body.classList.add('fonts-loaded');
    });
  } else {
    // Fallback for browsers without Font Loading API
    setTimeout(() => {
      document.body.classList.remove('fonts-loading');
      document.body.classList.add('fonts-loaded');
    }, 3000);
  }
};

/**
 * Check if fonts are loaded
 */
export const areFontsLoaded = (): Promise<boolean> => {
  if (typeof window === 'undefined') return Promise.resolve(false);
  
  if ('fonts' in document) {
    return document.fonts.ready.then(() => true);
  }
  
  // Fallback check
  return new Promise((resolve) => {
    const testString = 'abcdefghijklmnopqrstuvwxyz';
    const testSize = '72px';
    const fallbackFont = 'monospace';
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    
    if (!context) {
      resolve(false);
      return;
    }
    
    // Measure fallback font
    context.font = `${testSize} ${fallbackFont}`;
    const fallbackWidth = context.measureText(testString).width;
    
    // Check each font
    const fontChecks = Object.values(FONT_CONFIG).map(font => {
      return new Promise<boolean>((fontResolve) => {
        context.font = `${testSize} ${font.family}, ${fallbackFont}`;
        const fontWidth = context.measureText(testString).width;
        
        if (fontWidth !== fallbackWidth) {
          fontResolve(true);
        } else {
          // Retry after a short delay
          setTimeout(() => {
            const retryWidth = context.measureText(testString).width;
            fontResolve(retryWidth !== fallbackWidth);
          }, 100);
        }
      });
    });
    
    Promise.all(fontChecks).then(results => {
      resolve(results.every(loaded => loaded));
    });
  });
};