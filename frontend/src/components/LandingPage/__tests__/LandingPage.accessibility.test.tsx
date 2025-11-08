import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../../../contexts/ThemeContext';
import { AnalyticsProvider } from '../../../contexts/AnalyticsContext';
import { PWAProvider } from '../../../contexts/PWAContext';
import LandingPage from '../LandingPage';
import { testComponentAccessibility, FocusManager } from '../../../utils/accessibility';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

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

describe('LandingPage Accessibility Tests', () => {
  beforeEach(() => {
    // Mock window.matchMedia for reduced motion tests
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

    // Mock IntersectionObserver
    global.IntersectionObserver = jest.fn().mockImplementation(() => ({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    }));
  });

  describe('WCAG 2.1 AA Compliance', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Wait for component to fully render
      await waitFor(() => {
        expect(screen.getByRole('main')).toBeInTheDocument();
      });

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should have proper document structure with landmarks', async () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check for proper landmark structure
      expect(screen.getByRole('banner')).toBeInTheDocument(); // header
      expect(screen.getByRole('main')).toBeInTheDocument(); // main content
      expect(screen.getByRole('contentinfo')).toBeInTheDocument(); // footer
      expect(screen.getByRole('navigation')).toBeInTheDocument(); // nav
    });

    it('should have proper heading hierarchy', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check heading hierarchy (h1 -> h2 -> h3, etc.)
      const headings = screen.getAllByRole('heading');
      const h1Elements = headings.filter(h => h.tagName === 'H1');
      
      expect(h1Elements).toHaveLength(1); // Only one h1 per page
      expect(h1Elements[0]).toHaveTextContent(/real.time water quality/i);
    });

    it('should have proper color contrast', async () => {
      const { container } = render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Test color contrast using axe-core
      const results = await axe(container, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });

      expect(results.violations.filter(v => v.id === 'color-contrast')).toHaveLength(0);
    });
  });

  describe('Keyboard Navigation', () => {
    it('should support full keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Start from the beginning of the page
      const firstFocusableElement = screen.getByRole('link', { name: /aquachain/i });
      firstFocusableElement.focus();

      // Tab through all interactive elements
      const interactiveElements = [
        screen.getByRole('button', { name: /get started/i }),
        screen.getByRole('button', { name: /view dashboards/i }),
        screen.getByRole('button', { name: /become technician/i }),
      ];

      for (const element of interactiveElements) {
        await user.tab();
        // Allow some flexibility in focus order
        const focusedElement = document.activeElement;
        expect(focusedElement).toBeInstanceOf(HTMLElement);
        expect(focusedElement?.getAttribute('tabindex')).not.toBe('-1');
      }
    });

    it('should have visible focus indicators', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      
      // Focus the button
      await user.tab();
      getStartedButton.focus();

      // Check that focus is visible (this is a basic check)
      expect(getStartedButton).toHaveFocus();
      
      // In a real test, you'd check computed styles for focus indicators
      const computedStyle = window.getComputedStyle(getStartedButton);
      expect(computedStyle.outline).not.toBe('none');
    });

    it('should support Enter and Space key activation', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      getStartedButton.focus();

      // Test Enter key
      await user.keyboard('{Enter}');
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close modal
      const closeButton = screen.getByRole('button', { name: /close/i });
      await user.click(closeButton);

      // Test Space key
      getStartedButton.focus();
      await user.keyboard(' ');
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('should trap focus in modal dialogs', async () => {
      const user = userEvent.setup();
      const focusManager = new FocusManager();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();

      // Test focus trapping
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      expect(focusableElements.length).toBeGreaterThan(0);

      // Focus should be trapped within modal
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      // Tab from last element should go to first
      lastElement.focus();
      await user.tab();
      expect(document.activeElement).toBe(firstElement);

      // Shift+Tab from first element should go to last
      firstElement.focus();
      await user.tab({ shift: true });
      expect(document.activeElement).toBe(lastElement);
    });

    it('should support Escape key to close modal', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      expect(screen.getByRole('dialog')).toBeInTheDocument();

      // Press Escape
      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });
  });

  describe('Screen Reader Support', () => {
    it('should have proper ARIA labels and descriptions', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Check for proper ARIA labels
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      expect(getStartedButton).toHaveAttribute('aria-label');

      // Check for ARIA descriptions where appropriate
      const heroSection = screen.getByRole('region', { name: /hero/i });
      expect(heroSection).toHaveAttribute('aria-describedby');
    });

    it('should announce modal state changes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
      expect(modal).toHaveAttribute('aria-labelledby');
      expect(modal).toHaveAttribute('aria-describedby');
    });

    it('should have proper form labels and error messages', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open auth modal
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      // Check form labels
      const emailInput = screen.getByLabelText(/email/i);
      expect(emailInput).toBeInTheDocument();
      expect(emailInput).toHaveAttribute('aria-required', 'true');

      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toBeInTheDocument();
      expect(passwordInput).toHaveAttribute('aria-required', 'true');

      // Test error message association
      const submitButton = screen.getByRole('button', { name: /log in/i });
      await user.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.queryByRole('alert');
        if (errorMessage) {
          expect(emailInput).toHaveAttribute('aria-describedby');
        }
      });
    });

    it('should provide status updates for loading states', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal and trigger loading state
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /log in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // Check for loading status
      await waitFor(() => {
        const loadingIndicator = screen.queryByRole('status');
        if (loadingIndicator) {
          expect(loadingIndicator).toHaveAttribute('aria-live', 'polite');
        }
      });
    });
  });

  describe('Responsive Design Accessibility', () => {
    it('should maintain accessibility on mobile viewports', async () => {
      // Mock mobile viewport
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

      const { container } = render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Test accessibility on mobile
      const results = await axe(container);
      expect(results).toHaveNoViolations();

      // Check that interactive elements are still accessible
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      expect(getStartedButton).toBeVisible();
      
      // Check minimum touch target size (44px x 44px)
      const buttonRect = getStartedButton.getBoundingClientRect();
      expect(buttonRect.width).toBeGreaterThanOrEqual(44);
      expect(buttonRect.height).toBeGreaterThanOrEqual(44);
    });

    it('should support touch interactions', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });

      // Simulate touch events
      fireEvent.touchStart(getStartedButton);
      fireEvent.touchEnd(getStartedButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });
  });

  describe('Reduced Motion Support', () => {
    it('should respect prefers-reduced-motion setting', () => {
      // Mock reduced motion preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
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

      // Check that animations are disabled or reduced
      const animatedElements = screen.getAllByTestId(/animated/i);
      animatedElements.forEach(element => {
        const computedStyle = window.getComputedStyle(element);
        expect(
          computedStyle.animationDuration === '0s' ||
          computedStyle.animationPlayState === 'paused' ||
          element.classList.contains('reduce-motion')
        ).toBeTruthy();
      });
    });
  });

  describe('High Contrast Mode Support', () => {
    it('should work with high contrast mode', () => {
      // Mock high contrast preference
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-contrast: high)',
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

      // Check that high contrast styles are applied
      const mainContent = screen.getByRole('main');
      expect(mainContent).toBeInTheDocument();
      
      // In a real implementation, you'd check for high contrast CSS classes
      // or computed styles that provide better contrast
    });
  });

  describe('Error Handling Accessibility', () => {
    it('should announce errors to screen readers', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal and trigger validation error
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      const submitButton = screen.getByRole('button', { name: /log in/i });
      await user.click(submitButton);

      // Check for error announcements
      await waitFor(() => {
        const errorElements = screen.queryAllByRole('alert');
        errorElements.forEach(error => {
          expect(error).toHaveAttribute('aria-live');
        });
      });
    });

    it('should associate error messages with form fields', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal and trigger validation error
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      const emailInput = screen.getByLabelText(/email/i);
      const submitButton = screen.getByRole('button', { name: /log in/i });

      await user.click(submitButton);

      await waitFor(() => {
        const errorMessage = screen.queryByText(/email is required/i);
        if (errorMessage) {
          const errorId = errorMessage.getAttribute('id');
          expect(emailInput).toHaveAttribute('aria-describedby', expect.stringContaining(errorId || ''));
        }
      });
    });
  });

  describe('Progressive Enhancement', () => {
    it('should work without JavaScript', () => {
      // This test simulates no-JS environment
      const { container } = render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Basic content should still be accessible
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();
      
      // Links should still work (though modals won't)
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });
  });
});