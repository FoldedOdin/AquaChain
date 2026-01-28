import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { CreditCard, Banknote, CheckCircle } from 'lucide-react';
import { PaymentMethodSelectorProps, PaymentMethod, PaymentMethodOption } from '../../types/ordering';

/**
 * PaymentMethodSelector Component
 * 
 * Provides a user interface for selecting between Cash on Delivery (COD) and Online Payment methods.
 * Features clear descriptions, accessibility support, and responsive design following AquaChain's design system.
 * 
 * Requirements: 1.1, 1.2, 1.4
 */
const PaymentMethodSelector: React.FC<PaymentMethodSelectorProps> = ({
  onMethodSelect,
  disabled = false
}) => {
  const [selectedMethod, setSelectedMethod] = useState<PaymentMethod | null>(null);

  // Payment method options with clear descriptions
  const paymentMethods: PaymentMethodOption[] = [
    {
      id: 'COD',
      name: 'Cash on Delivery',
      description: 'Pay when the device is delivered to your location. No advance payment required.',
      icon: 'banknote'
    },
    {
      id: 'ONLINE',
      name: 'Online Payment',
      description: 'Pay securely online using UPI, cards, or net banking via Razorpay.',
      icon: 'credit-card'
    }
  ];

  // Handle payment method selection
  const handleMethodSelect = useCallback((method: PaymentMethod) => {
    if (disabled) return;
    
    setSelectedMethod(method);
    onMethodSelect(method);
  }, [onMethodSelect, disabled]);

  // Get icon component based on icon name
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'banknote':
        return <Banknote className="w-6 h-6" />;
      case 'credit-card':
        return <CreditCard className="w-6 h-6" />;
      default:
        return <CreditCard className="w-6 h-6" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="text-center mb-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          Choose Payment Method
        </h3>
        <p className="text-gray-600 text-sm">
          Select how you'd like to pay for your water quality device
        </p>
      </div>

      {/* Payment Method Options */}
      <div className="grid gap-4 md:grid-cols-2">
        {paymentMethods.map((method) => {
          const isSelected = selectedMethod === method.id;
          
          return (
            <motion.button
              key={method.id}
              type="button"
              onClick={() => handleMethodSelect(method.id)}
              disabled={disabled}
              className={`
                relative p-6 rounded-xl border-2 text-left transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed
                ${isSelected
                  ? 'border-cyan-500 bg-cyan-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                }
              `}
              whileHover={!disabled ? { scale: 1.02 } : {}}
              whileTap={!disabled ? { scale: 0.98 } : {}}
              aria-pressed={isSelected}
              aria-describedby={`${method.id}-description`}
              role="radio"
              tabIndex={0}
            >
              {/* Selection Indicator */}
              {isSelected && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute top-4 right-4"
                >
                  <CheckCircle className="w-6 h-6 text-cyan-500" />
                </motion.div>
              )}

              {/* Method Icon and Title */}
              <div className="flex items-start space-x-4 mb-3">
                <div className={`
                  p-3 rounded-lg
                  ${isSelected ? 'bg-cyan-100 text-cyan-600' : 'bg-gray-100 text-gray-600'}
                `}>
                  {getIcon(method.icon)}
                </div>
                <div className="flex-1">
                  <h4 className={`
                    font-semibold text-lg
                    ${isSelected ? 'text-cyan-900' : 'text-gray-900'}
                  `}>
                    {method.name}
                  </h4>
                </div>
              </div>

              {/* Method Description */}
              <p
                id={`${method.id}-description`}
                className={`
                  text-sm leading-relaxed
                  ${isSelected ? 'text-cyan-800' : 'text-gray-600'}
                `}
              >
                {method.description}
              </p>

              {/* Additional Info for COD */}
              {method.id === 'COD' && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-xs text-blue-800">
                    <strong>Note:</strong> You'll have a 10-second confirmation window to cancel if needed.
                  </p>
                </div>
              )}

              {/* Additional Info for Online Payment */}
              {method.id === 'ONLINE' && (
                <div className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
                  <p className="text-xs text-green-800">
                    <strong>Secure:</strong> Powered by Razorpay with 256-bit SSL encryption.
                  </p>
                </div>
              )}
            </motion.button>
          );
        })}
      </div>

      {/* Selection Status */}
      {selectedMethod && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg"
        >
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <p className="text-sm font-medium text-green-800">
              {selectedMethod === 'COD' ? 'Cash on Delivery' : 'Online Payment'} selected
            </p>
          </div>
          <p className="text-xs text-green-700 mt-1">
            Click "Continue" to proceed with your selected payment method.
          </p>
        </motion.div>
      )}

      {/* Accessibility Instructions */}
      <div className="sr-only" aria-live="polite">
        {selectedMethod && (
          `${selectedMethod === 'COD' ? 'Cash on Delivery' : 'Online Payment'} payment method selected`
        )}
      </div>
    </div>
  );
};

export default PaymentMethodSelector;