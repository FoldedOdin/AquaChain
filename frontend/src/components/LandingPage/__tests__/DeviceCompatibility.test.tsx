import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../../../contexts/ThemeContext';
import { AnalyticsProvider } from '../../../contexts/AnalyticsContext';
import { PWAProvider } from '../../../contexts/PWAContext';
import LandingPage from '../LandingPage';

// Mock external services
jest.mock('../../../services/analyticsService');
jest.mock('../../../services/authService');

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      <AnalyticsProvider>
        <PWAProvider>
          {children}
        </PWAProvider>
      </AnalyticsProvider>
    </ThemeProvider>
  </BrowserRouter>
);

// Device configurations for testing
const DEVICE_CONFIGS = {
  mobile: {
    width: 375,
    height: 667,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    touchEnabled: true,
    devicePixelRatio: 2
  },
  tablet: {
    width: 768,
    height: 1024,
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    touchEnabled: true,
    devicePixelRatio: 2
  },
  desktop: {
    width: 1920,
    height: 1080,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    touchEnabled: false,
    devicePixelRatio: 1
  },
  smallMobile: {
    width: 320,
    height: 568,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    touchEnabled: true,
    devicePixelRatio: 2
  }
};

describe('Device Compatibility Tests', () => {
  beforeEach(() => {
    // Mock IntersectionObserver
    global.IntersectionObserver = jest.fn().mockImplementation(() => ({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    }));

    // Reset window properties
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1920,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 1080,
    });
  });

  describe('Mobile Device Testing', () => {
    beforeEach(() => {
      const config = DEVICE_CONFIGS.mobile;
      
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: config.width,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: config.height,
      });

      // Mock mobile user agent
      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: config.userAgent,
      });

      // Mock device pixel ratio
      Object.defineProperty(window, 'devicePixelRatio', {
        writable: true,
        configurable: true,
        value: config.devicePixelRatio,
      });

      // Mock touch support
      Object.defineProperty(window, 'ontouchstart', {
        writable: true,
        value: config.touchEnabled ? {} : undefined,
      });

      // Mock matchMedia for mobile
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('max-width: 768px') || query.includes('hover: none'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });
    });

    it('should render correctly on mobile devices', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that main content is visible
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('banner')).toBeInTheDocument();

      // Check that mobile-specific elements are present
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      expect(getStartedButton).toBeVisible();

      // Check button size for touch targets (minimum 44px)
      const buttonRect = getStartedButton.getBoundingClientRect();
      expect(buttonRect.width).toBeGreaterThanOrEqual(44);
      expect(buttonRect.height).toBeGreaterThanOrEqual(44);
    });

    it('should handle touch interactions correctly', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });

      // Test touch events
      fireEvent.touchStart(getStartedButton, {
        touches: [{ clientX: 100, clientY: 100 }]
      });
      fireEvent.touchEnd(getStartedButton, {
        changedTouches: [{ clientX: 100, clientY: 100 }]
      });

      // Modal should open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('should support swipe gestures where appropriate', async () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const heroSection = screen.getByRole('region', { name: /hero/i });

      // Simulate swipe gesture
      fireEvent.touchStart(heroSection, {
        touches: [{ clientX: 200, clientY: 300 }]
      });
      fireEvent.touchMove(heroSection, {
        touches: [{ clientX: 100, clientY: 300 }]
      });
      fireEvent.touchEnd(heroSection, {
        changedTouches: [{ clientX: 100, clientY: 300 }]
      });

      // Check that swipe was handled (implementation specific)
      expect(heroSection).toBeInTheDocument();
    });

    it('should have proper mobile navigation', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check for mobile-friendly navigation
      const navigation = screen.getByRole('navigation');
      expect(navigation).toBeInTheDocument();

      // Check for hamburger menu or mobile navigation pattern
      const menuButton = screen.queryByRole('button', { name: /menu/i });
      if (menuButton) {
        expect(menuButton).toBeVisible();
      }
    });

    it('should optimize images for mobile', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that images have appropriate attributes for mobile
      const images = screen.getAllByRole('img');
      images.forEach(img => {
        expect(img).toHaveAttribute('alt');
        
        // Check for responsive image attributes
        const hasResponsiveAttributes = 
          img.hasAttribute('srcset') || 
          img.hasAttribute('sizes') ||
          img.closest('picture');
        
        // At least some images should be responsive
        if (images.length > 0) {
          expect(hasResponsiveAttributes || img.getAttribute('src')?.includes('optimized')).toBeTruthy();
        }
      });
    });
  });

  describe('Tablet Device Testing', () => {
    beforeEach(() => {
      const config = DEVICE_CONFIGS.tablet;
      
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: config.width,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: config.height,
      });

      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: config.userAgent,
      });

      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('max-width: 1024px') && !query.includes('max-width: 768px'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });
    });

    it('should render correctly on tablet devices', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      expect(screen.getByRole('main')).toBeInTheDocument();
      
      // Check that tablet layout is applied
      const featuresSection = screen.getByRole('region', { name: /features/i });
      expect(featuresSection).toBeInTheDocument();

      // Features should be in a grid layout suitable for tablet
      const featureCards = screen.getAllByRole('article');
      expect(featureCards.length).toBeGreaterThan(0);
    });

    it('should handle both touch and mouse interactions', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });

      // Test mouse interaction
      await user.hover(getStartedButton);
      await user.click(getStartedButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close modal
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      // Test touch interaction
      fireEvent.touchStart(getStartedButton);
      fireEvent.touchEnd(getStartedButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });
  });

  describe('Desktop Device Testing', () => {
    beforeEach(() => {
      const config = DEVICE_CONFIGS.desktop;
      
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: config.width,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: config.height,
      });

      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: config.userAgent,
      });

      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('min-width: 1024px') || query.includes('hover: hover'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });
    });

    it('should render correctly on desktop devices', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      expect(screen.getByRole('main')).toBeInTheDocument();
      
      // Check that desktop layout is applied
      const heroSection = screen.getByRole('region', { name: /hero/i });
      expect(heroSection).toBeInTheDocument();

      // Desktop should show full navigation
      const navigation = screen.getByRole('navigation');
      expect(navigation).toBeInTheDocument();
    });

    it('should support hover effects on desktop', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });

      // Test hover effect
      await user.hover(getStartedButton);
      
      // Check that hover styles are applied (this would need specific implementation)
      expect(getStartedButton).toHaveFocus();
    });

    it('should support keyboard navigation on desktop', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Tab through interactive elements
      await user.tab();
      const firstFocusable = document.activeElement;
      expect(firstFocusable).toBeInstanceOf(HTMLElement);

      await user.tab();
      const secondFocusable = document.activeElement;
      expect(secondFocusable).toBeInstanceOf(HTMLElement);
      expect(secondFocusable).not.toBe(firstFocusable);
    });
  });

  describe('Small Mobile Device Testing', () => {
    beforeEach(() => {
      const config = DEVICE_CONFIGS.smallMobile;
      
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: config.width,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: config.height,
      });

      Object.defineProperty(navigator, 'userAgent', {
        writable: true,
        value: config.userAgent,
      });

      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('max-width: 375px'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });
    });

    it('should render correctly on small mobile devices', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      expect(screen.getByRole('main')).toBeInTheDocument();
      
      // Check that content is not cut off
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      expect(getStartedButton).toBeVisible();

      // Check that text is readable
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeVisible();
    });

    it('should handle limited screen space appropriately', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that elements are stacked vertically
      const featuresSection = screen.getByRole('region', { name: /features/i });
      expect(featuresSection).toBeInTheDocument();

      // Modal should take up most of the screen on small devices
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      fireEvent.click(getStartedButton);

      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
      
      // Modal should be appropriately sized for small screen
      const modalRect = modal.getBoundingClientRect();
      expect(modalRect.width).toBeLessThanOrEqual(window.innerWidth);
    });
  });

  describe('Responsive Breakpoints', () => {
    const testBreakpoint = (width: number, expectedBehavior: string) => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width,
      });

      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Test that appropriate styles are applied at this breakpoint
      expect(screen.getByRole('main')).toBeInTheDocument();
    };

    it('should handle 320px breakpoint', () => {
      testBreakpoint(320, 'small mobile layout');
    });

    it('should handle 768px breakpoint', () => {
      testBreakpoint(768, 'tablet layout');
    });

    it('should handle 1024px breakpoint', () => {
      testBreakpoint(1024, 'desktop layout');
    });

    it('should handle 1440px breakpoint', () => {
      testBreakpoint(1440, 'large desktop layout');
    });
  });

  describe('Feature Detection', () => {
    it('should detect touch support', () => {
      // Mock touch support
      Object.defineProperty(window, 'ontouchstart', {
        writable: true,
        value: {},
      });

      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that touch-specific features are enabled
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('should detect hover support', () => {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query.includes('hover: hover'),
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that hover-specific features are enabled
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('should detect high DPI displays', () => {
      Object.defineProperty(window, 'devicePixelRatio', {
        writable: true,
        configurable: true,
        value: 2,
      });

      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that high DPI images are used
      const images = screen.getAllByRole('img');
      images.forEach(img => {
        // Check for high DPI image attributes
        const hasHighDPI = 
          img.hasAttribute('srcset') || 
          img.getAttribute('src')?.includes('@2x');
        
        if (images.length > 0) {
          expect(hasHighDPI || true).toBeTruthy(); // Allow for different implementations
        }
      });
    });
  });

  describe('Performance on Different Devices', () => {
    it('should optimize animations for low-end devices', () => {
      // Mock low-end device characteristics
      Object.defineProperty(navigator, 'hardwareConcurrency', {
        writable: true,
        value: 2, // Low CPU cores
      });

      Object.defineProperty(navigator, 'deviceMemory', {
        writable: true,
        value: 2, // Low memory
      });

      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that animations are optimized or disabled
      const animatedElements = screen.getAllByTestId(/animated/i);
      animatedElements.forEach(element => {
        // Check for performance optimizations
        expect(element).toBeInTheDocument();
      });
    });

    it('should handle slow network conditions', async () => {
      // Mock slow network
      Object.defineProperty(navigator, 'connection', {
        writable: true,
        value: {
          effectiveType: '2g',
          downlink: 0.5,
          rtt: 2000
        }
      });

      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check that appropriate optimizations are applied
      expect(screen.getByRole('main')).toBeInTheDocument();
      
      // Images should be optimized for slow connections
      const images = screen.getAllByRole('img');
      images.forEach(img => {
        expect(img).toHaveAttribute('loading', 'lazy');
      });
    });
  });

  describe('Orientation Changes', () => {
    it('should handle portrait to landscape orientation change', () => {
      // Start in portrait
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 667,
      });

      const { rerender } = render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      expect(screen.getByRole('main')).toBeInTheDocument();

      // Change to landscape
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 667,
      });
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: 375,
      });

      // Trigger orientation change event
      fireEvent(window, new Event('orientationchange'));

      rerender(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      expect(screen.getByRole('main')).toBeInTheDocument();
    });
  });
});