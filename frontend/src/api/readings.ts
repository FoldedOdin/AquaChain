/**
 * Readings API Domain Module
 *
 * All device sensor reading operations. Consumers import from here
 * rather than calling apiFetch directly or using DataService.getDeviceReadings.
 */

import { apiFetch } from './client';
import { ENDPOINTS } from './endpoints';
import type { WaterQualityReading } from '../types';

export interface ReadingHistoryResponse {
  success: boolean;
  readings: WaterQualityReading[];
  deviceId: string;
  days: number;
  count: number;
}

export interface LatestReadingResponse {
  success: boolean;
  reading: WaterQualityReading;
  deviceId: string;
}

export interface TrendDataPoint {
  date: string;
  wqi: number;
}

export const readingsApi = {
  /**
   * Fetch the most recent sensor reading for a device.
   * Returns null when the device has no readings yet (404 is treated as empty).
   */
  async getLatest(
    deviceId: string,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<WaterQualityReading | null> {
    try {
      const data = await apiFetch<LatestReadingResponse>(
        ENDPOINTS.readings.latest(deviceId),
        {},
        tokenRefresher
      );
      // Unwrap envelope variants: { reading: ... } | { data: ... } | flat object
      if (data && typeof data === 'object') {
        const d = data as unknown as Record<string, unknown>;
        if (d.reading) return d.reading as WaterQualityReading;
        if (d.data) return d.data as WaterQualityReading;
        return data as unknown as WaterQualityReading;
      }
      return null;
    } catch (err: any) {
      if (err?.status === 404) return null;
      throw err;
    }
  },

  /** Fetch historical readings for a device over the last `days` days. */
  async getHistory(
    deviceId: string,
    days = 7,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<WaterQualityReading[]> {
    const data = await apiFetch<ReadingHistoryResponse>(
      ENDPOINTS.readings.history(deviceId, days),
      {},
      tokenRefresher
    );
    // Handle { readings: [...] } or direct array
    if (Array.isArray(data)) return data;
    const d = data as unknown as Record<string, unknown>;
    return (Array.isArray(d.readings) ? d.readings : []) as WaterQualityReading[];
  },

  /**
   * Derive daily average WQI trend data from raw readings.
   * Returns an empty array if the data set is too sparse for the requested period.
   */
  async getHistoricalTrend(
    deviceId: string,
    days = 7,
    tokenRefresher?: () => Promise<string | null>
  ): Promise<TrendDataPoint[]> {
    const readings = await readingsApi.getHistory(deviceId, days, tokenRefresher);
    if (!readings.length) return [];

    const oldestTs = readings[readings.length - 1]?.timestamp;
    if (oldestTs) {
      const oldestDate = new Date(oldestTs);
      const requestedStart = new Date();
      requestedStart.setDate(requestedStart.getDate() - days);
      if (oldestDate > requestedStart) return [];
    }

    const dailyMap = new Map<string, { sum: number; count: number }>();
    for (const r of readings) {
      if (r.wqi && r.wqi > 0) {
        const label = new Date(r.timestamp).toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        });
        const entry = dailyMap.get(label) ?? { sum: 0, count: 0 };
        entry.sum += r.wqi;
        entry.count += 1;
        dailyMap.set(label, entry);
      }
    }

    return Array.from(dailyMap.entries())
      .map(([date, { sum, count }]) => ({ date, wqi: Math.round(sum / count) }))
      .sort(
        (a, b) =>
          new Date(a.date + ', 2024').getTime() - new Date(b.date + ', 2024').getTime()
      );
  },

  /** Request a data export for a device. */
  async requestExport(
    deviceId: string,
    days = 7,
    format: 'json' | 'csv' | 'pdf' = 'json',
    tokenRefresher?: () => Promise<string | null>
  ): Promise<unknown> {
    return apiFetch(
      ENDPOINTS.readings.export(deviceId, days, format),
      {},
      tokenRefresher
    );
  },
};
