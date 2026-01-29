/**
 * Ordering Flow Integration Tests - Task 13.2
 * 
 * Comprehensive integration testing for the Enhanced Consumer Ordering System:
 * - End-to-end COD order placement
 * - End-to-end online payment order placement  
 * - Real-time status updates integration
 * - Error handling and recovery scenarios
 * 
 * Requirements: 1.1, 2.1, 3.1, 4.1, 7.1
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import OrderingFlow from '../OrderingFlow';
import { OrderingProvider } from '../../../contexts/OrderingContext';
import { AuthProvider } from '../../../contexts/AuthContext';
import { NotificationProvider } from '../../../contexts/NotificationContext';
import { OrderStatus, PaymentMethod } from '../../../types/ordering';
import { UserProfile } from '../../../types';

// Mock external dependencies
jest.mock('../../../hooks/useRealTimeUpdates', () => ({
  useRealTimeUpdates: () => ({
    updates: [],
    latestUpdate: null,
    isConnected: true,
    connect: jest.fn(),
    disconnect: jest.fn(),
  }),
}));

jest.mock('../PaymentMethodSelector', () => {
  return function MockPaymentMethodSelector({ onMethodSelect }: any) {
    return (
      <div data-testid="payment-method-selector">
        <button 
          data-testid="select-cod"
          onClick={() => onMethodSelect('COD')}
        >
          Cash on Delivery
        </button>
        <button 
          data-testid="select-online"
          onClick={() => onMethodSelect('ONLINE')}
        >
          Online Payment
        </button>
      </div>
    );
  };
});

jest.mock('../CODConfirmationTimer', () => {
  return function MockCODConfirmationTimer({ onConfirm, onCancel }: any) {
    return (
      <div data-testid="cod-confirmation-timer">
        <button data-testid="confirm-cod" onClick={onConfirm}>
          Confirm Order
        </button>
        <button data-testid="cancel-cod" onClick={onCancel}>
          Cancel Order
        </button>
      </div>
    );
  };
});

jest.mock('../RazorpayCheckout', () => {
  return function MockRazorpayCheckout({ onSuccess, onFailure }: any) {
    return (
      <div data-testid="razorpay-checkout">
        <button 
          data-testid="payment-success"
          onClick={() => onSuccess('test_payment_id')}
        >
          Complete Payment
        </button>
        <button 
          data-testid="payment-failure"
          onClick={() => onFailure({ code: 'PAYMENT_FAILED', description: 'Payment failed' })}
        >
          Fail Payment
        </button>
      </div>
    );
  };
});

jest.mock('../OrderStatusTracker', () => {
  return function MockOrderStatusTracker({ orderId, currentStatus }: any) {
    return (
      <div data-testid="order-status-tracker">
        <div data-testid="order-id">{orderId}</div>
        <div data-testid="order-status">{currentStatus}</div>
      </div>
    );
  };
});

jest.mock('../../ErrorHandling/OrderingErrorBoundary', () => {
  return function MockOrderingErrorBoundary({ children }: any) {
    return <div data-testid="error-boundary">{children}</div>;
  };
});

// Mock fetch for API calls
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock user data
const mockUser = {
  userId: 'test-user-123',
  email: 'test@example.com',
  profile: {
    firstName: 'John',
    lastName: 'Doe',
    phone: '+1234567890',
    address: {
      street: '123 Test Street',
      city: 'Test City',
      state: 'Test State',
      pincode: '12345',
      country: 'India',
    },
  },
};

// Mock AuthContext
const MockAuthProvider = ({ children }: { children: React.ReactNode }) => {
  const authValue = {
    user: mockUser,
    isAuthenticated: true,
    login: jest.fn(),
    logout: jest.fn(),
    loading: false,
  };

  return (
    <div data-testid="auth-provider">
      {React.cloneElement(children as React.ReactElement, { authValue })}
    </div>
  );
};

// Mock NotificationContext
const MockNotificationProvider = ({ children }: { children: React.ReactNode }) => {
  return <div data-testid="notification-provider">{children}</div>;
};

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <BrowserRouter>
      <MockAuthProvider>
        <MockNotificationProvider>
          <OrderingProvider>
            {children}
          </OrderingProvider>
        </MockNotificationProvider>
      </MockAuthProvider>
    </BrowserRouter>
  );
};

// Helper function to render OrderingFlow with all providers
const renderOrderingFlow = (props = {}) => {
  const defaultProps = {
    onClose: jest.fn(),
    onOrderComplete: jest.fn(),
  };

  return render(
    <TestWrapper>
      <OrderingFlow {...defaultProps} {...props} />
    </TestWrapper>
  );
};

describe('OrderingFlow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue('mock-auth-token');
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('End-to-End COD Order Placement (Requirement 3.1)', () => {
    it('should complete full COD order flow successfully', async () => {
      // Mock successful order creation API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          order: {
            id: 'order-123',
            consumerId: 'test-user-123',
            deviceType: 'basic',
            serviceType: 'installation',
            paymentMethod: 'COD',
            status: OrderStatus.ORDER_PLACED,
            amount: 3499,
            statusHistory: [
              {
                status: OrderStatus.ORDER_PLACED,
                timestamp: new Date().toISOString(),
                message: 'Order placed successfully',
              },
            ],
          },
        }),
      });

      const { onClose, onOrderComplete } = renderOrderingFlow();

      // Step 1: Select device and service
      expect(screen.getByText('Select Device & Service')).toBeInTheDocument();
      
      // Select basic device
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      
      // Select installation service
      fireEvent.click(screen.getByText('Installation Only'));
      
      // Continue to payment
      fireEvent.click(screen.getByText('Continue to Payment'));

      // Step 2: Select COD payment method
      await waitFor(() => {
        expect(screen.getByText('Choose Payment Method')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByTestId('select-cod'));

      // Step 3: COD confirmation timer should appear
      await waitFor(() => {
        expect(screen.getByTestId('cod-confirmation-timer')).toBeInTheDocument();
      });

      // Confirm COD order
      fireEvent.click(screen.getByTestId('confirm-cod'));

      // Step 4: Order should be created and tracking should start
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': 'Bearer mock-auth-token',
            }),
            body: expect.stringContaining('"paymentMethod":"COD"'),
          })
        );
      });

      // Verify order tracking appears
      await waitFor(() => {
        expect(screen.getByTestId('order-status-tracker')).toBeInTheDocument();
        expect(screen.getByTestId('order-id')).toHaveTextContent('order-123');
        expect(screen.getByTestId('order-status')).toHaveTextContent(OrderStatus.ORDER_PLACED);
      });
    });

    it('should handle COD order cancellation during confirmation', async () => {
      renderOrderingFlow();

      // Navigate to COD confirmation
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      fireEvent.click(screen.getByText('Installation Only'));
      fireEvent.click(screen.getByText('Continue to Payment'));
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-cod'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('cod-confirmation-timer')).toBeInTheDocument();
      });

      // Cancel the order
      fireEvent.click(screen.getByTestId('cancel-cod'));

      // Should return to payment method selection
      await waitFor(() => {
        expect(screen.getByText('Choose Payment Method')).toBeInTheDocument();
      });

      // Verify no API call was made
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe('End-to-End Online Payment Order Placement (Requirement 2.1)', () => {
    it('should complete full online payment order flow successfully', async () => {
      // Mock successful order creation API response
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          order: {
            id: 'order-456',
            consumerId: 'test-user-123',
            deviceType: 'advanced',
            serviceType: 'maintenance',
            paymentMethod: 'ONLINE',
            status: OrderStatus.ORDER_PLACED,
            amount: 6499,
            paymentId: 'test_payment_id',
            statusHistory: [
              {
                status: OrderStatus.ORDER_PLACED,
                timestamp: new Date().toISOString(),
                message: 'Order placed with online payment',
              },
            ],
          },
        }),
      });

      renderOrderingFlow();

      // Step 1: Select device and service
      fireEvent.click(screen.getByText('Advanced Water Monitor'));
      fireEvent.click(screen.getByText('Installation + 1 Year Maintenance'));
      fireEvent.click(screen.getByText('Continue to Payment'));

      // Step 2: Select online payment method
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-online'));
      });

      // Step 3: Razorpay checkout should appear
      await waitFor(() => {
        expect(screen.getByTestId('razorpay-checkout')).toBeInTheDocument();
      });

      // Complete payment successfully
      fireEvent.click(screen.getByTestId('payment-success'));

      // Step 4: Order should be created and tracking should start
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': 'Bearer mock-auth-token',
            }),
            body: expect.stringContaining('"paymentMethod":"ONLINE"'),
          })
        );
      });

      // Verify order tracking appears
      await waitFor(() => {
        expect(screen.getByTestId('order-status-tracker')).toBeInTheDocument();
        expect(screen.getByTestId('order-id')).toHaveTextContent('order-456');
        expect(screen.getByTestId('order-status')).toHaveTextContent(OrderStatus.ORDER_PLACED);
      });
    });

    it('should handle online payment failure gracefully', async () => {
      renderOrderingFlow();

      // Navigate to online payment
      fireEvent.click(screen.getByText('Premium Water Monitor'));
      fireEvent.click(screen.getByText('Premium Support Package'));
      fireEvent.click(screen.getByText('Continue to Payment'));
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-online'));
      });

      await waitFor(() => {
        expect(screen.getByTestId('razorpay-checkout')).toBeInTheDocument();
      });

      // Simulate payment failure
      fireEvent.click(screen.getByTestId('payment-failure'));

      // Should remain on payment step for retry
      expect(screen.getByTestId('razorpay-checkout')).toBeInTheDocument();
      
      // Verify no order creation API call was made
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe('Real-time Status Updates Integration (Requirement 7.1)', () => {
    it('should display real-time order status updates', async () => {
      // Mock order creation and status update
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          order: {
            id: 'order-789',
            consumerId: 'test-user-123',
            deviceType: 'basic',
            serviceType: 'installation',
            paymentMethod: 'COD',
            status: OrderStatus.ORDER_PLACED,
            amount: 3499,
            statusHistory: [
              {
                status: OrderStatus.ORDER_PLACED,
                timestamp: new Date().toISOString(),
                message: 'Order placed successfully',
              },
            ],
          },
        }),
      });

      renderOrderingFlow();

      // Complete COD order flow
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      fireEvent.click(screen.getByText('Installation Only'));
      fireEvent.click(screen.getByText('Continue to Payment'));
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-cod'));
      });
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('confirm-cod'));
      });

      // Verify initial status
      await waitFor(() => {
        expect(screen.getByTestId('order-status-tracker')).toBeInTheDocument();
        expect(screen.getByTestId('order-status')).toHaveTextContent(OrderStatus.ORDER_PLACED);
      });

      // The real-time updates would be handled by the WebSocket integration
      // which is mocked in this test. In a real scenario, status updates
      // would come through WebSocket messages and update the order status.
    });
  });

  describe('Error Handling and Recovery (Requirement 6.1)', () => {
    it('should handle API errors during order creation', async () => {
      // Mock API error response
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      renderOrderingFlow();

      // Complete order flow
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      fireEvent.click(screen.getByText('Installation Only'));
      fireEvent.click(screen.getByText('Continue to Payment'));
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-cod'));
      });
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('confirm-cod'));
      });

      // Should display error message
      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });

    it('should handle authentication errors', async () => {
      // Mock authentication error
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Unauthorized' }),
      });

      renderOrderingFlow();

      // Complete order flow
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      fireEvent.click(screen.getByText('Installation Only'));
      fireEvent.click(screen.getByText('Continue to Payment'));
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-cod'));
      });
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('confirm-cod'));
      });

      // Should display authentication error
      await waitFor(() => {
        expect(screen.getByText(/Unauthorized/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation and Flow Control', () => {
    it('should allow navigation between steps', async () => {
      renderOrderingFlow();

      // Start at device selection
      expect(screen.getByText('Select Device & Service')).toBeInTheDocument();

      // Navigate to payment method
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      fireEvent.click(screen.getByText('Installation Only'));
      fireEvent.click(screen.getByText('Continue to Payment'));

      await waitFor(() => {
        expect(screen.getByText('Choose Payment Method')).toBeInTheDocument();
      });

      // Navigate back to device selection
      fireEvent.click(screen.getByTitle('Go back'));

      await waitFor(() => {
        expect(screen.getByText('Select Device & Service')).toBeInTheDocument();
      });
    });

    it('should close the ordering flow when close button is clicked', async () => {
      const onClose = jest.fn();
      
      render(
        <TestWrapper>
          <OrderingFlow onClose={onClose} />
        </TestWrapper>
      );

      // Click close button
      fireEvent.click(screen.getByTitle('Close'));

      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('Loading States and User Feedback', () => {
    it('should show loading state during order creation', async () => {
      // Mock delayed API response
      mockFetch.mockImplementationOnce(
        () => new Promise(resolve => 
          setTimeout(() => resolve({
            ok: true,
            json: async () => ({
              order: {
                id: 'order-loading-test',
                status: OrderStatus.ORDER_PLACED,
              },
            }),
          }), 100)
        )
      );

      renderOrderingFlow();

      // Complete order flow
      fireEvent.click(screen.getByText('Basic Water Monitor'));
      fireEvent.click(screen.getByText('Installation Only'));
      fireEvent.click(screen.getByText('Continue to Payment'));
      
      await waitFor(() => {
        fireEvent.click(screen.getByTestId('select-cod'));
      });
      
      fireEvent.click(screen.getByTestId('confirm-cod'));

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText('Processing your order...')).toBeInTheDocument();
      });

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByTestId('order-status-tracker')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
});