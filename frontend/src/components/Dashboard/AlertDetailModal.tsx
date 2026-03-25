/**
 * AlertDetailModal
 * Action-oriented alert detail panel with lifecycle state machine:
 * TRIGGERED → ACKNOWLEDGED → RESOLVED → ARCHIVED
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  CheckCircleIcon,
  WrenchScrewdriverIcon,
  BellSlashIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  DevicePhoneMobileIcon,
} from '@heroicons/react/24/outline';
import { dataService } from '../../services/dataService';

export type AlertStatus = 'TRIGGERED' | 'ACKNOWLEDGED' | 'RESOLVED' | 'ARCHIVED';

export interface AlertDetail {
  alertId: string;
  deviceId: string;
  deviceName?: string;
  issue: string;
  parameter?: string;       // e.g. 'pH', 'turbidity', 'tds', 'temperature'
  value?: number;
  threshold?: number;
  unit?: string;
  severity: 'critical' | 'warning' | 'info';
  status: AlertStatus;
  timestamp: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  location?: string;
}

interface AlertDetailModalProps {
  alert: AlertDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onAcknowledged: (alertId: string) => void;
  onServiceRequested: (alert: AlertDetail) => void;
  onMuted: (alertId: string) => void;
  onViewTrend: (deviceId: string, parameter: string) => void;
}

const SEVERITY_CONFIG = {
  critical: {
    bg: 'bg-red-50',
    border: 'border-red-400',
    badge: 'bg-red-100 text-red-800',
    icon: 'text-red-500',
    label: 'Critical',
  },
  warning: {
    bg: 'bg-amber-50',
    border: 'border-amber-400',
    badge: 'bg-amber-100 text-amber-800',
    icon: 'text-amber-500',
    label: 'Warning',
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    badge: 'bg-blue-100 text-blue-800',
    icon: 'text-blue-500',
    label: 'Info',
  },
};

const STATUS_CONFIG: Record<AlertStatus, { label: string; color: string }> = {
  TRIGGERED:    { label: 'Active',       color: 'bg-red-100 text-red-800' },
  ACKNOWLEDGED: { label: 'Acknowledged', color: 'bg-amber-100 text-amber-800' },
  RESOLVED:     { label: 'Resolved',     color: 'bg-green-100 text-green-800' },
  ARCHIVED:     { label: 'Archived',     color: 'bg-gray-100 text-gray-600' },
};

const AlertDetailModal: React.FC<AlertDetailModalProps> = ({
  alert,
  isOpen,
  onClose,
  onAcknowledged,
  onServiceRequested,
  onMuted,
  onViewTrend,
}) => {
  const [isAcknowledging, setIsAcknowledging] = useState(false);
  const [isMuting, setIsMuting] = useState(false);

  if (!isOpen || !alert) return null;

  const sev = SEVERITY_CONFIG[alert.severity] ?? SEVERITY_CONFIG.warning;
  const statusCfg = STATUS_CONFIG[alert.status] ?? STATUS_CONFIG.TRIGGERED;
  const isActive = alert.status === 'TRIGGERED';

  const handleAcknowledge = async () => {
    setIsAcknowledging(true);
    try {
      await dataService.acknowledgeAlert(alert.alertId);
      onAcknowledged(alert.alertId);
    } finally {
      setIsAcknowledging(false);
    }
  };

  const handleMute = async () => {
    setIsMuting(true);
    try {
      await dataService.muteAlert(alert.alertId, alert.deviceId, alert.parameter || '', 120);
      onMuted(alert.alertId);
    } finally {
      setIsMuting(false);
    }
  };

  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: true,
      });
    } catch { return ts; }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.18 }}
          className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
        >
          {/* Header */}
          <div className={`px-6 py-4 border-l-4 ${sev.border} ${sev.bg} flex items-start justify-between`}>
            <div className="flex items-center gap-3">
              <ExclamationTriangleIcon className={`w-6 h-6 ${sev.icon} flex-shrink-0`} />
              <div>
                <h2 className="text-base font-semibold text-gray-900">{alert.issue}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${sev.badge}`}>
                    {sev.label}
                  </span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${statusCfg.color}`}>
                    {statusCfg.label}
                  </span>
                </div>
              </div>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/60 rounded-lg transition-colors">
              <XMarkIcon className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Body */}
          <div className="px-6 py-5 space-y-4">
            {/* Device info */}
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
              <DevicePhoneMobileIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
              <div>
                <p className="text-xs text-gray-500">Device</p>
                <p className="text-sm font-medium text-gray-900">
                  {alert.deviceName || alert.deviceId}
                </p>
                {alert.location && (
                  <p className="text-xs text-gray-500 mt-0.5">{alert.location}</p>
                )}
              </div>
            </div>

            {/* Parameter reading vs threshold */}
            {alert.parameter && alert.value !== undefined && (
              <div className="p-3 bg-gray-50 rounded-xl">
                <p className="text-xs text-gray-500 mb-2">Reading vs Threshold</p>
                <div className="flex items-end gap-4">
                  <div>
                    <p className="text-2xl font-bold text-gray-900">
                      {alert.value}{alert.unit || ''}
                    </p>
                    <p className="text-xs text-gray-500">{alert.parameter} (current)</p>
                  </div>
                  {alert.threshold !== undefined && (
                    <>
                      <div className="text-gray-300 text-lg mb-1">vs</div>
                      <div>
                        <p className="text-2xl font-bold text-gray-400">
                          {alert.threshold}{alert.unit || ''}
                        </p>
                        <p className="text-xs text-gray-500">threshold</p>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Timestamp */}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <ClockIcon className="w-4 h-4 text-gray-400" />
              <span>Triggered: {formatTime(alert.timestamp)}</span>
            </div>
            {alert.acknowledgedAt && (
              <div className="flex items-center gap-2 text-sm text-amber-600">
                <CheckCircleIcon className="w-4 h-4" />
                <span>Acknowledged: {formatTime(alert.acknowledgedAt)}</span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="px-6 pb-6 grid grid-cols-2 gap-3">
            {/* Acknowledge */}
            <button
              onClick={handleAcknowledge}
              disabled={!isActive || isAcknowledging}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-green-600 text-white text-sm font-medium rounded-xl hover:bg-green-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <CheckCircleIcon className="w-4 h-4" />
              {isAcknowledging ? 'Acknowledging…' : 'Acknowledge'}
            </button>

            {/* Create Service Request */}
            <button
              onClick={() => onServiceRequested(alert)}
              className="flex items-center justify-center gap-2 px-4 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-xl hover:bg-indigo-700 transition-colors"
            >
              <WrenchScrewdriverIcon className="w-4 h-4" />
              Request Tech
            </button>

            {/* Mute similar */}
            <button
              onClick={handleMute}
              disabled={isMuting}
              className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-40"
            >
              <BellSlashIcon className="w-4 h-4" />
              {isMuting ? 'Muting…' : 'Mute 2h'}
            </button>

            {/* View trend */}
            <button
              onClick={() => onViewTrend(alert.deviceId, alert.parameter || '')}
              className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 text-gray-700 text-sm font-medium rounded-xl hover:bg-gray-50 transition-colors"
            >
              <ChartBarIcon className="w-4 h-4" />
              View Trend
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default AlertDetailModal;
