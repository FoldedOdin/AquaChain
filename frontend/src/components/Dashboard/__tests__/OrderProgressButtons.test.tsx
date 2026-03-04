/**
 * OrderProgressButtons Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import OrderProgressButtons from '../OrderProgressButtons';
import { OrderStatus } from '../../../types/ordering';
import { NotificationProvider } from '../../../contexts/NotificationContext';

// Mock the error notification hook
jest.mock('../../ErrorHandling', () => ({
  useErrorNotification: () => ({
    showErrorNotification: jest.fn()
  }),
  OrderingError: class OrderingError extends Error {
    constructor(message: string, options?: any) {
      super(message);
      this.name = 'OrderingError';
    }
  }
}));

describe('OrderProgressButtons Component', () => {
  const mockOnStatusUpdate = jest.fn();

  const renderWithWrapper = (component: React.ReactElement) => {
    return render(
      <NotificationProvider>
        {component}
      </NotificationProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Button Rendering', () => {
    it('renders progress button for ORDER_PLACED status', () => {
      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.ORDER_PLACED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      expect(screen.getByText('Mark as Shipped')).toBeInTheDocument();
      expect(screen.getByText('Cancel Order')).toBeInTheDocument();
    });

    it('renders progress button for SHIPPED status', () => {
      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.SHIPPED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      expect(screen.getByText('Out for Delivery')).toBeInTheDocument();
    });

    it('does not render buttons for DELIVERED status', () => {
      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.DELIVERED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      expect(screen.queryByText('Mark as Shipped')).not.toBeInTheDocument();
      expect(screen.queryByText('Cancel Order')).not.toBeInTheDocument();
    });

    it('does not render cancel button for DELIVERED status', () => {
      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.DELIVERED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      expect(screen.queryByText('Cancel Order')).not.toBeInTheDocument();
    });
  });

  describe('Button Interactions', () => {
    it('calls onStatusUpdate when progress button is clicked', async () => {
      mockOnStatusUpdate.mockResolvedValueOnce(undefined);

      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.ORDER_PLACED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      const progressButton = screen.getByText('Mark as Shipped');
      fireEvent.click(progressButton);

      await waitFor(() => {
        expect(mockOnStatusUpdate).toHaveBeenCalledWith(OrderStatus.SHIPPED);
      });
    });

    it('shows confirmation dialog when cancel button is clicked', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(true);
      mockOnStatusUpdate.mockResolvedValueOnce(undefined);

      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.ORDER_PLACED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      const cancelButton = screen.getByText('Cancel Order');
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(mockOnStatusUpdate).toHaveBeenCalledWith(OrderStatus.CANCELLED);
      });

      confirmSpy.mockRestore();
    });

    it('does not cancel order if user declines confirmation', async () => {
      const confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);

      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.ORDER_PLACED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      const cancelButton = screen.getByText('Cancel Order');
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(confirmSpy).toHaveBeenCalled();
        expect(mockOnStatusUpdate).not.toHaveBeenCalled();
      });

      confirmSpy.mockRestore();
    });

    it('disables buttons when disabled prop is true', () => {
      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.ORDER_PLACED}
          onStatusUpdate={mockOnStatusUpdate}
          disabled={true}
        />
      );

      const progressButton = screen.getByText('Mark as Shipped');
      const cancelButton = screen.getByText('Cancel Order');

      expect(progressButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
    });

    it('shows loading state while updating', async () => {
      mockOnStatusUpdate.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      renderWithWrapper(
        <OrderProgressButtons
          orderId="order-123"
          currentStatus={OrderStatus.ORDER_PLACED}
          onStatusUpdate={mockOnStatusUpdate}
        />
      );

      const progressButton = screen.getByText('Mark as Shipped');
      fireEvent.click(progressButton);

      await waitFor(() => {
        expect(screen.getByText('Updating...')).toBeInTheDocument();
      });
    });
  });

  describe('Status Progression', () => {
    it('shows correct next status for each current status', () => {
      const statusTests = [
        { current: OrderStatus.ORDER_PLACED, next: 'SHIPPED' },
        { current: OrderStatus.SHIPPED, next: 'OUT_FOR_DELIVERY' },
        { current: OrderStatus.OUT_FOR_DELIVERY, next: 'DELIVERED' }
      ];

      statusTests.forEach(({ current, next }) => {
        const { unmount } = renderWithWrapper(
          <OrderProgressButtons
            orderId="order-123"
            currentStatus={current}
            onStatusUpdate={mockOnStatusUpdate}
          />
        );

        expect(screen.getByText(new RegExp(next.replace(/_/g, ' '), 'i'))).toBeInTheDocument();
        unmount();
      });
    });
  });
});
