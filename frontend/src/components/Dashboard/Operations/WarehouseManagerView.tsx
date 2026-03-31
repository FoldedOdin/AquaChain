import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import {
  Package, Truck, CheckCircle, RefreshCw, ChevronRight,
  AlertTriangle, Scan, Layers, BarChart2, ClipboardList,
  MapPin, Zap, ArrowRight, X, BoxSelect, Archive, Send
} from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

interface PipelineOrder {
  orderId: string;
  status: string;
  deviceSKU?: string;
  consumerName: string;
  consumerEmail: string;
  createdAt: string;
  updatedAt: string;
  paymentMethod?: string;
  address?: string;
  priority?: 'high' | 'standard';
}

// Human-readable SKU labels — extend as new plans are added
const SKU_LABELS: Record<string, string> = {
  basic:       'AquaChain Basic',
  pro:         'AquaChain Pro',
  enterprise:  'AquaChain Enterprise',
  'aq-001':    'AquaChain Basic',
  'aq-002':    'AquaChain Pro',
  'aq-003':    'AquaChain Enterprise',
};

function skuLabel(sku?: string): string {
  if (!sku) return 'AquaChain Basic';
  return SKU_LABELS[sku.toLowerCase()] ?? `AquaChain ${sku}`;
}

interface Part {
  partId: string;
  name: string;
  category: string;
  quantity: number;
  location: string;
  status: string;
  minQuantity?: number;
  unitPrice?: number;
}

type TaskException = 'shortage' | 'damaged' | 'wrong_item' | 'delay' | null;

interface WMSTask {
  id: string;
  type: 'pick' | 'pack' | 'dispatch' | 'restock';
  partName: string;
  partId: string;
  location: string;
  quantity: number;
  orderId?: string;
  priority: 'urgent' | 'normal' | 'low';
  assignee?: string;
  startedAt?: number;   // Date.now() when started
  completedAt?: number;
  exception?: TaskException;
  status: 'pending' | 'in_progress' | 'done' | 'exception';
}

const API = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
function getToken() {
  return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
}

// ─── Pipeline stage config ────────────────────────────────────────────────────

const STAGES = [
  { key: 'ORDER_PLACED',       label: 'Order Placed',  icon: Package,      color: 'bg-blue-100 text-blue-700 border-blue-200',     dot: 'bg-blue-500' },
  { key: 'DEVICE_READY',       label: 'Picking',       icon: BoxSelect,    color: 'bg-violet-100 text-violet-700 border-violet-200', dot: 'bg-violet-500' },
  { key: 'TECHNICIAN_ASSIGNED',label: 'Packing',       icon: Archive,      color: 'bg-indigo-100 text-indigo-700 border-indigo-200', dot: 'bg-indigo-500' },
  { key: 'SHIPPED',            label: 'Dispatch',      icon: Send,         color: 'bg-cyan-100 text-cyan-700 border-cyan-200',      dot: 'bg-cyan-500' },
  { key: 'DELIVERED',          label: 'Delivered',     icon: CheckCircle,  color: 'bg-green-100 text-green-700 border-green-200',   dot: 'bg-green-500' },
] as const;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function parseZone(location: string): string {
  if (location.startsWith('Warehouse A')) return 'Zone A';
  if (location.startsWith('Warehouse B')) return 'Zone B';
  if (location.startsWith('Warehouse C')) return 'Zone C';
  if (location.startsWith('Tool Room'))   return 'Tool Room';
  return 'Other';
}

function utilizationColor(pct: number): string {
  if (pct >= 80) return 'bg-red-500';
  if (pct >= 50) return 'bg-amber-400';
  return 'bg-green-500';
}

