import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Building2, ShoppingCart, AlertTriangle, CheckCircle,
  Clock, Star, ChevronRight, RefreshCw, Plus, X,
  ArrowUpRight, Truck, BarChart2, IndianRupee, ChevronDown,
  Zap, Filter, ThumbsUp, ThumbsDown, Calendar
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Supplier {
  supplierId: string;
  name: string;
  contactEmail?: string;
  products?: string[];
  leadTimeDays?: number;
  performanceScore?: number;
  status?: string;
  rating?: number;
}

interface SupplierPerformance {
  onTimeDeliveryRate?: number;
  defectRate?: number;
  avgLeadTimeDays?: number;
  delaysLastMonth?: number;
  overallScore?: number;
  recommendations?: string[];
  riskLevel?: string;
}

interface PurchaseOrder {
  poId?: string;
  orderId?: string;
  supplierId: string;
  supplierName?: string;
  items: Array<{ name: string; quantity: number; unitPrice?: number }>;
  status: string;
  totalAmount?: number;
  createdAt: string;
  expectedDelivery?: string;
  actualDelivery?: string;
  budgetCategory?: string;
}

interface InventoryItem {
  item_id?: string;
  partId?: string;
  name: string;
  quantity: number;
  minQuantity?: number;
  reorder_point?: number;
  preferred_supplier_id?: string;
  daily_usage?: number;        // units consumed per day (from ML/history)
  safety_stock?: number;       // buffer stock to hold
  unitPrice?: number;
}

interface ReorderAlert {
  item_id: string;
  item_name?: string;
  name?: string;
  urgency: string;
  current_quantity?: number;
  reorder_point?: number;
  recommended_quantity?: number;
  preferred_supplier_id?: string;
  projected_stockout_date?: string;
  daily_usage?: number;
  safety_stock?: number;
  unit_price?: number;
}

