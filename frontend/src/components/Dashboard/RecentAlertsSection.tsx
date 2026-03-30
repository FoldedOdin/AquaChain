/**
 * RecentAlertsSection
 * Improved alert display for the consumer dashboard:
 * - Severity-based colour coding (critical/warning/info)
 * - Status filters (Active / Acknowledged / Resolved)
 * - Clickable rows → AlertDetailModal
 * - Real-time pulse animation for new TRIGGERED alerts
 * - Deduplication: groups repeated alerts by parameter
 * - Inline acknowledge action
 */

import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BellIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import AlertDetailModal, { AlertDetail, AlertLocation, AlertStatus } from './AlertDetailModal';
import { dataService } from '../../services/dataService';

type FilterTab = 'active' | 'acknowledged' | 'resolved';

interface RawAlert {
  alertId?: string;
  id?: string;
  deviceId?: string;
  device_id?: string;
  deviceName?: string;
  issue?: string;
  message?: string;
  parameter?: string;
  value?: number;
  threshold?: number;
  unit?: string;
  severity?: string;
  status?: string;
  timestamp?: string;
  createdAt?: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  location?: string | AlertLocation;
}

interface RecentAlertsSectionProps {
  alerts: RawAlert[];
  onRefresh: () => void;
  onViewTrend?: (deviceId: string, parameter: string) => void;
  onServiceRequested?: (alert: AlertDetail) => void;
}

// Normalise raw alert from API into AlertDetail shape
function normalise(raw: RawAlert): AlertDetail {
  const rawSev = (raw.severity || 'warning').toLowerCase();
  const sev: AlertDetail['severity'] =
    rawSev === 'critical' ? 'critical' : rawSev === 'info' ? 'info' : 'warning';

  const rawStatus = (raw.status || 'TRIGGERED').toUpperCase();
  const status: AlertStatus =
    rawStatus === 'ACKNOWLEDGED' ? 'ACKNOWLEDGED'
    : rawStatus === 'RESOLVED'   ? 'RESOLVED'
    : rawStatus === 'ARCHIVED'   ? 'ARCHIVED'
    : 'TRIGGERED';

  return {
    alertId:       raw.alertId || raw.id || '',
    deviceId:      raw.deviceId || raw.device_id || '',
    deviceName:    raw.deviceName,
    issue:         raw.issue || raw.message || 'Water quality alert',
    parameter:     raw.parameter,
    value:         raw.value,
    threshold:     raw.threshold,
    unit:          raw.unit,
    severity:      sev,
    status,
    timestamp:     raw.timestamp || raw.createdAt || new Date().toISOString(),
    acknowledgedAt: raw.acknowledgedAt,
    resolvedAt:    raw.resolvedAt,
    location:      raw.location,
  };
}

