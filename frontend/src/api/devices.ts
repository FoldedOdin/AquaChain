/**
 * Devices API Domain Module
 */

import { apiFetch } from './client';
import { ENDPOINTS } from './endpoints';
import type { DeviceStatus } from '../types';

export const devicesApi = {
  async getAll(tokenRefresher?: () => Promise<string | null>): Promise<DeviceStatus[]> {
    const data = await apiFetch<DeviceStatus[] | { devices?: DeviceStatus[]; data?: DeviceStatus[] }>(
      ENDPOINTS.devices.list,
      {},
      tokenRefresher
    );
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object') {
      const d = data as unknown as Record<string, unknown>;
      if (Array.isArray(d.devices)) return d.devices as DeviceStatus[];
      if (Array.isArray(d.data)) return d.data as DeviceStatus[];
    }
    return [];
  },

  async getById(
    deviceId: string,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<DeviceStatus | null> {
    try {
      return await apiFetch<DeviceStatus>(
        ENDPOINTS.devices.byId(deviceId),
        {},
        tokenRefresher
      );
    } catch (err: any) {
      if (err?.status === 404) return null;
      throw err;
    }
  },

  async updateStatus(
    deviceId: string,
    status: string,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<DeviceStatus> {
    return apiFetch<DeviceStatus>(
      ENDPOINTS.devices.updateStatus(deviceId),
      { method: 'PUT', body: JSON.stringify({ status }) },
      tokenRefresher
    );
  },
};
