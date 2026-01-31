import React, { useState, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { CreditCard, Loader2, AlertCircle, CheckCircle, Shield } from 'lucide-react';
import { RazorpayCheckoutProps, RazorpayError } from '../../types/ordering';
import { apiClient } from '../../services/apiClient';

// Razorpay script URL
const RAZORPAY_SCRIPT_URL = 'https://checkout.razorpay.com/v1/checkout.js';

// Razorpay global interface
declare global {
  interface Window {
    Razorpay: any;
  }
}

/**
 * RazorpayCheckout Component
 * 
 * Integrates Razorpay SDK for secure online payment processing.
 * Features payment success/failure handling, loading states, and comprehensive error feedback.
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4
 */
const RazorpayCheckout: React.FC<RazorpayCheckoutProps> = ({
  orderId,
  amount,
  onSuccess,
  onFailure,
  customerInfo
}) => {
  const [isScriptLoaded, setIsScriptLoaded] = useState(false);
  const [razorpayOrderId, setRazorpayOrderId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Load Razorpay script
  useEffect(() => {
    const loadRazorpayScript = () => {
      return new Promise<boolean>((resolve) => {
        if (window.Razorpay) {
          setIsScriptLoaded(true);
          resolve(true);
          return;
        }

        const existingScript = document.querySelector(`script[src="${RAZORPAY_SCRIPT_URL}"]`);
        if (existingScript) {
          existingScript.addEventListener('load', () => {
            setIsScriptLoaded(true);
            resolve(true);
          });
          return;
        }

        const script = document.createElement('script');
        script.src = RAZORPAY_SCRIPT_URL;
        script.async = true;
        
        script.onload = () => {
          setIsScriptLoaded(true);
          resolve(true);
        };
        
        script.onerror = () => {
          setError(new Error('Failed to load Razorpay payment gateway'));
          resolve(false);
        };

        document.body.appendChild(script);
      });
    };

    loadRazorpayScript();
  }, []);

  // Simple makeRequest implementation
  const makeRequest = useCallback(async (fn: any, options: any = {}) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await fn();
      setIsLoading(false);
      return result;
    } catch (err: any) {
      setError(err);
      setIsLoading(false);
      if (options.onError) {
        options.onError(err);
      }
      throw err;
    }
  }, []);

  // Create Razorpay order
  const createRazorpayOrder = useCallback(async () => {
    const result = await makeRequest(
      async () => {
        interface CreateRazorpayOrderResponse {
          razorpayOrderId: string;
          amount: number;
          currency: string;
        }

        const response = await apiClient.post<CreateRazorpayOrderResponse>('/api/payments/create-razorpay-order', {
          amount: amount * 100,
          orderId,
          currency: 'INR'
        });

        if (response.data?.razorpayOrderId) {
          setRazorpayOrderId(response.data.razorpayOrderId);
          return response.data.razorpayOrderId;
        } else {
          throw new Error('Failed to create payment order');
        }
      },
      {
        onError: (error: any) => {
          const razorpayError: RazorpayError = {
            code: 'ORDER_CREATION_FAILED',
            description: error.message,
            source: 'api',
            step: 'order_creation',
            reason: 'unknown'
          };
          onFailure(razorpayError);
        }
      }
    );

    return result;
  }, [amount, orderId, onFailure, makeRequest]);

  // Handle payment success
  const handlePaymentSuccess = useCallback(async (response: any) => {
    const result = await makeRequest(
      async () => {
        interface VerifyPaymentResponse {
          verified: boolean;
          paymentId?: string;
          orderId?: string;
        }

        const verificationResponse = await apiClient.post<VerifyPaymentResponse>('/api/payments/verify-payment', {
          razorpay_payment_id: response.razorpay_payment_id,
          razorpay_order_id: response.razorpay_order_id,
          razorpay_signature: response.razorpay_signature,
          orderId
        });

        if (verificationResponse.data?.verified) {
          onSuccess(response.razorpay_payment_id);
          return verificationResponse.data;
        } else {
          throw new Error('Payment verification failed');
        }
      },
      {
        onError: (error: any) => {
          const razorpayError: RazorpayError = {
            code: 'VERIFICATION_FAILED',
            description: error.message,
            source: 'verification',
            step: 'payment_verification',
            reason: 'verification_error'
          };
          onFailure(razorpayError);
        }
      }
    );

    return result;
  }, [orderId, onSuccess, onFailure, makeRequest]);

  // Handle payment failure
  const handlePaymentFailure = useCallback((response: any) => {
    const razorpayError: RazorpayError = {
      code: response.error?.code || 'PAYMENT_FAILED',
      description: response.error?.description || 'Payment failed',
      source: response.error?.source || 'razorpay',
      step: response.error?.step || 'payment',
      reason: response.error?.reason || 'user_cancelled'
    };

    onFailure(razorpayError);
  }, [onFailure]);

  // Initiate payment
  const initiatePayment = useCallback(async () => {
    if (!isScriptLoaded || !window.Razorpay) {
      setError(new Error('Payment gateway not loaded'));
      return;
    }

    try {
      const razorpayOrderId = await createRazorpayOrder();
      
      if (!razorpayOrderId) {
        return;
      }
      
      const options = {
        key: process.env.REACT_APP_RAZORPAY_KEY_ID,
        amount: amount * 100,
        currency: 'INR',
        name: 'AquaChain',
        description: `Water Quality Device Order #${orderId}`,
        order_id: razorpayOrderId,
        handler: handlePaymentSuccess,
        prefill: {
          name: customerInfo.name,
          email: customerInfo.email,
          contact: customerInfo.phone
        },
        notes: {
          order_id: orderId,
          customer_id: customerInfo.email
        },
        theme: {
          color: '#0891b2'
        },
        modal: {
          ondismiss: () => {
            const razorpayError: RazorpayError = {
              code: 'PAYMENT_CANCELLED',
              description: 'Payment was cancelled by user',
              source: 'user',
              step: 'payment',
              reason: 'user_cancelled'
            };
            handlePaymentFailure({ error: razorpayError });
          }
        },
        retry: {
          enabled: true,
          max_count: 3
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.on('payment.failed', handlePaymentFailure);
      razorpay.open();

    } catch (err: any) {
      console.error('Payment initiation failed:', err);
    }
  }, [
    isScriptLoaded,
    amount,
    orderId,
    customerInfo,
    createRazorpayOrder,
    handlePaymentSuccess,
    handlePaymentFailure
  ]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="p-3 bg-cyan-100 rounded-full">
            <CreditCard className="w-8 h-8 text-cyan-600" />
          </div>
        </div>
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Secure Online Payment
        </h3>
        <p className="text-gray-600 text-sm">
          Complete your payment securely using Razorpay
        </p>
      </div>

      {/* Order Summary */}
      <div className="bg-gray-50 rounded-lg p-4 border">
        <h4 className="font-medium text-gray-900 mb-3">Order Summary</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Order ID:</span>
            <span className="font-mono text-gray-900">#{orderId}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Customer:</span>
            <span className="text-gray-900">{customerInfo.name}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Email:</span>
            <span className="text-gray-900">{customerInfo.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Phone:</span>
            <span className="text-gray-900">{customerInfo.phone}</span>
          </div>
          <div className="border-t pt-2 mt-3">
            <div className="flex justify-between font-semibold">
              <span className="text-gray-900">Total Amount:</span>
              <span className="text-cyan-600">₹{amount.toLocaleString('en-IN')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security Notice */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Shield className="w-5 h-5 text-green-600 mt-0.5" />
          <div>
            <h5 className="font-medium text-green-800 mb-1">Secure Payment</h5>
            <p className="text-sm text-green-700">
              Your payment is secured with 256-bit SSL encryption and processed by Razorpay,
              a PCI DSS compliant payment gateway trusted by millions.
            </p>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
            <div className="flex-1">
              <h5 className="font-medium text-red-800 mb-1">Payment Error</h5>
              <p className="text-sm text-red-700">{error.message}</p>
              <button
                onClick={() => setError(null)}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Button */}
      <div className="space-y-4">
        <motion.button
          type="button"
          onClick={initiatePayment}
          disabled={isLoading || !isScriptLoaded || !!error}
          className={`
            w-full py-4 px-6 rounded-lg font-semibold text-white
            transition-all duration-200 flex items-center justify-center space-x-2
            focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2
            ${isLoading || !isScriptLoaded || !!error
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-cyan-600 hover:bg-cyan-700 active:bg-cyan-800'
            }
          `}
          {...(process.env.NODE_ENV !== 'test' && !isLoading && isScriptLoaded && !error ? {
            whileHover: { scale: 1.02 },
            whileTap: { scale: 0.98 }
          } : {})}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Processing Payment...</span>
            </>
          ) : !isScriptLoaded ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Loading Payment Gateway...</span>
            </>
          ) : (
            <>
              <CreditCard className="w-5 h-5" />
              <span>Pay ₹{amount.toLocaleString('en-IN')} Securely</span>
            </>
          )}
        </motion.button>

        {/* Payment Methods Info */}
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-2">Accepted Payment Methods</p>
          <div className="flex items-center justify-center space-x-4 text-xs text-gray-400">
            <span>UPI</span>
            <span>•</span>
            <span>Cards</span>
            <span>•</span>
            <span>Net Banking</span>
            <span>•</span>
            <span>Wallets</span>
          </div>
        </div>
      </div>

      {/* Success State */}
      {razorpayOrderId && !error && (
        <motion.div
          {...(process.env.NODE_ENV !== 'test' ? {
            initial: { opacity: 0, y: 10 },
            animate: { opacity: 1, y: 0 }
          } : {})}
          className="bg-blue-50 border border-blue-200 rounded-lg p-4"
        >
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-800">
                Payment order created successfully
              </p>
              <p className="text-xs text-blue-600 mt-1">
                Order ID: {razorpayOrderId}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Powered by Razorpay */}
      <div className="text-center pt-4 border-t">
        <p className="text-xs text-gray-400">
          Powered by{' '}
          <a
            href="https://razorpay.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-600 hover:text-cyan-700"
          >
            Razorpay
          </a>
        </p>
      </div>
    </div>
  );
};

export default RazorpayCheckout;