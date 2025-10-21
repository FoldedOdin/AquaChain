# Testing Strategy for UI/UX Improvements

## Overview

This document outlines comprehensive testing requirements and strategies for implementing UI/UX improvements as specified in the AquaChain PRD. The testing strategy ensures that all improvements meet accessibility standards, maintain performance benchmarks, and provide excellent user experiences across all devices and user personas.

## Testing Framework Architecture

### Testing Pyramid Structure

```
                    E2E Tests
                   /           \
              Integration Tests
             /                   \
        Component Tests
       /                         \
  Unit Tests                Design Token Tests
```

### Testing Tools and Technologies

**Unit and Component Testing**
- **Jest**: JavaScript testing framework
- **React Testing Library**: Component testing utilities
- **@testing-library/jest-dom**: Custom Jest matchers
- **@axe-core/react**: Accessibility testing

**Integration Testing**
- **Playwright**: Cross-browser testing
- **Cypress**: End-to-end testing alternative
- **Mock Service Worker (MSW)**: API mocking

**Accessibility Testing**
- **axe-core**: Automated accessibility testing
- **Pa11y**: Command-line accessibility testing
- **Lighthouse CI**: Performance and accessibility auditing
- **WAVE**: Web accessibility evaluation

**Visual Testing**
- **Chromatic**: Visual regression testing
- **Percy**: Visual testing platform
- **Storybook**: Component documentation and testing

**Performance Testing**
- **Lighthouse**: Performance auditing
- **WebPageTest**: Performance analysis
- **Bundle Analyzer**: Bundle size analysis

## Unit Testing Requirements

### Component Testing Standards

#### Accessibility Testing

```javascript
// accessibility.test.js
import { render, screen } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import userEvent from '@testing-library/user-event';
import { Button } from '../Button';

expect.extend(toHaveNoViolations);

describe('Button Accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should be keyboard accessible', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button');
    await user.tab();
    expect(button).toHaveFocus();
    
    await user.keyboard('{Enter}');
    expect(handleClick).toHaveBeenCalledTimes(1);
    
    await user.keyboard(' ');
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  it('should have proper ARIA attributes', () => {
    render(<Button disabled>Disabled Button</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-disabled', 'true');
  });

  it('should meet color contrast requirements', () => {
    render(<Button variant="primary">Primary Button</Button>);
    
    const button = screen.getByRole('button');
    const styles = getComputedStyle(button);
    
    // This would use a contrast calculation utility
    const contrastRatio = calculateContrastRatio(
      styles.color,
      styles.backgroundColor
    );
    
    expect(contrastRatio).toBeGreaterThanOrEqual(4.5);
  });

  it('should provide screen reader feedback for state changes', () => {
    const { rerender } = render(<Button loading={false}>Submit</Button>);
    
    rerender(<Button loading={true}>Submit</Button>);
    
    const statusElement = screen.getByRole('status', { hidden: true });
    expect(statusElement).toHaveTextContent('Loading');
  });
});
```

#### Responsive Design Testing

```javascript
// responsive.test.js
import { render } from '@testing-library/react';
import { NavigationBar } from '../NavigationBar';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

describe('NavigationBar Responsive Behavior', () => {
  it('should show desktop navigation on large screens', () => {
    // Mock large screen
    window.matchMedia.mockImplementation(query => ({
      matches: query === '(min-width: 1024px)',
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    render(<NavigationBar />);
    
    expect(screen.getByTestId('desktop-nav')).toBeVisible();
    expect(screen.queryByTestId('mobile-nav')).not.toBeInTheDocument();
  });

  it('should show mobile navigation on small screens', () => {
    // Mock small screen
    window.matchMedia.mockImplementation(query => ({
      matches: query === '(max-width: 768px)',
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));

    render(<NavigationBar />);
    
    expect(screen.getByTestId('mobile-nav')).toBeVisible();
    expect(screen.queryByTestId('desktop-nav')).not.toBeInTheDocument();
  });

  it('should handle touch interactions on mobile', async () => {
    const user = userEvent.setup();
    
    render(<NavigationBar />);
    
    const menuButton = screen.getByRole('button', { name: /menu/i });
    
    // Simulate touch interaction
    await user.pointer({ keys: '[TouchA>]', target: menuButton });
    await user.pointer({ keys: '[/TouchA]' });
    
    expect(screen.getByRole('navigation')).toHaveAttribute('aria-expanded', 'true');
  });
});
```

#### Design Token Testing

