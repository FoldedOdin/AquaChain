/**
 * Order Progress Buttons Component
 * Provides manual buttons to progress order status through its lifecycle
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRightIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { OrderStatus } from '../../types/ordering';
import { useErrorNotification, OrderingError } from '../ErrorHandling';

interface OrderProgressButtonsProps {
  orderId: string;
  currentStatus: OrderStatus | string;
  onStatusUpdate: (newStatus: OrderStatus) => Promise<void>;
  disabled?: boolean;
}

/**
 * OrderProgressButtons Component
 * Displays action buttons to manually progress order status
 */
const OrderProgressButtons: React.FC<OrderProgressButtonsProps> = ({
  orderId,
  currentStatus,
  onStatusUpdate,
  disabled = false
}) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const { showErrorNotification } = useErrorNotification();

  // Map frontend statuses to backend-allowed statuses
  // Backend now accepts: PENDING_PAYMENT, PENDING_CONFIRMATION, ORDER_PLACED, DEVICE_READY, TECHNICIAN_ASSIGNED, SHIPPED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED, FAILED
  const FRONTEND_TO_BACKEND_STATUS: Record<string, string> = {
    'ORDER_PLACED': 'ORDER_PLACED',
    'PENDING_PAYMENT': 'PENDING_PAYMENT',
    'PENDING_CONFIRMATION': 'PENDING_CONFIRMATION',
    'DEVICE_READY': 'DEVICE_READY',
    'TECHNICIAN_ASSIGNED': 'TECHNICIAN_ASSIGNED',
    'PROCESSING': 'ORDER_PLACED',
    'SHIPPED': 'SHIPPED',
    'OUT_FOR_DELIVERY': 'OUT_FOR_DELIVERY',
    'DELIVERED': 'DELIVERED',
    'CANCELLED': 'CANCELLED',
    'FAILED': 'FAILED'
  };

  // Normalize raw status strings to their canonical enum equivalent
  // so the progression map always gets a valid key
  const normalizeStatus = (status: string): string => {
    const aliases: Record<string, string> = {
      'accepted': OrderStatus.TECHNICIAN_ASSIGNED,
      'assigned': OrderStatus.TECHNICIAN_ASSIGNED,
      'provisioned': OrderStatus.DEVICE_READY,
      'shipped': OrderStatus.SHIPPED,
      'out_for_delivery': OrderStatus.OUT_FOR_DELIVERY,
      'in_progress': OrderStatus.OUT_FOR_DELIVERY,  // technician started work = device is out for delivery
      'installing': OrderStatus.DELIVERED,
      'completed': OrderStatus.DELIVERED,
      'delivered': OrderStatus.DELIVERED,
      'pending': OrderStatus.ORDER_PLACED,
    };
    return aliases[status] ?? status;
  };

  const normalizedStatus = normalizeStatus(currentStatus as string);

  // Define status progression map
  const statusProgressionMap: Record<string, OrderStatus | null> = {
    [OrderStatus.PENDING_PAYMENT]: OrderStatus.ORDER_PLACED,
    [OrderStatus.PENDING_CONFIRMATION]: OrderStatus.ORDER_PLACED,
    [OrderStatus.ORDER_PLACED]: OrderStatus.DEVICE_READY,
    [OrderStatus.DEVICE_READY]: OrderStatus.TECHNICIAN_ASSIGNED,
    [OrderStatus.TECHNICIAN_ASSIGNED]: OrderStatus.SHIPPED,
    [OrderStatus.SHIPPED]: OrderStatus.OUT_FOR_DELIVERY,
    [OrderStatus.OUT_FOR_DELIVERY]: OrderStatus.DELIVERED,
    [OrderStatus.DELIVERED]: null,
    [OrderStatus.CANCELLED]: null,
    [OrderStatus.FAILED]: null,
  };

  // Get button labels for each status
  const getButtonLabel = (status: string): string => {
    const labels: Record<string, string> = {
      [OrderStatus.PENDING_PAYMENT]: 'Confirm Payment',
      [OrderStatus.PENDING_CONFIRMATION]: 'Confirm Order',
      [OrderStatus.ORDER_PLACED]: 'Mark Device Ready',
      [OrderStatus.DEVICE_READY]: 'Assign Technician',
      [OrderStatus.TECHNICIAN_ASSIGNED]: 'Mark as Shipped',
      [OrderStatus.SHIPPED]: 'Out for Delivery',
      [OrderStatus.OUT_FOR_DELIVERY]: 'Mark as Delivered',
    };
    return labels[status] || 'Next Status';
  };

  // Get next status
  const nextStatus = statusProgressionMap[normalizedStatus];

  // Check if order can be progressed
  const canProgress = nextStatus !== null && nextStatus !== undefined;

  // Check if order can be cancelled
  const canCancel = ![
    OrderStatus.DELIVERED,
    OrderStatus.CANCELLED,
    OrderStatus.FAILED
  ].includes(normalizedStatus as OrderStatus);

  // Handle status progression
  const handleProgressStatus = async () => {
    if (!nextStatus || isUpdating) return;

    setIsUpdating(true);
    try {
      // Map frontend status to backend-allowed status
      const backendStatus = FRONTEND_TO_BACKEND_STATUS[nextStatus] || nextStatus;
      
      console.log(`Updating order ${orderId}: ${currentStatus} → ${nextStatus} (backend: ${backendStatus})`);
      
      await onStatusUpdate(backendStatus as OrderStatus);
    } catch (error) {
      const updateError = new OrderingError('Failed to update order status', {
        code: 'STATUS_UPDATE_FAILED',
        retryable: true,
        context: {
          component: 'OrderProgressButtons',
          action: 'progress_status',
          orderId
        },
        cause: error as Error
      });
      
      showErrorNotification(updateError, {
        context: { orderId, component: 'OrderProgressButtons' }
      });
    } finally {
      setIsUpdating(false);
    }
  };

  // Handle order cancellation
  const handleCancelOrder = async () => {
    if (isUpdating) return;

    const confirmed = window.confirm(
      'Are you sure you want to cancel this order? This action cannot be undone.'
    );

    if (!confirmed) return;

    setIsUpdating(true);
    try {
      // Backend expects 'CANCELLED' status
      await onStatusUpdate('CANCELLED' as OrderStatus);
    } catch (error) {
      const cancelError = new OrderingError('Failed to cancel order', {
        code: 'CANCEL_ORDER_FAILED',
        retryable: true,
        context: {
          component: 'OrderProgressButtons',
          action: 'cancel_order',
          orderId
        },
        cause: error as Error
      });
      
      showErrorNotification(cancelError, {
        context: { orderId, component: 'OrderProgressButtons' }
      });
    } finally {
      setIsUpdating(false);
    }
  };

  // Don't render if no actions available
  if (!canProgress && !canCancel) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200"
    >
      <h5 className="text-sm font-medium text-gray-900 mb-3">Order Actions</h5>
      
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Progress Button */}
        {canProgress && (
          <button
            onClick={handleProgressStatus}
            disabled={disabled || isUpdating}
            className={`
              flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              font-medium text-sm transition-all duration-200
              ${disabled || isUpdating
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
              }
            `}
          >
            {isUpdating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                <span>Updating...</span>
              </>
            ) : (
              <>
                <CheckCircleIcon className="h-5 w-5" />
                <span>{getButtonLabel(normalizedStatus)}</span>
                <ArrowRightIcon className="h-4 w-4" />
              </>
            )}
          </button>
        )}

        {/* Cancel Button */}
        {canCancel && (
          <button
            onClick={handleCancelOrder}
            disabled={disabled || isUpdating}
            className={`
              flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
              font-medium text-sm transition-all duration-200 border
              ${disabled || isUpdating
                ? 'bg-gray-100 text-gray-400 border-gray-300 cursor-not-allowed'
                : 'bg-white text-red-600 border-red-300 hover:bg-red-50 active:scale-95'
              }
            `}
          >
            <XMarkIcon className="h-5 w-5" />
            <span>Cancel Order</span>
          </button>
        )}
      </div>

      {/* Status Information */}
      {canProgress && (
        <div className="mt-3 p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-800">
            <span className="font-medium">Next Status:</span>{' '}
            {nextStatus.replace(/_/g, ' ')}
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default OrderProgressButtons;
