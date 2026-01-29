/**
 * Simple API Client Tests
 * Basic tests for the enhanced API client functionality
 */

import { apiClient } from '../apiClient';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
});

describe('Enhanced API Client - Basic Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
    mockLocalStorage.getItem.mockReturnValue('mock-token');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Order Management', () => {
    it('should have createOrder method', () => {
      expect(typeof apiClient.createOrder).toBe('function');
    });

    it('should have getOrder method', () => {
      expect(typeof apiClient.getOrder).toBe('function');
    });

    it('should have getOrdersByConsumer method', () => {
      expect(typeof apiClient.getOrdersByConsumer).toBe('function');
    });

    it('should have updateOrderStatus method', () => {
      expect(typeof apiClient.updateOrderStatus).toBe('function');
    });

    it('should have cancelOrder method', () => {
      expect(typeof apiClient.cancelOrder).toBe('function');
    });
  });

  describe('Payment Processing', () => {
    it('should have createRazorpayOrder method', () => {
      expect(typeof apiClient.createRazorpayOrder).toBe('function');
    });

    it('should have verifyRazorpayPayment method', () => {
      expect(typeof apiClient.verifyRazorpayPayment).toBe('function');
    });

    it('should have createCODPayment method', () => {
      expect(typeof apiClient.createCODPayment).toBe('function');
    });

    it('should have getPaymentStatus method', () => {
      expect(typeof apiClient.getPaymentStatus).toBe('function');
    });
  });

  describe('Technician Assignment', () => {
    it('should have assignTechnician method', () => {
      expect(typeof apiClient.assignTechnician).toBe('function');
    });

    it('should have getAvailableTechnicians method', () => {
      expect(typeof apiClient.getAvailableTechnicians).toBe('function');
    });

    it('should have updateTechnicianAvailability method', () => {
      expect(typeof apiClient.updateTechnicianAvailability).toBe('function');
    });
  });

  describe('Status Simulator', () => {
    it('should have startStatusSimulation method', () => {
      expect(typeof apiClient.startStatusSimulation).toBe('function');
    });

    it('should have stopStatusSimulation method', () => {
      expect(typeof apiClient.stopStatusSimulation).toBe('function');
    });

    it('should have getSimulationStatus method', () => {
      expect(typeof apiClient.getSimulationStatus).toBe('function');
    });
  });

  describe('Error Handling and Retry Logic', () => {
    it('should have retryApiCall method', () => {
      expect(typeof apiClient.retryApiCall).toBe('function');
    });

    it('should have checkApiHealth method', () => {
      expect(typeof apiClient.checkApiHealth).toBe('function');
    });

    it('should have getApiVersion method', () => {
      expect(typeof apiClient.getApiVersion).toBe('function');
    });
  });

  describe('WebSocket Connection Management', () => {
    it('should have getWebSocketUrl method', () => {
      expect(typeof apiClient.getWebSocketUrl).toBe('function');
    });

    it('should have connectToOrderUpdates method', () => {
      expect(typeof apiClient.connectToOrderUpdates).toBe('function');
    });

    it('should have disconnectFromOrderUpdates method', () => {
      expect(typeof apiClient.disconnectFromOrderUpdates).toBe('function');
    });

    it('should have connectToOrderNotifications method', () => {
      expect(typeof apiClient.connectToOrderNotifications).toBe('function');
    });

    it('should have disconnectFromOrderNotifications method', () => {
      expect(typeof apiClient.disconnectFromOrderNotifications).toBe('function');
    });
  });

  describe('Basic API Functionality', () => {
    it('should make a successful API call', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: () => Promise.resolve({ status: 'healthy' }),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      const result = await apiClient.checkApiHealth();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/health'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-token'
          })
        })
      );

      expect(result.data).toEqual({ status: 'healthy' });
      expect(result.status).toBe(200);
    });

    it('should handle API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ error: 'Server error' })
      });

      await expect(apiClient.checkApiHealth())
        .rejects
        .toMatchObject({
          message: 'Server error',
          status: 500
        });
    });
  });

  describe('WebSocket URL Generation', () => {
    it('should generate correct WebSocket URL for HTTPS', () => {
      Object.defineProperty(window, 'location', {
        value: { protocol: 'https:', host: 'example.com' },
        writable: true
      });

      const url = apiClient.getWebSocketUrl();
      expect(url).toContain('wss://');
    });

    it('should generate correct WebSocket URL for HTTP', () => {
      Object.defineProperty(window, 'location', {
        value: { protocol: 'http:', host: 'localhost:3000' },
        writable: true
      });

      const url = apiClient.getWebSocketUrl();
      expect(url).toContain('ws://');
    });
  });
});