```javascript
// design-tokens.test.js
import { render } from '@testing-library/react';
import { ThemeProvider } from '../ThemeProvider';
import { Button } from '../Button';
import designTokens from '../design-tokens.json';

describe('Design Token Usage', () => {
  it('should use design tokens for colors', () => {
    render(
      <ThemeProvider>
        <Button variant="primary">Test Button</Button>
      </ThemeProvider>
    );
    
    const button = screen.getByRole('button');
    const styles = getComputedStyle(button);
    
    // Verify CSS custom properties are used
    expect(styles.backgroundColor).toBe('var(--color-primary-500)');
    expect(styles.color).toBe('var(--color-neutral-white)');
  });

  it('should use design tokens for spacing', () => {
    render(
      <ThemeProvider>
        <Button size="large">Large Button</Button>
      </ThemeProvider>
    );
    
    const button = screen.getByRole('button');
    const styles = getComputedStyle(button);
    
    expect(styles.padding).toBe('var(--spacing-4) var(--spacing-6)');
  });

  it('should use design tokens for typography', () => {
    render(
      <ThemeProvider>
        <Button>Button Text</Button>
      </ThemeProvider>
    );
    
    const button = screen.getByRole('button');
    const styles = getComputedStyle(button);
    
    expect(styles.fontFamily).toBe('var(--font-family-primary)');
    expect(styles.fontSize).toBe('var(--font-size-base)');
    expect(styles.fontWeight).toBe('var(--font-weight-medium)');
  });

  it('should validate design token values', () => {
    // Test that design tokens meet accessibility requirements
    const primaryColor = designTokens.colors.primary['500'];
    const whiteColor = designTokens.colors.neutral.white;
    
    const contrastRatio = calculateContrastRatio(primaryColor, whiteColor);
    expect(contrastRatio).toBeGreaterThanOrEqual(4.5);
  });
});
```

### Performance Testing

```javascript
// performance.test.js
import { render, act } from '@testing-library/react';
import { DataVisualization } from '../DataVisualization';

describe('Component Performance', () => {
  it('should render within performance budget', () => {
    const startTime = performance.now();
    
    act(() => {
      render(<DataVisualization data={largeDataset} />);
    });
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should render within 16ms (60fps budget)
    expect(renderTime).toBeLessThan(16);
  });

  it('should not cause memory leaks', () => {
    const { unmount } = render(<DataVisualization />);
    
    const initialMemory = performance.memory?.usedJSHeapSize || 0;
    
    // Render and unmount multiple times
    for (let i = 0; i < 100; i++) {
      const { unmount: unmountInstance } = render(<DataVisualization />);
      unmountInstance();
    }
    
    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }
    
    const finalMemory = performance.memory?.usedJSHeapSize || 0;
    const memoryIncrease = finalMemory - initialMemory;
    
    // Memory increase should be minimal
    expect(memoryIncrease).toBeLessThan(1000000); // 1MB threshold
  });

  it('should handle large datasets efficiently', () => {
    const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
      id: i,
      value: Math.random() * 100,
      timestamp: new Date(Date.now() - i * 1000)
    }));
    
    const startTime = performance.now();
    
    render(<DataVisualization data={largeDataset} />);
    
    const endTime = performance.now();
    const renderTime = endTime - startTime;
    
    // Should handle large datasets within reasonable time
    expect(renderTime).toBeLessThan(100);
  });
});
```

## Integration Testing Requirements

### User Flow Testing

```javascript
// user-flow.test.js
import { test, expect } from '@playwright/test';

test.describe('Consumer Dashboard User Flow', () => {
  test('should complete water quality monitoring workflow', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/dashboard/consumer');
    
    // Verify accessibility
    await expect(page).toHaveTitle(/Water Quality Dashboard/);
    await expect(page.locator('h1')).toBeVisible();
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    await expect(page.locator('[data-testid="nav-item"]:focus')).toBeVisible();
    
    // Interact with water quality data
    await page.click('[data-testid="location-selector"]');
    await page.selectOption('[data-testid="location-selector"]', 'location-1');
    
    // Verify data updates
    await expect(page.locator('[data-testid="quality-metrics"]')).toBeVisible();
    await expect(page.locator('[data-testid="quality-chart"]')).toBeVisible();
    
    // Test responsive behavior
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();
    
    // Test alert functionality
    await page.click('[data-testid="alert-settings"]');
    await page.fill('[data-testid="alert-threshold"]', '7.5');
    await page.click('[data-testid="save-alert"]');
    
    // Verify success feedback
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="success-message"]')).toHaveText(/Alert settings saved/);
  });

  test('should handle error states gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/water-quality/**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });
    
    await page.goto('/dashboard/consumer');
    
    // Verify error handling
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // Test retry functionality
    await page.click('[data-testid="retry-button"]');
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
  });
});
```

