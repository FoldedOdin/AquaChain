import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Package, MapPin, Phone, CreditCard, Calendar } from 'lucide-react';

interface RequestDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const RequestDeviceModal: React.FC<RequestDeviceModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    deviceSKU: 'AC-HOME-V1',
    address: '',
    phone: '',
    paymentMethod: 'COD',
    preferredSlot: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch('http://localhost:3002/api/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('Failed to create order');
      }

      const result = await response.json();
      console.log('Order created:', result);
      
      setSubmitted(true);
      setTimeout(() => {
        onSuccess();
        onClose();
        setSubmitted(false);
        setFormData({
          deviceSKU: 'AC-HOME-V1',
          address: '',
          phone: '',
          paymentMethod: 'COD',
          preferredSlot: ''
        });
      }, 2000);
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Failed to create order. Please try again.');
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
            <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
              {/* Header */}
              <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Package className="w-6 h-6 text-white" />
                  <h2 className="text-2xl font-bold text-white">Request Water Quality Device</h2>
                </div>
                <button
                  onClick={onClose}
                  className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Content */}
              <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6">
                {submitted ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">Order Submitted!</h3>
                    <p className="text-gray-600 mb-4">
                      Your device request has been submitted successfully.
                    </p>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left max-w-md mx-auto">
                      <p className="text-sm text-blue-900 mb-2">
                        <strong>What happens next?</strong>
                      </p>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>• Admin will review your request</li>
                        <li>• You'll receive a quote within 24 hours</li>
                        <li>• Track your order in "My Orders"</li>
                      </ul>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit}>
                    <p className="text-gray-600 mb-6">
                      Fill in your details to request a water quality monitoring device. Our team will review and provide a quote.
                    </p>

                    {/* Device SKU */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        <Package className="w-4 h-4 inline mr-2" />
                        Device Model <span className="text-red-500">*</span>
                      </label>
                      <select
                        value={formData.deviceSKU}
                        onChange={(e) => setFormData({ ...formData, deviceSKU: e.target.value })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        required
                      >
                        <option value="AC-HOME-V1">AquaChain Home V1 - ₹15,000</option>
                      </select>
                    </div>

                    {/* Address */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        <MapPin className="w-4 h-4 inline mr-2" />
                        Installation Address <span className="text-red-500">*</span>
                      </label>
                      <textarea
                        value={formData.address}
                        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                        placeholder="Enter complete address with pincode"
                        rows={3}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 resize-none"
                        required
                      />
                    </div>

                    {/* Phone */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        <Phone className="w-4 h-4 inline mr-2" />
                        Contact Phone <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        placeholder="+91-9876543210"
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        required
                      />
                    </div>

                    {/* Payment Method */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        <CreditCard className="w-4 h-4 inline mr-2" />
                        Payment Method <span className="text-red-500">*</span>
                      </label>
                      <div className="grid grid-cols-2 gap-4">
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, paymentMethod: 'COD' })}
                          className={`p-4 border-2 rounded-lg transition ${
                            formData.paymentMethod === 'COD'
                              ? 'border-cyan-500 bg-cyan-50'
                              : 'border-gray-200 hover:border-cyan-300'
                          }`}
                        >
                          <div className="font-semibold text-gray-900">Cash on Delivery</div>
                          <div className="text-xs text-gray-600">Pay when device is delivered</div>
                        </button>
                        <button
                          type="button"
                          onClick={() => setFormData({ ...formData, paymentMethod: 'ONLINE' })}
                          className={`p-4 border-2 rounded-lg transition ${
                            formData.paymentMethod === 'ONLINE'
                              ? 'border-cyan-500 bg-cyan-50'
                              : 'border-gray-200 hover:border-cyan-300'
                          }`}
                        >
                          <div className="font-semibold text-gray-900">Online Payment</div>
                          <div className="text-xs text-gray-600">Pay online after quote</div>
                        </button>
                      </div>
                    </div>

                    {/* Preferred Installation Slot */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        <Calendar className="w-4 h-4 inline mr-2" />
                        Preferred Installation Date (Optional)
                      </label>
                      <input
                        type="datetime-local"
                        value={formData.preferredSlot}
                        onChange={(e) => setFormData({ ...formData, preferredSlot: e.target.value })}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      />
                    </div>

                    {/* Info Box */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                      <p className="text-sm text-blue-900">
                        <strong>Note:</strong> After submitting, our admin team will review your request and provide a detailed quote. You'll be notified via email and can track the order status in your dashboard.
                      </p>
                    </div>

                    {/* Footer */}
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
                        className="px-6 py-3 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                      >
                        {isSubmitting ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Submitting...</span>
                          </>
                        ) : (
                          <>
                            <Package className="w-4 h-4" />
                            <span>Submit Request</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default RequestDeviceModal;
