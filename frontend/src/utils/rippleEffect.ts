import React from 'react';

/**
 * Ripple Effect Utility
 * Creates interactive ripple animations for click interactions
 */

export interface RippleConfig {
  color?: string;
  duration?: number;
  size?: number;
}

export class RippleEffect {
  private static defaultConfig: Required<RippleConfig> = {
    color: 'rgba(255, 255, 255, 0.3)',
    duration: 600,
    size: 100
  };

  /**
   * Create a ripple effect at the click position
   */
  static create(
    element: HTMLElement,
    event: React.MouseEvent | MouseEvent,
    config: RippleConfig = {}
  ): void {
    const finalConfig = { ...this.defaultConfig, ...config };
    
    // Get element bounds
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    
    // Calculate ripple position
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    // Create ripple element
    const ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      background: ${finalConfig.color};
      transform: scale(0);
      animation: ripple-animation ${finalConfig.duration}ms ease-out;
      left: ${x}px;
      top: ${y}px;
      width: ${size}px;
      height: ${size}px;
      pointer-events: none;
      z-index: 1000;
    `;
    
    // Ensure parent has relative positioning
    const originalPosition = element.style.position;
    if (!originalPosition || originalPosition === 'static') {
      element.style.position = 'relative';
    }
    
    // Add overflow hidden to contain ripple
    const originalOverflow = element.style.overflow;
    element.style.overflow = 'hidden';
    
    // Add ripple to element
    element.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
      if (ripple.parentNode) {
        ripple.parentNode.removeChild(ripple);
      }
      
      // Restore original styles if no other ripples exist
      const remainingRipples = element.querySelectorAll('.ripple-effect');
      if (remainingRipples.length === 0) {
        if (!originalPosition || originalPosition === 'static') {
          element.style.position = originalPosition || '';
        }
        element.style.overflow = originalOverflow || '';
      }
    }, finalConfig.duration);
  }

  /**
   * Create ripple effect hook for React components
   */
  static useRipple(config: RippleConfig = {}) {
    return (event: React.MouseEvent<HTMLElement>) => {
      const element = event.currentTarget;
      this.create(element, event, config);
    };
  }

  /**
   * Add ripple effect to multiple elements
   */
  static addToElements(
    selector: string,
    config: RippleConfig = {}
  ): void {
    const elements = document.querySelectorAll(selector);
    
    elements.forEach((element) => {
      if (element instanceof HTMLElement) {
        element.addEventListener('click', (event) => {
          this.create(element, event, config);
        });
      }
    });
  }

  /**
   * Initialize CSS animation keyframes
   */
  static initializeCSS(): void {
    // Check if styles already exist
    if (document.querySelector('#ripple-effect-styles')) {
      return;
    }

    const style = document.createElement('style');
    style.id = 'ripple-effect-styles';
    style.textContent = `
      @keyframes ripple-animation {
        0% {
          transform: scale(0);
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
        100% {
          transform: scale(1);
          opacity: 0;
        }
      }
      
      .ripple-container {
        position: relative;
        overflow: hidden;
      }
      
      .ripple-effect {
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
        z-index: 1000;
      }
    `;
    
    document.head.appendChild(style);
  }
}

/**
 * React Hook for ripple effects
 */
export const useRippleEffect = (config: RippleConfig = {}) => {
  const createRipple = (event: React.MouseEvent<HTMLElement>) => {
    RippleEffect.create(event.currentTarget, event, config);
  };

  return createRipple;
};

/**
 * Higher-order component to add ripple effects
 * Properly typed with generic component props
 */
export const withRipple = <P extends { onClick?: (event: React.MouseEvent<HTMLElement>) => void }>(
  Component: React.ComponentType<P>,
  config: RippleConfig = {}
) => {
  return React.forwardRef<HTMLElement, P>((props, ref) => {
    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
      RippleEffect.create(event.currentTarget, event, config);
      if (props.onClick) {
        props.onClick(event);
      }
    };

    return React.createElement(Component, { ...props, ref, onClick: handleClick });
  });
};

// Initialize CSS on module load
if (typeof document !== 'undefined') {
  RippleEffect.initializeCSS();
}