import { axe, toHaveNoViolations } from 'jest-axe';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

export interface AccessibilityConfig {
  rules?: Record<string, { enabled: boolean }>;
  tags?: string[];
  exclude?: string[];
  include?: string[];
}

export const DEFAULT_A11Y_CONFIG: AccessibilityConfig = {
  rules: {
    // Core accessibility rules (using valid axe-core rule IDs)
    'color-contrast': { enabled: true },
    'focus-order-semantics': { enabled: true },
    'aria-allowed-attr': { enabled: true },
    'aria-required-attr': { enabled: true },
    'heading-order': { enabled: true },
    'landmark-one-main': { enabled: true },
    'image-alt': { enabled: true },
    label: { enabled: true },
  },
  tags: ['wcag2a', 'wcag2aa', 'wcag21aa'],
  exclude: [
    // Exclude third-party components that we can't control
    '[data-testid="third-party"]',
  ],
};

export class AccessibilityTester {
  constructor(_config: AccessibilityConfig = DEFAULT_A11Y_CONFIG) {}

  /**
   * Test a DOM element for accessibility violations
   */
  async testElement(element: Element): Promise<void> {
    const results = await axe(element);
    expect(results).toHaveNoViolations();
  }

  /**
   * Test the entire document for accessibility violations
   */
  async testDocument(): Promise<void> {
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  }

  /**
   * Test keyboard navigation for an element
   */
  testKeyboardNavigation(element: Element): void {
    // Check if element is focusable
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    focusableElements.forEach(el => {
      expect(el).toBeVisible();
      expect(el).not.toHaveAttribute('tabindex', '-1');
    });
  }

  /**
   * Test ARIA labels and roles
   */
  testAriaLabels(element: Element): void {
    // Check for proper ARIA labels
    const interactiveElements = element.querySelectorAll(
      'button, [role="button"], input, select, textarea, [role="textbox"]'
    );

    interactiveElements.forEach(el => {
      const hasLabel =
        el.hasAttribute('aria-label') ||
        el.hasAttribute('aria-labelledby') ||
        el.querySelector('label') ||
        el.textContent?.trim();

      expect(hasLabel).toBeTruthy();
    });
  }

  /**
   * Test color contrast (requires manual verification in most cases)
   */
  testColorContrast(element: Element): void {
    // This is a basic check - real color contrast testing requires visual analysis
    const textElements = element.querySelectorAll(
      'p, span, div, h1, h2, h3, h4, h5, h6, label'
    );

    textElements.forEach(el => {
      const styles = window.getComputedStyle(el);
      const color = styles.color;
      const backgroundColor = styles.backgroundColor;

      // Basic check that colors are defined
      expect(color).not.toBe('');
      expect(backgroundColor).not.toBe('');
    });
  }
}

// Utility functions for common accessibility testing patterns
export const a11yTester = new AccessibilityTester();

/**
 * Test component accessibility in React Testing Library tests
 */
export async function testComponentAccessibility(
  container: Element
): Promise<void> {
  await a11yTester.testElement(container);
}

/**
 * Test keyboard navigation in React Testing Library tests
 */
export function testKeyboardNavigation(container: Element): void {
  a11yTester.testKeyboardNavigation(container);
}

/**
 * Test ARIA labels in React Testing Library tests
 */
export function testAriaLabels(container: Element): void {
  a11yTester.testAriaLabels(container);
}

/**
 * Accessibility testing utilities for Storybook
 */
export const storybookA11yConfig = {
  config: {
    rules: [
      {
        id: 'color-contrast',
        enabled: true,
      },
      {
        id: 'focus-order-semantics',
        enabled: true,
      },
      {
        id: 'keyboard-navigation',
        enabled: true,
      },
    ],
  },
  options: {
    checks: { 'color-contrast': { options: { noScroll: true } } },
    restoreScroll: true,
  },
};

/**
 * Reduced motion detection utility
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;

  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * High contrast mode detection utility
 */
export function prefersHighContrast(): boolean {
  if (typeof window === 'undefined') return false;

  return window.matchMedia('(prefers-contrast: high)').matches;
}

/**
 * Focus management utilities
 */
export class FocusManager {
  private previousFocus: Element | null = null;

  /**
   * Save the currently focused element
   */
  saveFocus(): void {
    this.previousFocus = document.activeElement;
  }

  /**
   * Restore focus to the previously saved element
   */
  restoreFocus(): void {
    if (this.previousFocus && 'focus' in this.previousFocus) {
      (this.previousFocus as HTMLElement).focus();
    }
  }

  /**
   * Trap focus within a container element
   */
  trapFocus(container: Element): () => void {
    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstFocusable = focusableElements[0] as HTMLElement;
    const lastFocusable = focusableElements[
      focusableElements.length - 1
    ] as HTMLElement;

    const handleKeyDown = (e: Event) => {
      const keyboardEvent = e as KeyboardEvent;
      if (keyboardEvent.key === 'Tab') {
        if (keyboardEvent.shiftKey) {
          if (document.activeElement === firstFocusable) {
            keyboardEvent.preventDefault();
            lastFocusable.focus();
          }
        } else {
          if (document.activeElement === lastFocusable) {
            keyboardEvent.preventDefault();
            firstFocusable.focus();
          }
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    // Focus the first element
    if (firstFocusable) {
      firstFocusable.focus();
    }

    // Return cleanup function
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }
}

export const focusManager = new FocusManager();
