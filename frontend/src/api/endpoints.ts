/**
 * API Endpoints Registry
 *
 * Single source of truth for all backend routes.
 * WHY: With 12+ services and dual parallel data-service files, the same
 * endpoint strings were spread across 5+ files with no central contract.
 * Any rename of an endpoint required a grep + multi-file edit.
 *
 * Usage:
 *   import { ENDPOINTS } from '../api/endpoints';
 *   apiFetch(ENDPOINTS.readings.latest(deviceId));
 */

export const ENDPOINTS = {
  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------
  health: '/api/health',

  // ---------------------------------------------------------------------------
  // Auth (handled by Cognito; these are internal API side-effects)
  // ---------------------------------------------------------------------------
  auth: {
    refresh: '/api/auth/refresh',
  },

  // ---------------------------------------------------------------------------
  // Devices
  // ---------------------------------------------------------------------------
  devices: {
    list: '/api/devices',
    byId: (deviceId: string) => `/api/devices/${deviceId}`,
    update: (deviceId: string) => `/api/devices/${deviceId}`,
    updateStatus: (deviceId: string) => `/api/devices/${deviceId}/status`,
  },

  // ---------------------------------------------------------------------------
  // Readings (device sensor data)
  // ---------------------------------------------------------------------------
  readings: {
    latest: (deviceId: string) =>
      `/api/v1/readings/${deviceId}/latest?_t=${Date.now()}`,
    history: (deviceId: string, days: number) =>
      `/api/v1/readings/${deviceId}/history?days=${days}`,
    export: (deviceId: string, days: number, format: string) =>
      `/api/v1/readings/${deviceId}/export?days=${days}&format=${format}`,
    waterQuality: (range = '24h') => `/api/water-quality?range=${range}`,
    waterQualityLatest: '/api/water-quality/latest',
  },

  // ---------------------------------------------------------------------------
  // Alerts
  // ---------------------------------------------------------------------------
  alerts: {
    list: (limit = 50) => `/alerts?limit=${limit}`,
    bySeverity: (severity: string) => `/alerts?severity=${severity}`,
    acknowledge: (alertId: string) => `/api/alerts/${alertId}/acknowledge`,
    mute: (alertId: string) => `/api/alerts/${alertId}/mute`,
  },

  // ---------------------------------------------------------------------------
  // Service Requests
  // ---------------------------------------------------------------------------
  serviceRequests: {
    list: '/api/v1/service-requests',
    create: '/api/v1/service-requests',
    byId: (id: string) => `/api/v1/service-requests/${id}`,
    update: (id: string) => `/api/v1/service-requests/${id}`,
    assign: (id: string) => `/api/v1/service-requests/${id}/assign`,
  },

  // ---------------------------------------------------------------------------
  // Users
  // ---------------------------------------------------------------------------
  users: {
    list: '/api/v1/users',
    byId: (userId: string) => `/api/v1/users/${userId}`,
    update: (userId: string) => `/api/v1/users/${userId}`,
    create: '/api/v1/users',
  },

  // ---------------------------------------------------------------------------
  // Dashboard
  // ---------------------------------------------------------------------------
  dashboard: {
    stats: '/api/dashboard/stats',
    adminStats: '/api/dashboard/admin-stats',
    technicianStats: '/api/dashboard/technician-stats',
  },

  // ---------------------------------------------------------------------------
  // Notifications
  // ---------------------------------------------------------------------------
  notifications: {
    preferences: '/api/notifications/preferences',
    updatePreferences: '/api/notifications/preferences',
  },
} as const;
