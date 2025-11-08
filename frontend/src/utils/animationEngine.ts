/**
 * Animation Engine for AquaChain Landing Page
 * Centralized animation management with performance optimization
 */

import { PerformanceMonitor } from './performanceMonitor';

// Bubble interface
export interface Bubble {
  id: string;
  x: number;
  y: number;
  size: number;
  speed: number;
  drift: number;
  opacity: number;
  element?: HTMLElement;
}

// Ripple interface
export interface Ripple {
  id: string;
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  opacity: number;
  element?: HTMLElement;
}

// Animation settings
export interface AnimationSettings {
  enableParallax: boolean;
  enableRipples: boolean;
  enableBubbles: boolean;
  performanceMode: 'high' | 'medium' | 'low';
}

// Performance mode configurations
const PERFORMANCE_CONFIGS = {
  high: {
    maxBubbles: 15,
    maxRipples: 5,
    animationFrameRate: 60,
    enableGPUAcceleration: true
  },
  medium: {
    maxBubbles: 10,
    maxRipples: 3,
    animationFrameRate: 30,
    enableGPUAcceleration: true
  },
  low: {
    maxBubbles: 5,
    maxRipples: 1,
    animationFrameRate: 15,
    enableGPUAcceleration: false
  }
};

export class BubbleSystem {
  private bubbles: Bubble[] = [];
  private maxBubbles: number;
  private animationFrame: number = 0;
  private container: HTMLElement | null = null;
  private isRunning = false;
  private performanceMonitor: PerformanceMonitor;

  constructor(
    container: HTMLElement,
    performanceMode: 'high' | 'medium' | 'low' = 'high',
    performanceMonitor: PerformanceMonitor
  ) {
    this.container = container;
    this.maxBubbles = PERFORMANCE_CONFIGS[performanceMode].maxBubbles;
    this.performanceMonitor = performanceMonitor;
  }

  public start(): void {
    if (this.isRunning || !this.container) return;
    
    this.isRunning = true;
    this.generateBubbles();
    this.animate();
  }

  public stop(): void {
    this.isRunning = false;
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    this.clearBubbles();
  }

  private generateBubbles(): void {
    if (!this.container) return;

    const containerRect = this.container.getBoundingClientRect();
    
    for (let i = 0; i < this.maxBubbles; i++) {
      const bubble: Bubble = {
        id: `bubble-${i}`,
        x: Math.random() * containerRect.width,
        y: containerRect.height + Math.random() * 200,
        size: Math.random() * 20 + 10,
        speed: Math.random() * 2 + 1,
        drift: Math.random() * 0.5 - 0.25,
        opacity: Math.random() * 0.6 + 0.2
      };

      this.createBubbleElement(bubble);
      this.bubbles.push(bubble);
    }
  }

  private createBubbleElement(bubble: Bubble): void {
    if (!this.container) return;

    const element = document.createElement('div');
    element.className = 'bubble absolute rounded-full pointer-events-none';
    element.style.cssText = `
      width: ${bubble.size}px;
      height: ${bubble.size}px;
      background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.8), rgba(6, 182, 212, 0.4));
      transform: translate3d(${bubble.x}px, ${bubble.y}px, 0);
      opacity: ${bubble.opacity};
      will-change: transform;
      backdrop-filter: blur(1px);
    `;

    bubble.element = element;
    this.container.appendChild(element);
  }

  private animate(): void {
    if (!this.isRunning) return;

    const startTime = performance.now();

    this.updateBubbles();

    const endTime = performance.now();
    this.performanceMonitor.recordAnimationFrame(endTime - startTime);

    this.animationFrame = requestAnimationFrame(() => this.animate());
  }

  private updateBubbles(): void {
    if (!this.container) return;

    const containerRect = this.container.getBoundingClientRect();

    this.bubbles.forEach(bubble => {
      // Update position
      bubble.y -= bubble.speed;
      bubble.x += Math.sin(bubble.y * 0.01) * bubble.drift;

      // Update element position
      if (bubble.element) {
        bubble.element.style.transform = `translate3d(${bubble.x}px, ${bubble.y}px, 0)`;
      }

      // Recycle bubble if it's off screen
      if (bubble.y < -50) {
        this.recycleBubble(bubble, containerRect);
      }
    });
  }

  private recycleBubble(bubble: Bubble, containerRect: DOMRect): void {
    bubble.x = Math.random() * containerRect.width;
    bubble.y = containerRect.height + Math.random() * 200;
    bubble.size = Math.random() * 20 + 10;
    bubble.speed = Math.random() * 2 + 1;
    bubble.drift = Math.random() * 0.5 - 0.25;
    bubble.opacity = Math.random() * 0.6 + 0.2;

    if (bubble.element) {
      bubble.element.style.width = `${bubble.size}px`;
      bubble.element.style.height = `${bubble.size}px`;
      bubble.element.style.opacity = `${bubble.opacity}`;
    }
  }

  private clearBubbles(): void {
    this.bubbles.forEach(bubble => {
      if (bubble.element && bubble.element.parentNode) {
        bubble.element.parentNode.removeChild(bubble.element);
      }
    });
    this.bubbles = [];
  }
}

export class RippleSystem {
  private ripples: Ripple[] = [];
  private maxRipples: number;
  private container: HTMLElement | null = null;
  private animationFrame: number = 0;
  private isRunning = false;

