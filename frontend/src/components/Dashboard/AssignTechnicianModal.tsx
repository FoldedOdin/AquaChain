import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { Wrench } from 'lucide-react';

interface AssignTechnicianModalProps {
  isOpen: boolean;
  onClose: () => void;
  order: any;
  onSuccess: () => void;
}

const AssignTechnicianModal: React.FC<AssignTechnicianModalProps> = ({ isOpen, onClose, order, onSuccess }) => {
  const [technicians, setTechnicians] = useState<any[]>([]);
  const [selectedTechId, setSelectedTechId] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      fetchTechnicians();
    }
  }, [isOpen]);

  const fetchTechnicians = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch('http://localhost:3002/api/admin/users', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const techs = data.users.filter((u: any) => u.role === 'technician');
        setTechnicians(techs);
      }
    } catch (error) {
      console.error('Failed to fetch technicians:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTechId) {
      alert('Please select a technician');
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const response = await fetch(`http://localhost:3002/api/admin/orders/${order.orderId}/assign`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ technicianId: selectedTechId })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to assign technician');
      }

      onSuccess();
      onClose();
    } catch (error: any) {
      console.error('Error assigning technician:', error);
      alert(error.message || 'Failed to assign technician. Please try again.');
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
              <div className="bg-gradient-to-r from-indigo-500 to-blue-600 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Wrench className="w-6 h-6 text-white" />
                  <h2 className="text-2xl font-bold text-white">Assign Technician</h2>
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
                    <p className="text-sm text-gray-600">Device: {order.provisionedDeviceId}</p>
                    <p className="text-sm text-gray-600">Address: {order.address.split(',')[0]}</p>
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Technician <span className="text-red-500">*</span>
                  </label>
                  {isLoading ? (
                    <div className="text-center py-4">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
                      <p className="text-sm text-gray-600 mt-2">Loading technicians...</p>
                    </div>
                  ) : technicians.length === 0 ? (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
                      <p className="text-sm text-yellow-800">No technicians available</p>
                    </div>
                  ) : (
                    <select
                      value={selectedTechId}
                      onChange={(e) => setSelectedTechId(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      required
                    >
                      <option value="">Choose a technician...</option>
                      {technicians.map((tech) => (
                        <option key={tech.userId} value={tech.userId}>
                          {tech.profile?.firstName} {tech.profile?.lastName} ({tech.email})
                        </option>
                      ))}
                    </select>
                  )}
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
                    disabled={isSubmitting || technicians.length === 0}
                    className="px-6 py-3 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSubmitting ? 'Assigning...' : 'Assign Technician'}
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

export default AssignTechnicianModal;
