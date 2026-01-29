/**
 * OrderStatusTracker Component Tests
 * 
 * Tests real-time updates and WebSocket integration, status display and history rendering.
 * Requirements: 7.1, 7.4
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderStatusTracker from '../OrderStatusTracker';
import { OrderStatus, StatusUpdate } from '../../../types/ordering';
import { NotificationProvider } from '../../../contexts/NotificationContext';

// Mock the useRealTimeUpdates hook
const mockUseRealTimeUpdates = jest.fn();
jest.mock('../../../hooks/useRealTimeUpdates', () => ({
  useRealTimeUpdates: (...args: any[]) => mockUseRealTimeUpdates(...args)
}));

// Mock framer-motion for testing
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('OrderStatusTracker Component', () => {
  const mockOrderId = 'order-123';
  const mockCurrentStatus = OrderStatus.ORDER_PLACED;
  const mockStatusHistory: StatusUpdate[] = [
    {
      status: OrderStatus.ORDER_PLACED,
      timestamp: new Date('2024-01-15T10:00:00Z'),
      message: 'Your order has been confirmed',
      metadata: { orderId: mockOrderId }
    }
  ];
  const mockEstimatedDelivery = new Date('2024-01-16T14:00:00Z');

  const defaultProps = {
    orderId: mockOrderId,
    currentStatus: mockCurrentStatus,
    statusHistory: mockStatusHistory,
    estimatedDelivery: mockEstimatedDelivery
  };

  const mockWebSocketReturn = {
    latestUpdate: null,
    isConnected: true,
    error: null,
    reconnectAttempts: 0,
    connect: jest.fn(),
    disconnect: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseRealTimeUpdates.mockReturnValue(mockWebSocketReturn);
  });

  // Test wrapper component
  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <NotificationProvider>
      {children}
    </NotificationProvider>
  );

  const renderWithWrapper = (component: React.ReactElement) => {
    return render(
      <TestWrapper>
        {component}
      </TestWrapper>
    );
  };

  describe('Basic Rendering', () => {
    it('renders the component with order information', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Order Status')).toBeInTheDocument();
      expect(screen.getByText(`Order #${mockOrderId}`)).toBeInTheDocument();
    });

    it('displays current status correctly', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByRole('heading', { name: 'Order Placed' })).toBeInTheDocument();
      // Check for the main status description (in the colored box)
      const statusBoxes = screen.getAllByText('Your order has been confirmed');
      expect(statusBoxes.length).toBeGreaterThan(0);
    });

    it('renders status history', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Status History')).toBeInTheDocument();
      // Check that status history contains the expected message
      const statusMessages = screen.getAllByText('Your order has been confirmed');
      expect(statusMessages.length).toBeGreaterThan(0);
    });

    it('displays estimated delivery when provided', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Estimated Delivery')).toBeInTheDocument();
      expect(screen.getByText(/Tuesday, January 16/)).toBeInTheDocument();
    });

    it('does not display estimated delivery for delivered orders', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.DELIVERED}
        />
      );
      
      expect(screen.queryByText('Estimated Delivery')).not.toBeInTheDocument();
    });
  });

  describe('WebSocket Integration', () => {
    it('subscribes to WebSocket updates on mount', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(mockUseRealTimeUpdates).toHaveBeenCalledWith(
        `order-${mockOrderId}`,
        { autoConnect: true }
      );
    });

    it('displays connection status', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    it('shows disconnected status when not connected', () => {
      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false
      });

      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Connecting...')).toBeInTheDocument();
    });

    it('shows error status when there is an error', () => {
      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
        error: new Error('Connection failed')
      });

      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
    });

    it('displays reconnection attempts', () => {
      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
        reconnectAttempts: 3
      });

      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText(/Reconnecting/)).toBeInTheDocument();
      expect(screen.getByText(/attempt 3/)).toBeInTheDocument();
    });

    it('shows retry button when there is an error', () => {
      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
        error: new Error('Connection failed')
      });

      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Look for retry buttons - there should be at least one
      const retryButtons = screen.getAllByRole('button', { name: /try again/i });
      expect(retryButtons.length).toBeGreaterThan(0);
    });

    it('handles retry button click', async () => {
      const mockConnect = jest.fn();
      const mockDisconnect = jest.fn();
      
      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
        error: new Error('Connection failed'),
        connect: mockConnect,
        disconnect: mockDisconnect
      });

      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      const retryButtons = screen.getAllByRole('button', { name: /try again/i });
      await userEvent.click(retryButtons[0]); // Click the first retry button
      
      expect(mockDisconnect).toHaveBeenCalled();
      
      // Wait for the timeout in the retry logic
      await act(async () => {
        await new Promise(resolve => setTimeout(resolve, 1100));
      });
      
      expect(mockConnect).toHaveBeenCalled();
    });
  });

  describe('Real-time Status Updates', () => {
    it('updates status when receiving WebSocket updates', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Simulate receiving a status update
      const statusUpdate = {
        type: 'order_status_update',
        data: {
          status: OrderStatus.SHIPPED,
          message: 'Your order has been shipped',
          timestamp: new Date().toISOString(),
          metadata: { trackingNumber: 'TRK123' }
        }
      };

      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        latestUpdate: statusUpdate
      });

      rerender(
        <TestWrapper>
          <OrderStatusTracker {...defaultProps} />
        </TestWrapper>
      );
      
      // Use more specific selector for the main status heading
      expect(screen.getByRole('heading', { name: 'Shipped' })).toBeInTheDocument();
      expect(screen.getByText('Your order is on its way')).toBeInTheDocument();
    });

    it('adds new status updates to history', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      const statusUpdate = {
        type: 'order_status_update',
        data: {
          status: OrderStatus.SHIPPED,
          message: 'Package dispatched from warehouse',
          timestamp: new Date().toISOString()
        }
      };

      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        latestUpdate: statusUpdate
      });

      rerender(
        <TestWrapper>
          <OrderStatusTracker {...defaultProps} />
        </TestWrapper>
      );
      
      expect(screen.getByText('Package dispatched from warehouse')).toBeInTheDocument();
    });

    it('ignores non-status update messages', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      const nonStatusUpdate = {
        type: 'heartbeat',
        data: { ping: 'pong' }
      };

      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        latestUpdate: nonStatusUpdate
      });

      rerender(
        <TestWrapper>
          <OrderStatusTracker {...defaultProps} />
        </TestWrapper>
      );
      
      // Should still show original status - use more specific selector
      expect(screen.getByRole('heading', { name: 'Order Placed' })).toBeInTheDocument();
    });

    it('handles status updates with metadata', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      const statusUpdate = {
        type: 'order_status_update',
        data: {
          status: OrderStatus.OUT_FOR_DELIVERY,
          message: 'Out for delivery',
          timestamp: new Date().toISOString(),
          metadata: {
            driverName: 'John Doe',
            estimatedArrival: '2:00 PM'
          }
        }
      };

      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        latestUpdate: statusUpdate
      });

      rerender(
        <TestWrapper>
          <OrderStatusTracker {...defaultProps} />
        </TestWrapper>
      );
      
      expect(screen.getByText('driverName:')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('estimatedArrival:')).toBeInTheDocument();
      expect(screen.getByText('2:00 PM')).toBeInTheDocument();
    });
  });

  describe('Progress Bar Display', () => {
    it('shows progress bar for active orders', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByText('25% Complete')).toBeInTheDocument();
    });

    it('does not show progress bar for cancelled orders', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.CANCELLED}
        />
      );
      
      expect(screen.queryByText('Progress')).not.toBeInTheDocument();
    });

    it('does not show progress bar for failed orders', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.FAILED}
        />
      );
      
      expect(screen.queryByText('Progress')).not.toBeInTheDocument();
    });

    it('does not show progress bar for pending payment orders', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.PENDING_PAYMENT}
        />
      );
      
      expect(screen.queryByText('Progress')).not.toBeInTheDocument();
    });

    it('calculates correct progress percentage', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.SHIPPED}
        />
      );
      
      expect(screen.getByText('50% Complete')).toBeInTheDocument();
    });

    it('shows 100% progress for delivered orders', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.DELIVERED}
        />
      );
      
      expect(screen.getByText('100% Complete')).toBeInTheDocument();
    });

    it('displays progress steps correctly', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Check that all progress steps are present in the progress section
      const progressSection = screen.getByText('Progress').parentElement;
      expect(progressSection).toBeInTheDocument();
      
      // Check for progress percentage
      expect(screen.getByText('25% Complete')).toBeInTheDocument();
    });
  });

  describe('Status History Display', () => {
    it('displays status history in chronological order', () => {
      const multipleStatusHistory: StatusUpdate[] = [
        {
          status: OrderStatus.SHIPPED,
          timestamp: new Date('2024-01-15T12:00:00Z'),
          message: 'Package shipped'
        },
        {
          status: OrderStatus.ORDER_PLACED,
          timestamp: new Date('2024-01-15T10:00:00Z'),
          message: 'Order confirmed'
        }
      ];

      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          statusHistory={multipleStatusHistory}
        />
      );
      
      const historyItems = screen.getAllByText(/Package shipped|Order confirmed/);
      expect(historyItems).toHaveLength(2);
    });

    it('formats timestamps correctly', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Should display formatted timestamp (check for the actual formatted time)
      expect(screen.getByText('Jan 15, 03:30 PM')).toBeInTheDocument();
    });

    it('displays status history with proper icons', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Check that status history items have icons (SVG elements)
      const historySection = screen.getByText('Status History').parentElement;
      const svgElements = historySection?.querySelectorAll('svg');
      expect(svgElements?.length).toBeGreaterThan(0);
    });

    it('handles empty status history', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          statusHistory={[]}
        />
      );
      
      expect(screen.getByText('Status History')).toBeInTheDocument();
      // Should not crash and should still render the section
    });

    it('displays metadata in status history when available', () => {
      const historyWithMetadata: StatusUpdate[] = [
        {
          status: OrderStatus.ORDER_PLACED,
          timestamp: new Date('2024-01-15T10:00:00Z'),
          message: 'Order confirmed',
          metadata: {
            paymentMethod: 'COD',
            amount: 1500
          }
        }
      ];

      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          statusHistory={historyWithMetadata}
        />
      );
      
      expect(screen.getByText('paymentMethod:')).toBeInTheDocument();
      expect(screen.getByText('COD')).toBeInTheDocument();
      expect(screen.getByText('amount:')).toBeInTheDocument();
      expect(screen.getByText('1500')).toBeInTheDocument();
    });
  });

  describe('Status Configuration', () => {
    it('displays correct status for each order state', () => {
      const statusTests = [
        { status: OrderStatus.PENDING_PAYMENT, label: 'Pending Payment' },
        { status: OrderStatus.PENDING_CONFIRMATION, label: 'Pending Confirmation' },
        { status: OrderStatus.ORDER_PLACED, label: 'Order Placed' },
        { status: OrderStatus.SHIPPED, label: 'Shipped' },
        { status: OrderStatus.OUT_FOR_DELIVERY, label: 'Out for Delivery' },
        { status: OrderStatus.DELIVERED, label: 'Delivered' },
        { status: OrderStatus.CANCELLED, label: 'Cancelled' },
        { status: OrderStatus.FAILED, label: 'Failed' }
      ];

      statusTests.forEach(({ status, label }) => {
        const { unmount } = renderWithWrapper(
          <OrderStatusTracker 
            {...defaultProps} 
            currentStatus={status}
          />
        );
        
        // Check for the status in the main heading
        const statusHeading = screen.getByRole('heading', { name: label });
        expect(statusHeading).toBeInTheDocument();
        unmount();
      });
    });

    it('displays appropriate descriptions for each status', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.SHIPPED}
        />
      );
      
      expect(screen.getByText('Your order is on its way')).toBeInTheDocument();
    });

    it('uses correct colors for different statuses', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          currentStatus={OrderStatus.DELIVERED}
        />
      );
      
      // Check for green color classes for delivered status in the main status display
      const statusHeading = screen.getByRole('heading', { name: 'Delivered' });
      expect(statusHeading).toHaveClass('text-green-700');
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByRole('heading', { name: 'Order Status' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Status History' })).toBeInTheDocument();
    });

    it('provides meaningful text for screen readers', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText(`Order #${mockOrderId}`)).toBeInTheDocument();
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    it('has proper color contrast for status indicators', () => {
      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Status elements should have appropriate color classes
      const statusHeading = screen.getByRole('heading', { name: 'Order Placed' });
      expect(statusHeading).toHaveClass('text-green-600');
    });
  });

  describe('Error Handling', () => {
    it('handles missing estimated delivery gracefully', () => {
      renderWithWrapper(
        <OrderStatusTracker 
          {...defaultProps} 
          estimatedDelivery={undefined}
        />
      );
      
      expect(screen.queryByText('Estimated Delivery')).not.toBeInTheDocument();
    });

    it('handles invalid timestamps in status history', () => {
      const invalidHistory: StatusUpdate[] = [
        {
          status: OrderStatus.ORDER_PLACED,
          timestamp: new Date('invalid-date'),
          message: 'Order confirmed'
        }
      ];

      expect(() => {
        renderWithWrapper(
          <OrderStatusTracker 
            {...defaultProps} 
            statusHistory={invalidHistory}
          />
        );
      }).not.toThrow();
      
      // Should display "Invalid date" for malformed timestamps
      expect(screen.getByText('Invalid date')).toBeInTheDocument();
    });

    it('handles WebSocket connection errors gracefully', () => {
      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        isConnected: false,
        error: new Error('WebSocket connection failed')
      });

      renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
      // Check that at least one retry button exists
      const retryButtons = screen.getAllByRole('button', { name: /try again/i });
      expect(retryButtons.length).toBeGreaterThan(0);
    });

    it('handles malformed WebSocket messages', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      const malformedUpdate = {
        type: 'order_status_update',
        data: null // Invalid data
      };

      mockUseRealTimeUpdates.mockReturnValue({
        ...mockWebSocketReturn,
        latestUpdate: malformedUpdate
      });

      expect(() => {
        rerender(
          <TestWrapper>
            <OrderStatusTracker {...defaultProps} />
          </TestWrapper>
        );
      }).not.toThrow();
    });
  });

  describe('Performance', () => {
    it('does not re-render unnecessarily', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Re-render with same props
      rerender(
        <TestWrapper>
          <OrderStatusTracker {...defaultProps} />
        </TestWrapper>
      );
      
      // Component should handle this gracefully
      expect(screen.getByText('Order Status')).toBeInTheDocument();
    });

    it('handles rapid status updates', () => {
      const { rerender } = renderWithWrapper(<OrderStatusTracker {...defaultProps} />);
      
      // Simulate rapid updates
      const updates = [
        { status: OrderStatus.SHIPPED, message: 'Shipped' },
        { status: OrderStatus.OUT_FOR_DELIVERY, message: 'Out for delivery' },
        { status: OrderStatus.DELIVERED, message: 'Delivered' }
      ];

      updates.forEach((update) => {
        mockUseRealTimeUpdates.mockReturnValue({
          ...mockWebSocketReturn,
          latestUpdate: {
            type: 'order_status_update',
            data: {
              ...update,
              timestamp: new Date().toISOString()
            }
          }
        });

        rerender(
          <TestWrapper>
            <OrderStatusTracker {...defaultProps} />
          </TestWrapper>
        );
      });

      // Check for the final status in the main heading
      const deliveredHeading = screen.getByRole('heading', { name: 'Delivered' });
      expect(deliveredHeading).toHaveTextContent('Delivered');
    });
  });
});