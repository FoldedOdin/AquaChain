import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNotification } from '../../../contexts/NotificationContext';

// ─── Types (matching the real /api/v1/technician/inventory shape) ─────────────
interface Part {
  partId: string;
  name: string;
  category: string;
  quantity: number;
  location: string;
  status: string;
  description?: string;
  unitPrice?: number;
  minQuantity?: number;
  lastRestocked?: string;
}

const API = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';

function getToken() {
  return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
}

// ─── Status badge helper ──────────────────────────────────────────────────────
function StockBadge({ part }: { part: Part }) {
  const min = part.minQuantity ?? 5;
  if (part.quantity === 0)
    return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">Out of Stock</span>;
  if (part.quantity <= min)
    return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">Low Stock</span>;
  return <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">In Stock</span>;
}

// ─── Restock Modal ────────────────────────────────────────────────────────────
function RestockModal({ part, onClose, onSuccess }: {
  part: Part;
  onClose: () => void;
  onSuccess: (partId: string, qty: number) => void;
}) {
  const [qty, setQty] = useState(part.minQuantity ?? 10);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (qty <= 0) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/admin/inventory/${part.partId}/restock`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: qty }),
      });
      if (res.ok) {
        onSuccess(part.partId, qty);
        onClose();
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-40 z-50" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Restock Item</h3>
          <p className="text-sm text-gray-500 mb-4">{part.name}</p>
          <label className="block text-sm font-medium text-gray-700 mb-1">Quantity to add</label>
          <input
            type="number" min={1} value={qty}
            onChange={e => setQty(Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-400 mb-4"
          />
          <div className="flex gap-3 justify-end">
            <button onClick={onClose} className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50">Cancel</button>
            <button
              onClick={submit} disabled={loading || qty <= 0}
              className="px-4 py-2 text-sm bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
            >
              {loading ? 'Restocking…' : 'Confirm Restock'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────
const InventoryManagerView: React.FC = () => {
  const { showNotification } = useNotification();
  const [parts, setParts] = useState<Part[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [restockTarget, setRestockTarget] = useState<Part | null>(null);

  // ── Fetch from the same endpoint technicians use ──────────────────────────
  const fetchInventory = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/technician/inventory`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        const data = await res.json();
        setParts(data.inventory || []);
      } else {
        showNotification('Failed to load inventory', 'error');
      }
    } catch {
      showNotification('Network error loading inventory', 'error');
    } finally {
      setIsLoading(false);
    }
  }, [showNotification]);

  useEffect(() => { fetchInventory(); }, [fetchInventory]);

  // ── Admin: delete item ────────────────────────────────────────────────────
  const handleDelete = async (part: Part) => {
    if (!window.confirm(`Delete "${part.name}" from inventory? This cannot be undone.`)) return;
    try {
      const res = await fetch(`${API}/api/admin/inventory/${part.partId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) {
        setParts(prev => prev.filter(p => p.partId !== part.partId));
        showNotification(`"${part.name}" removed from inventory`, 'success');
      } else {
        showNotification('Failed to delete item', 'error');
      }
    } catch {
      showNotification('Network error', 'error');
    }
  };

  // ── After successful restock, update local quantity ───────────────────────
  const handleRestockSuccess = (partId: string, qty: number) => {
    setParts(prev => prev.map(p =>
      p.partId === partId ? { ...p, quantity: p.quantity + qty } : p
    ));
    showNotification('Inventory restocked successfully', 'success');
  };

  // ── Derived data ──────────────────────────────────────────────────────────
  const categories = useMemo(() =>
    ['all', ...Array.from(new Set(parts.map(p => p.category)))],
    [parts]
  );

  const filtered = useMemo(() => parts.filter(p => {
    const q = searchTerm.toLowerCase();
    const matchSearch = !q || p.name.toLowerCase().includes(q) || p.partId.toLowerCase().includes(q);
    const matchCat = selectedCategory === 'all' || p.category === selectedCategory;
    return matchSearch && matchCat;
  }), [parts, searchTerm, selectedCategory]);

  const alerts = useMemo(() => parts.filter(p => {
    const min = p.minQuantity ?? 5;
    return p.quantity <= min;
  }), [parts]);

  const stats = useMemo(() => ({
    total: parts.length,
    lowStock: parts.filter(p => { const m = p.minQuantity ?? 5; return p.quantity > 0 && p.quantity <= m; }).length,
    outOfStock: parts.filter(p => p.quantity === 0).length,
    totalValue: parts.reduce((s, p) => s + (p.quantity * (p.unitPrice ?? 0)), 0),
  }), [parts]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-8 h-8 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mr-3" />
        <span className="text-gray-500 text-sm">Loading inventory…</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Parts', value: stats.total, color: 'text-blue-600', bg: 'bg-blue-50' },
          { label: 'Low Stock', value: stats.lowStock, color: 'text-amber-600', bg: 'bg-amber-50' },
          { label: 'Out of Stock', value: stats.outOfStock, color: 'text-red-600', bg: 'bg-red-50' },
          { label: 'Total Value', value: `₹${stats.totalValue.toLocaleString()}`, color: 'text-green-600', bg: 'bg-green-50' },
        ].map(s => (
          <div key={s.label} className={`${s.bg} rounded-lg p-4 border border-gray-100`}>
            <p className="text-xs text-gray-500 mb-1">{s.label}</p>
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {/* Stock Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">Stock Alerts</h3>
          <div className="space-y-2">
            {alerts.map(p => {
              const isCritical = p.quantity === 0;
              return (
                <div key={p.partId} className={`flex items-center justify-between p-3 rounded-lg border-l-4 ${
                  isCritical ? 'bg-red-50 border-red-400' : 'bg-amber-50 border-amber-400'
                }`}>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{p.name}</p>
                    <p className="text-xs text-gray-500">
                      Stock: {p.quantity} / Min: {p.minQuantity ?? 5} — {p.location}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      isCritical ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                    }`}>{isCritical ? 'CRITICAL' : 'WARNING'}</span>
                    <button
                      onClick={() => setRestockTarget(p)}
                      className="text-xs px-3 py-1 bg-orange-500 text-white rounded-lg hover:bg-orange-600"
                    >
                      Restock
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          type="text" placeholder="Search by name or part ID…"
          value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
        />
        <select
          value={selectedCategory} onChange={e => setSelectedCategory(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
        >
          {categories.map(c => (
            <option key={c} value={c}>{c === 'all' ? 'All Categories' : c}</option>
          ))}
        </select>
        <button
          onClick={fetchInventory}
          className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Inventory Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {['Part', 'Category', 'Stock', 'Min Qty', 'Unit Price', 'Location', 'Status', 'Actions'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-gray-400 text-sm">No items found</td>
                </tr>
              ) : filtered.map(part => (
                <tr key={part.partId} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{part.name}</p>
                    <p className="text-xs text-gray-400 font-mono">{part.partId}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{part.category}</td>
                  <td className="px-4 py-3 font-semibold text-gray-900">{part.quantity}</td>
                  <td className="px-4 py-3 text-gray-500">{part.minQuantity ?? 5}</td>
                  <td className="px-4 py-3 text-gray-600">
                    {part.unitPrice ? `₹${part.unitPrice.toLocaleString()}` : '—'}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">{part.location}</td>
                  <td className="px-4 py-3"><StockBadge part={part} /></td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setRestockTarget(part)}
                        className="px-3 py-1 text-xs bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                      >
                        Restock
                      </button>
                      <button
                        onClick={() => handleDelete(part)}
                        className="px-3 py-1 text-xs border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Restock Modal */}
      {restockTarget && (
        <RestockModal
          part={restockTarget}
          onClose={() => setRestockTarget(null)}
          onSuccess={handleRestockSuccess}
        />
      )}
    </div>
  );
};

export default InventoryManagerView;
