/**
 * Data Service Selector
 * 
 * Automatically selects between real API and mock data based on:
 * 1. Environment variables
 * 2. Authentication status
 * 3. API connectivity
 */

import { dataService } from './dataService';
import { MockDataService } from './mockDataService';

// Check if we should use mock data
const shouldUseMockData = () => {
  // Force mock data if explicitly set
  if (process.env.REACT_APP_USE_MOCK_DATA === 'true') {
    return true;
  }
  
  // Use mock data in development with localhost API
  if (process.env.NODE_ENV === 'development' && 
      process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
    return true;
  }
  
  // Check authentication status
  const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  const isDevelopmentToken = token && token.startsWith('dev-token-');
  const isProductionAPI = process.env.REACT_APP_API_ENDPOINT?.includes('amazonaws.com');
  
  // Use mock data if development token with production API
  if (isDevelopmentToken && isProductionAPI) {
    console.warn('🔄 Switching to mock data: Development token detected with production API');
    return true;
  }
  
  // Use mock data if no token
  if (!token) {
    console.log('ℹ️ No token found - user needs to log in');
    return false;
  }
  
  return false;
};

// Create a unified service interface
export const unifiedDataService = {
  async getDevices() {
    if (shouldUseMockData()) {
      console.log('📊 Using mock data for devices');
      return MockDataService.getDevices();
    }
    console.log('📊 Using real API for devices');
    return await dataService.getDevices();
  },

  async getLatestDeviceReading(deviceId: string) {
    if (shouldUseMockData()) {
      console.log('📊 Using mock data for device reading');
      // Generate mock reading data
      return {
        deviceId,
        timestamp: new Date().toISOString(),
        pH: 7.2 + (Math.random() - 0.5) * 0.4,
        turbidity: 2.5 + (Math.random() - 0.5) * 1.0,
        tds: 450 + (Math.random() - 0.5) * 100,
        temperature: 22 + (Math.random() - 0.5) * 4,
      };
    }
    console.log('📊 Using real API for device reading');
    return await dataService.getLatestDeviceReading(deviceId);
  },

  async getDeviceReadings(deviceId: string, days: number = 7) {
    if (shouldUseMockData()) {
      console.log('📊 Using mock data for device readings');
      // Generate mock historical data
      const readings = [];
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        readings.push({
          deviceId,
          timestamp: date.toISOString(),
          pH: 7.2 + (Math.random() - 0.5) * 0.4,
          turbidity: 2.5 + (Math.random() - 0.5) * 1.0,
          tds: 450 + (Math.random() - 0.5) * 100,
          temperature: 22 + (Math.random() - 0.5) * 4,
        });
      }
      return readings;
    }
    console.log('📊 Using real API for device readings');
    return await dataService.getDeviceReadings(deviceId, days);
  },

  async getAlerts() {
    if (shouldUseMockData()) {
      console.log('📊 Using mock data for alerts');
      return MockDataService.getAlerts();
    }
    console.log('📊 Using real API for alerts');
    return await dataService.getAlerts();
  },

  async getDashboardStats() {
    if (shouldUseMockData()) {
      console.log('📊 Using mock data for dashboard stats');
      return {
        totalDevices: 3,
        activeDevices: 2,
        criticalAlerts: 1,
        averageWQI: 78,
        totalUsers: 1,
        pendingRequests: 0,
      };
    }
    console.log('📊 Using real API for dashboard stats');
    return await dataService.getDashboardStats();
  },

  // Utility methods
  isUsingMockData: shouldUseMockData,
  
  async checkBackendHealth() {
    if (shouldUseMockData()) {
      return true; // Mock data is always "healthy"
    }
    return await dataService.checkBackendHealth();
  }
};

export default unifiedDataService;