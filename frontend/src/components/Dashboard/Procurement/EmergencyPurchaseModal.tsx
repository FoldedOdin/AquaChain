/**
 * Emergency Purchase Modal Component
 * Modal for submitting emergency purchase requests with expedited workflow
 */

import React, { useState, useEffect } from 'react';
import { useNotification } from '../../../contexts/NotificationContext';
import LoadingSpinner from '../../Loading/LoadingSpinner';
import { EmergencyPurchaseRequest, PurchaseOrderItem } from '../../../services/procurementService';

interface EmergencyPurchaseModalProps {
  onSubmit: (request: EmergencyPurchaseRequest) => void;
  onClose: () => void;
}

const EmergencyPurchaseModal: React.FC<EmergencyPurchaseModalProps> = ({
  onSubmit,
  onClose
}) => {
  const { showNotification } = useNotification();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    supplierId: '',
    supplierName: '',
    budgetCategory: 'operations',
    emergencyReason: '',
    businessJustification: '',
    expectedDelivery: '',
    alternativeOptions: ''
  });
  const [items, setItems] = useState<PurchaseOrderItem[]>([{
    itemId: '',
    itemName: '',
    quantity: 1,
    unitPrice: 0,
    totalPrice: 0,
    specifications: ''
  }]);

  // Calculate total amount
  const totalAmount = items.reduce((sum, item) => sum + item.totalPrice, 0);

  // Update item total price when quantity or unit price changes
  const updateItemTotal = (index: number, quantity: number, unitPrice: number) => {
    const updatedItems = [...items];
    updatedItems[index] = {
      ...updatedItems[index],
      quantity,
      unitPrice,
      totalPrice: quantity * unitPrice
    };
    setItems(updatedItems);
  };

  // Add new item
  const addItem = () => {
    setItems([...items, {
      itemId: '',
      itemName: '',
      quantity: 1,
      unitPrice: 0,
      totalPrice: 0,
      specifications: ''
    }]);
  };

  // Remove item
  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  // Update item field
  const updateItem = (index: number, field: keyof PurchaseOrderItem, value: any) => {
    const updatedItems = [...items];
    updatedItems[index] = { ...updatedItems[index], [field]: value };
    
    // Update total price if quantity or unit price changed
    if (field === 'quantity' || field === 'unitPrice') {
      const quantity = field === 'quantity' ? value : updatedItems[index].quantity;
      const unitPrice = field === 'unitPrice' ? value : updatedItems[index].unitPrice;
      updatedItems[index].totalPrice = quantity * unitPrice;
    }
    
    setItems(updatedItems);
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (!formData.supplierId || !formData.supplierName) {
      showNotification('Supplier information is required', 'error');
      return;
    }

    if (!formData.emergencyReason.trim()) {
      showNotification('Emergency reason is required', 'error');
      return;
    }

    if (!formData.businessJustification.trim()) {
      showNotification('Business justification is required', 'error');
      return;
    }

    if (!formData.expectedDelivery) {
      showNotification('Expected delivery date is required', 'error');
      return;
    }

    // Validate items
    const validItems = items.filter(item => 
      item.itemName.trim() && item.quantity > 0 && item.unitPrice > 0
    );

    if (validItems.length === 0) {
      showNotification('At least one valid item is required', 'error');
      return;
    }

    if (totalAmount <= 0) {
      showNotification('Total amount must be greater than zero', 'error');
      return;
    }

    try {
      setIsSubmitting(true);
      
      const request: EmergencyPurchaseRequest = {
        supplierId: formData.supplierId,
        items: validItems,
        totalAmount,
        budgetCategory: formData.budgetCategory,
        emergencyReason: formData.emergencyReason.trim(),
        businessJustification: formData.businessJustification.trim(),
        expectedDelivery: formData.expectedDelivery,
        alternativeOptions: formData.alternativeOptions.trim() || undefined
      };

      await onSubmit(request);
    } catch (error) {
      console.error('Error submitting emergency purchase:', error);
      showNotification('Failed to submit emergency purchase request', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  // Get minimum date (today)
  const getMinDate = () => {
    return new Date().toISOString().split('T')[0];
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <svg className="w-6 h-6 text-red-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              Emergency Purchase Request
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Submit high-priority procurement with expedited approval workflow
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isSubmitting}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Supplier Information */}
          <div className="bg-red-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-4">Supplier Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Supplier ID <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.supplierId}
                  onChange={(e) => setFormData({ ...formData, supplierId: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="Enter supplier ID"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Supplier Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.supplierName}
                  onChange={(e) => setFormData({ ...formData, supplierName: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="Enter supplier name"
                  required
                />
              </div>
            </div>
          </div>

          {/* Items */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex justify-between items-center mb-4">
              <h4 className="font-medium text-gray-900">Items</h4>
              <button
                type="button"
                onClick={addItem}
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-3 py-1 rounded text-sm transition-colors duration-200"
              >
                Add Item
              </button>
            </div>
            
            <div className="space-y-4">
              {items.map((item, index) => (
                <div key={index} className="bg-white p-4 rounded-lg border">
                  <div className="flex justify-between items-start mb-3">
                    <h5 className="font-medium text-gray-900">Item {index + 1}</h5>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="lg:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Item Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={item.itemName}
                        onChange={(e) => updateItem(index, 'itemName', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter item name"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Quantity <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Unit Price <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.unitPrice}
                        onChange={(e) => updateItem(index, 'unitPrice', parseFloat(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="mt-3">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Specifications (Optional)
                    </label>
                    <textarea
                      value={item.specifications || ''}
                      onChange={(e) => updateItem(index, 'specifications', e.target.value)}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter item specifications..."
                    />
                  </div>
                  
                  <div className="mt-3 text-right">
                    <span className="text-sm text-gray-600">Total: </span>
                    <span className="font-medium text-lg">{formatCurrency(item.totalPrice)}</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 text-right border-t pt-4">
              <span className="text-lg font-semibold">Grand Total: {formatCurrency(totalAmount)}</span>
            </div>
          </div>

          {/* Emergency Details */}
          <div className="bg-amber-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-4">Emergency Details</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Budget Category <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.budgetCategory}
                  onChange={(e) => setFormData({ ...formData, budgetCategory: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
                  required
                >
                  <option value="operations">Operations</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="equipment">Equipment</option>
                  <option value="supplies">Supplies</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Expected Delivery <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  min={getMinDate()}
                  value={formData.expectedDelivery}
                  onChange={(e) => setFormData({ ...formData, expectedDelivery: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
                  required
                />
              </div>
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Emergency Reason <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.emergencyReason}
                onChange={(e) => setFormData({ ...formData, emergencyReason: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="Explain why this purchase is urgent and cannot wait for normal approval process..."
                required
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Business Justification <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.businessJustification}
                onChange={(e) => setFormData({ ...formData, businessJustification: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="Provide detailed business justification for this emergency purchase..."
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Alternative Options Considered (Optional)
              </label>
              <textarea
                value={formData.alternativeOptions}
                onChange={(e) => setFormData({ ...formData, alternativeOptions: e.target.value })}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500"
                placeholder="Describe any alternative options that were considered..."
              />
            </div>
          </div>

          {/* Risk Warning */}
          <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h5 className="font-medium text-red-800 mb-1">Emergency Purchase Risk Assessment</h5>
                <p className="text-sm text-red-700">
                  Emergency purchases bypass normal approval workflows and may carry higher risks. 
                  This request will be subject to enhanced scrutiny and audit. Ensure all information 
                  is accurate and the emergency nature is justified.
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || totalAmount <= 0}
              className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isSubmitting && <LoadingSpinner size="small" />}
              <span>Submit Emergency Request</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmergencyPurchaseModal;