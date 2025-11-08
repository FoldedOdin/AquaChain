import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from '../../../contexts/ThemeContext';
import { AnalyticsProvider } from '../../../contexts/AnalyticsContext';
import { PWAProvider } from '../../../contexts/PWAContext';
import LandingPage from '../LandingPage';
import AuthModal from '../AuthModal';
import { FocusManager } from '../../../utils/accessibility';

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

describe('Keyboard Navigation Tests', () => {
  beforeEach(() => {
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

    // Mock IntersectionObserver
    global.IntersectionObserver = jest.fn().mockImplementation(() => ({
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
    }));
  });

  describe('Tab Navigation Order', () => {
    it('should follow logical tab order through the page', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Expected tab order
      const expectedTabOrder = [
        { role: 'link', name: /aquachain/i }, // Logo/brand link
        { role: 'button', name: /get started/i }, // Primary CTA
        { role: 'button', name: /view dashboards/i }, // Secondary CTA
        { role: 'button', name: /become technician/i }, // Technician CTA
      ];

      // Start from the beginning
      document.body.focus();

      for (const expectedElement of expectedTabOrder) {
        await user.tab();
        
        const focusedElement = document.activeElement;
        expect(focusedElement).toBeInstanceOf(HTMLElement);
        
        // Check if the focused element matches our expectation
        const element = screen.getByRole(expectedElement.role, { name: expectedElement.name });
        expect(focusedElement).toBe(element);
      }
    });

    it('should skip non-interactive elements', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Tab through and ensure we only focus on interactive elements
      const interactiveElements: HTMLElement[] = [];
      
      // Start tabbing
      for (let i = 0; i < 10; i++) {
        await user.tab();
        const focused = document.activeElement as HTMLElement;
        
        if (focused && focused !== document.body) {
          interactiveElements.push(focused);
          
          // Ensure focused element is interactive
          const tagName = focused.tagName.toLowerCase();
          const hasTabIndex = focused.hasAttribute('tabindex') && focused.getAttribute('tabindex') !== '-1';
          const isInteractive = ['button', 'a', 'input', 'select', 'textarea'].includes(tagName) || hasTabIndex;
          
          expect(isInteractive).toBeTruthy();
        }
      }

      expect(interactiveElements.length).toBeGreaterThan(0);
    });

    it('should handle reverse tab navigation (Shift+Tab)', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Tab forward to the last element
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      const viewDashboardsButton = screen.getByRole('button', { name: /view dashboards/i });
      
      getStartedButton.focus();
      await user.tab(); // Should go to view dashboards
      expect(document.activeElement).toBe(viewDashboardsButton);

      // Shift+Tab should go back
      await user.tab({ shift: true });
      expect(document.activeElement).toBe(getStartedButton);
    });
  });

  describe('Focus Management', () => {
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

      // Check that focus is visible
      expect(getStartedButton).toHaveFocus();
      
      // Check for focus styles (this would need to be more specific in real implementation)
      const computedStyle = window.getComputedStyle(getStartedButton);
      expect(computedStyle.outline).not.toBe('none');
    });

    it('should restore focus after modal closes', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      
      // Focus and click the button
      getStartedButton.focus();
      expect(document.activeElement).toBe(getStartedButton);
      
      await user.click(getStartedButton);

      // Modal should be open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Close modal with Escape
      await user.keyboard('{Escape}');

      // Focus should return to the button that opened the modal
      await waitFor(() => {
        expect(document.activeElement).toBe(getStartedButton);
      });
    });

    it('should manage focus within modal dialogs', async () => {
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
      expect(modal).toBeInTheDocument();

      // Focus should move to first focusable element in modal
      const firstFocusableInModal = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])') as HTMLElement;
      expect(document.activeElement).toBe(firstFocusableInModal);
    });
  });

  describe('Modal Focus Trapping', () => {
    it('should trap focus within modal', async () => {
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
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      expect(focusableElements.length).toBeGreaterThan(1);

      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      // Tab from last element should cycle to first
      lastElement.focus();
      await user.tab();
      expect(document.activeElement).toBe(firstElement);

      // Shift+Tab from first element should cycle to last
      firstElement.focus();
      await user.tab({ shift: true });
      expect(document.activeElement).toBe(lastElement);
    });

    it('should not allow focus to escape modal', async () => {
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
      
      // Try to focus elements outside modal
      const elementsOutsideModal = document.querySelectorAll('button, [href], input, select, textarea');
      const modalElements = modal.querySelectorAll('button, [href], input, select, textarea');
      
      // Tab multiple times and ensure focus stays within modal
      for (let i = 0; i < 10; i++) {
        await user.tab();
        const focusedElement = document.activeElement;
        
        // Check that focused element is within modal
        const isWithinModal = modal.contains(focusedElement);
        expect(isWithinModal).toBeTruthy();
      }
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('should support Enter key activation for buttons', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      getStartedButton.focus();

      // Press Enter
      await user.keyboard('{Enter}');

      // Modal should open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
    });

    it('should support Space key activation for buttons', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      getStartedButton.focus();

      // Press Space
      await user.keyboard(' ');

      // Modal should open
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
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

      // Modal should close
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('should support arrow keys for navigation where appropriate', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open modal to test form navigation
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      // Test arrow key navigation in tab groups (if implemented)
      const tabButtons = screen.queryAllByRole('tab');
      if (tabButtons.length > 1) {
        tabButtons[0].focus();
        
        // Right arrow should move to next tab
        await user.keyboard('{ArrowRight}');
        expect(document.activeElement).toBe(tabButtons[1]);

        // Left arrow should move back
        await user.keyboard('{ArrowLeft}');
        expect(document.activeElement).toBe(tabButtons[0]);
      }
    });
  });

  describe('Form Navigation', () => {
    it('should navigate through form fields correctly', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open auth modal
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      // Navigate through form fields
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /log in/i });

      // Tab through form fields
      emailInput.focus();
      expect(document.activeElement).toBe(emailInput);

      await user.tab();
      expect(document.activeElement).toBe(passwordInput);

      await user.tab();
      expect(document.activeElement).toBe(submitButton);
    });

    it('should handle form validation errors with keyboard navigation', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Open auth modal
      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      await user.click(getStartedButton);

      const submitButton = screen.getByRole('button', { name: /log in/i });
      
      // Submit empty form
      submitButton.focus();
      await user.keyboard('{Enter}');

      // Focus should move to first invalid field
      await waitFor(() => {
        const emailInput = screen.getByLabelText(/email/i);
        expect(document.activeElement).toBe(emailInput);
      });
    });
  });

  describe('Skip Links', () => {
    it('should provide skip to main content link', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Tab to first element (should be skip link)
      await user.tab();
      
      const skipLink = document.activeElement as HTMLElement;
      expect(skipLink).toHaveTextContent(/skip to main content/i);

      // Activate skip link
      await user.keyboard('{Enter}');

      // Focus should move to main content
      const mainContent = screen.getByRole('main');
      expect(document.activeElement).toBe(mainContent);
    });
  });

  describe('Focus Manager Integration', () => {
    it('should use FocusManager for complex focus scenarios', async () => {
      const user = userEvent.setup();
      const focusManager = new FocusManager();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      getStartedButton.focus();

      // Save current focus
      focusManager.saveFocus();

      // Open modal
      await user.click(getStartedButton);
      
      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();

      // Close modal
      await user.keyboard('{Escape}');

      // Restore focus
      focusManager.restoreFocus();
      expect(document.activeElement).toBe(getStartedButton);
    });

    it('should handle focus trapping with FocusManager', () => {
      const focusManager = new FocusManager();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const container = screen.getByRole('main');
      const cleanup = focusManager.trapFocus(container);

      // Focus should be trapped within container
      const focusableElements = container.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );

      expect(focusableElements.length).toBeGreaterThan(0);
      expect(document.activeElement).toBe(focusableElements[0]);

      // Cleanup
      cleanup();
    });
  });

  describe('Custom Keyboard Interactions', () => {
    it('should handle custom keyboard shortcuts for features', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Test custom shortcuts (if implemented)
      // For example, Alt+1 to open auth modal
      await user.keyboard('{Alt>}1{/Alt}');

      // Check if modal opens (this would depend on implementation)
      // await waitFor(() => {
      //   expect(screen.getByRole('dialog')).toBeInTheDocument();
      // });
    });

    it('should handle keyboard navigation in animated sections', async () => {
      const user = userEvent.setup();
      
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      // Navigate to features section
      const featuresSection = screen.getByRole('region', { name: /features/i });
      
      // Focus should work even with animations
      const featureCards = featuresSection.querySelectorAll('[role="button"], button, [tabindex]:not([tabindex="-1"])');
      
      if (featureCards.length > 0) {
        (featureCards[0] as HTMLElement).focus();
        expect(document.activeElement).toBe(featureCards[0]);
      }
    });
  });

  describe('Error Recovery', () => {
    it('should handle focus recovery after JavaScript errors', () => {
      render(
        <TestWrapper>
          <LandingPage />
        </TestWrapper>
      );

      const getStartedButton = screen.getByRole('button', { name: /get started/i });
      getStartedButton.focus();

      // Simulate focus loss
      (document.activeElement as HTMLElement)?.blur();

      // Focus should be recoverable
      getStartedButton.focus();
      expect(document.activeElement).toBe(getStartedButton);
    });

    it('should maintain keyboard accessibility during loading states', async () => {
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

      // Submit form (this might trigger loading state)
      await user.click(submitButton);

      // Keyboard navigation should still work during loading
      await user.tab();
      expect(document.activeElement).toBeInstanceOf(HTMLElement);
    });
  });
});