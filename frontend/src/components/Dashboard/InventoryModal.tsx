import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { 
  Package, 
  Search, 
  Filter, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  TrendingDown,
  Box,
  Wrench,
  Droplet,
  Zap
} from 'lucide-react';

interface InventoryItem {
  partId: string;
  name: string;
  category: string;
  quantity: number;
  location: string;
  status: string;
  description?: string;
  unitPrice?: number;
  lastRestocked?: string;
  minQuantity?: number;
}

interface CheckedOutItem {
  partId: string;
  name: string;
  quantity: number;
  checkedOutAt: string;
  taskId?: string;
}

interface InventoryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const InventoryModal: React.FC<InventoryModalProps> = ({ isOpen, onClose }) => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [myCheckouts, setMyCheckouts] = useState<CheckedOutItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [checkoutQuantity, setCheckoutQuantity] = useState(1);
  const [checkoutTaskId, setCheckoutTaskId] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<'available' | 'my-checkouts'>('available');

  // Fetch inventory
  useEffect(() => {
    if (isOpen) {
      fetchInventory();
    }
  }, [isOpen]);

  const fetchInventory = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/v1/technician/inventory`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setInventory(data.inventory || []);
      } else {
        console.error('Failed to fetch inventory');
      }
    } catch (error) {
      console.error('Error fetching inventory:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter inventory
  const filteredInventory = useMemo(() => {
    return inventory.filter(item => {
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           item.description?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [inventory, searchTerm, selectedCategory]);

  // Get categories
  const categories = useMemo(() => {
    const cats = new Set(inventory.map(item => item.category));
    return Array.from(cats);
  }, [inventory]);

  // Get stock status
  const getStockStatus = (item: InventoryItem) => {
    const minQty = item.minQuantity || 5;
    if (item.quantity === 0) return { label: 'Out of Stock', color: 'bg-red-100 text-red-800 border-red-300' };
    if (item.quantity <= minQty) return { label: 'Low Stock', color: 'bg-yellow-100 text-yellow-800 border-yellow-300' };
    return { label: 'In Stock', color: 'bg-green-100 text-green-800 border-green-300' };
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'sensors': return <Zap className="w-5 h-5" />;
      case 'filters': return <Droplet className="w-5 h-5" />;
      case 'tools': return <Wrench className="w-5 h-5" />;
      case 'chemicals': return <Droplet className="w-5 h-5" />;
      case 'parts': return <Box className="w-5 h-5" />;
      default: return <Package className="w-5 h-5" />;
    }
  };

  // Handle checkout
  const handleCheckout = useCallback((item: InventoryItem) => {
    setSelectedItem(item);
    setCheckoutQuantity(1);
    setCheckoutTaskId('');
    setShowCheckoutModal(true);
  }, []);

  // Submit checkout
  const submitCheckout = async () => {
    if (!selectedItem || checkoutQuantity <= 0 || checkoutQuantity > selectedItem.quantity) {
      alert('Invalid quantity');
      return;
    }

    setIsProcessing(true);
    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/v1/technician/inventory/checkout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          partId: selectedItem.partId,
          quantity: checkoutQuantity,
          taskId: checkoutTaskId || undefined
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update local inventory
        setInventory(prev => prev.map(item => 
          item.partId === selectedItem.partId 
            ? { ...item, quantity: item.quantity - checkoutQuantity }
            : item
        ));
        
        // Add to my checkouts
        setMyCheckouts(prev => {
          const existing = prev.find(c => c.partId === selectedItem.partId && c.taskId === checkoutTaskId);
          if (existing) {
            return prev.map(c => 
              c.partId === selectedItem.partId && c.taskId === checkoutTaskId
                ? { ...c, quantity: c.quantity + checkoutQuantity }
                : c
            );
          } else {
            return [...prev, {
              partId: selectedItem.partId,
              name: selectedItem.name,
              quantity: checkoutQuantity,
              checkedOutAt: data.checkedOutAt || new Date().toISOString(),
              taskId: checkoutTaskId || undefined
            }];
          }
        });
        
        setShowCheckoutModal(false);
        setSelectedItem(null);
        alert(`Successfully checked out ${checkoutQuantity} ${selectedItem.name}`);
      } else {
        const error = await response.json();
        alert(error.error || 'Checkout failed');
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Checkout failed');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle return
  const handleReturn = async (item: InventoryItem) => {
    const quantity = prompt(`How many ${item.name} are you returning?`);
    if (!quantity || parseInt(quantity) <= 0) return;

    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/v1/technician/inventory/return`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          partId: item.partId,
          quantity: parseInt(quantity)
        })
      });

      if (response.ok) {
        // Update local inventory
        setInventory(prev => prev.map(i => 
          i.partId === item.partId 
            ? { ...i, quantity: i.quantity + parseInt(quantity) }
            : i
        ));
        
        // Remove from my checkouts
        setMyCheckouts(prev => {
          const checkout = prev.find(c => c.partId === item.partId);
          if (checkout) {
            if (checkout.quantity <= parseInt(quantity)) {
              return prev.filter(c => c.partId !== item.partId);
            } else {
              return prev.map(c => 
                c.partId === item.partId
                  ? { ...c, quantity: c.quantity - parseInt(quantity) }
                  : c
              );
            }
          }
          return prev;
        });
        
        alert(`Successfully returned ${quantity} ${item.name}`);
      } else {
        const error = await response.json();
        alert(error.error || 'Return failed');
      }
    } catch (error) {
      console.error('Return error:', error);
      alert('Return failed');
    }
  };

  // Handle request restock
  const handleRequestRestock = async (item: InventoryItem) => {
    const quantity = prompt(`How many ${item.name} do you need?`);
    if (!quantity || parseInt(quantity) <= 0) return;

    const reason = prompt('Reason for restock request (optional):') || 'Stock running low';

    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/v1/technician/inventory/request-restock`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          partId: item.partId,
          partName: item.name,
          quantity: parseInt(quantity),
          reason: reason,
          currentStock: item.quantity
        })
      });

      if (response.ok) {
        alert(`Restock request sent to admin for ${quantity} ${item.name}`);
      } else {
        const error = await response.json();
        alert(error.error || 'Request failed');
      }
    } catch (error) {
      console.error('Request error:', error);
      alert('Request failed');
    }
  };

  // Calculate statistics
  const stats = useMemo(() => {
    const total = inventory.length;
    const inStock = inventory.filter(item => item.quantity > (item.minQuantity || 5)).length;
    const lowStock = inventory.filter(item => item.quantity > 0 && item.quantity <= (item.minQuantity || 5)).length;
    const outOfStock = inventory.filter(item => item.quantity === 0).length;
    return { total, inStock, lowStock, outOfStock };
  }, [inventory]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40" 
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Parts & Tools Inventory</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {activeTab === 'available' 
                      ? `${filteredInventory.length} item${filteredInventory.length !== 1 ? 's' : ''} available`
                      : `${myCheckouts.length} item${myCheckouts.length !== 1 ? 's' : ''} checked out`
                    }
                  </p>
                </div>
                <button 
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex border-b bg-gray-50">
                <button
                  onClick={() => setActiveTab('available')}
                  className={`flex-1 px-6 py-3 font-medium transition-colors ${
                    activeTab === 'available'
                      ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  Available Inventory
                </button>
                <button
                  onClick={() => setActiveTab('my-checkouts')}
                  className={`flex-1 px-6 py-3 font-medium transition-colors relative ${
                    activeTab === 'my-checkouts'
                      ? 'text-blue-600 border-b-2 border-blue-600 bg-white'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  My Checkouts
                  {myCheckouts.length > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-blue-600 rounded-full">
                      {myCheckouts.reduce((sum, item) => sum + item.quantity, 0)}
                    </span>
                  )}
                </button>
              </div>

              {/* Statistics - Only show for Available tab */}
              {activeTab === 'available' && (
                <div className="p-4 border-b bg-gray-50">
                  <div className="grid grid-cols-4 gap-4">
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    <div className="flex items-center gap-2 mb-1">
                      <Package className="w-4 h-4 text-blue-600" />
                      <span className="text-xs font-medium text-gray-600">Total Items</span>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-green-200">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                      <span className="text-xs font-medium text-gray-600">In Stock</span>
                    </div>
                    <p className="text-2xl font-bold text-green-600">{stats.inStock}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-yellow-200">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingDown className="w-4 h-4 text-yellow-600" />
                      <span className="text-xs font-medium text-gray-600">Low Stock</span>
                    </div>
                    <p className="text-2xl font-bold text-yellow-600">{stats.lowStock}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3 border border-red-200">
                    <div className="flex items-center gap-2 mb-1">
                      <AlertTriangle className="w-4 h-4 text-red-600" />
                      <span className="text-xs font-medium text-gray-600">Out of Stock</span>
                    </div>
                    <p className="text-2xl font-bold text-red-600">{stats.outOfStock}</p>
                  </div>
                </div>
              </div>
              )}

              {/* Search and Filter - Only show for Available tab */}
              {activeTab === 'available' && (
              <div className="p-4 border-b bg-gray-50">
                <div className="flex gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search parts and tools..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-gray-600" />
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Categories</option>
                      {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              )}

              {/* Content Area */}
              <div className="flex-1 overflow-y-auto p-6">
                {activeTab === 'available' ? (
                  /* Available Inventory */
                  isLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading inventory...</p>
                  </div>
                ) : filteredInventory.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredInventory.map((item) => {
                      const stockStatus = getStockStatus(item);
                      return (
                        <div 
                          key={item.partId} 
                          className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-all"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                                {getCategoryIcon(item.category)}
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900">{item.name}</h4>
                                <p className="text-xs text-gray-500">{item.category}</p>
                              </div>
                            </div>
                          </div>

                          {item.description && (
                            <p className="text-sm text-gray-600 mb-3">{item.description}</p>
                          )}

                          <div className="space-y-2 mb-3">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Quantity:</span>
                              <span className="font-semibold text-gray-900">{item.quantity}</span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Location:</span>
                              <span className="text-gray-900">{item.location}</span>
                            </div>
                            {item.unitPrice && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">Unit Price:</span>
                                <span className="text-gray-900">₹{item.unitPrice.toFixed(2)}</span>
                              </div>
                            )}
                          </div>

                          <div className="mb-3">
                            <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium border ${stockStatus.color}`}>
                              {stockStatus.label}
                            </span>
                          </div>

                          <div className="space-y-2">
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleCheckout(item)}
                                disabled={item.quantity === 0}
                                className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                              >
                                Checkout
                              </button>
                              <button
                                onClick={() => handleReturn(item)}
                                className="px-3 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-sm font-medium"
                              >
                                Return
                              </button>
                            </div>
                            {item.quantity <= (item.minQuantity || 5) && (
                              <button
                                onClick={() => handleRequestRestock(item)}
                                className="w-full px-3 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm font-medium flex items-center justify-center gap-2"
                              >
                                <AlertTriangle className="w-4 h-4" />
                                Request Restock
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Items Found</h3>
                    <p className="text-gray-600">
                      {searchTerm || selectedCategory !== 'all'
                        ? 'Try adjusting your search or filters.'
                        : 'No inventory items available.'}
                    </p>
                  </div>
                )
                ) : (
                  /* My Checkouts */
                  myCheckouts.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {myCheckouts.map((checkout, index) => (
                        <div 
                          key={`${checkout.partId}-${checkout.taskId || index}`}
                          className="border-2 border-blue-200 bg-blue-50 rounded-lg p-4"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                                <Package className="w-5 h-5" />
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-900">{checkout.name}</h4>
                                <p className="text-xs text-gray-600">
                                  Checked out {new Date(checkout.checkedOutAt).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-2 mb-3">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Quantity:</span>
                              <span className="font-bold text-blue-600 text-lg">{checkout.quantity}</span>
                            </div>
                            {checkout.taskId && (
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-gray-600">Task ID:</span>
                                <span className="text-gray-900 font-mono text-xs">{checkout.taskId}</span>
                              </div>
                            )}
                          </div>

                          <button
                            onClick={() => {
                              const item = inventory.find(i => i.partId === checkout.partId);
                              if (item) handleReturn(item);
                            }}
                            className="w-full px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                          >
                            Return Items
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <CheckCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">No Checked Out Items</h3>
                      <p className="text-gray-600">
                        You haven't checked out any items yet. Switch to Available Inventory to checkout items.
                      </p>
                    </div>
                  )
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Tip:</span> Low stock items are highlighted in yellow
                  </div>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Checkout Modal */}
          <AnimatePresence>
            {showCheckoutModal && selectedItem && (
              <>
                <div className="fixed inset-0 bg-black bg-opacity-50 z-[60]" onClick={() => !isProcessing && setShowCheckoutModal(false)} />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="fixed inset-0 z-[70] flex items-center justify-center p-4"
                >
                  <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Checkout Item</h3>
                    
                    <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                          {getCategoryIcon(selectedItem.category)}
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">{selectedItem.name}</h4>
                          <p className="text-sm text-gray-600">Available: {selectedItem.quantity}</p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 mb-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Quantity *
                        </label>
                        <input
                          type="number"
                          min="1"
                          max={selectedItem.quantity}
                          value={checkoutQuantity}
                          onChange={(e) => setCheckoutQuantity(parseInt(e.target.value) || 1)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Task ID (Optional)
                        </label>
                        <input
                          type="text"
                          placeholder="e.g., TASK-001"
                          value={checkoutTaskId}
                          onChange={(e) => setCheckoutTaskId(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Link this checkout to a specific task</p>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowCheckoutModal(false)}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={submitCheckout}
                        disabled={isProcessing || checkoutQuantity <= 0 || checkoutQuantity > selectedItem.quantity}
                        className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isProcessing ? 'Processing...' : 'Confirm Checkout'}
                      </button>
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </>
      )}
    </AnimatePresence>
  );
};

export default InventoryModal;
