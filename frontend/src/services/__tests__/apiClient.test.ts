/**
 * API Client Tests
 * Tests for the enhanced API client with order management endpoints
 */

import { apiClient } from '../apiClient';
import { 
  CreateOrderRequest, 
  OrderStatus, 
  PaymentStatus, 
  PaymentMethod,
  Location 
} from '../../types/ordering';

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

// Mock WebSocket service
jest.mock('../websocketService', () => ({
  websocketService: {
    connect: jest.fn(),
    disconnect: jest.fn()
  }
}));

describe('Enhanced API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch.mockClear();
    mockLocalStorage.getItem.mockReturnValue('mock-token');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Order Management API', () => {
    const mockOrder = {
      id: 'order-123',
      consumerId: 'consumer-456',
      deviceType: 'pH Sensor',
      serviceType: 'Installation',
      paymentMethod: 'COD' as PaymentMethod,
      status: OrderStatus.ORDER_PLACED,
      amount: 5000,
      deliveryAddress: {
        street: '123 Main St',
        city: 'Mumbai',
        state: 'Maharashtra',
        pincode: '400001',
        country: 'India'
      },
      contactInfo: {
        name: 'John Doe',
        phone: '+91-9876543210',
        email: 'john@example.com'
      },
      createdAt: new Date(),
      updatedAt: new Date(),
      statusHistory: []
    };

    const mockCreateOrderRequest: CreateOrderRequest = {
      consumerId: 'consumer-456',
      deviceType: 'pH Sensor',
      serviceType: 'Installation',
      paymentMethod: 'COD',
      deliveryAddress: {
        street: '123 Main St',
        city: 'Mumbai',
        state: 'Maharashtra',
        pincode: '400001',
        country: 'India'
      },
      contactInfo: {
        name: 'John Doe',
        phone: '+91-9876543210',
        email: 'john@example.com'
      }
    };

    describe('createOrder', () => {
      it('creates a new order successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 201,
          statusText: 'Created',
          json: () => Promise.resolve(mockOrder),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.createOrder(mockCreateOrderRequest);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders'),
          expect.objectContaining({
            method: 'POST',
            headers: expect.objectContaining({
              'Content-Type': 'application/json',
              'Authorization': 'Bearer mock-token'
            }),
            body: JSON.stringify(mockCreateOrderRequest)
          })
        );

        expect(result.data).toEqual(mockOrder);
        expect(result.status).toBe(201);
      });

      it('handles order creation errors', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 400,
          statusText: 'Bad Request',
          json: () => Promise.resolve({ error: 'Invalid order data' })
        });

        await expect(apiClient.createOrder(mockCreateOrderRequest))
          .rejects
          .toMatchObject({
            message: 'Invalid order data',
            status: 400
          });
      });
    });

    describe('getOrder', () => {
      it('fetches order by ID successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockOrder),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.getOrder('order-123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders/order-123'),
          expect.objectContaining({
            method: 'GET',
            headers: expect.objectContaining({
              'Authorization': 'Bearer mock-token'
            })
          })
        );

        expect(result.data).toEqual(mockOrder);
      });

      it('handles order not found', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 404,
          statusText: 'Not Found',
          json: () => Promise.resolve({ error: 'Order not found' })
        });

        await expect(apiClient.getOrder('nonexistent-order'))
          .rejects
          .toMatchObject({
            message: 'Order not found',
            status: 404
          });
      });
    });

    describe('getOrdersByConsumer', () => {
      it('fetches consumer orders successfully', async () => {
        const mockOrders = [mockOrder];
        
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockOrders),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.getOrdersByConsumer('consumer-456');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders/consumer/consumer-456'),
          expect.objectContaining({
            method: 'GET'
          })
        );

        expect(result.data).toEqual(mockOrders);
      });
    });

    describe('updateOrderStatus', () => {
      it('updates order status successfully', async () => {
        const updatedOrder = { ...mockOrder, status: OrderStatus.SHIPPED };
        
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(updatedOrder),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.updateOrderStatus('order-123', OrderStatus.SHIPPED, { note: 'Shipped via courier' });

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders/order-123/status'),
          expect.objectContaining({
            method: 'PATCH',
            body: JSON.stringify({ 
              status: OrderStatus.SHIPPED, 
              metadata: { note: 'Shipped via courier' } 
            })
          })
        );

        expect(result.data).toEqual(updatedOrder);
      });
    });

    describe('cancelOrder', () => {
      it('cancels order successfully', async () => {
        const cancelledOrder = { ...mockOrder, status: OrderStatus.CANCELLED };
        
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(cancelledOrder),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.cancelOrder('order-123', 'Customer requested cancellation');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/orders/order-123/cancel'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ reason: 'Customer requested cancellation' })
          })
        );

        expect(result.data).toEqual(cancelledOrder);
      });
    });
  });

  describe('Payment Processing API', () => {
    describe('createRazorpayOrder', () => {
      it('creates Razorpay order successfully', async () => {
        const mockRazorpayOrder = {
          id: 'order_razorpay_123',
          amount: 5000,
          currency: 'INR',
          receipt: 'order-123',
          status: 'created'
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 201,
          statusText: 'Created',
          json: () => Promise.resolve(mockRazorpayOrder),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.createRazorpayOrder(5000, 'order-123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/payments/razorpay/create'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ amount: 5000, orderId: 'order-123' })
          })
        );

        expect(result.data).toEqual(mockRazorpayOrder);
      });

      it('handles Razorpay order creation errors', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: false,
          status: 400,
          statusText: 'Bad Request',
          json: () => Promise.resolve({ error: 'Invalid amount' })
        });

        await expect(apiClient.createRazorpayOrder(-100, 'order-123'))
          .rejects
          .toMatchObject({
            message: 'Invalid amount',
            status: 400
          });
      });
    });

    describe('verifyRazorpayPayment', () => {
      it('verifies payment successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(true),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.verifyRazorpayPayment('pay_123', 'order_123', 'signature_123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/payments/razorpay/verify'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ 
              paymentId: 'pay_123', 
              orderId: 'order_123', 
              signature: 'signature_123' 
            })
          })
        );

        expect(result.data).toBe(true);
      });

      it('handles payment verification failure', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(false),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.verifyRazorpayPayment('pay_123', 'order_123', 'invalid_signature');

        expect(result.data).toBe(false);
      });
    });

    describe('createCODPayment', () => {
      it('creates COD payment successfully', async () => {
        const mockPayment = {
          id: 'payment-123',
          orderId: 'order-123',
          amount: 5000,
          paymentMethod: 'COD' as PaymentMethod,
          status: PaymentStatus.COD_PENDING,
          createdAt: new Date(),
          updatedAt: new Date()
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 201,
          statusText: 'Created',
          json: () => Promise.resolve(mockPayment),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.createCODPayment('order-123', 5000);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/payments/cod/create'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ orderId: 'order-123', amount: 5000 })
          })
        );

        expect(result.data).toEqual(mockPayment);
      });
    });

    describe('getPaymentStatus', () => {
      it('fetches payment status successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(PaymentStatus.COMPLETED),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.getPaymentStatus('order-123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/payments/status/order-123'),
          expect.objectContaining({
            method: 'GET'
          })
        );

        expect(result.data).toBe(PaymentStatus.COMPLETED);
      });
    });
  });

  describe('Technician Assignment API', () => {
    const mockLocation: Location = {
      latitude: 19.0760,
      longitude: 72.8777,
      address: '123 Main St, Mumbai',
      city: 'Mumbai',
      state: 'Maharashtra',
      pincode: '400001'
    };

    const mockTechnician = {
      id: 'tech-123',
      name: 'John Technician',
      phone: '+91-9876543210',
      email: 'tech@example.com',
      location: mockLocation,
      available: true,
      skills: ['pH Sensor', 'TDS Meter'],
      rating: 4.5
    };

    describe('assignTechnician', () => {
      it('assigns technician successfully', async () => {
        const mockAssignment = {
          orderId: 'order-123',
          technicianId: 'tech-123',
          assignedAt: new Date(),
          distance: 5.2
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockAssignment),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.assignTechnician('order-123', mockLocation);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/technicians/assign'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ orderId: 'order-123', serviceLocation: mockLocation })
          })
        );

        expect(result.data).toEqual(mockAssignment);
      });
    });

    describe('getAvailableTechnicians', () => {
      it('fetches available technicians successfully', async () => {
        const mockTechnicians = [mockTechnician];

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockTechnicians),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.getAvailableTechnicians(mockLocation, 25);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/technicians/available'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ location: mockLocation, radius: 25 })
          })
        );

        expect(result.data).toEqual(mockTechnicians);
      });

      it('uses default radius when not provided', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve([]),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        await apiClient.getAvailableTechnicians(mockLocation);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/technicians/available'),
          expect.objectContaining({
            body: JSON.stringify({ location: mockLocation, radius: 50 })
          })
        );
      });
    });

    describe('updateTechnicianAvailability', () => {
      it('updates technician availability successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve({}),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.updateTechnicianAvailability('tech-123', false);

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/technicians/tech-123/availability'),
          expect.objectContaining({
            method: 'PATCH',
            body: JSON.stringify({ available: false })
          })
        );

        expect(result.status).toBe(200);
      });
    });
  });

  describe('Status Simulator API', () => {
    describe('startStatusSimulation', () => {
      it('starts simulation successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve({}),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.startStatusSimulation('order-123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/simulator/start'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ orderId: 'order-123' })
          })
        );

        expect(result.status).toBe(200);
      });
    });

    describe('stopStatusSimulation', () => {
      it('stops simulation successfully', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve({}),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.stopStatusSimulation('order-123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/simulator/stop'),
          expect.objectContaining({
            method: 'POST',
            body: JSON.stringify({ orderId: 'order-123' })
          })
        );

        expect(result.status).toBe(200);
      });
    });

    describe('getSimulationStatus', () => {
      it('fetches simulation status successfully', async () => {
        const mockStatus = {
          orderId: 'order-123',
          currentStatus: OrderStatus.SHIPPED,
          nextStatus: OrderStatus.OUT_FOR_DELIVERY,
          nextTransitionAt: new Date(),
          isActive: true
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockStatus),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.getSimulationStatus('order-123');

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/simulator/status/order-123'),
          expect.objectContaining({
            method: 'GET'
          })
        );

        expect(result.data).toEqual(mockStatus);
      });
    });
  });

  describe('Error Handling and Retry Logic', () => {
    describe('retryApiCall', () => {
      it('retries failed API calls with exponential backoff', async () => {
        const mockApiCall = jest.fn()
          .mockRejectedValueOnce({ status: 500, message: 'Server Error' })
          .mockRejectedValueOnce({ status: 500, message: 'Server Error' })
          .mockResolvedValueOnce({ data: 'success', status: 200, statusText: 'OK' });

        jest.useFakeTimers();

        const retryPromise = apiClient.retryApiCall(mockApiCall, 3, 1000);

        // Fast-forward through the retry delays
        jest.advanceTimersByTime(1000); // First retry
        jest.advanceTimersByTime(2000); // Second retry

        const result = await retryPromise;

        expect(mockApiCall).toHaveBeenCalledTimes(3);
        expect(result.data).toBe('success');

        jest.useRealTimers();
      });

      it('does not retry client errors (4xx)', async () => {
        const mockApiCall = jest.fn()
          .mockRejectedValueOnce({ status: 400, message: 'Bad Request' });

        await expect(apiClient.retryApiCall(mockApiCall, 3, 1000))
          .rejects
          .toMatchObject({
            status: 400,
            message: 'Bad Request'
          });

        expect(mockApiCall).toHaveBeenCalledTimes(1);
      });

      it('throws error after max retries exceeded', async () => {
        const mockApiCall = jest.fn()
          .mockRejectedValue({ status: 500, message: 'Server Error' });

        jest.useFakeTimers();

        const retryPromise = apiClient.retryApiCall(mockApiCall, 2, 1000);

        // Fast-forward through all retry attempts
        jest.advanceTimersByTime(1000); // First retry
        jest.advanceTimersByTime(2000); // Second retry

        await expect(retryPromise)
          .rejects
          .toMatchObject({
            status: 500,
            message: 'Server Error'
          });

        expect(mockApiCall).toHaveBeenCalledTimes(3); // Initial + 2 retries

        jest.useRealTimers();
      });
    });

    describe('checkApiHealth', () => {
      it('checks API health successfully', async () => {
        const mockHealthResponse = {
          status: 'healthy',
          timestamp: new Date().toISOString()
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockHealthResponse),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.checkApiHealth();

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/health'),
          expect.objectContaining({
            method: 'GET'
          })
        );

        expect(result.data).toEqual(mockHealthResponse);
      });
    });

    describe('getApiVersion', () => {
      it('fetches API version successfully', async () => {
        const mockVersionResponse = {
          version: '1.0.0',
          build: 'abc123'
        };

        mockFetch.mockResolvedValueOnce({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: () => Promise.resolve(mockVersionResponse),
          headers: new Headers({ 'content-type': 'application/json' })
        });

        const result = await apiClient.getApiVersion();

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/version'),
          expect.objectContaining({
            method: 'GET'
          })
        );

        expect(result.data).toEqual(mockVersionResponse);
      });
    });
  });

  describe('WebSocket Connection Management', () => {
    const { websocketService } = require('../websocketService');

    describe('getWebSocketUrl', () => {
      it('returns correct WebSocket URL for HTTPS', () => {
        Object.defineProperty(window, 'location', {
          value: { protocol: 'https:', host: 'example.com' },
          writable: true
        });

        const url = apiClient.getWebSocketUrl();
        expect(url).toContain('wss://');
      });

      it('returns correct WebSocket URL for HTTP', () => {
        Object.defineProperty(window, 'location', {
          value: { protocol: 'http:', host: 'localhost:3000' },
          writable: true
        });

        const url = apiClient.getWebSocketUrl();
        expect(url).toContain('ws://');
      });

      it('uses environment variable when available', () => {
        process.env.REACT_APP_WEBSOCKET_ENDPOINT = 'wss://custom-ws.example.com';
        
        const url = apiClient.getWebSocketUrl();
        expect(url).toBe('wss://custom-ws.example.com');
        
        delete process.env.REACT_APP_WEBSOCKET_ENDPOINT;
      });
    });

    describe('connectToOrderUpdates', () => {
      it('connects to order-specific WebSocket topic', () => {
        const mockCallback = jest.fn();
        
        apiClient.connectToOrderUpdates('order-123', mockCallback);
        
        expect(websocketService.connect).toHaveBeenCalledWith('order-order-123', mockCallback);
      });
    });

    describe('disconnectFromOrderUpdates', () => {
      it('disconnects from order-specific WebSocket topic', () => {
        const mockCallback = jest.fn();
        
        apiClient.disconnectFromOrderUpdates('order-123', mockCallback);
        
        expect(websocketService.disconnect).toHaveBeenCalledWith('order-order-123', mockCallback);
      });

      it('disconnects all subscribers when no callback provided', () => {
        apiClient.disconnectFromOrderUpdates('order-123');
        
        expect(websocketService.disconnect).toHaveBeenCalledWith('order-order-123', undefined);
      });
    });

    describe('connectToOrderNotifications', () => {
      it('connects to consumer-specific order notifications', () => {
        const mockCallback = jest.fn();
        
        apiClient.connectToOrderNotifications('consumer-456', mockCallback);
        
        expect(websocketService.connect).toHaveBeenCalledWith('consumer-consumer-456-orders', mockCallback);
      });
    });

    describe('disconnectFromOrderNotifications', () => {
      it('disconnects from consumer-specific order notifications', () => {
        const mockCallback = jest.fn();
        
        apiClient.disconnectFromOrderNotifications('consumer-456', mockCallback);
        
        expect(websocketService.disconnect).toHaveBeenCalledWith('consumer-consumer-456-orders', mockCallback);
      });
    });
  });

  describe('Authentication', () => {
    it('includes auth token in requests when available', async () => {
      mockLocalStorage.getItem.mockReturnValue('test-auth-token');
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: () => Promise.resolve({}),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiClient.checkApiHealth();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-auth-token'
          })
        })
      );
    });

    it('works without auth token', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: () => Promise.resolve({}),
        headers: new Headers({ 'content-type': 'application/json' })
      });

      await apiClient.checkApiHealth();

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.not.objectContaining({
            'Authorization': expect.any(String)
          })
        })
      );
    });
  });
});