function utilizationBg(pct: number): string {
  if (pct >= 80) return 'bg-red-50 border-red-200';
  if (pct >= 50) return 'bg-amber-50 border-amber-200';
  return 'bg-green-50 border-green-200';
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const STAGE_ACTIONS: Record<string, { label: string; next: string; color: string }> = {
  ORDER_PLACED:        { label: 'Start Picking',  next: 'DEVICE_READY',        color: 'bg-violet-600 hover:bg-violet-700' },
  DEVICE_READY:        { label: 'Mark Packed',    next: 'TECHNICIAN_ASSIGNED', color: 'bg-indigo-600 hover:bg-indigo-700' },
  TECHNICIAN_ASSIGNED: { label: 'Dispatch',       next: 'SHIPPED',             color: 'bg-cyan-600 hover:bg-cyan-700' },
  SHIPPED:             { label: 'Mark Delivered', next: 'DELIVERED',           color: 'bg-green-600 hover:bg-green-700' },
};

function OrderCard({ order, onAdvance }: { order: PipelineOrder; onAdvance?: (orderId: string, next: string) => void }) {
  const age = Math.floor((Date.now() - new Date(order.createdAt).getTime()) / 86400000);
  const action = STAGE_ACTIONS[order.status];
  const isHigh = order.priority === 'high' || age > 5;

  return (
    <div className={`bg-white border rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow ${isHigh ? 'border-red-300' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between gap-2 mb-1">
        <span className="font-mono text-xs text-gray-500 truncate">{order.orderId.slice(0, 14)}…</span>
        <div className="flex items-center gap-1 shrink-0">
          {isHigh && <span className="text-xs font-bold text-red-600">🔥</span>}
          {age > 3 && (
            <span className="flex items-center gap-0.5 text-xs text-amber-600">
              <AlertTriangle className="w-3 h-3" />{age}d
            </span>
          )}
        </div>
      </div>
      <p className="text-sm font-medium text-gray-900 truncate">{skuLabel(order.deviceSKU)}</p>
      <p className="text-xs text-gray-500 truncate">{order.consumerName || order.consumerEmail || '—'}</p>
      {order.paymentMethod && (
        <span className="mt-1 inline-block text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-600 uppercase">
          {order.paymentMethod}
        </span>
      )}
      {action && onAdvance && (
        <button
          onClick={() => onAdvance(order.orderId, action.next)}
          className={`mt-2 w-full text-xs text-white py-1.5 rounded-lg font-medium transition-colors ${action.color}`}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

// ─── 1. Pipeline Tab ──────────────────────────────────────────────────────────

function PipelineTab({ orders }: { orders: PipelineOrder[] }) {
  const [localOrders, setLocalOrders] = useState(orders);
  const [advancing, setAdvancing] = useState<string | null>(null);

  // Sync when parent orders change
  useEffect(() => { setLocalOrders(orders); }, [orders]);

  const byStage = STAGES.reduce((acc, s) => {
    acc[s.key] = localOrders.filter(o => o.status === s.key);
    return acc;
  }, {} as Record<string, PipelineOrder[]>);

  // Avg age per stage (days)
  const avgAge = (stageOrders: PipelineOrder[]) => {
    if (!stageOrders.length) return null;
    const avg = stageOrders.reduce((s, o) => s + (Date.now() - new Date(o.createdAt).getTime()) / 86400000, 0) / stageOrders.length;
    return avg.toFixed(1);
  };

  const handleAdvance = async (orderId: string, nextStatus: string) => {
    setAdvancing(orderId);
    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      const res = await fetch(`${API}/api/admin/orders/${orderId}/status`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (res.ok) {
        // Optimistic update
        setLocalOrders(prev => prev.map(o => o.orderId === orderId ? { ...o, status: nextStatus } : o));
      }
    } catch { /* non-critical */ }
    finally { setAdvancing(null); }
  };

  return (
    <div className="space-y-4">
      {/* Stage flow strip */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          const count = byStage[stage.key]?.length ?? 0;
          const avg = avgAge(byStage[stage.key] ?? []);
          return (
            <React.Fragment key={stage.key}>
              <div className={`flex flex-col px-3 py-2 rounded-lg border text-sm font-medium shrink-0 ${stage.color}`}>
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4" />
                  <span>{stage.label}</span>
                  <span className="ml-1 bg-white bg-opacity-60 rounded-full px-1.5 py-0.5 text-xs font-bold">{count}</span>
                </div>
                {avg && <span className="text-xs opacity-70 mt-0.5">⏱ avg {avg}d</span>}
              </div>
              {i < STAGES.length - 1 && <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />}
            </React.Fragment>
          );
        })}
      </div>

      {/* Kanban columns */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        {STAGES.map(stage => {
          const stageOrders = byStage[stage.key] ?? [];
          return (
            <div key={stage.key} className="bg-gray-50 rounded-xl p-3 min-h-[120px]">
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full ${stage.dot}`} />
                <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">{stage.label}</span>
                <span className="ml-auto text-xs text-gray-400">{stageOrders.length}</span>
              </div>
              <div className="space-y-2">
                {stageOrders.length === 0 ? (
                  <p className="text-xs text-gray-400 text-center py-4 italic">✔ Clear</p>
                ) : (
                  stageOrders.map(o => (
                    <OrderCard
                      key={o.orderId}
                      order={o}
                      onAdvance={advancing ? undefined : handleAdvance}
                    />
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {orders.length === 0 && (
        <div className="text-center py-8 text-gray-400">
          <CheckCircle className="w-10 h-10 mx-auto mb-2 text-green-400" />
          <p className="font-medium text-gray-600">No active orders</p>
          <p className="text-sm">System running normally ✔</p>
        </div>
      )}
    </div>
  );
}

// ─── 2. Task Board Tab ────────────────────────────────────────────────────────

const OPERATORS = ['Unassigned', 'Ravi Kumar', 'Priya Singh', 'Arjun Nair', 'Meena Das'];

const EXCEPTION_LABELS: Record<string, string> = {
  shortage:   '⚠ Shortage',
  damaged:    '⚠ Damaged Stock',
  wrong_item: '⚠ Wrong Item',
  delay:      '⏳ Delay',
};

function elapsed(ms?: number): string {
  if (!ms) return '—';
  const s = Math.floor((Date.now() - ms) / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

function TaskBoardTab({ parts, orders }: { parts: Part[]; orders: PipelineOrder[] }) {
  const [tasks, setTasks] = useState<WMSTask[]>([]);
  const [tick, setTick] = useState(0);

  // Tick every 10s to refresh elapsed times
  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 10000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const generated: WMSTask[] = [];

    // Restock tasks
    parts.forEach(p => {
      const min = p.minQuantity ?? 5;
      if (p.quantity === 0) {
        generated.push({ id: `restock-${p.partId}`, type: 'restock', partName: p.name, partId: p.partId, location: p.location || 'Receiving Dock', quantity: min * 2, priority: 'urgent', status: 'pending' });
      } else if (p.quantity <= min) {
        generated.push({ id: `restock-low-${p.partId}`, type: 'restock', partName: p.name, partId: p.partId, location: p.location || 'Receiving Dock', quantity: min, priority: 'normal', status: 'pending' });
      }
    });

    // Pick tasks
    orders.filter(o => o.status === 'ORDER_PLACED').forEach(o => {
      const isHigh = o.priority === 'high' || (Date.now() - new Date(o.createdAt).getTime()) / 86400000 > 5;
      generated.push({
        id: `pick-${o.orderId}`, type: 'pick',
        partName: `${skuLabel(o.deviceSKU)} → ${o.consumerName || o.consumerEmail || 'customer'}`,
        partId: '', location: 'Warehouse A · Shelf 3 · Bay A1-B2',
        quantity: 1, orderId: o.orderId,
        priority: isHigh ? 'urgent' : 'normal', status: 'pending',
      });
    });

    // Pack tasks
    orders.filter(o => o.status === 'DEVICE_READY').forEach(o => {
      generated.push({
        id: `pack-${o.orderId}`, type: 'pack',
        partName: `Pack & label — ${skuLabel(o.deviceSKU)}`,
        partId: '', location: 'Packing Station · Table 2',
        quantity: 1, orderId: o.orderId, priority: 'normal', status: 'pending',
      });
    });

    // Dispatch tasks
    orders.filter(o => o.status === 'TECHNICIAN_ASSIGNED').forEach(o => {
      generated.push({
        id: `dispatch-${o.orderId}`, type: 'dispatch',
        partName: `Dispatch → ${o.address?.split(',')[0] ?? 'customer'}`,
        partId: '', location: 'Dispatch Bay · Door 1',
        quantity: 1, orderId: o.orderId, priority: 'urgent', status: 'pending',
      });
    });

    setTasks(prev => {
      // Preserve in-progress/done/exception state for existing tasks
      const prevMap = Object.fromEntries(prev.map(t => [t.id, t]));
      return generated.map(t => prevMap[t.id] ?? t);
    });
  }, [parts, orders]);

  const update = (id: string, patch: Partial<WMSTask>) =>
    setTasks(prev => prev.map(t => t.id === id ? { ...t, ...patch } : t));

  const start = (id: string) => update(id, { status: 'in_progress', startedAt: Date.now() });
  const complete = (id: string) => update(id, { status: 'done', completedAt: Date.now() });
  const setException = (id: string, ex: TaskException) => update(id, { status: 'exception', exception: ex });
  const setAssignee = (id: string, name: string) => update(id, { assignee: name });

  const priorityColor: Record<string, string> = {
    urgent: 'bg-red-100 text-red-700 border-red-200',
    normal: 'bg-blue-100 text-blue-700 border-blue-200',
    low:    'bg-gray-100 text-gray-600 border-gray-200',
  };
  const typeLabel: Record<string, string> = {
    pick: '📦 Pick', pack: '📥 Pack', dispatch: '🚚 Dispatch', restock: '🔄 Restock',
  };

  const pending    = tasks.filter(t => t.status === 'pending');
  const inProgress = tasks.filter(t => t.status === 'in_progress');
  const exceptions = tasks.filter(t => t.status === 'exception');
  const done       = tasks.filter(t => t.status === 'done');

  // Avg completion time
  const avgMs = done.filter(t => t.startedAt && t.completedAt)
    .map(t => t.completedAt! - t.startedAt!);
  const avgTime = avgMs.length ? elapsed(Date.now() - avgMs.reduce((a, b) => a + b, 0) / avgMs.length) : null;

  const renderTask = (task: WMSTask) => (
    <div key={task.id} className={`bg-white border rounded-xl p-3 shadow-sm ${task.status === 'exception' ? 'border-red-300 bg-red-50' : task.status === 'in_progress' ? 'border-indigo-300' : 'border-gray-200'}`}>
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold text-gray-400">{typeLabel[task.type]}</span>
            <span className={`text-xs px-1.5 py-0.5 rounded-full border font-medium ${priorityColor[task.priority]}`}>{task.priority}</span>
            {task.status === 'in_progress' && (
              <span className="text-xs text-indigo-600 font-medium ml-auto">⏱ {elapsed(task.startedAt)}</span>
            )}
          </div>
          <p className="text-sm font-semibold text-gray-900 truncate">{task.partName}</p>
          <p className="text-xs text-gray-500 flex items-center gap-1 mt-0.5">
            <MapPin className="w-3 h-3 shrink-0" />{task.location} · Qty: <strong>{task.quantity}</strong>
          </p>
          {task.exception && (
            <p className="text-xs text-red-600 font-medium mt-1">{EXCEPTION_LABELS[task.exception]}</p>
          )}
        </div>
      </div>

      {/* Assignee */}
      <div className="mt-2 flex items-center gap-2">
        <select
          value={task.assignee ?? ''}
          onChange={e => setAssignee(task.id, e.target.value)}
          className="flex-1 text-xs border border-gray-200 rounded-lg px-2 py-1 bg-white focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
        </select>
      </div>

      {/* Action buttons */}
      <div className="mt-2 flex gap-2">
        {task.status === 'pending' && (
          <button onClick={() => start(task.id)}
            className="flex-1 text-xs py-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium">
            ▶ Start
          </button>
        )}
        {task.status === 'in_progress' && (
          <button onClick={() => complete(task.id)}
            className="flex-1 text-xs py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium">
            ✓ Complete
          </button>
        )}
        {(task.status === 'pending' || task.status === 'in_progress') && (
          <div className="relative group">
            <button className="text-xs px-2 py-1.5 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors">
              ⚠
            </button>
            <div className="absolute right-0 top-8 z-10 hidden group-hover:flex flex-col bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden min-w-[140px]">
              {(Object.keys(EXCEPTION_LABELS) as TaskException[]).filter(Boolean).map(ex => (
                <button key={ex!} onClick={() => setException(task.id, ex)}
                  className="text-xs px-3 py-2 text-left hover:bg-red-50 text-red-700 whitespace-nowrap">
                  {EXCEPTION_LABELS[ex!]}
                </button>
              ))}
            </div>
          </div>
        )}
        {task.status === 'exception' && (
          <button onClick={() => update(task.id, { status: 'pending', exception: null })}
            className="flex-1 text-xs py-1.5 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors">
            Reset
          </button>
        )}
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Stats bar */}
      <div className="flex items-center gap-4 text-sm flex-wrap">
        <span><strong className="text-indigo-600">{inProgress.length}</strong> in progress</span>
        <span><strong className="text-amber-600">{pending.length}</strong> pending</span>
        {exceptions.length > 0 && <span><strong className="text-red-600">{exceptions.length}</strong> exceptions</span>}
        <span><strong className="text-green-600">{done.length}</strong> done</span>
        {avgTime && <span className="text-gray-400 text-xs ml-auto">avg task: {avgTime}</span>}
      </div>

      {/* Exceptions first */}
      {exceptions.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-red-600 uppercase mb-2">⚠ Exceptions — Needs Attention</p>
          <div className="space-y-2">{exceptions.map(renderTask)}</div>
        </div>
      )}

      {/* In progress */}
      {inProgress.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-indigo-600 uppercase mb-2">▶ In Progress</p>
          <div className="space-y-2">{inProgress.map(renderTask)}</div>
        </div>
      )}

      {/* Pending */}
      {pending.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Pending ({pending.length})</p>
          <div className="space-y-2">{pending.map(renderTask)}</div>
        </div>
      )}

      {pending.length === 0 && inProgress.length === 0 && exceptions.length === 0 && (
        <p className="text-sm text-gray-400 py-6 text-center">All tasks complete 🎉</p>
      )}

      {/* Completed */}
      {done.length > 0 && (
        <details>
          <summary className="text-xs text-gray-400 cursor-pointer select-none">Show {done.length} completed</summary>
          <div className="space-y-2 mt-2 opacity-60">
            {done.map(task => (
              <div key={task.id} className="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-lg p-3">
                <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-500 line-through truncate">{task.partName}</p>
                  {task.startedAt && task.completedAt && (
                    <p className="text-xs text-gray-400">{task.assignee ?? 'Unassigned'} · {Math.round((task.completedAt - task.startedAt) / 60000)}m</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

// ─── 3. Heatmap Tab ───────────────────────────────────────────────────────────

function HeatmapTab({ parts }: { parts: Part[] }) {
  // Group by location, compute utilization as qty / (max_qty_in_zone * 1.5)
  const locationData = useMemo(() => {
    const map: Record<string, { parts: Part[]; totalQty: number; zone: string }> = {};
    parts.forEach(p => {
      if (!map[p.location]) map[p.location] = { parts: [], totalQty: 0, zone: parseZone(p.location) };
      map[p.location].parts.push(p);
      map[p.location].totalQty += p.quantity;
    });
    const maxQty = Math.max(...Object.values(map).map(v => v.totalQty), 1);
    return Object.entries(map).map(([loc, data]) => ({
      location: loc,
      zone: data.zone,
      partCount: data.parts.length,
      totalQty: data.totalQty,
      utilization: Math.round((data.totalQty / maxQty) * 100),
      lowStockCount: data.parts.filter(p => p.quantity <= (p.minQuantity ?? 5)).length,
      parts: data.parts,
    })).sort((a, b) => b.utilization - a.utilization);
  }, [parts]);

        const zones = Array.from(new Set(locationData.map(l => l.zone)));

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-500">Relative stock density per location. Red = high concentration, green = normal.</p>
      {zones.map(zone => {
        const zoneLocs = locationData.filter(l => l.zone === zone);
        return (
          <div key={zone}>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">{zone}</h4>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {zoneLocs.map(loc => (
                <div key={loc.location} className={`border rounded-lg p-3 ${utilizationBg(loc.utilization)}`}>
                  <div className="flex items-start justify-between mb-2">
                    <p className="text-xs font-semibold text-gray-800 leading-tight">{loc.location.replace(zone.replace('Zone ', 'Warehouse '), '').replace('Tool Room', '').trim().replace(/^-\s*/, '')}</p>
                    {loc.lowStockCount > 0 && (
                      <span className="text-xs text-amber-600 flex items-center gap-0.5 shrink-0">
                        <AlertTriangle className="w-3 h-3" />{loc.lowStockCount}
                      </span>
                    )}
                  </div>
                  {/* Heat bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div className={`h-2 rounded-full transition-all ${utilizationColor(loc.utilization)}`} style={{ width: `${loc.utilization}%` }} />
                  </div>
                  <div className="flex justify-between text-xs text-gray-600">
                    <span>{loc.partCount} parts</span>
                    <span className="font-semibold">{loc.utilization}%</span>
                  </div>
                  {/* Part list */}
                  <div className="mt-2 space-y-0.5">
                    {loc.parts.slice(0, 3).map(p => (
                      <p key={p.partId} className="text-xs text-gray-500 truncate">
                        {p.name} <span className={p.quantity === 0 ? 'text-red-600 font-semibold' : p.quantity <= (p.minQuantity ?? 5) ? 'text-amber-600' : 'text-gray-400'}>({p.quantity})</span>
                      </p>
                    ))}
                    {loc.parts.length > 3 && <p className="text-xs text-gray-400">+{loc.parts.length - 3} more</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── 4. Scanner Tab ───────────────────────────────────────────────────────────

function ScannerTab({ parts }: { parts: Part[] }) {
  const [input, setInput] = useState('');
  const [result, setResult] = useState<{ part: Part; action: string } | null>(null);
  const [history, setHistory] = useState<Array<{ query: string; found: boolean; name?: string; location?: string; qty?: number }>>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleScan = useCallback((query: string) => {
    const q = query.trim().toLowerCase();
    if (!q) return;
    const part = parts.find(p =>
      p.partId.toLowerCase() === q ||
      p.name.toLowerCase().includes(q) ||
      p.location.toLowerCase().includes(q)
    );
    if (part) {
      setResult({ part, action: part.quantity === 0 ? 'OUT OF STOCK' : part.quantity <= (part.minQuantity ?? 5) ? 'LOW STOCK — restock needed' : 'Located' });
      setHistory(prev => [{ query, found: true, name: part.name, location: part.location, qty: part.quantity }, ...prev.slice(0, 9)]);
    } else {
      setResult(null);
      setHistory(prev => [{ query, found: false }, ...prev.slice(0, 9)]);
    }
    setInput('');
  }, [parts]);

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleScan(input);
  };

  // Slot suggestion: find least-loaded zone for a category
  const suggestSlot = (part: Part) => {
    const sameCat = parts.filter(p => p.category === part.category && p.partId !== part.partId);
    if (sameCat.length === 0) return 'Warehouse A - Shelf 3';
    const locCounts: Record<string, number> = {};
    sameCat.forEach(p => { locCounts[p.location] = (locCounts[p.location] || 0) + p.quantity; });
    return Object.entries(locCounts).sort((a, b) => a[1] - b[1])[0][0];
  };

  return (
    <div className="space-y-4">
      {/* Scan input */}
      <div className="relative">
        <Scan className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder="Scan barcode or type part ID / name — press Enter"
          className="w-full pl-10 pr-4 py-3 border-2 border-indigo-300 rounded-xl text-sm focus:outline-none focus:border-indigo-500 bg-white"
          autoFocus
        />
        {input && (
          <button onClick={() => setInput('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
      <button onClick={() => handleScan(input)} className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
        Look Up
      </button>

      {/* Result */}
      {result && (
        <div className={`rounded-xl border p-4 ${result.part.quantity === 0 ? 'bg-red-50 border-red-200' : result.part.quantity <= (result.part.minQuantity ?? 5) ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'}`}>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-semibold text-gray-900">{result.part.name}</p>
              <p className="text-sm text-gray-600 flex items-center gap-1 mt-1"><MapPin className="w-3 h-3" />{result.part.location}</p>
              <p className="text-sm text-gray-600 mt-0.5">Qty: <strong>{result.part.quantity}</strong> · Category: {result.part.category}</p>
            </div>
            <span className={`text-xs font-semibold px-2 py-1 rounded-full ${result.part.quantity === 0 ? 'bg-red-100 text-red-700' : result.part.quantity <= (result.part.minQuantity ?? 5) ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
              {result.action}
            </span>
          </div>
          {/* Slot suggestion */}
          <div className="mt-3 pt-3 border-t border-gray-200 flex items-center gap-2 text-xs text-gray-600">
            <Zap className="w-3 h-3 text-indigo-500" />
            <span>Suggested slot for new stock:</span>
            <strong className="text-indigo-700">{suggestSlot(result.part)}</strong>
          </div>
        </div>
      )}

      {/* Scan history */}
      {history.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Recent Lookups</p>
          <div className="space-y-1">
            {history.map((h, i) => (
              <div key={i} className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${h.found ? 'bg-gray-50' : 'bg-red-50'}`}>
                {h.found
                  ? <><CheckCircle className="w-3 h-3 text-green-500 shrink-0" /><span className="font-medium">{h.name}</span><span className="text-gray-400 ml-auto">{h.location} · {h.qty}</span></>
                  : <><X className="w-3 h-3 text-red-500 shrink-0" /><span className="text-red-600">Not found: "{h.query}"</span></>
                }
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── 5. Operator Mode Tab ─────────────────────────────────────────────────────

function OperatorModeTab({ parts, orders }: { parts: Part[]; orders: PipelineOrder[] }) {
  const [activeTask, setActiveTask] = useState<null | { label: string; location: string; qty: number; orderId?: string }>(null);
  const [done, setDone] = useState(false);

  const urgentTasks = [
    ...parts.filter(p => p.quantity === 0).map(p => ({ label: `RESTOCK: ${p.name}`, location: p.location, qty: (p.minQuantity ?? 5) * 2 })),
    ...orders.filter(o => o.status === 'ORDER_PLACED').map(o => ({ label: `PICK: ${skuLabel(o.deviceSKU)} for ${o.consumerName || o.consumerEmail || 'customer'}`, location: 'Warehouse A - Shelf 3', qty: 1, orderId: o.orderId })),
    ...parts.filter(p => p.quantity > 0 && p.quantity <= (p.minQuantity ?? 5)).map(p => ({ label: `LOW STOCK: ${p.name}`, location: p.location, qty: p.minQuantity ?? 5 })),
  ];

  if (activeTask) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center gap-6 p-4">
        {done ? (
          <>
            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-green-700">Task Complete!</p>
            <button onClick={() => { setActiveTask(null); setDone(false); }} className="px-8 py-4 bg-gray-800 text-white rounded-2xl text-lg font-semibold hover:bg-gray-900 transition-colors">
              Next Task
            </button>
          </>
        ) : (
          <>
            <div className="w-full max-w-sm bg-white border-2 border-indigo-200 rounded-2xl p-6 text-center shadow-lg">
              <p className="text-xs font-semibold text-indigo-500 uppercase mb-2">Current Task</p>
              <p className="text-xl font-bold text-gray-900 mb-4">{activeTask.label}</p>
              <div className="flex items-center justify-center gap-2 text-gray-600 mb-2">
                <MapPin className="w-5 h-5 text-indigo-500" />
                <span className="text-lg font-semibold">{activeTask.location}</span>
              </div>
              <div className="text-3xl font-black text-indigo-600 mt-2">× {activeTask.qty}</div>
            </div>
            <div className="flex gap-4 w-full max-w-sm">
              <button onClick={() => setActiveTask(null)} className="flex-1 py-4 border-2 border-gray-300 text-gray-700 rounded-2xl text-lg font-semibold hover:bg-gray-50 transition-colors">
                Skip
              </button>
              <button onClick={() => setDone(true)} className="flex-2 flex-grow py-4 bg-green-600 text-white rounded-2xl text-lg font-bold hover:bg-green-700 transition-colors shadow-lg">
                ✓ Done
              </button>
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-500">Tap a task to enter focused operator mode — large buttons, minimal distractions.</p>
      {urgentTasks.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
          <p className="font-medium">No pending tasks</p>
        </div>
      )}
      {urgentTasks.map((task, i) => (
        <button
          key={i}
          onClick={() => { setActiveTask(task); setDone(false); }}
          className="w-full flex items-center gap-4 bg-white border-2 border-gray-200 rounded-2xl p-4 hover:border-indigo-400 hover:shadow-md transition-all text-left"
        >
          <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center shrink-0">
            <Package className="w-6 h-6 text-indigo-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-900 truncate">{task.label}</p>
            <p className="text-sm text-gray-500 flex items-center gap-1"><MapPin className="w-3 h-3" />{task.location} · Qty {task.qty}</p>
          </div>
          <ArrowRight className="w-5 h-5 text-gray-400 shrink-0" />
        </button>
      ))}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

type Tab = 'pipeline' | 'tasks' | 'heatmap' | 'scanner' | 'operator';

const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
  { key: 'pipeline', label: 'Pipeline',  icon: Layers },
  { key: 'tasks',    label: 'Tasks',     icon: ClipboardList },
  { key: 'heatmap',  label: 'Heatmap',   icon: BarChart2 },
  { key: 'scanner',  label: 'Scanner',   icon: Scan },
  { key: 'operator', label: 'Operator',  icon: Zap },
];

const WarehouseManagerView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('pipeline');
  const [orders, setOrders] = useState<PipelineOrder[]>([]);
  const [parts, setParts] = useState<Part[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (refresh = false) => {
    refresh ? setIsRefreshing(true) : setIsLoading(true);
    setError(null);
    try {
      const headers = { Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' };
      const [ordersRes, invRes] = await Promise.all([
        fetch(`${API}/api/admin/orders`, { headers }),
        fetch(`${API}/api/v1/technician/inventory`, { headers }),
      ]);
      if (ordersRes.ok) {
        const data = await ordersRes.json();
        const pipelineStatuses = new Set(['ORDER_PLACED', 'DEVICE_READY', 'TECHNICIAN_ASSIGNED', 'SHIPPED', 'DELIVERED']);
        setOrders((data.orders || []).filter((o: PipelineOrder) => pipelineStatuses.has(o.status)));
      }
      if (invRes.ok) {
        const data = await invRes.json();
        setParts(data.inventory || data.items || []);
      }
    } catch {
      setError('Failed to load warehouse data');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  // Inventory summary stats
  const invStats = useMemo(() => ({
    total: parts.length,
    inStock: parts.filter(p => p.quantity > (p.minQuantity ?? 5)).length,
    lowStock: parts.filter(p => p.quantity > 0 && p.quantity <= (p.minQuantity ?? 5)).length,
    outOfStock: parts.filter(p => p.quantity === 0).length,
  }), [parts]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Top stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Pipeline Orders', value: orders.length,          color: 'text-blue-700',   bg: 'bg-blue-50' },
          { label: 'Parts In Stock',  value: invStats.inStock,       color: 'text-green-700',  bg: 'bg-green-50' },
          { label: 'Low Stock',       value: invStats.lowStock,      color: 'text-amber-700',  bg: 'bg-amber-50' },
          { label: 'Out of Stock',    value: invStats.outOfStock,    color: 'text-red-700',    bg: 'bg-red-50' },
        ].map(s => (
          <div key={s.label} className={`${s.bg} border border-gray-100 rounded-lg p-3`}>
            <p className="text-xs text-gray-500 mb-0.5">{s.label}</p>
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">{error}</div>}

      {/* Tab bar */}
      <div className="flex items-center gap-1 border-b border-gray-200 overflow-x-auto">
        {TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                isActive ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
        <button
          onClick={() => fetchData(true)}
          disabled={isRefreshing}
          className="ml-auto flex items-center gap-1 px-3 py-2 text-xs text-gray-500 hover:text-gray-700 disabled:opacity-50 shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'pipeline' && <PipelineTab orders={orders} />}
        {activeTab === 'tasks'    && <TaskBoardTab parts={parts} orders={orders} />}
        {activeTab === 'heatmap'  && <HeatmapTab parts={parts} />}
        {activeTab === 'scanner'  && <ScannerTab parts={parts} />}
        {activeTab === 'operator' && <OperatorModeTab parts={parts} orders={orders} />}
      </div>
    </div>
  );
};

export default WarehouseManagerView;