const API = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
function getToken() { return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken'); }
function authHeaders() { return { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' }; }

// ─── Helpers ──────────────────────────────────────────────────────────────────

function ScoreBadge({ score }: { score?: number }) {
  if (score == null) return <span className="text-gray-400 text-xs">—</span>;
  const color = score >= 85 ? 'text-green-700 bg-green-50' : score >= 65 ? 'text-amber-700 bg-amber-50' : 'text-red-700 bg-red-50';
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${color}`}>{score}%</span>;
}

function RiskBadge({ level }: { level?: string }) {
  if (!level) return null;
  const map: Record<string, string> = { low: 'bg-green-100 text-green-700', medium: 'bg-amber-100 text-amber-700', high: 'bg-red-100 text-red-700' };
  return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${map[level] ?? 'bg-gray-100 text-gray-600'}`}>{level.toUpperCase()} RISK</span>;
}

function StatusBadge({ status }: { status: string }) {
  const s = (status ?? '').toLowerCase();
  const map: Record<string, string> = {
    draft: 'bg-gray-100 text-gray-700', pending: 'bg-yellow-100 text-yellow-800',
    'pending approval': 'bg-yellow-100 text-yellow-800', approved: 'bg-blue-100 text-blue-800',
    ordered: 'bg-indigo-100 text-indigo-800', shipped: 'bg-cyan-100 text-cyan-800',
    'in transit': 'bg-cyan-100 text-cyan-800', received: 'bg-green-100 text-green-800',
    closed: 'bg-emerald-100 text-emerald-800', rejected: 'bg-red-100 text-red-800',
    delayed: 'bg-orange-100 text-orange-800',
  };
  const icons: Record<string, React.ReactNode> = {
    pending: <Clock className="w-3 h-3" />, 'pending approval': <Clock className="w-3 h-3" />,
    approved: <CheckCircle className="w-3 h-3" />, shipped: <Truck className="w-3 h-3" />,
    'in transit': <Truck className="w-3 h-3" />, received: <CheckCircle className="w-3 h-3" />,
    rejected: <X className="w-3 h-3" />, delayed: <AlertTriangle className="w-3 h-3" />,
  };
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${map[s] ?? 'bg-gray-100 text-gray-600'}`}>
      {icons[s]}{status}
    </span>
  );
}

function UrgencyDot({ urgency }: { urgency: string }) {
  const map: Record<string, string> = { critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-amber-400', low: 'bg-green-500' };
  return <span className={`inline-block w-2 h-2 rounded-full shrink-0 ${map[urgency] ?? 'bg-gray-400'}`} />;
}

// ─── Supplier Detail Panel ────────────────────────────────────────────────────

function SupplierDetail({ supplier, onClose }: { supplier: Supplier; onClose: () => void }) {
  const [perf, setPerf] = useState<SupplierPerformance | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/suppliers/${supplier.supplierId}/performance`, { headers: authHeaders() })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setPerf(d.performance ?? d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [supplier.supplierId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black bg-opacity-40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-4 rounded-t-xl flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">{supplier.name}</h2>
            <p className="text-purple-200 text-xs mt-0.5">{supplier.contactEmail || '—'}</p>
          </div>
          <button onClick={onClose} className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-1.5 transition">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Lead Time', value: supplier.leadTimeDays != null ? `${supplier.leadTimeDays}d` : '—' },
              { label: 'Score', value: supplier.performanceScore != null ? `${supplier.performanceScore}%` : (perf?.overallScore != null ? `${perf.overallScore}%` : '—') },
              { label: 'Rating', value: supplier.rating != null ? `${supplier.rating}★` : '—' },
            ].map(s => (
              <div key={s.label} className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500 mb-1">{s.label}</p>
                <p className="text-lg font-bold text-gray-900">{s.value}</p>
              </div>
            ))}
          </div>
          {supplier.products?.length ? (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Products Supplied</p>
              <div className="flex flex-wrap gap-1.5">
                {supplier.products.map(p => <span key={p} className="text-xs bg-purple-50 text-purple-700 px-2 py-0.5 rounded-full">{p}</span>)}
              </div>
            </div>
          ) : null}
          {loading ? (
            <div className="flex justify-center py-4"><div className="w-5 h-5 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" /></div>
          ) : perf ? (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Performance Analytics</p>
              <div className="space-y-2">
                {[
                  { label: 'On-Time Delivery', value: perf.onTimeDeliveryRate, suffix: '%', good: 85, invert: false },
                  { label: 'Defect Rate',       value: perf.defectRate,        suffix: '%', good: 5,  invert: true },
                  { label: 'Avg Lead Time',     value: perf.avgLeadTimeDays,   suffix: 'd', good: 7,  invert: true },
                ].map(m => (
                  <div key={m.label} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">{m.label}</span>
                    <span className={`text-sm font-semibold ${m.value == null ? 'text-gray-400' : m.invert ? (m.value <= m.good ? 'text-green-600' : 'text-red-600') : (m.value >= m.good ? 'text-green-600' : 'text-red-600')}`}>
                      {m.value != null ? `${m.value}${m.suffix}` : '—'}
                    </span>
                  </div>
                ))}
                {perf.delaysLastMonth != null && (
                  <div className="flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    {perf.delaysLastMonth} delay{perf.delaysLastMonth !== 1 ? 's' : ''} last month
                  </div>
                )}
              </div>
              {perf.riskLevel && <div className="mt-3"><RiskBadge level={perf.riskLevel} /></div>}
              {perf.recommendations?.length ? (
                <div className="mt-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1.5">Recommendations</p>
                  <ul className="space-y-1">
                    {perf.recommendations.map((r, i) => (
                      <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                        <ChevronRight className="w-3 h-3 text-purple-400 mt-0.5 shrink-0" />{r}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : <p className="text-sm text-gray-400 text-center py-2">No performance data available yet</p>}
        </div>
      </div>
    </div>
  );
}

// ─── Supplier Management Tab ──────────────────────────────────────────────────

function SupplierManagementTab() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Supplier | null>(null);
  const [reorderAlerts, setReorderAlerts] = useState<ReorderAlert[]>([]);

  const fetchSuppliers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/suppliers`, { headers: authHeaders() });
      if (res.ok) { const d = await res.json(); setSuppliers(d.suppliers ?? d.items ?? []); }
    } catch { /* non-critical */ } finally { setLoading(false); }
  }, []);

  const fetchReorderAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/inventory/reorder-alerts`, { headers: authHeaders() });
      if (res.ok) { const d = await res.json(); setReorderAlerts((d.body?.alerts ?? d.alerts ?? []).slice(0, 5)); }
    } catch { /* non-critical */ }
  }, []);

  useEffect(() => { fetchSuppliers(); fetchReorderAlerts(); }, [fetchSuppliers, fetchReorderAlerts]);

  if (loading) return <div className="flex justify-center py-16"><div className="w-7 h-7 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-5">
      {reorderAlerts.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-amber-800 mb-2 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> Smart Reorder Alerts
          </p>
          <div className="space-y-1.5">
            {reorderAlerts.map(a => (
              <div key={a.item_id} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-1.5 text-gray-700">
                  <UrgencyDot urgency={a.urgency} />{a.item_name ?? a.name ?? a.item_id}
                </span>
                <span className="text-amber-700 font-medium">
                  Reorder {a.recommended_quantity ?? '—'} units
                  {a.projected_stockout_date && ` · stockout ${new Date(a.projected_stockout_date).toLocaleDateString()}`}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Supplier Directory ({suppliers.length})</h3>
        <button onClick={fetchSuppliers} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition"><RefreshCw className="w-4 h-4" /></button>
      </div>
      {suppliers.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <Building2 className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No suppliers found in the database</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {suppliers.map(s => (
            <button key={s.supplierId} onClick={() => setSelected(s)}
              className="text-left bg-white border border-gray-200 rounded-xl p-4 hover:border-purple-300 hover:shadow-md transition-all group">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center shrink-0">
                    <Building2 className="w-4 h-4 text-purple-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">{s.name}</p>
                    <p className="text-xs text-gray-500 truncate">{s.contactEmail || '—'}</p>
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-gray-300 group-hover:text-purple-500 transition shrink-0" />
              </div>
              <div className="flex items-center gap-3 mt-2">
                {s.leadTimeDays != null && <span className="flex items-center gap-1 text-xs text-gray-500"><Truck className="w-3 h-3" />{s.leadTimeDays}d lead</span>}
                <ScoreBadge score={s.performanceScore} />
                {s.status && <span className={`text-xs px-1.5 py-0.5 rounded-full ${s.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>{s.status}</span>}
              </div>
              {s.products?.length ? (
                <p className="text-xs text-gray-400 mt-1.5 truncate">
                  {s.products.slice(0, 3).join(' · ')}{s.products.length > 3 ? ` +${s.products.length - 3}` : ''}
                </p>
              ) : null}
            </button>
          ))}
        </div>
      )}
      {selected && <SupplierDetail supplier={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

// ─── Procurement Control Tab ──────────────────────────────────────────────────

function ProcurementTab() {
  const [pos, setPos] = useState<PurchaseOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [reorderAlerts, setReorderAlerts] = useState<ReorderAlert[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [supplierFilter, setSupplierFilter] = useState('all');
  const [prefillItem, setPrefillItem] = useState<ReorderAlert | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const h = authHeaders();
      const [posRes, suppRes, invRes, alertsRes] = await Promise.allSettled([
        fetch(`${API}/api/procurement/orders`, { headers: h }),
        fetch(`${API}/api/suppliers`, { headers: h }),
        fetch(`${API}/api/v1/technician/inventory`, { headers: h }),
        fetch(`${API}/api/inventory/reorder-alerts`, { headers: h }),
      ]);
      if (posRes.status === 'fulfilled' && posRes.value.ok) {
        const d = await posRes.value.json(); setPos(d.orders ?? d.purchaseOrders ?? []);
      }
      if (suppRes.status === 'fulfilled' && suppRes.value.ok) {
        const d = await suppRes.value.json(); setSuppliers(d.suppliers ?? []);
      }
      if (invRes.status === 'fulfilled' && invRes.value.ok) {
        const d = await invRes.value.json(); setInventory(d.inventory ?? d.items ?? []);
      }
      if (alertsRes.status === 'fulfilled' && alertsRes.value.ok) {
        const d = await alertsRes.value.json(); setReorderAlerts(d.body?.alerts ?? d.alerts ?? []);
      }
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const refreshPOs = useCallback(async () => {
    const res = await fetch(`${API}/api/procurement/orders`, { headers: authHeaders() });
    if (res.ok) { const d = await res.json(); setPos(d.orders ?? d.purchaseOrders ?? []); }
  }, []);

  const handleApprove = async (poId: string) => {
    setApprovingId(poId);
    try {
      await fetch(`${API}/api/procurement/orders/${poId}/approve`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ action: 'approve_purchase_order', orderId: poId }),
      });
      await refreshPOs();
    } finally { setApprovingId(null); }
  };

  const handleReject = async (poId: string) => {
    setApprovingId(poId);
    try {
      await fetch(`${API}/api/procurement/orders/${poId}/reject`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ action: 'reject_purchase_order', orderId: poId }),
      });
      await refreshPOs();
    } finally { setApprovingId(null); }
  };

  // ── Derived stats ──────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const now = new Date();
    const thisMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastMonthStart = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const thisMonth = pos.filter(p => new Date(p.createdAt) >= thisMonthStart);
    const lastMonth = pos.filter(p => {
      const d = new Date(p.createdAt);
      return d >= lastMonthStart && d < thisMonthStart;
    });
    const received = pos.filter(p => p.status?.toLowerCase() === 'received');
    const delayed = pos.filter(p =>
      p.expectedDelivery && new Date(p.expectedDelivery) < now &&
      !['received', 'closed', 'rejected'].includes(p.status?.toLowerCase())
    );
    const leadTimes = received
      .filter(p => p.actualDelivery)
      .map(p => (new Date(p.actualDelivery!).getTime() - new Date(p.createdAt).getTime()) / 86400000);
    const avgLeadDays = leadTimes.length ? Math.round(leadTimes.reduce((a, b) => a + b, 0) / leadTimes.length) : null;
    const monthlySpend = thisMonth.reduce((s, p) => s + (p.totalAmount ?? 0), 0);
    const lastMonthSpend = lastMonth.reduce((s, p) => s + (p.totalAmount ?? 0), 0);
    const spendTrend = lastMonthSpend > 0 ? Math.round(((monthlySpend - lastMonthSpend) / lastMonthSpend) * 100) : null;
    const supplierCounts: Record<string, number> = {};
    pos.forEach(p => { if (p.supplierId) supplierCounts[p.supplierId] = (supplierCounts[p.supplierId] ?? 0) + 1; });
    const topSupplierId = Object.entries(supplierCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
    const topSupplier = suppliers.find(s => s.supplierId === topSupplierId)?.name ?? topSupplierId;
    const itemCounts: Record<string, number> = {};
    pos.forEach(p => p.items?.forEach(i => { itemCounts[i.name] = (itemCounts[i.name] ?? 0) + i.quantity; }));
    const topItem = Object.entries(itemCounts).sort((a, b) => b[1] - a[1])[0]?.[0];
    return {
      open: pos.filter(p => ['pending', 'approved', 'draft', 'pending approval', 'ordered'].includes(p.status?.toLowerCase())).length,
      delayed: delayed.length,
      monthlySpend,
      lastMonthSpend,
      spendTrend,
      avgLeadDays,
      topSupplier,   // undefined when no data
      topItem,       // undefined when no data
      pendingApproval: pos.filter(p => ['pending', 'pending approval', 'draft'].includes(p.status?.toLowerCase())).length,
    };
  }, [pos, suppliers]);

  const filteredPOs = useMemo(() => pos.filter(p => {
    const matchStatus = statusFilter === 'all' || p.status?.toLowerCase() === statusFilter;
    const matchSupplier = supplierFilter === 'all' || p.supplierId === supplierFilter;
    return matchStatus && matchSupplier;
  }), [pos, statusFilter, supplierFilter]);

  // ── Smart reorder suggestions: EOQ formula + incoming stock awareness ──────
  const reorderSuggestions = useMemo(() => {
    // Build incoming stock map from open POs (items already on order)
    const incomingByName: Record<string, number> = {};
    pos
      .filter(p => ['approved', 'ordered', 'shipped', 'in transit'].includes(p.status?.toLowerCase()))
      .forEach(p => p.items?.forEach(i => {
        incomingByName[i.name.toLowerCase()] = (incomingByName[i.name.toLowerCase()] ?? 0) + i.quantity;
      }));

    // EOQ-based reorder qty: (daily_usage × lead_time) + safety_stock - current_stock
    const calcReorderQty = (item: {
      currentStock: number; reorderPoint: number;
      dailyUsage?: number; leadTimeDays?: number; safetyStock?: number;
    }): number => {
      const dailyUsage = item.dailyUsage ?? 1;
      const leadTime = item.leadTimeDays ?? 7;
      const safety = item.safetyStock ?? Math.ceil(dailyUsage * 3);
      const needed = Math.ceil(dailyUsage * leadTime) + safety - item.currentStock;
      return Math.max(needed, item.reorderPoint * 2, 5);
    };

    type Suggestion = {
      id: string; name: string; currentStock: number; incoming: number;
      reorderPoint: number; recommendedQty: number; urgency: string;
      stockoutDate?: string; preferredSupplierId?: string;
      dailyUsage?: number; unitPrice?: number;
    };

    const suggestions: Suggestion[] = [];

    reorderAlerts.forEach(a => {
      const currentStock = a.current_quantity ?? 0;
      const itemNameKey = (a.item_name ?? a.name ?? '').toLowerCase();
      const incoming = incomingByName[itemNameKey] ?? 0;
      const reorderPoint = a.reorder_point ?? 0;
      if (currentStock + incoming > reorderPoint) return; // incoming covers it
      suggestions.push({
        id: a.item_id, name: a.item_name ?? a.name ?? a.item_id,
        currentStock, incoming, reorderPoint,
        recommendedQty: a.recommended_quantity ?? calcReorderQty({ currentStock, reorderPoint, dailyUsage: a.daily_usage, safetyStock: a.safety_stock }),
        urgency: a.urgency, stockoutDate: a.projected_stockout_date,
        preferredSupplierId: a.preferred_supplier_id,
        dailyUsage: a.daily_usage, unitPrice: a.unit_price,
      });
    });

    const alertIds = new Set(reorderAlerts.map(a => a.item_id));
    inventory
      .filter(i => {
        const id = i.item_id ?? i.partId ?? '';
        const min = i.minQuantity ?? i.reorder_point ?? 5;
        const incoming = incomingByName[i.name.toLowerCase()] ?? 0;
        return !alertIds.has(id) && (i.quantity + incoming) <= min;
      })
      .forEach(i => {
        const currentStock = i.quantity;
        const incoming = incomingByName[i.name.toLowerCase()] ?? 0;
        const reorderPoint = i.minQuantity ?? i.reorder_point ?? 5;
        suggestions.push({
          id: i.item_id ?? i.partId ?? i.name, name: i.name,
          currentStock, incoming, reorderPoint,
          recommendedQty: calcReorderQty({ currentStock, reorderPoint, dailyUsage: i.daily_usage, leadTimeDays: 7, safetyStock: i.safety_stock }),
          urgency: currentStock === 0 ? 'critical' : 'high',
          preferredSupplierId: i.preferred_supplier_id,
          dailyUsage: i.daily_usage, unitPrice: i.unitPrice,
        });
      });

    return suggestions.slice(0, 8);
  }, [reorderAlerts, inventory, pos]);

  if (loading) return <div className="flex justify-center py-16"><div className="w-7 h-7 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" /></div>;

  return (
    <div className="space-y-5">

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-blue-50 rounded-xl p-3 border border-gray-100">
          <div className="flex items-center gap-1.5 mb-1"><ShoppingCart className="w-3.5 h-3.5 text-blue-600" /><p className="text-xs text-gray-500">Open POs</p></div>
          <p className="text-xl font-bold text-blue-600">{stats.open}</p>
        </div>
        <div className="bg-red-50 rounded-xl p-3 border border-gray-100">
          <div className="flex items-center gap-1.5 mb-1"><AlertTriangle className="w-3.5 h-3.5 text-red-600" /><p className="text-xs text-gray-500">Delayed</p></div>
          <p className="text-xl font-bold text-red-600">{stats.delayed}</p>
        </div>
        <div className="bg-purple-50 rounded-xl p-3 border border-gray-100">
          <div className="flex items-center gap-1.5 mb-1"><IndianRupee className="w-3.5 h-3.5 text-purple-600" /><p className="text-xs text-gray-500">Monthly Spend</p></div>
          <div className="flex items-end gap-1.5">
            <p className="text-xl font-bold text-purple-600">₹{(stats.monthlySpend / 1000).toFixed(1)}k</p>
            {stats.spendTrend != null && (
              <span className={`text-xs font-medium mb-0.5 ${stats.spendTrend > 0 ? 'text-red-500' : 'text-green-600'}`}>
                {stats.spendTrend > 0 ? '↑' : '↓'}{Math.abs(stats.spendTrend)}%
              </span>
            )}
          </div>
        </div>
        <div className="bg-amber-50 rounded-xl p-3 border border-gray-100">
          <div className="flex items-center gap-1.5 mb-1"><Clock className="w-3.5 h-3.5 text-amber-600" /><p className="text-xs text-gray-500">Avg Lead Time</p></div>
          <p className="text-xl font-bold text-amber-600">{stats.avgLeadDays != null ? `${stats.avgLeadDays}d` : '—'}</p>
        </div>
      </div>

      {/* Procurement Insights — only shown when there's real data */}
      {(stats.topSupplier || stats.topItem || stats.pendingApproval > 0) && (
        <div className="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-100 rounded-xl p-4">
          <p className="text-xs font-semibold text-purple-700 mb-3 flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5" /> Procurement Insights
          </p>
          <div className="grid grid-cols-3 gap-4 text-center">
            {stats.topSupplier && (
              <div>
                <p className="text-xs text-gray-500 mb-0.5">Top Supplier</p>
                <p className="text-sm font-semibold text-gray-800 truncate">{stats.topSupplier}</p>
              </div>
            )}
            {stats.topItem && (
              <div>
                <p className="text-xs text-gray-500 mb-0.5">Most Ordered</p>
                <p className="text-sm font-semibold text-gray-800 truncate">{stats.topItem}</p>
              </div>
            )}
            <div>
              <p className="text-xs text-gray-500 mb-0.5">Pending Approval</p>
              <p className={`text-sm font-semibold ${stats.pendingApproval > 0 ? 'text-amber-600' : 'text-gray-800'}`}>
                {stats.pendingApproval} PO{stats.pendingApproval !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Smart Reorder Engine — unified action panel */}
      {reorderSuggestions.length > 0 && (
        <div className="border border-amber-200 rounded-xl overflow-hidden">
          <div className="bg-amber-50 px-4 py-2.5 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-600" />
            <p className="text-sm font-semibold text-amber-800">⚠ Action Required</p>
            <span className="ml-auto text-xs text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
              {reorderSuggestions.length} item{reorderSuggestions.length !== 1 ? 's' : ''} need reorder
            </span>
          </div>
          <div className="divide-y divide-amber-100">
            {reorderSuggestions.map(s => {
              const prefSupplier = suppliers.find(sup => sup.supplierId === s.preferredSupplierId);
              const bestSupplier = prefSupplier ?? [...suppliers].sort((a, b) => (a.leadTimeDays ?? 99) - (b.leadTimeDays ?? 99))[0];
              const unitPrice = s.unitPrice;
              const totalCost = unitPrice != null ? unitPrice * s.recommendedQty : null;
              return (
                <div key={s.id} className="bg-white px-4 py-3">
                  <div className="flex items-start gap-3">
                    <UrgencyDot urgency={s.urgency} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900">{s.name}</p>

                      {/* Stock row */}
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1">
                        <span className="text-xs text-gray-500">
                          Stock: <span className={s.currentStock === 0 ? 'text-red-600 font-bold' : 'text-amber-600 font-semibold'}>{s.currentStock}</span>
                          <span className="text-gray-400"> / min {s.reorderPoint}</span>
                        </span>
                        {s.incoming > 0 && (
                          <span className="text-xs text-blue-600 font-medium flex items-center gap-0.5">
                            <Truck className="w-3 h-3" />+{s.incoming} incoming
                          </span>
                        )}
                        {s.stockoutDate && (
                          <span className="text-xs text-red-600 flex items-center gap-0.5">
                            <Calendar className="w-3 h-3" />
                            Stockout {new Date(s.stockoutDate).toLocaleDateString()}
                          </span>
                        )}
                        {s.dailyUsage != null && (
                          <span className="text-xs text-gray-400">{s.dailyUsage}/day usage</span>
                        )}
                      </div>

                      {/* Supplier recommendation */}
                      {bestSupplier && (
                        <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
                          <span className="text-xs font-medium text-purple-700 flex items-center gap-1">
                            <Truck className="w-3 h-3" />
                            Best: {bestSupplier.name}
                          </span>
                          {bestSupplier.leadTimeDays != null && (
                            <span className="text-xs text-gray-500">{bestSupplier.leadTimeDays}d lead</span>
                          )}
                          {unitPrice != null && (
                            <span className="text-xs text-green-700 font-medium">₹{unitPrice}/unit</span>
                          )}
                          {bestSupplier.performanceScore != null && (
                            <span className="text-xs text-gray-400">{bestSupplier.performanceScore}% score</span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Action column */}
                    <div className="text-right shrink-0 ml-2">
                      <p className="text-xs text-gray-500">
                        Order <span className="font-bold text-gray-900">{s.recommendedQty} units</span>
                      </p>
                      {totalCost != null && (
                        <p className="text-xs text-purple-600 font-medium">≈ ₹{totalCost.toLocaleString()}</p>
                      )}
                      <button
                        onClick={() => {
                          setPrefillItem({
                            ...s, item_id: s.id, item_name: s.name,
                            recommended_quantity: s.recommendedQty,
                            preferred_supplier_id: bestSupplier?.supplierId,
                          });
                          setShowCreate(true);
                        }}
                        className="mt-1.5 text-xs px-2.5 py-1 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                      >
                        Create PO
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* PO List header + filters */}
      <div className="flex flex-wrap items-center gap-2 justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Purchase Orders ({filteredPOs.length})</h3>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="relative">
            <Filter className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
              className="pl-7 pr-6 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white">
              <option value="all">All Statuses</option>
              {['draft', 'pending', 'approved', 'ordered', 'shipped', 'received', 'rejected'].map(s => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
          </div>
          {suppliers.length > 0 && (
            <div className="relative">
              <select value={supplierFilter} onChange={e => setSupplierFilter(e.target.value)}
                className="pl-3 pr-6 py-1.5 border border-gray-300 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white max-w-[140px]">
                <option value="all">All Suppliers</option>
                {suppliers.map(s => <option key={s.supplierId} value={s.supplierId}>{s.name}</option>)}
              </select>
              <ChevronDown className="absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-gray-400 pointer-events-none" />
            </div>
          )}
          <button onClick={fetchAll} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={() => { setPrefillItem(null); setShowCreate(true); }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white text-xs font-medium rounded-lg hover:bg-purple-700 transition">
            <Plus className="w-3.5 h-3.5" /> New PO
          </button>
        </div>
      </div>

      {/* PO Table */}
      {filteredPOs.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <ShoppingCart className="w-10 h-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">{pos.length === 0 ? 'No purchase orders yet' : 'No POs match the current filter'}</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['PO ID', 'Supplier', 'Items', 'Amount', 'Status', 'Delivery', 'Actions'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredPOs.map(po => {
                  const poId = po.poId ?? po.orderId ?? '—';
                  const now = new Date();
                  const isDelayed = po.expectedDelivery && new Date(po.expectedDelivery) < now &&
                    !['received', 'closed', 'rejected'].includes(po.status?.toLowerCase());
                  const delayDays = isDelayed && po.actualDelivery
                    ? Math.round((new Date(po.actualDelivery).getTime() - new Date(po.expectedDelivery!).getTime()) / 86400000)
                    : null;
                  const isPendingApproval = ['pending', 'pending approval', 'draft'].includes(po.status?.toLowerCase());
                  const supplierName = suppliers.find(s => s.supplierId === po.supplierId)?.name ?? po.supplierName ?? po.supplierId ?? '—';
                  return (
                    <tr key={poId} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-gray-600">{poId.slice(0, 12)}…</td>
                      <td className="px-4 py-3 text-xs text-gray-700 max-w-[120px] truncate">{supplierName}</td>
                      <td className="px-4 py-3 text-xs text-gray-600 max-w-[160px]">
                        <span className="truncate block">
                          {po.items?.slice(0, 2).map(i => `${i.name} ×${i.quantity}`).join(', ')}
                          {(po.items?.length ?? 0) > 2 && ` +${po.items!.length - 2}`}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs font-medium text-gray-800 whitespace-nowrap">
                        {po.totalAmount != null ? `₹${po.totalAmount.toLocaleString()}` : '—'}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge status={isDelayed ? 'Delayed' : po.status} />
                      </td>
                      <td className="px-4 py-3 text-xs whitespace-nowrap">
                        {po.expectedDelivery ? (
                          <div>
                            <span className={isDelayed ? 'text-red-600 font-medium' : 'text-gray-500'}>
                              {isDelayed && <AlertTriangle className="w-3 h-3 inline mr-0.5" />}
                              Exp: {new Date(po.expectedDelivery).toLocaleDateString()}
                            </span>
                            {po.actualDelivery && (
                              <p className="text-gray-400 mt-0.5">
                                Act: {new Date(po.actualDelivery).toLocaleDateString()}
                                {delayDays != null && delayDays > 0 && <span className="text-red-500 ml-1">+{delayDays}d late</span>}
                              </p>
                            )}
                          </div>
                        ) : <span className="text-gray-400">—</span>}
                      </td>
                      <td className="px-4 py-3">
                        {isPendingApproval && (
                          <div className="flex items-center gap-1.5">
                            <button onClick={() => handleApprove(poId)} disabled={approvingId === poId}
                              className="flex items-center gap-1 px-2 py-1 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50">
                              <ThumbsUp className="w-3 h-3" /> Approve
                            </button>
                            <button onClick={() => handleReject(poId)} disabled={approvingId === poId}
                              className="flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition disabled:opacity-50">
                              <ThumbsDown className="w-3 h-3" /> Reject
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showCreate && (
        <CreatePOModal
          suppliers={suppliers}
          prefill={prefillItem}
          onClose={() => { setShowCreate(false); setPrefillItem(null); }}
          onCreated={() => { setShowCreate(false); setPrefillItem(null); fetchAll(); }}
        />
      )}
    </div>
  );
}

// ─── Create PO Modal ──────────────────────────────────────────────────────────

function CreatePOModal({ suppliers, prefill, onClose, onCreated }: {
  suppliers: Supplier[];
  prefill: ReorderAlert | null;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [supplierId, setSupplierId] = useState(prefill?.preferred_supplier_id ?? '');
  const [items, setItems] = useState([{
    name: prefill?.item_name ?? prefill?.name ?? '',
    quantity: prefill?.recommended_quantity ?? 1,
    unitPrice: 0,
  }]);
  const [budgetCategory, setBudgetCategory] = useState('operations');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Show supplier recommendation when prefill has a preferred supplier
  const recommendedSupplier = suppliers.find(s => s.supplierId === prefill?.preferred_supplier_id);

  const total = items.reduce((s, i) => s + (i.quantity * (i.unitPrice ?? 0)), 0);
  const addItem = () => setItems(prev => [...prev, { name: '', quantity: 1, unitPrice: 0 }]);
  const removeItem = (idx: number) => setItems(prev => prev.filter((_, i) => i !== idx));
  const updateItem = (idx: number, field: string, value: string | number) =>
    setItems(prev => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));

  const submit = async () => {
    if (!supplierId) { setError('Select a supplier'); return; }
    if (items.some(i => !i.name.trim())) { setError('All items need a name'); return; }
    setSubmitting(true); setError('');
    try {
      const res = await fetch(`${API}/api/procurement/orders`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          action: 'submit_purchase_order',
          orderData: { supplierId, items, budgetCategory, totalAmount: total },
        }),
      });
      if (res.ok) { onCreated(); }
      else { const d = await res.json(); setError(d.error ?? 'Failed to create PO'); }
    } catch { setError('Network error'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black bg-opacity-40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-5 py-4 rounded-t-xl flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white">New Purchase Order</h2>
            {prefill && <p className="text-purple-200 text-xs mt-0.5">Pre-filled from reorder suggestion</p>}
          </div>
          <button onClick={onClose} className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-1.5 transition">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="p-5 space-y-4">

          {/* Supplier recommendation banner */}
          {recommendedSupplier && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg px-3 py-2 flex items-center gap-2">
              <Truck className="w-4 h-4 text-purple-500 shrink-0" />
              <div className="text-xs">
                <span className="font-semibold text-purple-700">Recommended: </span>
                <span className="text-purple-600">{recommendedSupplier.name}</span>
                {recommendedSupplier.leadTimeDays != null && <span className="text-purple-500"> · {recommendedSupplier.leadTimeDays}d lead</span>}
                {recommendedSupplier.performanceScore != null && <span className="text-purple-500"> · {recommendedSupplier.performanceScore}% score</span>}
              </div>
            </div>
          )}

          {/* Supplier */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Supplier</label>
            <div className="relative">
              <select value={supplierId} onChange={e => setSupplierId(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white">
                <option value="">Select supplier…</option>
                {suppliers.map(s => (
                  <option key={s.supplierId} value={s.supplierId}>
                    {s.name}{s.leadTimeDays != null ? ` (${s.leadTimeDays}d lead)` : ''}
                    {s.performanceScore != null ? ` · ${s.performanceScore}%` : ''}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Budget category */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Budget Category</label>
            <div className="relative">
              <select value={budgetCategory} onChange={e => setBudgetCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none bg-white">
                <option value="operations">Operations</option>
                <option value="hardware">Hardware</option>
                <option value="maintenance">Maintenance</option>
                <option value="emergency">Emergency</option>
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          </div>

          {/* Items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-medium text-gray-700">Items</label>
              <button onClick={addItem} className="text-xs text-purple-600 hover:text-purple-700 flex items-center gap-1">
                <Plus className="w-3 h-3" /> Add item
              </button>
            </div>
            <div className="space-y-2">
              {items.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <input placeholder="Item name" value={item.name} onChange={e => updateItem(idx, 'name', e.target.value)}
                    className="flex-1 px-2.5 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  <input type="number" min={1} placeholder="Qty" value={item.quantity} onChange={e => updateItem(idx, 'quantity', Number(e.target.value))}
                    className="w-16 px-2 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  <input type="number" min={0} placeholder="₹" value={item.unitPrice} onChange={e => updateItem(idx, 'unitPrice', Number(e.target.value))}
                    className="w-20 px-2 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  {items.length > 1 && (
                    <button onClick={() => removeItem(idx)} className="text-gray-400 hover:text-red-500 transition"><X className="w-4 h-4" /></button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {total > 0 && (
            <div className="flex items-center justify-between bg-purple-50 rounded-lg px-3 py-2">
              <span className="text-sm text-gray-600">Total Amount</span>
              <span className="text-sm font-bold text-purple-700">₹{total.toLocaleString()}</span>
            </div>
          )}

          {error && <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}

          <div className="flex gap-3 pt-1">
            <button onClick={onClose} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 transition">Cancel</button>
            <button onClick={submit} disabled={submitting}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition disabled:opacity-50">
              {submitting ? 'Submitting…' : 'Submit PO'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Root Component ───────────────────────────────────────────────────────────

const SupplierCoordinatorView: React.FC = () => {
  const [tab, setTab] = useState<'suppliers' | 'procurement'>('suppliers');
  const tabs = [
    { key: 'suppliers' as const,   label: 'Supplier Management', icon: Building2 },
    { key: 'procurement' as const, label: 'Procurement Control',  icon: ShoppingCart },
  ];
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-200">
          {tabs.map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                tab === t.key ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}>
              <t.icon className="w-4 h-4" />
              {t.label}
            </button>
          ))}
        </div>
        <div className="p-4">
          {tab === 'suppliers'   && <SupplierManagementTab />}
          {tab === 'procurement' && <ProcurementTab />}
        </div>
      </div>
    </div>
  );
};

export default SupplierCoordinatorView;
