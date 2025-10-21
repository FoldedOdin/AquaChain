import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { toHaveNoViolations } from 'jest-axe';
import {
  AccessibilityTester,
  testComponentAccessibility,
  testKeyboardNavigation,
  testAriaLabels,
  FocusManager,
  prefersReducedMotion,
} from '../accessibility';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Sample components for testing
const AccessibleButton: React.FC<{ 
  children: React.ReactNode; 
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
}> = ({ children, onClick, disabled = false, type = 'button' }) => (
  <button
    type={type}
    onClick={onClick}
    disabled={disabled}
    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
    aria-label={typeof children === 'string' ? children : 'Button'}
  >
    {children}
  </button>
);

const AccessibleForm: React.FC = () => (
  <form>
    <div className="mb-4">
      <label htmlFor="email" className="block text-sm font-medium text-gray-700">
        Email Address
      </label>
      <input
        type="email"
        id="email"
        name="email"
        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md"
        aria-describedby="email-help"
        required
      />
      <p id="email-help" className="mt-1 text-sm text-gray-500">
        We'll never share your email with anyone else.
      </p>
    </div>
    <AccessibleButton type="submit">Submit</AccessibleButton>
  </form>
);

const ModalComponent: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ 
  isOpen, 
  onClose 
}) => {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
    >
      <div className="bg-white p-6 rounded-lg max-w-md w-full">
        <h2 id="modal-title" className="text-xl font-bold mb-4">
          Modal Title
        </h2>
        <p className="mb-4">This is a modal dialog for testing accessibility.</p>
        <div className="flex justify-end space-x-2">
          <AccessibleButton onClick={onClose}>Close</AccessibleButton>
        </div>
      </div>
    </div>
  );
};

describe('AccessibilityTester', () => {
  let tester: AccessibilityTester;

  beforeEach(() => {
    tester = new AccessibilityTester();
  });

  describe('testElement', () => {
    it('should pass accessibility tests for accessible button', async () => {
      const { container } = render(
        <AccessibleButton onClick={jest.fn()}>
          Click me
        </AccessibleButton>
      );

      await expect(tester.testElement(container)).resolves.not.toThrow();
    });

    it('should pass accessibility tests for accessible form', async () => {
      const { container } = render(<AccessibleForm />);

      await expect(tester.testElement(container)).resolves.not.toThrow();
    });
  });

  describe('testKeyboardNavigation', () => {
    it('should validate keyboard navigation for interactive elements', () => {
      const { container } = render(
        <div>
          <AccessibleButton onClick={jest.fn()}>Button 1</AccessibleButton>
          <AccessibleButton onClick={jest.fn()}>Button 2</AccessibleButton>
          <input type="text" placeholder="Text input" />
        </div>
      );

      expect(() => tester.testKeyboardNavigation(container)).not.toThrow();
    });

    it('should handle elements with proper tabindex', () => {
      const { container } = render(
        <div>
          <button tabIndex={0}>Focusable</button>
          <div tabIndex={-1}>Not focusable</div>
        </div>
      );

      expect(() => tester.testKeyboardNavigation(container)).not.toThrow();
    });
  });

  describe('testAriaLabels', () => {
    it('should validate ARIA labels for interactive elements', () => {
      const { container } = render(
        <div>
          <button aria-label="Close dialog">×</button>
          <input aria-labelledby="label-id" />
          <label id="label-id">Input label</label>
        </div>
      );

      expect(() => tester.testAriaLabels(container)).not.toThrow();
    });
  });
});

describe('Utility Functions', () => {
  describe('testComponentAccessibility', () => {
    it('should test component accessibility', async () => {
      const { container } = render(
        <AccessibleButton onClick={jest.fn()}>
          Accessible Button
        </AccessibleButton>
      );

      await expect(testComponentAccessibility(container)).resolves.not.toThrow();
    });
  });

  describe('testKeyboardNavigation', () => {
    it('should test keyboard navigation', () => {
      const { container } = render(
        <div>
          <button>Button 1</button>
          <button>Button 2</button>
        </div>
      );

      expect(() => testKeyboardNavigation(container)).not.toThrow();
    });
  });

  describe('testAriaLabels', () => {
    it('should test ARIA labels', () => {
      const { container } = render(
        <button aria-label="Test button">Click</button>
      );

      expect(() => testAriaLabels(container)).not.toThrow();
    });
  });
});

describe('FocusManager', () => {
  let focusManager: FocusManager;

  beforeEach(() => {
    focusManager = new FocusManager();
  });

  describe('saveFocus and restoreFocus', () => {
    it('should save and restore focus', () => {
      const { container } = render(
        <div>
          <button data-testid="button1">Button 1</button>
          <button data-testid="button2">Button 2</button>
        </div>
      );

      const button1 = screen.getByTestId('button1');
      const button2 = screen.getByTestId('button2');

      // Focus first button and save
      button1.focus();
      expect(document.activeElement).toBe(button1);
      focusManager.saveFocus();

      // Focus second button
      button2.focus();
      expect(document.activeElement).toBe(button2);

      // Restore focus to first button
      focusManager.restoreFocus();
      expect(document.activeElement).toBe(button1);
    });
  });

  describe('trapFocus', () => {
    it('should trap focus within container', async () => {
      const user = userEvent.setup();
      render(
        <div data-testid="modal">
          <button data-testid="first">First</button>
          <button data-testid="middle">Middle</button>
          <button data-testid="last">Last</button>
        </div>
      );

      const modal = screen.getByTestId('modal');
      const firstButton = screen.getByTestId('first');
      const lastButton = screen.getByTestId('last');

      const cleanup = focusManager.trapFocus(modal);

      // Should focus first element initially
      expect(document.activeElement).toBe(firstButton);

      // Tab to last element, then tab again should go to first
      await user.tab();
      await user.tab();
      expect(document.activeElement).toBe(lastButton);

      await user.tab();
      expect(document.activeElement).toBe(firstButton);

      // Shift+Tab from first should go to last
      await user.tab({ shift: true });
      expect(document.activeElement).toBe(lastButton);

      cleanup();
    });
  });
});

describe('Accessibility Utilities', () => {
  describe('prefersReducedMotion', () => {
    it('should detect reduced motion preference', () => {
      // Mock matchMedia to return reduced motion preference
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

      expect(prefersReducedMotion()).toBe(true);
    });

    it('should return false when reduced motion is not preferred', () => {
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(() => ({
          matches: false,
          media: '',
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn(),
        })),
      });

      expect(prefersReducedMotion()).toBe(false);
    });
  });
});

describe('Integration Tests', () => {
  it('should handle modal accessibility correctly', async () => {
    const user = userEvent.setup();

    const TestApp = () => {
      const [modalOpen, setModalOpen] = React.useState(false);

      return (
        <div>
          <AccessibleButton onClick={() => setModalOpen(true)}>
            Open Modal
          </AccessibleButton>
          <ModalComponent 
            isOpen={modalOpen} 
            onClose={() => setModalOpen(false)} 
          />
        </div>
      );
    };

    render(<TestApp />);

    // Open modal
    const openButton = screen.getByText('Open Modal');
    await user.click(openButton);

    // Test modal accessibility
    const modal = screen.getByRole('dialog');
    expect(modal).toBeInTheDocument();
    expect(modal).toHaveAttribute('aria-modal', 'true');
    expect(modal).toHaveAttribute('aria-labelledby', 'modal-title');

    // Test modal content accessibility
    await testComponentAccessibility(modal);

    // Close modal
    const closeButton = screen.getByText('Close');
    await user.click(closeButton);

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});