### Cross-Browser Compatibility Testing

```javascript
// cross-browser.test.js
import { devices } from '@playwright/test';

const browsers = [
  { name: 'Chrome', ...devices['Desktop Chrome'] },
  { name: 'Firefox', ...devices['Desktop Firefox'] },
  { name: 'Safari', ...devices['Desktop Safari'] },
  { name: 'Edge', ...devices['Desktop Edge'] }
];

browsers.forEach(browser => {
  test.describe(`${browser.name} Compatibility`, () => {
    test.use(browser);
    
    test('should render correctly', async ({ page }) => {
      await page.goto('/dashboard');
      
      // Take screenshot for visual comparison
      await expect(page).toHaveScreenshot(`dashboard-${browser.name.toLowerCase()}.png`);
      
      // Test core functionality
      await page.click('[data-testid="menu-button"]');
      await expect(page.locator('[data-testid="navigation-menu"]')).toBeVisible();
      
      // Test form interactions
      await page.fill('[data-testid="search-input"]', 'test query');
      await page.keyboard.press('Enter');
      
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    });
    
    test('should handle CSS features correctly', async ({ page }) => {
      await page.goto('/style-guide');
      
      // Test CSS Grid support
      const gridContainer = page.locator('[data-testid="grid-container"]');
      await expect(gridContainer).toHaveCSS('display', 'grid');
      
      // Test CSS Custom Properties
      const button = page.locator('[data-testid="primary-button"]');
      const backgroundColor = await button.evaluate(el => 
        getComputedStyle(el).backgroundColor
      );
      expect(backgroundColor).toBeTruthy();
      
      // Test CSS Flexbox
      const flexContainer = page.locator('[data-testid="flex-container"]');
      await expect(flexContainer).toHaveCSS('display', 'flex');
    });
  });
});
```

## End-to-End Testing Requirements

### User Persona Testing

```javascript
// persona-testing.test.js
import { test, expect } from '@playwright/test';

test.describe('Consumer Persona Testing', () => {
  test.beforeEach(async ({ page }) => {
    // Login as consumer user
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'consumer@test.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard/consumer');
  });

  test('should access consumer-specific features', async ({ page }) => {
    // Verify consumer dashboard elements
    await expect(page.locator('[data-testid="water-quality-overview"]')).toBeVisible();
    await expect(page.locator('[data-testid="location-selector"]')).toBeVisible();
    await expect(page.locator('[data-testid="alert-settings"]')).toBeVisible();
    
    // Verify restricted access
    await expect(page.locator('[data-testid="admin-panel"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="technician-tools"]')).not.toBeVisible();
  });

  test('should complete typical consumer workflow', async ({ page }) => {
    // Select location
    await page.selectOption('[data-testid="location-selector"]', 'home-location');
    
    // View water quality data
    await expect(page.locator('[data-testid="ph-level"]')).toBeVisible();
    await expect(page.locator('[data-testid="temperature"]')).toBeVisible();
    await expect(page.locator('[data-testid="turbidity"]')).toBeVisible();
    
    // Set up alerts
    await page.click('[data-testid="alert-settings"]');
    await page.fill('[data-testid="ph-threshold"]', '7.0');
    await page.check('[data-testid="email-notifications"]');
    await page.click('[data-testid="save-alerts"]');
    
    // Verify success
    await expect(page.locator('[data-testid="success-notification"]')).toBeVisible();
  });
});

test.describe('Technician Persona Testing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'technician@test.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard/technician');
  });

  test('should access technician-specific tools', async ({ page }) => {
    // Verify technician dashboard elements
    await expect(page.locator('[data-testid="device-management"]')).toBeVisible();
    await expect(page.locator('[data-testid="calibration-tools"]')).toBeVisible();
    await expect(page.locator('[data-testid="maintenance-schedule"]')).toBeVisible();
    
    // Test device management workflow
    await page.click('[data-testid="device-management"]');
    await expect(page.locator('[data-testid="device-list"]')).toBeVisible();
    
    await page.click('[data-testid="device-1"]');
    await expect(page.locator('[data-testid="device-details"]')).toBeVisible();
    await expect(page.locator('[data-testid="calibration-status"]')).toBeVisible();
  });
});
```

### Accessibility End-to-End Testing

