import React, { useState, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Package, CheckCircle, AlertTriangle, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useOrdering } from '../../contexts/OrderingContext';
import PaymentMethodSelector from './PaymentMethodSelector';
import CODConfirmationTimer from './CODConfirmationTimer';
import RazorpayCheckout from './RazorpayCheckout';
import OrderStatusTracker from './OrderStatusTracker';
import OrderingErrorBoundary from '../ErrorHandling/OrderingErrorBoundary';
import { PaymentMethod, CreateOrderRequest, OrderStatus, Address } from '../../types/ordering';

// Flow Steps
type OrderFlowStep = 
  | 'device-selection'
  | 'payment-method'
  | 'cod-confirmation'
  | 'online-payment'
  | 'order-tracking'
  | 'order-complete';

interface OrderingFlowProps {
  onClose: () => void;
  onOrderComplete?: (orderId: string) => void;
}

/**
 * OrderingFlow Component
 * 
 * Main component that orchestrates the complete ordering flow including:
 * - Device type selection
 * - Payment method selection
 * - COD confirmation or online payment processing
 * - Real-time order tracking
 * 
 * Requirements: 1.1, 1.2, 2.1, 3.1, 4.1, 7.1
 */
const OrderingFlow: React.FC<OrderingFlowProps> = ({ onClose, onOrderComplete }) => {
  const { user } = useAuth();
  const { state, setPaymentMethod, createOrder, clearError, resetOrderFlow } = useOrdering();
  
  // Flow state
  const [currentStep, setCurrentStep] = useState<OrderFlowStep>('device-selection');
  const [selectedDeviceType, setSelectedDeviceType] = useState<string>('');
  const [selectedServiceType, setSelectedServiceType] = useState<string>('');
  const [orderAmount, setOrderAmount] = useState<number>(0);

  // Device and service options
  const deviceTypes = [
    { id: 'basic', name: 'Basic Water Monitor', price: 4999, description: 'pH, TDS, Temperature, Turbidity monitoring', disabled: false },
    { id: 'premium', name: 'Premium Water Monitor', price: 7999, description: 'Full spectrum monitoring with IoT connectivity', disabled: true, comingSoon: true },
  ];

  const serviceTypes = [
    { id: 'installation', name: 'Installation Only', price: 500, description: 'Device setup and configuration' },
    { id: 'maintenance', name: 'Installation + 1 Year Maintenance', price: 1500, description: 'Setup plus annual maintenance' },
    { id: 'premium-support', name: 'Premium Support Package', price: 2500, description: 'Priority support with quarterly checkups' },
  ];

  // Calculate total amount
  useEffect(() => {
    const device = deviceTypes.find(d => d.id === selectedDeviceType);
    const service = serviceTypes.find(s => s.id === selectedServiceType);
    const total = (device?.price || 0) + (service?.price || 0);
    setOrderAmount(total);
  }, [selectedDeviceType, selectedServiceType]);

  // Handle device selection
  const handleDeviceSelection = useCallback(() => {
    if (!selectedDeviceType || !selectedServiceType) {
      return;
    }
    setCurrentStep('payment-method');
  }, [selectedDeviceType, selectedServiceType]);

  // Handle payment method selection
  const handlePaymentMethodSelect = useCallback((method: PaymentMethod) => {
    setPaymentMethod(method);
    
    if (method === 'COD') {
      setCurrentStep('cod-confirmation');
    } else {
      setCurrentStep('online-payment');
    }
  }, [setPaymentMethod]);

  // Handle COD confirmation
  const handleCODConfirm = useCallback(async () => {
    try {
      // Convert user profile address to proper Address format
      const userAddress = user?.profile?.address;
      let deliveryAddress: Address;
      
      if (typeof userAddress === 'string') {
        // If address is a string, create a basic Address object
        deliveryAddress = {
          street: userAddress,
          city: '',
          state: '',
          pincode: '',
          country: 'India',
        };
      } else if (userAddress && typeof userAddress === 'object') {
        // If address is an object, map it to Address format
        const addr = userAddress as any;
        deliveryAddress = {
          street: addr.street || addr.flatHouse || addr.areaStreet || '',
          city: addr.city || '',
          state: addr.state || '',
          pincode: addr.pincode || addr.zipCode || '',
          country: addr.country || 'India',
          landmark: addr.landmark,
        };
      } else {
        // Fallback if no address
        deliveryAddress = {
          street: '',
          city: '',
          state: '',
          pincode: '',
          country: 'India',
        };
      }

      const orderRequest: CreateOrderRequest = {
        consumerId: user?.userId || '',
        deviceType: selectedDeviceType,
        serviceType: selectedServiceType,
        paymentMethod: 'COD',
        deliveryAddress,
        contactInfo: {
          name: `${user?.profile?.firstName || ''} ${user?.profile?.lastName || ''}`.trim() || user?.email || 'Customer',
          phone: user?.profile?.phone || '',
          email: user?.email || '',
        },
        amount: orderAmount,
      };

      await createOrder(orderRequest);
      setCurrentStep('order-tracking');
    } catch (error) {
      console.error('Failed to create COD order:', error);
    }
  }, [user, selectedDeviceType, selectedServiceType, orderAmount, createOrder]);

  // Handle COD cancellation
  const handleCODCancel = useCallback(() => {
    setCurrentStep('payment-method');
  }, []);

  // Handle online payment success
  const handlePaymentSuccess = useCallback(async (paymentId: string) => {
    try {
      // Convert user profile address to proper Address format
      const userAddress = user?.profile?.address;
      let deliveryAddress: Address;
      
      if (typeof userAddress === 'string') {
        // If address is a string, create a basic Address object
        deliveryAddress = {
          street: userAddress,
          city: '',
          state: '',
          pincode: '',
          country: 'India',
        };
      } else if (userAddress && typeof userAddress === 'object') {
        // If address is an object, map it to Address format
        const addr = userAddress as any;
        deliveryAddress = {
          street: addr.street || addr.flatHouse || addr.areaStreet || '',
          city: addr.city || '',
          state: addr.state || '',
          pincode: addr.pincode || addr.zipCode || '',
          country: addr.country || 'India',
          landmark: addr.landmark,
        };
      } else {
        // Fallback if no address
        deliveryAddress = {
          street: '',
          city: '',
          state: '',
          pincode: '',
          country: 'India',
        };
      }

      const orderRequest: CreateOrderRequest = {
        consumerId: user?.userId || '',
        deviceType: selectedDeviceType,
        serviceType: selectedServiceType,
        paymentMethod: 'ONLINE',
        deliveryAddress,
        contactInfo: {
          name: `${user?.profile?.firstName || ''} ${user?.profile?.lastName || ''}`.trim() || user?.email || 'Customer',
          phone: user?.profile?.phone || '',
          email: user?.email || '',
        },
        amount: orderAmount,
        paymentId,
      };

      await createOrder(orderRequest);
      setCurrentStep('order-tracking');
    } catch (error) {
      console.error('Failed to create online order:', error);
    }
  }, [user, selectedDeviceType, selectedServiceType, orderAmount, createOrder]);

  // Handle payment failure
  const handlePaymentFailure = useCallback((error: any) => {
    console.error('Payment failed:', error);
    // Stay on payment step to allow retry
  }, []);

  // Handle order completion
  const handleOrderComplete = useCallback(() => {
    if (state.currentOrder) {
      onOrderComplete?.(state.currentOrder.id);
    }
    setCurrentStep('order-complete');
  }, [state.currentOrder, onOrderComplete]);

  // Handle close
  const handleClose = useCallback(() => {
    resetOrderFlow();
    onClose();
  }, [resetOrderFlow, onClose]);

  // Handle back navigation
  const handleBack = useCallback(() => {
    clearError();
    
    switch (currentStep) {
      case 'payment-method':
        setCurrentStep('device-selection');
        break;
      case 'cod-confirmation':
      case 'online-payment':
        setCurrentStep('payment-method');
        break;
      case 'order-tracking':
        // Don't allow back from tracking
        break;
      default:
        handleClose();
    }
  }, [currentStep, clearError, handleClose]);

  // Step titles
  const getStepTitle = (step: OrderFlowStep): string => {
    switch (step) {
      case 'device-selection':
        return 'Select Device & Service';
      case 'payment-method':
        return 'Choose Payment Method';
      case 'cod-confirmation':
        return 'Confirm Cash on Delivery';
      case 'online-payment':
        return 'Complete Payment';
      case 'order-tracking':
        return 'Track Your Order';
      case 'order-complete':
        return 'Order Complete';
      default:
        return 'Place Order';
    }
  };

  return createPortal(
    <OrderingErrorBoundary>
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-[9999] flex items-center justify-center p-4"
        style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          zIndex: 9999,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem'
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Package className="w-6 h-6 text-white" />
              <h2 className="text-2xl font-bold text-white">{getStepTitle(currentStep)}</h2>
            </div>
            <div className="flex items-center space-x-2">
              {currentStep !== 'order-tracking' && currentStep !== 'order-complete' && (
                <button
                  onClick={handleBack}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                  title="Go back"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
              )}
              <button
                onClick={handleClose}
                className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Progress Indicator */}
          <div className="bg-gray-50 px-6 py-3 border-b">
            <div className="flex items-center space-x-4">
              {['device-selection', 'payment-method', 'order-tracking'].map((step, index) => {
                const isActive = currentStep === step;
                const isCompleted = ['device-selection', 'payment-method'].indexOf(currentStep) > index;
                
                return (
                  <div key={step} className="flex items-center">
                    <div className={`
                      w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                      ${isCompleted ? 'bg-green-500 text-white' : 
                        isActive ? 'bg-cyan-500 text-white' : 'bg-gray-200 text-gray-600'}
                    `}>
                      {isCompleted ? <CheckCircle className="w-4 h-4" /> : index + 1}
                    </div>
                    {index < 2 && (
                      <div className={`w-12 h-1 mx-2 ${isCompleted ? 'bg-green-500' : 'bg-gray-200'}`} />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Error Display */}
          {state.error && (
            <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                <p className="text-sm font-medium text-red-800">{state.error}</p>
                <button
                  onClick={clearError}
                  className="ml-auto text-red-600 hover:text-red-800"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(90vh-200px)] p-6">
            <AnimatePresence mode="wait">
              {/* Device Selection Step */}
              {currentStep === 'device-selection' && (
                <motion.div
                  key="device-selection"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-6"
                >
                  {/* Device Type Selection */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose Device Type</h3>
                    <div className="grid gap-4 md:grid-cols-2">
                      {deviceTypes.map((device) => (
                        <button
                          key={device.id}
                          onClick={() => !device.disabled && setSelectedDeviceType(device.id)}
                          disabled={device.disabled}
                          className={`
                            p-4 rounded-lg border-2 text-left transition-all relative
                            ${device.disabled 
                              ? 'border-gray-200 bg-gray-50 opacity-60 cursor-not-allowed' 
                              : selectedDeviceType === device.id
                                ? 'border-cyan-500 bg-cyan-50'
                                : 'border-gray-200 hover:border-gray-300'
                            }
                          `}
                        >
                          {device.comingSoon && (
                            <span className="absolute top-2 right-2 bg-amber-500 text-white text-xs font-semibold px-2 py-1 rounded">
                              Coming Soon
                            </span>
                          )}
                          <h4 className="font-semibold text-gray-900">{device.name}</h4>
                          <p className="text-sm text-gray-600 mt-1">{device.description}</p>
                          <p className={`text-lg font-bold mt-2 ${device.disabled ? 'text-gray-400' : 'text-cyan-600'}`}>
                            {device.disabled ? '-----' : `₹${device.price.toLocaleString()}`}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Service Type Selection */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose Service Package</h3>
                    <div className="grid gap-4">
                      {serviceTypes.map((service) => (
                        <button
                          key={service.id}
                          onClick={() => setSelectedServiceType(service.id)}
                          className={`
                            p-4 rounded-lg border-2 text-left transition-all
                            ${selectedServiceType === service.id
                              ? 'border-cyan-500 bg-cyan-50'
                              : 'border-gray-200 hover:border-gray-300'
                            }
                          `}
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="font-semibold text-gray-900">{service.name}</h4>
                              <p className="text-sm text-gray-600 mt-1">{service.description}</p>
                            </div>
                            <p className="text-lg font-bold text-cyan-600">₹{service.price.toLocaleString()}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Total and Continue */}
                  {selectedDeviceType && selectedServiceType && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-lg font-semibold text-gray-900">Total Amount:</span>
                        <span className="text-2xl font-bold text-cyan-600">₹{orderAmount.toLocaleString()}</span>
                      </div>
                      <button
                        onClick={handleDeviceSelection}
                        className="w-full bg-cyan-500 text-white py-3 rounded-lg hover:bg-cyan-600 transition-colors font-medium"
                      >
                        Continue to Payment
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Payment Method Selection Step */}
              {currentStep === 'payment-method' && (
                <motion.div
                  key="payment-method"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <PaymentMethodSelector
                    onMethodSelect={handlePaymentMethodSelect}
                    disabled={state.isLoading}
                  />
                </motion.div>
              )}

              {/* COD Confirmation Step */}
              {currentStep === 'cod-confirmation' && (
                <motion.div
                  key="cod-confirmation"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <CODConfirmationTimer
                    onConfirm={handleCODConfirm}
                    onCancel={handleCODCancel}
                    countdownSeconds={10}
                  />
                </motion.div>
              )}

              {/* Online Payment Step */}
              {currentStep === 'online-payment' && (
                <motion.div
                  key="online-payment"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <RazorpayCheckout
                    orderId={state.currentOrder?.id || ''}
                    amount={orderAmount}
                    onSuccess={handlePaymentSuccess}
                    onFailure={handlePaymentFailure}
                    customerInfo={{
                      name: `${user?.profile?.firstName || ''} ${user?.profile?.lastName || ''}`.trim() || user?.email || 'Customer',
                      email: user?.email || '',
                      phone: user?.profile?.phone || '',
                    }}
                  />
                </motion.div>
              )}

              {/* Order Tracking Step */}
              {currentStep === 'order-tracking' && state.currentOrder && (
                <motion.div
                  key="order-tracking"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                >
                  <OrderStatusTracker
                    orderId={state.currentOrder.id}
                    currentStatus={state.currentOrder.status}
                    statusHistory={state.currentOrder.statusHistory || []}
                    demoMode={true}
                    progressInterval={20}
                  />
                  
                  {/* Order Complete Button */}
                  {state.currentOrder.status === OrderStatus.DELIVERED && (
                    <div className="mt-6 text-center">
                      <button
                        onClick={handleOrderComplete}
                        className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors font-medium"
                      >
                        Mark as Complete
                      </button>
                    </div>
                  )}
                </motion.div>
              )}

              {/* Order Complete Step */}
              {currentStep === 'order-complete' && (
                <motion.div
                  key="order-complete"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="text-center py-8"
                >
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Order Complete!</h3>
                  <p className="text-gray-600 mb-6">
                    Your water quality device has been successfully ordered and will be delivered soon.
                  </p>
                  <button
                    onClick={handleClose}
                    className="bg-cyan-500 text-white px-6 py-3 rounded-lg hover:bg-cyan-600 transition-colors font-medium"
                  >
                    Close
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Loading Overlay */}
          {state.isLoading && (
            <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Processing your order...</p>
              </div>
            </div>
          )}
        </motion.div>
      </div>
    </OrderingErrorBoundary>,
    document.body
  );
};

export default OrderingFlow;