  constructor(
    container: HTMLElement,
    performanceMode: 'high' | 'medium' | 'low' = 'high'
  ) {
    this.container = container;
    this.maxRipples = PERFORMANCE_CONFIGS[performanceMode].maxRipples;
  }

  public createRipple(x: number, y: number): void {
    if (!this.container || this.ripples.length >= this.maxRipples) return;

    const ripple: Ripple = {
      id: `ripple-${Date.now()}`,
      x,
      y,
      radius: 0,
      maxRadius: 200,
      opacity: 0.6
    };

    this.createRippleElement(ripple);
    this.ripples.push(ripple);

    if (!this.isRunning) {
      this.startAnimation();
    }
  }

  private createRippleElement(ripple: Ripple): void {
    if (!this.container) return;

    const element = document.createElement('div');
    element.className = 'ripple absolute rounded-full pointer-events-none';
    element.style.cssText = `
      width: 0px;
      height: 0px;
      border: 2px solid rgba(6, 182, 212, ${ripple.opacity});
      transform: translate3d(${ripple.x}px, ${ripple.y}px, 0) translate(-50%, -50%);
      will-change: transform, width, height, opacity;
    `;

    ripple.element = element;
    this.container.appendChild(element);
  }

  private startAnimation(): void {
    this.isRunning = true;
    this.animateRipples();
  }

  private animateRipples(): void {
    if (this.ripples.length === 0) {
      this.isRunning = false;
      return;
    }

    this.ripples = this.ripples.filter(ripple => {
      ripple.radius += 4;
      ripple.opacity = Math.max(0, ripple.opacity - 0.02);

      if (ripple.element) {
        const size = ripple.radius * 2;
        ripple.element.style.width = `${size}px`;
        ripple.element.style.height = `${size}px`;
        ripple.element.style.borderColor = `rgba(6, 182, 212, ${ripple.opacity})`;
      }

      // Remove ripple if it's fully expanded or transparent
      if (ripple.radius >= ripple.maxRadius || ripple.opacity <= 0) {
        if (ripple.element && ripple.element.parentNode) {
          ripple.element.parentNode.removeChild(ripple.element);
        }
        return false;
      }

      return true;
    });

    if (this.isRunning) {
      this.animationFrame = requestAnimationFrame(() => this.animateRipples());
    }
  }

  public stop(): void {
    this.isRunning = false;
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame);
    }
    this.clearRipples();
  }

  private clearRipples(): void {
    this.ripples.forEach(ripple => {
      if (ripple.element && ripple.element.parentNode) {
        ripple.element.parentNode.removeChild(ripple.element);
      }
    });
    this.ripples = [];
  }
}

export class ParallaxController {
  private elements: Array<{
    element: HTMLElement;
    speed: number;
    offset: number;
  }> = [];
  private isEnabled = true;

  public addElement(element: HTMLElement, speed: number = 0.5): void {
    this.elements.push({
      element,
      speed,
      offset: 0
    });
  }

  public removeElement(element: HTMLElement): void {
    this.elements = this.elements.filter(item => item.element !== element);
  }

  public updateParallax(scrollY: number): void {
    if (!this.isEnabled) return;

    this.elements.forEach(item => {
      const offset = scrollY * item.speed;
      item.element.style.transform = `translate3d(0, ${offset}px, 0)`;
    });
  }

  public setEnabled(enabled: boolean): void {
    this.isEnabled = enabled;
    
    if (!enabled) {
      // Reset all elements to their original position
      this.elements.forEach(item => {
        item.element.style.transform = 'translate3d(0, 0, 0)';
      });
    }
  }
}

export class AnimationEngine {
  public bubbleSystem: BubbleSystem | null = null;
  public rippleSystem: RippleSystem | null = null;
  public parallaxController: ParallaxController;
  public performanceMonitor: PerformanceMonitor;
  private settings: AnimationSettings;

  constructor(
    container: HTMLElement,
    settings: AnimationSettings,
    performanceMonitor: PerformanceMonitor
  ) {
    this.settings = settings;
    this.performanceMonitor = performanceMonitor;
    this.parallaxController = new ParallaxController();

    // Initialize systems based on settings
    if (settings.enableBubbles) {
      this.bubbleSystem = new BubbleSystem(
        container,
        settings.performanceMode,
        performanceMonitor
      );
    }

    if (settings.enableRipples) {
      this.rippleSystem = new RippleSystem(container, settings.performanceMode);
    }

    // Set up scroll listener for parallax
    if (settings.enableParallax) {
      this.setupParallaxScrollListener();
    }
  }

  public start(): void {
    if (this.bubbleSystem && this.settings.enableBubbles) {
      this.bubbleSystem.start();
    }
  }

  public stop(): void {
    if (this.bubbleSystem) {
      this.bubbleSystem.stop();
    }
    if (this.rippleSystem) {
      this.rippleSystem.stop();
    }
  }

  public createRipple(x: number, y: number): void {
    if (this.rippleSystem && this.settings.enableRipples) {
      this.rippleSystem.createRipple(x, y);
    }
  }

  public updateSettings(newSettings: Partial<AnimationSettings>): void {
    this.settings = { ...this.settings, ...newSettings };

    // Update parallax
    this.parallaxController.setEnabled(this.settings.enableParallax);
  }

  private setupParallaxScrollListener(): void {
    let ticking = false;

    const updateParallax = () => {
      this.parallaxController.updateParallax(window.scrollY);
      ticking = false;
    };

    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(updateParallax);
        ticking = true;
      }
    }, { passive: true });
  }
}

export default AnimationEngine;