```javascript
// accessibility-e2e.test.js
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility End-to-End Testing', () => {
  test('should be fully keyboard navigable', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Start keyboard navigation
    await page.keyboard.press('Tab');
    
    // Navigate through all interactive elements
    const focusableElements = await page.locator('button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])').all();
    
    for (let i = 0; i < focusableElements.length; i++) {
      const element = focusableElements[i];
      await expect(element).toBeFocused();
      
      // Verify focus is visible
      const focusStyles = await element.evaluate(el => {
        const styles = getComputedStyle(el);
        return {
          outline: styles.outline,
          boxShadow: styles.boxShadow
        };
      });
      
      expect(focusStyles.outline !== 'none' || focusStyles.boxShadow !== 'none').toBeTruthy();
      
      if (i < focusableElements.length - 1) {
        await page.keyboard.press('Tab');
      }
    }
  });

  test('should work with screen readers', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Test ARIA landmarks
    const landmarks = await page.locator('[role="banner"], [role="navigation"], [role="main"], [role="contentinfo"]').all();
    expect(landmarks.length).toBeGreaterThan(0);
    
    // Test heading hierarchy
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    let previousLevel = 0;
    
    for (const heading of headings) {
      const tagName = await heading.evaluate(el => el.tagName.toLowerCase());
      const currentLevel = parseInt(tagName.charAt(1));
      
      // Heading levels should not skip more than one level
      expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
      previousLevel = currentLevel;
    }
    
    // Test form labels
    const inputs = await page.locator('input, select, textarea').all();
    for (const input of inputs) {
      const hasLabel = await input.evaluate(el => {
        const id = el.id;
        const ariaLabel = el.getAttribute('aria-label');
        const ariaLabelledBy = el.getAttribute('aria-labelledby');
        const label = id ? document.querySelector(`label[for="${id}"]`) : null;
        
        return !!(ariaLabel || ariaLabelledBy || label);
      });
      
      expect(hasLabel).toBeTruthy();
    }
  });

  test('should pass automated accessibility tests', async ({ page }) => {
    await page.goto('/dashboard');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should handle high contrast mode', async ({ page }) => {
    // Simulate high contrast mode
    await page.emulateMedia({ colorScheme: 'dark', forcedColors: 'active' });
    
    await page.goto('/dashboard');
    
    // Verify elements are still visible and functional
    await expect(page.locator('[data-testid="main-navigation"]')).toBeVisible();
    await expect(page.locator('[data-testid="content-area"]')).toBeVisible();
    
    // Test interactions still work
    await page.click('[data-testid="menu-button"]');
    await expect(page.locator('[data-testid="dropdown-menu"]')).toBeVisible();
  });
});
```

## Performance Testing Requirements

### Core Web Vitals Testing

```javascript
// performance-e2e.test.js
import { test, expect } from '@playwright/test';

test.describe('Performance Testing', () => {
  test('should meet Core Web Vitals thresholds', async ({ page }) => {
    // Navigate to page and measure performance
    const response = await page.goto('/dashboard', { waitUntil: 'networkidle' });
    
    // Measure Largest Contentful Paint (LCP)
    const lcp = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          resolve(lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
      });
    });
    
    expect(lcp).toBeLessThan(2500); // 2.5 seconds
    
    // Measure First Input Delay (FID) simulation
    await page.click('[data-testid="interactive-element"]');
    
    const fid = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          if (entries.length > 0) {
            resolve(entries[0].processingStart - entries[0].startTime);
          }
        }).observe({ entryTypes: ['first-input'] });
      });
    });
    
    expect(fid).toBeLessThan(100); // 100 milliseconds
    
    // Measure Cumulative Layout Shift (CLS)
    const cls = await page.evaluate(() => {
      return new Promise((resolve) => {
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          resolve(clsValue);
        }).observe({ entryTypes: ['layout-shift'] });
        
        // Resolve after a delay to capture layout shifts
        setTimeout(() => resolve(clsValue), 5000);
      });
    });
    
    expect(cls).toBeLessThan(0.1); // 0.1 threshold
  });

  test('should load efficiently on slow networks', async ({ page, context }) => {
    // Simulate slow 3G network
    await context.route('**/*', route => {
      setTimeout(() => route.continue(), 100); // Add 100ms delay
    });
    
    const startTime = Date.now();
    await page.goto('/dashboard');
    const loadTime = Date.now() - startTime;
    
    // Should load within reasonable time even on slow network
    expect(loadTime).toBeLessThan(10000); // 10 seconds
    
    // Verify critical content is visible
    await expect(page.locator('[data-testid="main-content"]')).toBeVisible();
  });

  test('should handle large datasets efficiently', async ({ page }) => {
    // Navigate to page with large dataset
    await page.goto('/dashboard/analytics?dataset=large');
    
    // Measure rendering performance
    const renderingMetrics = await page.evaluate(() => {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        return entries.map(entry => ({
          name: entry.name,
          duration: entry.duration,
          startTime: entry.startTime
        }));
      });
      
      observer.observe({ entryTypes: ['measure', 'navigation'] });
      
      return performance.getEntriesByType('navigation')[0];
    });
    
    // Verify reasonable loading performance
    expect(renderingMetrics.loadEventEnd - renderingMetrics.loadEventStart).toBeLessThan(3000);
  });
});
```