// Deduplicate: keep only the most recent alert per (deviceId + parameter)
function deduplicate(alerts: AlertDetail[]): AlertDetail[] {
  const seen = new Map<string, AlertDetail>();
  for (const a of alerts) {
    const key = `${a.deviceId}::${a.parameter || a.issue}`;
    const existing = seen.get(key);
    if (!existing || new Date(a.timestamp) > new Date(existing.timestamp)) {
      seen.set(key, a);
    }
  }
  return Array.from(seen.values()).sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

const SEV_STYLES = {
  critical: {
    border: 'border-l-red-500',
    bg: 'bg-red-50 hover:bg-red-100',
    icon: 'text-red-500',
    badge: 'bg-red-100 text-red-700',
    pulse: true,
  },
  warning: {
    border: 'border-l-amber-500',
    bg: 'bg-amber-50 hover:bg-amber-100',
    icon: 'text-amber-500',
    badge: 'bg-amber-100 text-amber-700',
    pulse: false,
  },
  info: {
    border: 'border-l-blue-500',
    bg: 'bg-blue-50 hover:bg-blue-100',
    icon: 'text-blue-500',
    badge: 'bg-blue-100 text-blue-700',
    pulse: false,
  },
};

function timeAgo(ts: string): string {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const RecentAlertsSection: React.FC<RecentAlertsSectionProps> = ({
  alerts: rawAlerts,
  onRefresh,
  onViewTrend,
  onServiceRequested,
}) => {
  const [filter, setFilter] = useState<FilterTab>('active');
  const [selectedAlert, setSelectedAlert] = useState<AlertDetail | null>(null);
  // Local overrides for optimistic UI updates
  const [localStatuses, setLocalStatuses] = useState<Record<string, AlertStatus>>({});

  const allAlerts = useMemo(() => {
    const normalised = rawAlerts.map(normalise);
    // Apply local status overrides
    const withOverrides = normalised.map(a =>
      localStatuses[a.alertId] ? { ...a, status: localStatuses[a.alertId] } : a
    );
    return deduplicate(withOverrides);
  }, [rawAlerts, localStatuses]);

  const filtered = useMemo(() => {
    if (filter === 'active')       return allAlerts.filter(a => a.status === 'TRIGGERED');
    if (filter === 'acknowledged') return allAlerts.filter(a => a.status === 'ACKNOWLEDGED');
    return allAlerts.filter(a => a.status === 'RESOLVED' || a.status === 'ARCHIVED');
  }, [allAlerts, filter]);

  const counts = useMemo(() => ({
    active:       allAlerts.filter(a => a.status === 'TRIGGERED').length,
    acknowledged: allAlerts.filter(a => a.status === 'ACKNOWLEDGED').length,
    resolved:     allAlerts.filter(a => a.status === 'RESOLVED' || a.status === 'ARCHIVED').length,
  }), [allAlerts]);

  const handleAcknowledged = useCallback((alertId: string) => {
    setLocalStatuses(prev => ({ ...prev, [alertId]: 'ACKNOWLEDGED' }));
    setSelectedAlert(prev => prev?.alertId === alertId ? { ...prev, status: 'ACKNOWLEDGED' } : prev);
    onRefresh();
  }, [onRefresh]);

  const handleMuted = useCallback((alertId: string) => {
    setLocalStatuses(prev => ({ ...prev, [alertId]: 'ARCHIVED' }));
    setSelectedAlert(null);
    onRefresh();
  }, [onRefresh]);

  const handleInlineAcknowledge = useCallback(async (e: React.MouseEvent, alert: AlertDetail) => {
    e.stopPropagation();
    await dataService.acknowledgeAlert(alert.alertId);
    handleAcknowledged(alert.alertId);
  }, [handleAcknowledged]);

  const TABS: { key: FilterTab; label: string; count: number }[] = [
    { key: 'active',       label: '🔴 Active',       count: counts.active },
    { key: 'acknowledged', label: '🟡 Acknowledged', count: counts.acknowledged },
    { key: 'resolved',     label: '🟢 Resolved',     count: counts.resolved },
  ];

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-6 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <BellIcon className="w-5 h-5 text-gray-500" />
            <h2 className="text-base font-semibold text-gray-900">Recent Alerts</h2>
            {counts.active > 0 && (
              <span className="ml-1 px-2 py-0.5 text-xs font-bold bg-red-100 text-red-700 rounded-full animate-pulse">
                {counts.active}
              </span>
            )}
          </div>
          <FunnelIcon className="w-4 h-4 text-gray-400" />
        </div>

        {/* Filter tabs */}
        <div className="flex border-b border-gray-100">
          {TABS.map(tab => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
                filter === tab.key
                  ? 'border-b-2 border-indigo-500 text-indigo-600 bg-indigo-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className="ml-1 text-xs opacity-70">({tab.count})</span>
              )}
            </button>
          ))}
        </div>

        {/* Alert list */}
        <div className="divide-y divide-gray-50 max-h-72 overflow-y-auto">
          <AnimatePresence initial={false}>
            {filtered.length === 0 ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="py-10 text-center"
              >
                <CheckCircleIcon className="w-10 h-10 text-green-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">
                  {filter === 'active' ? 'No active alerts — all clear!' : 'Nothing here yet.'}
                </p>
              </motion.div>
            ) : (
              filtered.map((alert, idx) => {
                const styles = SEV_STYLES[alert.severity];
                return (
                  <motion.div
                    key={alert.alertId || idx}
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 16 }}
                    transition={{ delay: idx * 0.04 }}
                    onClick={() => setSelectedAlert(alert)}
                    className={`flex items-start gap-3 px-5 py-3.5 border-l-4 cursor-pointer transition-colors ${styles.border} ${styles.bg}`}
                  >
                    <div className="relative flex-shrink-0 mt-0.5">
                      <ExclamationTriangleIcon className={`w-5 h-5 ${styles.icon}`} />
                      {styles.pulse && alert.status === 'TRIGGERED' && (
                        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full animate-ping" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-gray-900 truncate">
                          {alert.issue}
                        </span>
                        <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${styles.badge}`}>
                          {alert.severity}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        {alert.parameter && alert.value !== undefined && (
                          <span className="text-xs text-gray-600">
                            {alert.parameter}: <strong>{alert.value}{alert.unit || ''}</strong>
                          </span>
                        )}
                        <span className="text-xs text-gray-400">{timeAgo(alert.timestamp)}</span>
                      </div>
                    </div>

                    {/* Inline acknowledge for active alerts */}
                    {alert.status === 'TRIGGERED' && (
                      <button
                        onClick={(e) => handleInlineAcknowledge(e, alert)}
                        title="Acknowledge"
                        className="flex-shrink-0 p-1.5 rounded-lg hover:bg-green-100 text-green-600 transition-colors"
                      >
                        <CheckCircleIcon className="w-4 h-4" />
                      </button>
                    )}
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        </div>

        {/* Footer */}
        {allAlerts.length > 0 && (
          <div className="px-5 py-2.5 bg-gray-50 border-t border-gray-100 text-xs text-gray-500 text-center">
            {allAlerts.length} total alert{allAlerts.length !== 1 ? 's' : ''} · tap any row for details
          </div>
        )}
      </motion.div>

      {/* Detail modal */}
      <AlertDetailModal
        alert={selectedAlert}
        isOpen={!!selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledged={handleAcknowledged}
        onMuted={handleMuted}
        onServiceRequested={(a) => {
          setSelectedAlert(null);
          onServiceRequested?.(a);
        }}
        onViewTrend={(deviceId, param) => {
          setSelectedAlert(null);
          onViewTrend?.(deviceId, param);
        }}
      />
    </>
  );
};

export default RecentAlertsSection;
