import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, X, CheckCircle, AlertTriangle } from 'lucide-react';
import { CODConfirmationTimerProps, TimerState } from '../../types/ordering';

/**
 * CODConfirmationTimer Component
 * 
 * Displays a 10-second countdown timer for COD order confirmation with progress bar.
 * Provides cancel functionality during countdown and auto-confirmation when completed.
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
 */
const CODConfirmationTimer: React.FC<CODConfirmationTimerProps> = ({
  onConfirm,
  onCancel,
  countdownSeconds = 10
}) => {
  const [timerState, setTimerState] = useState<TimerState>({
    remainingSeconds: countdownSeconds,
    isActive: true,
    progress: 0
  });
  const [showCancelModal, setShowCancelModal] = useState(false);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const hasConfirmedRef = useRef(false);

  // Calculate progress percentage (0-100)
  const calculateProgress = useCallback((remaining: number): number => {
    return ((countdownSeconds - remaining) / countdownSeconds) * 100;
  }, [countdownSeconds]);

  // Handle timer tick
  const tick = useCallback(() => {
    setTimerState(prevState => {
      const newRemaining = prevState.remainingSeconds - 1;
      
      if (newRemaining <= 0) {
        // Timer completed - show success message first
        if (!hasConfirmedRef.current) {
          hasConfirmedRef.current = true;
          // Delay calling onConfirm to show success message for 2 seconds
          setTimeout(() => {
            onConfirm();
          }, 2000);
        }
        return {
          remainingSeconds: 0,
          isActive: false,
          progress: 100
        };
      }

      return {
        remainingSeconds: newRemaining,
        isActive: true,
        progress: calculateProgress(newRemaining)
      };
    });
  }, [calculateProgress, onConfirm]);

  // Start timer on mount
  useEffect(() => {
    intervalRef.current = setInterval(tick, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [tick]);

  // Handle cancel button click
  const handleCancel = useCallback(() => {
    setShowCancelModal(true);
  }, []);

  // Confirm cancellation
  const handleConfirmCancel = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    setTimerState(prev => ({ ...prev, isActive: false }));
    setShowCancelModal(false);
    onCancel();
  }, [onCancel]);

  // Close cancel modal and continue countdown
  const handleCloseCancelModal = useCallback(() => {
    setShowCancelModal(false);
  }, []);

  // Format remaining time for display
  const formatTime = (seconds: number): string => {
    return seconds.toString().padStart(2, '0');
  };

  // Get progress bar color based on remaining time
  const getProgressColor = (): string => {
    if (timerState.remainingSeconds <= 3) return 'bg-red-500';
    if (timerState.remainingSeconds <= 6) return 'bg-yellow-500';
    return 'bg-cyan-500';
  };

  // Get text color based on remaining time
  const getTextColor = (): string => {
    if (timerState.remainingSeconds <= 3) return 'text-red-600';
    if (timerState.remainingSeconds <= 6) return 'text-yellow-600';
    return 'text-cyan-600';
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cod-timer-title"
        aria-describedby="cod-timer-description"
      >
        <motion.div
          initial={{ y: 50 }}
          animate={{ y: 0 }}
          className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center"
        >
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-center mb-4">
              <div className={`p-3 rounded-full ${timerState.remainingSeconds <= 3 ? 'bg-red-100' : 'bg-cyan-100'}`}>
                <Clock className={`w-8 h-8 ${getTextColor()}`} />
              </div>
            </div>
            <h2 id="cod-timer-title" className="text-2xl font-bold text-gray-900 mb-2">
              Order Confirmation
            </h2>
            <p id="cod-timer-description" className="text-gray-600 text-sm">
              Your Cash on Delivery order will be confirmed automatically
            </p>
          </div>

          {/* Timer Display */}
          <div className="mb-8">
            <div className={`text-6xl font-bold mb-4 ${getTextColor()}`}>
              {formatTime(timerState.remainingSeconds)}
            </div>
            <p className="text-gray-500 text-sm mb-4">
              seconds remaining
            </p>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4 overflow-hidden">
              <motion.div
                className={`h-full rounded-full ${getProgressColor()}`}
                initial={{ width: 0 }}
                animate={{ width: `${timerState.progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>

            {/* Status Message */}
            <AnimatePresence mode="wait">
              {timerState.remainingSeconds > 0 ? (
                <motion.div
                  key="countdown"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center justify-center space-x-2"
                >
                  <AlertTriangle className={`w-4 h-4 ${getTextColor()}`} />
                  <span className="text-sm text-gray-600">
                    Click "Cancel Order" if you want to cancel
                  </span>
                </motion.div>
              ) : (
                <motion.div
                  key="confirmed"
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex items-center justify-center space-x-2 text-green-600"
                >
                  <CheckCircle className="w-5 h-5" />
                  <span className="text-sm font-medium">
                    Order Confirmed!
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Action Buttons */}
          <AnimatePresence>
            {timerState.isActive && timerState.remainingSeconds > 0 && (
              <motion.div
                initial={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-3"
              >
                {/* Cancel Button */}
                <motion.button
                  type="button"
                  onClick={handleCancel}
                  className="w-full px-6 py-3 bg-red-600 text-white rounded-lg font-medium
                           hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                           transition-colors duration-200 flex items-center justify-center space-x-2"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  aria-label="Cancel order before confirmation"
                >
                  <X className="w-5 h-5" />
                  <span>Cancel Order</span>
                </motion.button>

                {/* Info Text */}
                <p className="text-xs text-gray-500">
                  Your order will be automatically confirmed when the timer reaches zero
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Confirmation Complete State */}
          {!timerState.isActive && timerState.remainingSeconds === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              <div className="p-6 bg-green-50 border-2 border-green-300 rounded-xl">
                <div className="flex flex-col items-center justify-center space-y-3">
                  <div className="p-3 bg-green-100 rounded-full">
                    <CheckCircle className="w-12 h-12 text-green-600" />
                  </div>
                  <h3 className="text-2xl font-bold text-green-800">
                    Order Placed Successfully!
                  </h3>
                  <p className="text-sm text-green-700 text-center">
                    Your Cash on Delivery order has been confirmed.
                  </p>
                  <p className="text-sm text-green-600 text-center">
                    You will receive updates about your order status shortly.
                  </p>
                </div>
              </div>
              
              <div className="flex items-center justify-center space-x-2 text-gray-500 text-sm">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                <span>Processing your order...</span>
              </div>
            </motion.div>
          )}

          {/* Accessibility Live Region */}
          <div className="sr-only" aria-live="polite" aria-atomic="true">
            {timerState.isActive && timerState.remainingSeconds > 0 && (
              `${timerState.remainingSeconds} seconds remaining to cancel order`
            )}
            {!timerState.isActive && timerState.remainingSeconds === 0 && (
              'Order has been confirmed automatically'
            )}
          </div>
        </motion.div>

        {/* Cancellation Confirmation Modal */}
        <AnimatePresence>
          {showCancelModal && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center z-10"
              onClick={handleCloseCancelModal}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white rounded-xl shadow-2xl max-w-sm w-full mx-4 p-6"
              >
                {/* Warning Icon */}
                <div className="flex justify-center mb-4">
                  <div className="p-3 bg-red-100 rounded-full">
                    <AlertTriangle className="w-10 h-10 text-red-600" />
                  </div>
                </div>

                {/* Title */}
                <h3 className="text-xl font-bold text-gray-900 text-center mb-2">
                  Cancel Order?
                </h3>

                {/* Description */}
                <p className="text-gray-600 text-center text-sm mb-6">
                  Are you sure you want to cancel this order? This action cannot be undone and you'll need to start the ordering process again.
                </p>

                {/* Action Buttons */}
                <div className="flex flex-col space-y-3">
                  <button
                    onClick={handleConfirmCancel}
                    className="w-full px-6 py-3 bg-red-600 text-white rounded-lg font-medium
                             hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2
                             transition-colors duration-200"
                  >
                    Yes, Cancel Order
                  </button>
                  <button
                    onClick={handleCloseCancelModal}
                    className="w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium
                             hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2
                             transition-colors duration-200"
                  >
                    No, Keep Order
                  </button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </AnimatePresence>
  );
};

export default CODConfirmationTimer;