## Visual Regression Testing

### Storybook Visual Testing

```javascript
// visual-regression.test.js
import { test, expect } from '@playwright/test';

test.describe('Visual Regression Testing', () => {
  test('should match component visual snapshots', async ({ page }) => {
    // Test Button component variations
    await page.goto('/storybook/iframe.html?id=button--primary');
    await expect(page.locator('[data-testid="button"]')).toHaveScreenshot('button-primary.png');
    
    await page.goto('/storybook/iframe.html?id=button--secondary');
    await expect(page.locator('[data-testid="button"]')).toHaveScreenshot('button-secondary.png');
    
    await page.goto('/storybook/iframe.html?id=button--disabled');
    await expect(page.locator('[data-testid="button"]')).toHaveScreenshot('button-disabled.png');
  });

  test('should match dashboard layout snapshots', async ({ page }) => {
    await page.goto('/dashboard/consumer');
    
    // Full page screenshot
    await expect(page).toHaveScreenshot('consumer-dashboard-full.png', { fullPage: true });
    
    // Component-specific screenshots
    await expect(page.locator('[data-testid="water-quality-chart"]')).toHaveScreenshot('water-quality-chart.png');
    await expect(page.locator('[data-testid="alert-panel"]')).toHaveScreenshot('alert-panel.png');
  });

  test('should match responsive design snapshots', async ({ page }) => {
    await page.goto('/dashboard');
    
    // Desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page).toHaveScreenshot('dashboard-desktop.png');
    
    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page).toHaveScreenshot('dashboard-tablet.png');
    
    // Mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page).toHaveScreenshot('dashboard-mobile.png');
  });

  test('should match dark mode snapshots', async ({ page }) => {
    // Enable dark mode
    await page.emulateMedia({ colorScheme: 'dark' });
    
    await page.goto('/dashboard');
    await expect(page).toHaveScreenshot('dashboard-dark-mode.png');
    
    // Test component variations in dark mode
    await page.goto('/storybook/iframe.html?id=button--primary&globals=theme:dark');
    await expect(page.locator('[data-testid="button"]')).toHaveScreenshot('button-primary-dark.png');
  });
});
```

## Test Automation and CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ui-ux-testing.yml
name: UI/UX Testing Pipeline

on:
  pull_request:
    paths:
      - 'frontend/**'
      - '.kiro/specs/aquachain-prd-styleguide/**'
  push:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:unit -- --coverage
      
      - name: Run accessibility tests
        run: npm run test:a11y
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run integration tests
        run: npm run test:integration
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: integration-test-results
          path: test-results/

  e2e-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps ${{ matrix.browser }}
      
      - name: Run E2E tests
        run: npm run test:e2e -- --project=${{ matrix.browser }}
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: e2e-test-results-${{ matrix.browser }}
          path: test-results/

  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build application
        run: npm run build
      
      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli@0.12.x
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}

  visual-regression:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run visual regression tests
        run: npm run test:visual
      
      - name: Upload visual diff artifacts
        uses: actions/upload-artifact@v3
        if: failure()
        with:
          name: visual-regression-diffs
          path: test-results/visual-diffs/
```

## Test Reporting and Metrics

### Test Coverage Requirements

- **Unit Test Coverage**: Minimum 80% for new code, 70% overall
- **Integration Test Coverage**: All critical user flows covered
- **Accessibility Test Coverage**: 100% of interactive components
- **Performance Test Coverage**: All pages and major components
- **Visual Regression Coverage**: All UI components and layouts

### Quality Metrics Dashboard

```javascript
// test-metrics.config.js
module.exports = {
  coverage: {
    statements: 80,
    branches: 75,
    functions: 80,
    lines: 80
  },
  accessibility: {
    wcagLevel: 'AA',
    minimumScore: 95,
    criticalViolations: 0
  },
  performance: {
    lcp: 2500,
    fid: 100,
    cls: 0.1,
    lighthouse: {
      performance: 90,
      accessibility: 95,
      bestPractices: 90
    }
  },
  visualRegression: {
    threshold: 0.2, // 0.2% pixel difference threshold
    failureThreshold: 5 // Maximum 5 failing visual tests
  }
};
```

This comprehensive testing strategy ensures that all UI/UX improvements meet the highest standards for accessibility, performance, and user experience while maintaining code quality and visual consistency across the AquaChain application.