import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { 
  Package, 
  Search, 
  Filter, 
  AlertTriangle, 
  CheckCircle, 
  Plus,
  Edit,
  Trash2,
  TrendingUp,
  History,
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

interface AdminInventoryManagementProps {
  isOpen: boolean;
  onClose: () => void;
}

const AdminInventoryManagement: React.FC<AdminInventoryManagementProps> = ({ isOpen, onClose }) => {
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRestockModal, setShowRestockModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  
  // Form states
  const [formData, setFormData] = useState({
    partId: '',
    name: '',
    category: 'Sensors',
    quantity: 0,
    location: '',
    description: '',
    unitPrice: 0,
    minQuantity: 5
  });
  const [restockQuantity, setRestockQuantity] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

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
      console.log('🔍 Fetching inventory with token:', token ? 'Present' : 'Missing');
      
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/inventory`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('📦 Inventory response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ Inventory data received:', data.count, 'items');
        console.log('📋 Inventory items:', data.inventory);
        setInventory(data.inventory || []);
      } else {
        const errorData = await response.json();
        console.error('❌ Inventory fetch failed:', errorData);
      }
    } catch (error) {
      console.error('💥 Error fetching inventory:', error);
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

  // Handle add item
  const handleAddItem = useCallback(() => {
    setFormData({
      partId: `PART-${Date.now().toString().slice(-3)}`,
      name: '',
      category: 'Sensors',
      quantity: 0,
      location: '',
      description: '',
      unitPrice: 0,
      minQuantity: 5
    });
    setShowAddModal(true);
  }, []);

  // Handle edit item
  const handleEditItem = useCallback((item: InventoryItem) => {
    setSelectedItem(item);
    setFormData({
      partId: item.partId,
      name: item.name,
      category: item.category,
      quantity: item.quantity,
      location: item.location,
      description: item.description || '',
      unitPrice: item.unitPrice || 0,
      minQuantity: item.minQuantity || 5
    });
    setShowEditModal(true);
  }, []);

  // Handle restock
  const handleRestock = useCallback((item: InventoryItem) => {
    setSelectedItem(item);
    setRestockQuantity(0);
    setShowRestockModal(true);
  }, []);

  // Handle delete
  const handleDelete = useCallback((item: InventoryItem) => {
    setSelectedItem(item);
    setShowDeleteModal(true);
  }, []);

  // Submit add
  const submitAdd = async () => {
    if (!formData.name || !formData.location) {
      alert('Please fill in all required fields');
      return;
    }

    setIsProcessing(true);
    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/inventory`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const data = await response.json();
        setInventory(prev => [...prev, data.item]);
        setShowAddModal(false);
        alert('Item added successfully');
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to add item');
      }
    } catch (error) {
      console.error('Add error:', error);
      alert('Failed to add item');
    } finally {
      setIsProcessing(false);
    }
  };

  // Submit edit
  const submitEdit = async () => {
    if (!selectedItem) return;

    setIsProcessing(true);
    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/inventory/${selectedItem.partId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setInventory(prev => prev.map(item => 
          item.partId === selectedItem.partId ? { ...item, ...formData } : item
        ));
        setShowEditModal(false);
        alert('Item updated successfully');
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to update item');
      }
    } catch (error) {
      console.error('Update error:', error);
      alert('Failed to update item');
    } finally {
      setIsProcessing(false);
    }
  };

  // Submit restock
  const submitRestock = async () => {
    if (!selectedItem || restockQuantity <= 0) {
      alert('Invalid quantity');
      return;
    }

    setIsProcessing(true);
    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/inventory/${selectedItem.partId}/restock`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ quantity: restockQuantity })
      });

      if (response.ok) {
        setInventory(prev => prev.map(item => 
          item.partId === selectedItem.partId 
            ? { ...item, quantity: item.quantity + restockQuantity, lastRestocked: new Date().toISOString() }
            : item
        ));
        setShowRestockModal(false);
        alert(`Successfully restocked ${restockQuantity} ${selectedItem.name}`);
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to restock');
      }
    } catch (error) {
      console.error('Restock error:', error);
      alert('Failed to restock');
    } finally {
      setIsProcessing(false);
    }
  };

  // Submit delete
  const submitDelete = async () => {
    if (!selectedItem) return;

    setIsProcessing(true);
    try {
      const token = localStorage.getItem('aquachain_token');
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002'}/api/admin/inventory/${selectedItem.partId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        setInventory(prev => prev.filter(item => item.partId !== selectedItem.partId));
        setShowDeleteModal(false);
        alert('Item deleted successfully');
      } else {
        const error = await response.json();
        alert(error.error || 'Failed to delete item');
      }
    } catch (error) {
      console.error('Delete error:', error);
      alert('Failed to delete item');
    } finally {
      setIsProcessing(false);
    }
  };

  // Calculate statistics
  const stats = useMemo(() => {
    const total = inventory.length;
    const inStock = inventory.filter(item => item.quantity > (item.minQuantity || 5)).length;
    const lowStock = inventory.filter(item => item.quantity > 0 && item.quantity <= (item.minQuantity || 5)).length;
    const outOfStock = inventory.filter(item => item.quantity === 0).length;
    const totalValue = inventory.reduce((sum, item) => sum + (item.quantity * (item.unitPrice || 0)), 0);
    return { total, inStock, lowStock, outOfStock, totalValue };
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
            <div className="bg-white rounded-xl shadow-xl w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b bg-gradient-to-r from-purple-600 to-blue-600">
                <div>
                  <h3 className="text-xl font-bold text-white">Inventory Management</h3>
                  <p className="text-sm text-purple-100 mt-1">
                    Manage all parts, tools, and supplies
                  </p>
                </div>
                <button 
                  onClick={onClose}
                  className="text-white hover:text-gray-200 transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Statistics */}
              <div className="p-4 border-b bg-gray-50">
                <div className="grid grid-cols-5 gap-4">
                  <div className="bg-white rounded-lg p-3 border border-gray-200">
                    <div className="flex items-center gap-2 mb-1">
                      <Package className="w-4 h-4 text-purple-600" />
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
                      <AlertTriangle className="w-4 h-4 text-yellow-600" />
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
                  <div className="bg-white rounded-lg p-3 border border-blue-200">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp className="w-4 h-4 text-blue-600" />
                      <span className="text-xs font-medium text-gray-600">Total Value</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-600">₹{stats.totalValue.toFixed(2)}</p>
                  </div>
                </div>
              </div>

              {/* Toolbar */}
              <div className="p-4 border-b bg-gray-50">
                <div className="flex gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search inventory..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-gray-600" />
                    <select
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                      className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="all">All Categories</option>
                      {categories.map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={handleAddItem}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium"
                  >
                    <Plus className="w-5 h-5" />
                    Add Item
                  </button>
                </div>
              </div>

              {/* Inventory Table */}
              <div className="flex-1 overflow-y-auto p-6">
                {isLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading inventory...</p>
                  </div>
                ) : filteredInventory.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b-2 border-gray-200">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Item</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Category</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Quantity</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Location</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Price</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {filteredInventory.map((item) => {
                          const stockStatus = getStockStatus(item);
                          return (
                            <tr key={item.partId} className="hover:bg-gray-50">
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600">
                                    {getCategoryIcon(item.category)}
                                  </div>
                                  <div>
                                    <p className="font-semibold text-gray-900">{item.name}</p>
                                    <p className="text-xs text-gray-500">{item.partId}</p>
                                  </div>
                                </div>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-900">{item.category}</td>
                              <td className="px-4 py-3">
                                <span className="font-semibold text-gray-900">{item.quantity}</span>
                                <span className="text-xs text-gray-500 ml-1">/ {item.minQuantity} min</span>
                              </td>
                              <td className="px-4 py-3 text-sm text-gray-600">{item.location}</td>
                              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                                ₹{(item.unitPrice || 0).toFixed(2)}
                              </td>
                              <td className="px-4 py-3">
                                <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium border ${stockStatus.color}`}>
                                  {stockStatus.label}
                                </span>
                              </td>
                              <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                  <button
                                    onClick={() => handleRestock(item)}
                                    className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors"
                                    title="Restock"
                                  >
                                    <TrendingUp className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => handleEditItem(item)}
                                    className="p-1.5 text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                    title="Edit"
                                  >
                                    <Edit className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => handleDelete(item)}
                                    className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                                    title="Delete"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Items Found</h3>
                    <p className="text-gray-600 mb-4">
                      {searchTerm || selectedCategory !== 'all'
                        ? 'Try adjusting your search or filters.'
                        : 'Get started by adding your first inventory item.'}
                    </p>
                    <button
                      onClick={handleAddItem}
                      className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      <Plus className="w-5 h-5" />
                      Add First Item
                    </button>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Tip:</span> Click the restock icon to quickly add more quantity
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

          {/* Add Item Modal */}
          <AnimatePresence>
            {showAddModal && (
              <>
                <div className="fixed inset-0 bg-black bg-opacity-50 z-[60]" onClick={() => !isProcessing && setShowAddModal(false)} />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="fixed inset-0 z-[70] flex items-center justify-center p-4"
                >
                  <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Add New Item</h3>
                    
                    <div className="space-y-4 mb-6">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Part ID *</label>
                          <input
                            type="text"
                            value={formData.partId}
                            onChange={(e) => setFormData({...formData, partId: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="PART-XXX"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Item name"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData({...formData, category: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="Sensors">Sensors</option>
                            <option value="Filters">Filters</option>
                            <option value="Tools">Tools</option>
                            <option value="Chemicals">Chemicals</option>
                            <option value="Parts">Parts</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Location *</label>
                          <input
                            type="text"
                            value={formData.location}
                            onChange={(e) => setFormData({...formData, location: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="Warehouse A - Shelf 1"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                          <input
                            type="number"
                            min="0"
                            value={formData.quantity}
                            onChange={(e) => setFormData({...formData, quantity: parseInt(e.target.value) || 0})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Unit Price</label>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={formData.unitPrice}
                            onChange={(e) => setFormData({...formData, unitPrice: parseFloat(e.target.value) || 0})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Min Quantity</label>
                          <input
                            type="number"
                            min="0"
                            value={formData.minQuantity}
                            onChange={(e) => setFormData({...formData, minQuantity: parseInt(e.target.value) || 5})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData({...formData, description: e.target.value})}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          placeholder="Item description..."
                        />
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowAddModal(false)}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={submitAdd}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                      >
                        {isProcessing ? 'Adding...' : 'Add Item'}
                      </button>
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Edit Item Modal */}
          <AnimatePresence>
            {showEditModal && selectedItem && (
              <>
                <div className="fixed inset-0 bg-black bg-opacity-50 z-[60]" onClick={() => !isProcessing && setShowEditModal(false)} />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="fixed inset-0 z-[70] flex items-center justify-center p-4"
                >
                  <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Edit Item: {selectedItem.name}</h3>
                    
                    <div className="space-y-4 mb-6">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Part ID</label>
                          <input
                            type="text"
                            value={formData.partId}
                            disabled
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => setFormData({...formData, name: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Category *</label>
                          <select
                            value={formData.category}
                            onChange={(e) => setFormData({...formData, category: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="Sensors">Sensors</option>
                            <option value="Filters">Filters</option>
                            <option value="Tools">Tools</option>
                            <option value="Chemicals">Chemicals</option>
                            <option value="Parts">Parts</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Location *</label>
                          <input
                            type="text"
                            value={formData.location}
                            onChange={(e) => setFormData({...formData, location: e.target.value})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                          <input
                            type="number"
                            min="0"
                            value={formData.quantity}
                            onChange={(e) => setFormData({...formData, quantity: parseInt(e.target.value) || 0})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Unit Price</label>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={formData.unitPrice}
                            onChange={(e) => setFormData({...formData, unitPrice: parseFloat(e.target.value) || 0})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Min Quantity</label>
                          <input
                            type="number"
                            min="0"
                            value={formData.minQuantity}
                            onChange={(e) => setFormData({...formData, minQuantity: parseInt(e.target.value) || 5})}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          />
                        </div>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData({...formData, description: e.target.value})}
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowEditModal(false)}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={submitEdit}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                      >
                        {isProcessing ? 'Saving...' : 'Save Changes'}
                      </button>
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Restock Modal */}
          <AnimatePresence>
            {showRestockModal && selectedItem && (
              <>
                <div className="fixed inset-0 bg-black bg-opacity-50 z-[60]" onClick={() => !isProcessing && setShowRestockModal(false)} />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="fixed inset-0 z-[70] flex items-center justify-center p-4"
                >
                  <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Restock Item</h3>
                    
                    <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center text-purple-600">
                          {getCategoryIcon(selectedItem.category)}
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-900">{selectedItem.name}</h4>
                          <p className="text-sm text-gray-600">Current stock: {selectedItem.quantity}</p>
                        </div>
                      </div>
                    </div>

                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Quantity to Add *
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={restockQuantity}
                        onChange={(e) => setRestockQuantity(parseInt(e.target.value) || 0)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="Enter quantity"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        New stock will be: {selectedItem.quantity + restockQuantity}
                      </p>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowRestockModal(false)}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={submitRestock}
                        disabled={isProcessing || restockQuantity <= 0}
                        className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                      >
                        {isProcessing ? 'Restocking...' : 'Confirm Restock'}
                      </button>
                    </div>
                  </div>
                </motion.div>
              </>
            )}
          </AnimatePresence>

          {/* Delete Confirmation Modal */}
          <AnimatePresence>
            {showDeleteModal && selectedItem && (
              <>
                <div className="fixed inset-0 bg-black bg-opacity-50 z-[60]" onClick={() => !isProcessing && setShowDeleteModal(false)} />
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="fixed inset-0 z-[70] flex items-center justify-center p-4"
                >
                  <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                        <AlertTriangle className="w-6 h-6 text-red-600" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">Delete Item</h3>
                        <p className="text-sm text-gray-600">This action cannot be undone</p>
                      </div>
                    </div>
                    
                    <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-700 mb-2">
                        Are you sure you want to delete:
                      </p>
                      <p className="font-semibold text-gray-900">{selectedItem.name}</p>
                      <p className="text-sm text-gray-600">Part ID: {selectedItem.partId}</p>
                    </div>

                    <div className="flex gap-3">
                      <button
                        onClick={() => setShowDeleteModal(false)}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={submitDelete}
                        disabled={isProcessing}
                        className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                      >
                        {isProcessing ? 'Deleting...' : 'Delete Item'}
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

export default AdminInventoryManagement;
