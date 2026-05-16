/**
 * Alerts API Domain Module
 */

import { apiFetch } from './client';
import { ENDPOINTS } from './endpoints';
import type { Alert } from '../types';

export const alertsApi = {
  async getAll(
    limit = 50,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<Alert[]> {
    const data = await apiFetch<Alert[] | { alerts?: Alert[]; data?: Alert[] }>(
      ENDPOINTS.alerts.list(limit),
      {},
      tokenRefresher
    );
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object') {
      const d = data as Record<string, unknown>;
      if (Array.isArray(d.alerts)) return d.alerts as Alert[];
      if (Array.isArray(d.data)) return d.data as Alert[];
    }
    return [];
  },

  async getCritical(
    tokenRefresher?: () => Promise<string | null>
  ): Promise<Alert[]> {
    const data = await apiFetch<Alert[]>(
      ENDPOINTS.alerts.bySeverity('critical'),
      {},
      tokenRefresher
    );
    return Array.isArray(data) ? data : [];
  },

  async acknowledge(
    alertId: string,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<void> {
    await apiFetch(
      ENDPOINTS.alerts.acknowledge(alertId),
      { method: 'PUT' },
      tokenRefresher
    );
  },

  async mute(
    alertId: string,
    deviceId: string,
    parameter: string,
    minutes = 120,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<void> {
    await apiFetch(
      ENDPOINTS.alerts.mute(alertId),
      {
        method: 'PUT',
        body: JSON.stringify({ deviceId, parameter, muteMinutes: minutes }),
      },
      tokenRefresher
    );
  },
};
