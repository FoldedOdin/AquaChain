/**
 * Order Status Tracker Component
 * Real-time order status display with WebSocket integration
 * Implements Requirements: 7.1, 7.2, 7.3, 7.4
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ClockIcon,
  TruckIcon,
  ExclamationTriangleIcon,
  WifiIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { Package, MapPin, User, Calendar } from 'lucide-react';
import { useRealTimeUpdates } from '../../hooks/useRealTimeUpdates';
import { OrderStatus, StatusUpdate, OrderStatusTrackerProps } from '../../types/ordering';

/**
 * OrderStatusTracker Component
 * Displays real-time order status with WebSocket integration
 */
const OrderStatusTracker: React.FC<OrderStatusTrackerProps> = ({
  orderId,
  currentStatus,
  statusHistory,
  estimatedDelivery
}) => {
  const [localStatusHistory, setLocalStatusHistory] = useState<StatusUpdate[]>(statusHistory);
  const [localCurrentStatus, setLocalCurrentStatus] = useState<OrderStatus>(currentStatus);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());

  // WebSocket subscription for real-time updates
  const {
    latestUpdate,
    isConnected,
    error,
    reconnectAttempts,
    connect,
    disconnect
  } = useRealTimeUpdates(`order-${orderId}`, { autoConnect: true });

  // Handle real-time status updates
  useEffect(() => {
    if (latestUpdate && latestUpdate.type === 'order_status_update' && latestUpdate.data) {
      try {
        const { status, message, timestamp, metadata } = latestUpdate.data;
        
        if (status && status !== localCurrentStatus) {
          setLocalCurrentStatus(status);
          
          const newStatusUpdate: StatusUpdate = {
            status,
            timestamp: new Date(timestamp || Date.now()),
            message: message || `Order status updated to ${status}`,
            metadata
          };
          
          setLocalStatusHistory(prev => [newStatusUpdate, ...prev]);
          setLastUpdateTime(new Date());
        }
      } catch (error) {
        console.error('Error processing status update:', error);
      }
    }
  }, [latestUpdate, localCurrentStatus]);

  // Status configuration with icons and colors
  const statusConfig = useMemo(() => ({
    [OrderStatus.PENDING_PAYMENT]: {
      icon: ClockIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      label: 'Pending Payment',
      description: 'Waiting for payment confirmation'
    },
    [OrderStatus.PENDING_CONFIRMATION]: {
      icon: ClockIcon,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
      label: 'Pending Confirmation',
      description: 'Awaiting order confirmation'
    },
    [OrderStatus.ORDER_PLACED]: {
      icon: CheckCircleIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
      label: 'Order Placed',
      description: 'Your order has been confirmed'
    },
    [OrderStatus.SHIPPED]: {
      icon: Package,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
      label: 'Shipped',
      description: 'Your order is on its way'
    },
    [OrderStatus.OUT_FOR_DELIVERY]: {
      icon: TruckIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
      label: 'Out for Delivery',
      description: 'Your order is out for delivery'
    },
    [OrderStatus.DELIVERED]: {
      icon: CheckCircleIcon,
      color: 'text-green-700',
      bgColor: 'bg-green-200',
      label: 'Delivered',
      description: 'Your order has been delivered'
    },
    [OrderStatus.CANCELLED]: {
      icon: ExclamationTriangleIcon,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      label: 'Cancelled',
      description: 'Your order has been cancelled'
    },
    [OrderStatus.FAILED]: {
      icon: ExclamationTriangleIcon,
      color: 'text-red-700',
      bgColor: 'bg-red-200',
      label: 'Failed',
      description: 'Order processing failed'
    }
  }), []);

  // Get status progression for progress bar
  const statusProgression = useMemo(() => [
    OrderStatus.ORDER_PLACED,
    OrderStatus.SHIPPED,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED
  ], []);

  const getCurrentProgressPercentage = useCallback(() => {
    if ([OrderStatus.CANCELLED, OrderStatus.FAILED].includes(localCurrentStatus)) {
      return 0;
    }
    
    const currentIndex = statusProgression.indexOf(localCurrentStatus);
    if (currentIndex === -1) return 0;
    
    return ((currentIndex + 1) / statusProgression.length) * 100;
  }, [localCurrentStatus, statusProgression]);

  // Format timestamp for display
  const formatTimestamp = useCallback((timestamp: Date) => {
    try {
      if (!timestamp || isNaN(timestamp.getTime())) {
        return 'Invalid date';
      }
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(timestamp);
    } catch (error) {
      console.error('Error formatting timestamp:', error);
      return 'Invalid date';
    }
  }, []);

  // Connection status indicator
  const ConnectionStatus = () => (
    <div className="flex items-center space-x-2 text-sm">
      <div className={`flex items-center space-x-1 ${
        isConnected ? 'text-green-600' : 'text-red-600'
      }`}>
        <WifiIcon className="h-4 w-4" />
        <span>
          {isConnected ? 'Connected' : error ? 'Connection Error' : 'Connecting...'}
        </span>
      </div>
      
      {reconnectAttempts > 0 && (
        <div className="flex items-center space-x-1 text-orange-600">
          <ArrowPathIcon className="h-4 w-4 animate-spin" />
          <span>Reconnecting... ({reconnectAttempts})</span>
        </div>
      )}
      
      <span className="text-gray-500">
        Last update: {formatTimestamp(lastUpdateTime)}
      </span>
    </div>
  );

  // Manual reconnect handler
  const handleReconnect = useCallback(() => {
    disconnect();
    setTimeout(() => connect(), 1000);
  }, [connect, disconnect]);

  const currentConfig = statusConfig[localCurrentStatus];
  const StatusIcon = currentConfig.icon;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-full ${currentConfig.bgColor}`}>
            <StatusIcon className={`h-6 w-6 ${currentConfig.color}`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Order Status
            </h3>
            <p className="text-sm text-gray-600">Order #{orderId}</p>
          </div>
        </div>
        
        {error && (
          <button
            onClick={handleReconnect}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Retry</span>
          </button>
        )}
      </div>

      {/* Current Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 rounded-lg ${currentConfig.bgColor} mb-6`}
      >
        <div className="flex items-center space-x-3">
          <StatusIcon className={`h-8 w-8 ${currentConfig.color}`} />
          <div>
            <h4 className={`text-xl font-semibold ${currentConfig.color}`}>
              {currentConfig.label}
            </h4>
            <p className="text-gray-700">{currentConfig.description}</p>
          </div>
        </div>
      </motion.div>

      {/* Progress Bar (for active orders) */}
      {![OrderStatus.CANCELLED, OrderStatus.FAILED, OrderStatus.PENDING_PAYMENT, OrderStatus.PENDING_CONFIRMATION].includes(localCurrentStatus) && (
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(getCurrentProgressPercentage())}% Complete</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              className="bg-blue-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${getCurrentProgressPercentage()}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
            />
          </div>
          
          {/* Progress Steps */}
          <div className="flex justify-between mt-3">
            {statusProgression.map((status, index) => {
              const config = statusConfig[status];
              const isCompleted = statusProgression.indexOf(localCurrentStatus) >= index;
              const isCurrent = localCurrentStatus === status;
              
              return (
                <div key={status} className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    isCompleted ? config.bgColor : 'bg-gray-100'
                  }`}>
                    <config.icon className={`h-4 w-4 ${
                      isCompleted ? config.color : 'text-gray-400'
                    }`} />
                  </div>
                  <span className={`text-xs mt-1 text-center ${
                    isCurrent ? config.color : isCompleted ? 'text-gray-700' : 'text-gray-400'
                  }`}>
                    {config.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Estimated Delivery */}
      {estimatedDelivery && localCurrentStatus !== OrderStatus.DELIVERED && (
        <div className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg mb-6">
          <Calendar className="h-5 w-5 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-900">Estimated Delivery</p>
            <p className="text-sm text-blue-700">
              {new Intl.DateTimeFormat('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              }).format(estimatedDelivery)}
            </p>
          </div>
        </div>
      )}

      {/* Status History */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold text-gray-900">Status History</h4>
        
        <div className="space-y-3 max-h-64 overflow-y-auto">
          <AnimatePresence>
            {localStatusHistory.map((update, index) => {
              const config = statusConfig[update.status];
              const UpdateIcon = config.icon;
              
              return (
                <motion.div
                  key={`${update.status}-${update.timestamp.getTime()}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div className={`p-1 rounded-full ${config.bgColor} flex-shrink-0`}>
                    <UpdateIcon className={`h-4 w-4 ${config.color}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-900">
                        {config.label}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatTimestamp(update.timestamp)}
                      </p>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {update.message}
                    </p>
                    {update.metadata && (
                      <div className="mt-2 text-xs text-gray-500">
                        {Object.entries(update.metadata).map(([key, value]) => (
                          <div key={key} className="flex items-center space-x-2">
                            <span className="capitalize">{key}:</span>
                            <span>{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>

      {/* Connection Status Footer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <ConnectionStatus />
      </div>
    </div>
  );
};

export default OrderStatusTracker;