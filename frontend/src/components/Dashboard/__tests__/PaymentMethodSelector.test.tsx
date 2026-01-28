/**
 * PaymentMethodSelector Component Tests
 * 
 * Tests payment method selection and routing logic, UI rendering, and accessibility features.
 * Requirements: 1.1, 1.4
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import PaymentMethodSelector from '../PaymentMethodSelector';
import { PaymentMethod } from '../../../types/ordering';

describe('PaymentMethodSelector Component', () => {
  const mockOnMethodSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the component with header and payment options', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      // Check header
      expect(screen.getByText('Choose Payment Method')).toBeInTheDocument();
      expect(screen.getByText('Select how you\'d like to pay for your water quality device')).toBeInTheDocument();
      
      // Check payment method options
      expect(screen.getByText('Cash on Delivery')).toBeInTheDocument();
      expect(screen.getByText('Online Payment')).toBeInTheDocument();
    });

    it('renders payment method descriptions correctly', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      expect(screen.getByText('Pay when the device is delivered to your location. No advance payment required.')).toBeInTheDocument();
      expect(screen.getByText('Pay securely online using UPI, cards, or net banking via Razorpay.')).toBeInTheDocument();
    });

    it('renders payment method icons', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      // Check for Lucide icons (they render as SVG elements)
      const icons = screen.getAllByRole('radio').map(button => 
        button.querySelector('svg')
      ).filter(Boolean);
      
      expect(icons).toHaveLength(2); // Two payment method buttons should have icons
    });

    it('renders additional info for each payment method', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      // COD additional info
      expect(screen.getByText(/You'll have a 10-second confirmation window/)).toBeInTheDocument();
      
      // Online payment additional info
      expect(screen.getByText(/Powered by Razorpay with 256-bit SSL encryption/)).toBeInTheDocument();
    });
  });

  describe('Payment Method Selection', () => {
    it('calls onMethodSelect when COD is clicked', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      expect(mockOnMethodSelect).toHaveBeenCalledWith('COD');
      expect(mockOnMethodSelect).toHaveBeenCalledTimes(1);
    });

    it('calls onMethodSelect when Online Payment is clicked', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const onlineButton = screen.getByRole('radio', { name: /online payment/i });
      await userEvent.click(onlineButton);
      
      expect(mockOnMethodSelect).toHaveBeenCalledWith('ONLINE');
      expect(mockOnMethodSelect).toHaveBeenCalledTimes(1);
    });

    it('updates visual state when a method is selected', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      // Check for selection indicator (CheckCircle icon)
      await waitFor(() => {
        expect(codButton.querySelector('svg[class*="text-cyan-500"]')).toBeInTheDocument();
      });
      
      // Check for selected styling
      expect(codButton).toHaveClass('border-cyan-500', 'bg-cyan-50');
    });

    it('shows selection status message when method is selected', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      await waitFor(() => {
        expect(screen.getByText('Cash on Delivery selected')).toBeInTheDocument();
        expect(screen.getByText('Click "Continue" to proceed with your selected payment method.')).toBeInTheDocument();
      });
    });

    it('can switch between payment methods', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      // Select COD first
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      expect(mockOnMethodSelect).toHaveBeenCalledWith('COD');
      
      // Then select Online Payment
      const onlineButton = screen.getByRole('radio', { name: /online payment/i });
      await userEvent.click(onlineButton);
      
      expect(mockOnMethodSelect).toHaveBeenCalledWith('ONLINE');
      expect(mockOnMethodSelect).toHaveBeenCalledTimes(2);
      
      // Check that Online Payment is now selected
      await waitFor(() => {
        expect(screen.getByText('Online Payment selected')).toBeInTheDocument();
      });
    });
  });

  describe('Disabled State', () => {
    it('renders disabled state correctly', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} disabled={true} />);
      
      const buttons = screen.getAllByRole('radio');
      buttons.forEach(button => {
        expect(button).toBeDisabled();
        expect(button).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
      });
    });

    it('does not call onMethodSelect when disabled', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} disabled={true} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      expect(mockOnMethodSelect).not.toHaveBeenCalled();
    });

    it('does not show hover effects when disabled', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} disabled={true} />);
      
      const buttons = screen.getAllByRole('radio');
      buttons.forEach(button => {
        expect(button).toHaveClass('disabled:opacity-50');
      });
    });
  });

  describe('Accessibility Features', () => {
    it('has proper ARIA attributes', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const buttons = screen.getAllByRole('radio');
      expect(buttons).toHaveLength(2);
      
      buttons.forEach(button => {
        expect(button).toHaveAttribute('aria-pressed', 'false');
        expect(button).toHaveAttribute('aria-describedby');
        expect(button).toHaveAttribute('tabIndex', '0');
      });
    });

    it('updates aria-pressed when method is selected', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      await waitFor(() => {
        expect(codButton).toHaveAttribute('aria-pressed', 'true');
      });
    });

    it('has proper focus management', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      
      // Focus the button
      codButton.focus();
      expect(codButton).toHaveFocus();
      
      // Should have focus ring styles
      expect(codButton).toHaveClass('focus:outline-none', 'focus:ring-2', 'focus:ring-cyan-500');
    });

    it('supports keyboard navigation', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      
      // Focus and press Enter
      codButton.focus();
      await userEvent.keyboard('{Enter}');
      
      expect(mockOnMethodSelect).toHaveBeenCalledWith('COD');
    });

    it('supports space key activation', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const onlineButton = screen.getByRole('radio', { name: /online payment/i });
      
      // Focus and press Space
      onlineButton.focus();
      await userEvent.keyboard(' ');
      
      expect(mockOnMethodSelect).toHaveBeenCalledWith('ONLINE');
    });

    it('has screen reader announcements', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      // Check for aria-live region
      await waitFor(() => {
        const liveRegion = screen.getByText('Cash on Delivery payment method selected');
        expect(liveRegion.closest('[aria-live="polite"]')).toBeInTheDocument();
      });
    });

    it('has proper describedby associations', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      const onlineButton = screen.getByRole('radio', { name: /online payment/i });
      
      // Check that buttons are described by their description elements
      expect(codButton).toHaveAttribute('aria-describedby', 'COD-description');
      expect(onlineButton).toHaveAttribute('aria-describedby', 'ONLINE-description');
      
      // Check that description elements exist
      expect(document.getElementById('COD-description')).toBeInTheDocument();
      expect(document.getElementById('ONLINE-description')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('has responsive grid classes', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const gridContainer = screen.getAllByRole('radio')[0].parentElement;
      expect(gridContainer).toHaveClass('grid', 'gap-4', 'md:grid-cols-2');
    });

    it('maintains proper spacing on different screen sizes', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const buttons = screen.getAllByRole('radio');
      buttons.forEach(button => {
        expect(button).toHaveClass('p-6', 'rounded-xl');
      });
    });
  });

  describe('Visual Feedback', () => {
    it('shows hover effects on non-disabled buttons', () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const buttons = screen.getAllByRole('radio');
      buttons.forEach(button => {
        expect(button).toHaveClass('hover:border-gray-300', 'hover:shadow-sm');
      });
    });

    it('shows different styles for selected vs unselected states', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      const onlineButton = screen.getByRole('radio', { name: /online payment/i });
      
      // Initially both should be unselected
      expect(codButton).toHaveClass('border-gray-200', 'bg-white');
      expect(onlineButton).toHaveClass('border-gray-200', 'bg-white');
      
      // Select COD
      await userEvent.click(codButton);
      
      await waitFor(() => {
        expect(codButton).toHaveClass('border-cyan-500', 'bg-cyan-50');
        expect(onlineButton).toHaveClass('border-gray-200', 'bg-white');
      });
    });

    it('shows selection indicator only for selected method', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      await userEvent.click(codButton);
      
      await waitFor(() => {
        // Should have CheckCircle icons (selection indicators)
        const checkIcons = codButton.querySelectorAll('svg[class*="text-cyan-500"]');
        expect(checkIcons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Error Handling', () => {
    it('handles missing onMethodSelect prop gracefully', () => {
      // This should not throw an error
      expect(() => {
        render(<PaymentMethodSelector onMethodSelect={undefined as any} />);
      }).not.toThrow();
    });

    it('handles rapid clicking without issues', async () => {
      render(<PaymentMethodSelector onMethodSelect={mockOnMethodSelect} />);
      
      const codButton = screen.getByRole('radio', { name: /cash on delivery/i });
      
      // Rapid clicks
      await userEvent.click(codButton);
      await userEvent.click(codButton);
      await userEvent.click(codButton);
      
      // Should still work correctly
      expect(mockOnMethodSelect).toHaveBeenCalledWith('COD');
      expect(mockOnMethodSelect).toHaveBeenCalledTimes(3);
    });
  });
});