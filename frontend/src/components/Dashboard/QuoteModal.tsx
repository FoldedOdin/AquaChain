import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { IndianRupee, Package } from 'lucide-react';

interface QuoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: any;
  onSuccess: () => void;
}

const QuoteModal: React.FC<QuoteModalProps> = ({ isOpen, onClose, order, onSuccess }) => {
  const [quoteAmount, setQuoteAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState(order.paymentMethod || 'COD');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quoteAmount || parseFloat(quoteAmount) <= 0) {
      alert('Please enter a valid quote amount');
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:3002/api/admin/orders/${order.orderId}/quote`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          quoteAmount: parseFloat(quoteAmount),
          paymentMethod
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to set quote');
      }

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error setting quote:', error);
      alert(error.message || 'Failed to set quote. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full">
              <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <IndianRupee className="w-6 h-6 text-white" />
                  <h2 className="text-2xl font-bold text-white">Set Quote</h2>
                </div>
                <button onClick={onClose} className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition">
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-6">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Order Details
                  </label>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-1">
                    <p className="text-sm text-gray-600">Order ID: {order.orderId.slice(0, 8)}</p>
                    <p className="text-sm text-gray-600">Consumer: {order.consumerName}</p>
                    <p className="text-sm text-gray-600">Device: {order.deviceSKU}</p>
                  </div>
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Quote Amount (₹) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    value={quoteAmount}
                    onChange={(e) => setQuoteAmount(e.target.value)}
                    placeholder="Enter amount in rupees"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                    min="1"
                    step="1"
                  />
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Payment Method
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setPaymentMethod('COD')}
                      className={`p-3 border-2 rounded-lg transition ${
                        paymentMethod === 'COD'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="font-semibold text-gray-900">COD</div>
                      <div className="text-xs text-gray-600">Cash on Delivery</div>
                    </button>
                    <button
                      type="button"
                      onClick={() => setPaymentMethod('ONLINE')}
                      className={`p-3 border-2 rounded-lg transition ${
                        paymentMethod === 'ONLINE'
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-blue-300'
                      }`}
                    >
                      <div className="font-semibold text-gray-900">Online</div>
                      <div className="text-xs text-gray-600">Online Payment</div>
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={isSubmitting}
                    className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? 'Setting Quote...' : 'Set Quote'}
                  </button>
                </div>
              </form>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default QuoteModal;
