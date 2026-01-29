import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import RazorpayCheckout from '../RazorpayCheckout';
import { RazorpayCheckoutProps, RazorpayError, ContactInfo } from '../../../types/ordering';
import { apiClient } from '../../../services/apiClient';
import { NotificationProvider } from '../../../contexts/NotificationContext';
import { NetworkErrorHandler } from '../../ErrorHandling/NetworkErrorHandler';

// Mock the API client
jest.mock('../../../services/apiClient', () => ({
  apiClient: {
    post: jest.fn()
  }
}));

// Mock Framer Motion to avoid animation issues in tests
jest.mock('framer-motion', () => ({
  motion: {
    div: (props: any) => {
      const { whileHover, whileTap, initial, animate, ...validProps } = props;
      return require('react').createElement('div', validProps);
    },
    button: (props: any) => {
      const { whileHover, whileTap, initial, animate, ...validProps } = props;
      return require('react').createElement('button', validProps);
    }
  }
}));

// Mock Razorpay global object
const mockRazorpay = {
  open: jest.fn(),
  on: jest.fn()
};

// Mock window.Razorpay
Object.defineProperty(window, 'Razorpay', {
  value: jest.fn(() => mockRazorpay),
  writable: true
});

describe('RazorpayCheckout Component', () => {
  const mockProps: RazorpayCheckoutProps = {
    orderId: 'ORDER_123',
    amount: 5000,
    onSuccess: jest.fn(),
    onFailure: jest.fn(),
    customerInfo: {
      name: 'John Doe',
      email: 'john@example.com',
      phone: '+919876543210'
    }
  };

  const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

  // Test wrapper component
  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <NotificationProvider>
      <NetworkErrorHandler>
        {children}
      </NetworkErrorHandler>
    </NotificationProvider>
  );

  const renderWithWrapper = (component: React.ReactElement) => {
    return render(
      <TestWrapper>
        {component}
      </TestWrapper>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset environment variables
    process.env.REACT_APP_RAZORPAY_KEY_ID = 'rzp_test_123456';
    
    // Mock successful API responses by default
    mockApiClient.post.mockResolvedValue({
      data: {
        razorpayOrderId: 'order_razorpay_123',
        verified: true
      },
      status: 200,
      statusText: 'OK'
    });

    // Mock script loading - simulate immediate load
    const originalCreateElement = document.createElement.bind(document);
    jest.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      if (tagName === 'script') {
        const script = originalCreateElement('script');
        // Simulate script loading success immediately
        setTimeout(() => {
          if (script.onload) {
            (script.onload as any)({} as Event);
          }
        }, 0);
        return script;
      }
      return originalCreateElement(tagName);
    });

    jest.spyOn(document.body, 'appendChild').mockImplementation((node) => node);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders the component with header and payment information', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      // Wait for script to load
      await waitFor(() => {
        expect(screen.getByText('Secure Online Payment')).toBeInTheDocument();
      });
      
      expect(screen.getByText('Complete your payment securely using Razorpay')).toBeInTheDocument();
    });

    it('displays order summary correctly', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Order Summary')).toBeInTheDocument();
      });
      
      expect(screen.getByText('#ORDER_123')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('+919876543210')).toBeInTheDocument();
      expect(screen.getByText('₹5,000')).toBeInTheDocument();
    });

    it('displays security notice', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        expect(screen.getByText('Secure Payment')).toBeInTheDocument();
      });
      
      expect(screen.getByText(/256-bit SSL encryption/)).toBeInTheDocument();
      expect(screen.getByText(/PCI DSS compliant/)).toBeInTheDocument();
    });
  });

  describe('Payment Flow Initiation', () => {
    it('creates Razorpay order when payment button is clicked', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      // Wait for script to load and button to be enabled
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/create-razorpay-order', {
        amount: 500000, // 5000 * 100 (converted to paise)
        orderId: 'ORDER_123',
        currency: 'INR'
      });
    });

    it('opens Razorpay checkout with correct options', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      await waitFor(() => {
        expect(window.Razorpay).toHaveBeenCalledWith(
          expect.objectContaining({
            key: 'rzp_test_123456',
            amount: 500000,
            currency: 'INR',
            name: 'AquaChain',
            description: 'Water Quality Device Order #ORDER_123',
            order_id: 'order_razorpay_123',
            prefill: {
              name: 'John Doe',
              email: 'john@example.com',
              contact: '+919876543210'
            }
          })
        );
      });
      
      expect(mockRazorpay.open).toHaveBeenCalled();
    });
  });

  describe('Payment Success Handling', () => {
    it('verifies payment on backend when Razorpay returns success', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      // Wait for Razorpay to be initialized
      await waitFor(() => {
        expect(window.Razorpay).toHaveBeenCalled();
      });
      
      // Get the handler function passed to Razorpay
      const razorpayOptions = (window.Razorpay as jest.Mock).mock.calls[0][0];
      const successHandler = razorpayOptions.handler;
      
      // Simulate successful payment response
      const paymentResponse = {
        razorpay_payment_id: 'pay_123',
        razorpay_order_id: 'order_razorpay_123',
        razorpay_signature: 'signature_123'
      };
      
      await act(async () => {
        await successHandler(paymentResponse);
      });
      
      expect(mockApiClient.post).toHaveBeenCalledWith('/api/payments/verify-payment', {
        razorpay_payment_id: 'pay_123',
        razorpay_order_id: 'order_razorpay_123',
        razorpay_signature: 'signature_123',
        orderId: 'ORDER_123'
      });
    });

    it('calls onSuccess when payment is verified', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      await waitFor(() => {
        expect(window.Razorpay).toHaveBeenCalled();
      });
      
      const razorpayOptions = (window.Razorpay as jest.Mock).mock.calls[0][0];
      const successHandler = razorpayOptions.handler;
      
      const paymentResponse = {
        razorpay_payment_id: 'pay_123',
        razorpay_order_id: 'order_razorpay_123',
        razorpay_signature: 'signature_123'
      };
      
      await act(async () => {
        await successHandler(paymentResponse);
      });
      
      expect(mockProps.onSuccess).toHaveBeenCalledWith('pay_123');
    });
  });

  describe('Payment Failure Handling', () => {
    it('handles order creation failure', async () => {
      mockApiClient.post.mockRejectedValueOnce(new Error('Network error'));
      
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      await waitFor(() => {
        expect(screen.getByText(/Network error/)).toBeInTheDocument();
      });
      
      expect(mockProps.onFailure).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 'ORDER_CREATION_FAILED',
          description: 'Network error',
          source: 'api',
          step: 'order_creation'
        })
      );
    });

    it('handles payment cancellation by user', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      await waitFor(() => {
        expect(window.Razorpay).toHaveBeenCalled();
      });
      
      // Get the modal dismiss handler
      const razorpayOptions = (window.Razorpay as jest.Mock).mock.calls[0][0];
      const dismissHandler = razorpayOptions.modal.ondismiss;
      
      act(() => {
        dismissHandler();
      });
      
      expect(mockProps.onFailure).toHaveBeenCalledWith(
        expect.objectContaining({
          code: 'PAYMENT_CANCELLED',
          description: 'Payment was cancelled by user',
          source: 'user',
          step: 'payment',
          reason: 'user_cancelled'
        })
      );
    });
  });

  describe('Loading States', () => {
    it('shows loading state while script is loading', () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      const payButton = screen.getByRole('button');
      expect(payButton).toHaveTextContent('Loading Payment Gateway...');
      expect(payButton).toBeDisabled();
    });

    it('enables payment button after script loads', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).toHaveTextContent(/Pay ₹5,000 Securely/);
        expect(payButton).not.toBeDisabled();
      });
    });

    it('prevents duplicate submissions during loading', async () => {
      mockApiClient.post.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({
          data: { razorpayOrderId: 'order_123' },
          status: 200,
          statusText: 'OK'
        }), 100))
      );
      
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      
      // Click multiple times rapidly
      await userEvent.click(payButton);
      await userEvent.click(payButton);
      await userEvent.click(payButton);
      
      // Should only make one API call
      expect(mockApiClient.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('Error Handling', () => {
    it('displays error messages to user', async () => {
      mockApiClient.post.mockRejectedValueOnce(new Error('Server error'));
      
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      await waitFor(() => {
        expect(screen.getByText('Payment Error')).toBeInTheDocument();
        expect(screen.getByText('Server error')).toBeInTheDocument();
      });
    });

    it('allows dismissing error messages', async () => {
      mockApiClient.post.mockRejectedValueOnce(new Error('Test error'));
      
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).not.toBeDisabled();
      });
      
      const payButton = screen.getByRole('button');
      await userEvent.click(payButton);
      
      await waitFor(() => {
        expect(screen.getByText('Test error')).toBeInTheDocument();
      });
      
      const dismissButton = screen.getByText('Dismiss');
      await userEvent.click(dismissButton);
      
      expect(screen.queryByText('Test error')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper button labeling', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).toHaveAccessibleName();
      });
    });

    it('has proper focus management', async () => {
      renderWithWrapper(<RazorpayCheckout {...mockProps} />);
      
      await waitFor(() => {
        const payButton = screen.getByRole('button');
        expect(payButton).toHaveClass('focus:outline-none', 'focus:ring-2');
      });
    });
  });
});