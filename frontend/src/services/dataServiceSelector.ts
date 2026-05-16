/**
 * Data Service Selector — Compatibility Shim
 *
 * This file previously contained a complex selector that duplicated the
 * mock/real routing logic spread across 3+ files. It has been replaced
 * by the `src/api/` domain modules (client.ts, readings.ts, alerts.ts,
 * devices.ts, users.ts).
 *
 * This shim preserves the `unifiedDataService` export so existing
 * components do NOT require a simultaneous refactor. Migrate components
 * one-by-one to import directly from `src/api/` and delete this file
 * once no imports remain.
 *
 * Mock data gate: controlled exclusively by the env var
 * REACT_APP_USE_MOCK_DATA=true — the previous heuristic that
 * auto-switched to mock data in dev was a source of confusion.
 */

import logger from '../lib/logger';
import { readingsApi } from '../api/readings';
import { alertsApi } from '../api/alerts';
import { devicesApi } from '../api/devices';
import { dataService } from './dataService';

const USE_MOCK = process.env.REACT_APP_USE_MOCK_DATA === 'true';

export const unifiedDataService = {
  async getDevices() {
    if (USE_MOCK) {
      logger.debug('Mock data: getDevices');
      return [];
    }
    return devicesApi.getAll();
  },

  async getLatestDeviceReading(deviceId: string) {
    if (USE_MOCK) {
      logger.debug('Mock data: getLatestDeviceReading', { deviceId });
      return {
        deviceId,
        timestamp: new Date().toISOString(),
        pH: 7.2 + (Math.random() - 0.5) * 0.4,
        turbidity: 2.5 + (Math.random() - 0.5) * 1.0,
        tds: 450 + (Math.random() - 0.5) * 100,
        temperature: 22 + (Math.random() - 0.5) * 4,
      };
    }
    return readingsApi.getLatest(deviceId);
  },

  async getDeviceReadings(deviceId: string, days = 7) {
    if (USE_MOCK) {
      logger.debug('Mock data: getDeviceReadings', { deviceId, days });
      return Array.from({ length: days }, (_, i) => {
        const date = new Date();
        date.setDate(date.getDate() - (days - 1 - i));
        return {
          deviceId,
          timestamp: date.toISOString(),
          pH: 7.2 + (Math.random() - 0.5) * 0.4,
          turbidity: 2.5 + (Math.random() - 0.5) * 1.0,
          tds: 450 + (Math.random() - 0.5) * 100,
          temperature: 22 + (Math.random() - 0.5) * 4,
        };
      });
    }
    return readingsApi.getHistory(deviceId, days);
  },

  async getAlerts(limit = 50) {
    if (USE_MOCK) {
      logger.debug('Mock data: getAlerts');
      return [];
    }
    return alertsApi.getAll(limit);
  },

  async getDeviceById(deviceId: string) {
    if (USE_MOCK) {
      logger.debug('Mock data: getDeviceById', { deviceId });
      return null;
    }
    return devicesApi.getById(deviceId);
  },

  async getDashboardStats() {
    if (USE_MOCK) {
      return {
        totalDevices: 3,
        activeDevices: 2,
        criticalAlerts: 1,
        averageWQI: 78,
        totalUsers: 1,
        pendingRequests: 0,
      };
    }
    return dataService.getDashboardStats();
  },

  isUsingMockData: () => USE_MOCK,

  async checkBackendHealth() {
    if (USE_MOCK) return true;
    return dataService.checkBackendHealth();
  },
};

export default unifiedDataService;