/**
 * Ordering Service Tests
 * Tests for the high-level ordering service that uses the enhanced API client
 */

import { orderingService } from '../orderingService';
import { apiClient } from '../apiClient';
import { websocketService } from '../websocketService';
import {
  CreateOrderRequest,
  Order,
  OrderStatus,
  PaymentStatus,
  PaymentMethod,
  Location
} from '../../types/ordering';

// Mock the API client
jest.mock('../apiClient', () => ({
  apiClient: {
    retryApiCall: jest.fn(),
    createOrder: jest.fn(),
    getOrder: jest.fn(),
    getOrdersByConsumer: jest.fn(),
    updateOrderStatus: jest.fn(),
    cancelOrder: jest.fn(),
    createRazorpayOrder: jest.fn(),
    verifyRazorpayPayment: jest.fn(),
    createCODPayment: jest.fn(),
    getPaymentStatus: jest.fn(),
    assignTechnician: jest.fn(),
    getAvailableTechnicians: jest.fn(),
    startStatusSimulation: jest.fn(),
    stopStatusSimulation: jest.fn(),
    getSimulationStatus: jest.fn(),
    checkApiHealth: jest.fn(),
    getApiVersion: jest.fn()
  }
}));

// Mock the WebSocket service
jest.mock('../websocketService', () => ({
  websocketService: {
    connect: jest.fn(),
    disconnect: jest.fn()
  }
}));

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;
const mockWebSocketService = websocketService as jest.Mocked<typeof websocketService>;

describe('Ordering Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const mockOrder: Order = {
    id: 'order-123',
    consumerId: 'consumer-456',
    deviceType: 'pH Sensor',
    serviceType: 'Installation',
    paymentMethod: 'COD',
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

  describe('Order Management', () => {
    describe('createOrder', () => {
      it('creates order successfully with retry logic', async () => {
        mockApiClient.retryApiCall.mockResolvedValueOnce({
          data: mockOrder,
          status: 201,
          statusText: 'Created'
        });

        const result = await orderingService.createOrder(mockCreateOrderRequest);

        expect(mockApiClient.retryApiCall).toHaveBeenCalledWith(
          expect.any(Function),
          3,
          1000
        );
        expect(result).toEqual(mockOrder);
      });

      it('throws error when no order data received', async () => {
        mockApiClient.retryApiCall.mockResolvedValueOnce({
          data: null,
          status: 201,
          statusText: 'Created'
        });

        await expect(orderingService.createOrder(mockCreateOrderRequest))
          .rejects
          .toThrow('No order data received from server');
      });

      it('handles API errors gracefully', async () => {
        mockApiClient.retryApiCall.mockRejectedValueOnce(new Error('Network error'));

        await expect(orderingService.createOrder(mockCreateOrderRequest))
          .rejects
          .toThrow('Failed to create order: Network error');
      });
    });

    describe('getOrder', () => {
      it('fetches order successfully', async () => {
        mockApiClient.getOrder.mockResolvedValueOnce({
          data: mockOrder,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getOrder('order-123');

        expect(mockApiClient.getOrder).toHaveBeenCalledWith('order-123');
        expect(result).toEqual(mockOrder);
      });

      it('throws error when order not found', async () => {
        mockApiClient.getOrder.mockResolvedValueOnce({
          data: null,
          status: 404,
          statusText: 'Not Found'
        });

        await expect(orderingService.getOrder('nonexistent'))
          .rejects
          .toThrow('Order not found');
      });
    });

    describe('getOrdersByConsumer', () => {
      it('fetches consumer orders successfully', async () => {
        const mockOrders = [mockOrder];
        mockApiClient.getOrdersByConsumer.mockResolvedValueOnce({
          data: mockOrders,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getOrdersByConsumer('consumer-456');

        expect(mockApiClient.getOrdersByConsumer).toHaveBeenCalledWith('consumer-456');
        expect(result).toEqual(mockOrders);
      });

      it('returns empty array when no data received', async () => {
        mockApiClient.getOrdersByConsumer.mockResolvedValueOnce({
          data: null,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getOrdersByConsumer('consumer-456');

        expect(result).toEqual([]);
      });
    });

    describe('updateOrderStatus', () => {
      it('updates order status successfully', async () => {
        const updatedOrder = { ...mockOrder, status: OrderStatus.SHIPPED };
        mockApiClient.updateOrderStatus.mockResolvedValueOnce({
          data: updatedOrder,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.updateOrderStatus('order-123', OrderStatus.SHIPPED, { note: 'Shipped' });

        expect(mockApiClient.updateOrderStatus).toHaveBeenCalledWith('order-123', OrderStatus.SHIPPED, { note: 'Shipped' });
        expect(result).toEqual(updatedOrder);
      });
    });

    describe('cancelOrder', () => {
      it('cancels order successfully', async () => {
        const cancelledOrder = { ...mockOrder, status: OrderStatus.CANCELLED };
        mockApiClient.cancelOrder.mockResolvedValueOnce({
          data: cancelledOrder,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.cancelOrder('order-123', 'Customer request');

        expect(mockApiClient.cancelOrder).toHaveBeenCalledWith('order-123', 'Customer request');
        expect(result).toEqual(cancelledOrder);
      });
    });
  });

  describe('Payment Processing', () => {
    describe('createRazorpayOrder', () => {
      it('creates Razorpay order successfully', async () => {
        const mockRazorpayOrder = {
          id: 'order_razorpay_123',
          amount: 5000,
          currency: 'INR',
          receipt: 'order-123',
          status: 'created'
        };

        mockApiClient.createRazorpayOrder.mockResolvedValueOnce({
          data: mockRazorpayOrder,
          status: 201,
          statusText: 'Created'
        });

        const result = await orderingService.createRazorpayOrder(5000, 'order-123');

        expect(mockApiClient.createRazorpayOrder).toHaveBeenCalledWith(5000, 'order-123');
        expect(result).toEqual(mockRazorpayOrder);
      });
    });

    describe('verifyRazorpayPayment', () => {
      it('verifies payment successfully', async () => {
        mockApiClient.verifyRazorpayPayment.mockResolvedValueOnce({
          data: true,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.verifyRazorpayPayment('pay_123', 'order_123', 'sig_123');

        expect(mockApiClient.verifyRazorpayPayment).toHaveBeenCalledWith('pay_123', 'order_123', 'sig_123');
        expect(result).toBe(true);
      });

      it('returns false when verification fails', async () => {
        mockApiClient.verifyRazorpayPayment.mockResolvedValueOnce({
          data: null,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.verifyRazorpayPayment('pay_123', 'order_123', 'invalid_sig');

        expect(result).toBe(false);
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

        mockApiClient.createCODPayment.mockResolvedValueOnce({
          data: mockPayment,
          status: 201,
          statusText: 'Created'
        });

        const result = await orderingService.createCODPayment('order-123', 5000);

        expect(mockApiClient.createCODPayment).toHaveBeenCalledWith('order-123', 5000);
        expect(result).toEqual(mockPayment);
      });
    });

    describe('getPaymentStatus', () => {
      it('fetches payment status successfully', async () => {
        mockApiClient.getPaymentStatus.mockResolvedValueOnce({
          data: PaymentStatus.COMPLETED,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getPaymentStatus('order-123');

        expect(mockApiClient.getPaymentStatus).toHaveBeenCalledWith('order-123');
        expect(result).toBe(PaymentStatus.COMPLETED);
      });

      it('returns PENDING when no data received', async () => {
        mockApiClient.getPaymentStatus.mockResolvedValueOnce({
          data: null,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getPaymentStatus('order-123');

        expect(result).toBe(PaymentStatus.PENDING);
      });
    });
  });

  describe('Technician Assignment', () => {
    const mockLocation: Location = {
      latitude: 19.0760,
      longitude: 72.8777,
      address: '123 Main St, Mumbai',
      city: 'Mumbai',
      state: 'Maharashtra',
      pincode: '400001'
    };

    describe('assignTechnician', () => {
      it('assigns technician successfully', async () => {
        const mockAssignment = {
          orderId: 'order-123',
          technicianId: 'tech-123',
          assignedAt: new Date(),
          distance: 5.2
        };

        mockApiClient.assignTechnician.mockResolvedValueOnce({
          data: mockAssignment,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.assignTechnician('order-123', mockLocation);

        expect(mockApiClient.assignTechnician).toHaveBeenCalledWith('order-123', mockLocation);
        expect(result).toEqual(mockAssignment);
      });
    });

    describe('getAvailableTechnicians', () => {
      it('fetches available technicians successfully', async () => {
        const mockTechnicians = [{
          id: 'tech-123',
          name: 'John Technician',
          phone: '+91-9876543210',
          email: 'tech@example.com',
          location: mockLocation,
          available: true,
          skills: ['pH Sensor'],
          rating: 4.5
        }];

        mockApiClient.getAvailableTechnicians.mockResolvedValueOnce({
          data: mockTechnicians,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getAvailableTechnicians(mockLocation, 25);

        expect(mockApiClient.getAvailableTechnicians).toHaveBeenCalledWith(mockLocation, 25);
        expect(result).toEqual(mockTechnicians);
      });

      it('returns empty array when no data received', async () => {
        mockApiClient.getAvailableTechnicians.mockResolvedValueOnce({
          data: null,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getAvailableTechnicians(mockLocation);

        expect(result).toEqual([]);
      });
    });
  });

  describe('Status Simulation', () => {
    describe('startStatusSimulation', () => {
      it('starts simulation successfully', async () => {
        mockApiClient.startStatusSimulation.mockResolvedValueOnce({
          data: undefined,
          status: 200,
          statusText: 'OK'
        });

        await orderingService.startStatusSimulation('order-123');

        expect(mockApiClient.startStatusSimulation).toHaveBeenCalledWith('order-123');
      });
    });

    describe('stopStatusSimulation', () => {
      it('stops simulation successfully', async () => {
        mockApiClient.stopStatusSimulation.mockResolvedValueOnce({
          data: undefined,
          status: 200,
          statusText: 'OK'
        });

        await orderingService.stopStatusSimulation('order-123');

        expect(mockApiClient.stopStatusSimulation).toHaveBeenCalledWith('order-123');
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

        mockApiClient.getSimulationStatus.mockResolvedValueOnce({
          data: mockStatus,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getSimulationStatus('order-123');

        expect(mockApiClient.getSimulationStatus).toHaveBeenCalledWith('order-123');
        expect(result).toEqual(mockStatus);
      });
    });
  });

  describe('Real-time Updates', () => {
    describe('subscribeToOrderUpdates', () => {
      it('subscribes to order updates and returns unsubscribe function', () => {
        const mockCallback = jest.fn();
        
        const unsubscribe = orderingService.subscribeToOrderUpdates('order-123', mockCallback);

        expect(mockWebSocketService.connect).toHaveBeenCalledWith('order-order-123', expect.any(Function));
        expect(typeof unsubscribe).toBe('function');

        // Test unsubscribe
        unsubscribe();
        expect(mockWebSocketService.disconnect).toHaveBeenCalledWith('order-order-123', expect.any(Function));
      });

      it('filters messages for correct order ID', () => {
        const mockCallback = jest.fn();
        let messageHandler: (data: any) => void;

        mockWebSocketService.connect.mockImplementation((topic, handler) => {
          messageHandler = handler;
        });

        orderingService.subscribeToOrderUpdates('order-123', mockCallback);

        // Simulate correct message
        messageHandler({ type: 'order_update', orderId: 'order-123', data: 'test' });
        expect(mockCallback).toHaveBeenCalledWith({ type: 'order_update', orderId: 'order-123', data: 'test' });

        // Simulate incorrect message (different order ID)
        mockCallback.mockClear();
        messageHandler({ type: 'order_update', orderId: 'order-456', data: 'test' });
        expect(mockCallback).not.toHaveBeenCalled();

        // Simulate incorrect message type
        messageHandler({ type: 'other_update', orderId: 'order-123', data: 'test' });
        expect(mockCallback).not.toHaveBeenCalled();
      });
    });

    describe('subscribeToOrderNotifications', () => {
      it('subscribes to consumer order notifications', () => {
        const mockCallback = jest.fn();
        
        const unsubscribe = orderingService.subscribeToOrderNotifications('consumer-456', mockCallback);

        expect(mockWebSocketService.connect).toHaveBeenCalledWith('consumer-consumer-456-orders', expect.any(Function));
        expect(typeof unsubscribe).toBe('function');

        // Test unsubscribe
        unsubscribe();
        expect(mockWebSocketService.disconnect).toHaveBeenCalledWith('consumer-consumer-456-orders', expect.any(Function));
      });

      it('filters messages for correct consumer ID', () => {
        const mockCallback = jest.fn();
        let messageHandler: (data: any) => void;

        mockWebSocketService.connect.mockImplementation((topic, handler) => {
          messageHandler = handler;
        });

        orderingService.subscribeToOrderNotifications('consumer-456', mockCallback);

        // Simulate correct message
        messageHandler({ type: 'order_notification', consumerId: 'consumer-456', data: 'test' });
        expect(mockCallback).toHaveBeenCalledWith({ type: 'order_notification', consumerId: 'consumer-456', data: 'test' });

        // Simulate incorrect message (different consumer ID)
        mockCallback.mockClear();
        messageHandler({ type: 'order_notification', consumerId: 'consumer-789', data: 'test' });
        expect(mockCallback).not.toHaveBeenCalled();
      });
    });
  });

  describe('Complete Order Flow Helpers', () => {
    describe('placeOrderWithCOD', () => {
      it('places COD order successfully', async () => {
        const mockPayment = {
          id: 'payment-123',
          orderId: 'order-123',
          amount: 5000,
          paymentMethod: 'COD' as PaymentMethod,
          status: PaymentStatus.COD_PENDING,
          createdAt: new Date(),
          updatedAt: new Date()
        };

        mockApiClient.retryApiCall.mockResolvedValueOnce({
          data: mockOrder,
          status: 201,
          statusText: 'Created'
        });
        mockApiClient.createCODPayment.mockResolvedValueOnce({
          data: mockPayment,
          status: 201,
          statusText: 'Created'
        });
        mockApiClient.startStatusSimulation.mockResolvedValueOnce({
          data: undefined,
          status: 200,
          statusText: 'OK'
        });

        // Mock environment variable
        const originalEnv = process.env.REACT_APP_ENABLE_STATUS_SIMULATION;
        process.env.REACT_APP_ENABLE_STATUS_SIMULATION = 'true';

        const result = await orderingService.placeOrderWithCOD(mockCreateOrderRequest);

        expect(result.order).toEqual(mockOrder);
        expect(result.payment).toEqual(mockPayment);
        expect(mockApiClient.startStatusSimulation).toHaveBeenCalledWith('order-123');

        // Restore environment variable
        process.env.REACT_APP_ENABLE_STATUS_SIMULATION = originalEnv;
      });

      it('does not start simulation when disabled', async () => {
        const mockPayment = {
          id: 'payment-123',
          orderId: 'order-123',
          amount: 5000,
          paymentMethod: 'COD' as PaymentMethod,
          status: PaymentStatus.COD_PENDING,
          createdAt: new Date(),
          updatedAt: new Date()
        };

        mockApiClient.retryApiCall.mockResolvedValueOnce({
          data: mockOrder,
          status: 201,
          statusText: 'Created'
        });
        mockApiClient.createCODPayment.mockResolvedValueOnce({
          data: mockPayment,
          status: 201,
          statusText: 'Created'
        });

        // Mock environment variable
        const originalEnv = process.env.REACT_APP_ENABLE_STATUS_SIMULATION;
        process.env.REACT_APP_ENABLE_STATUS_SIMULATION = 'false';

        const result = await orderingService.placeOrderWithCOD(mockCreateOrderRequest);

        expect(result.order).toEqual(mockOrder);
        expect(result.payment).toEqual(mockPayment);
        expect(mockApiClient.startStatusSimulation).not.toHaveBeenCalled();

        // Restore environment variable
        process.env.REACT_APP_ENABLE_STATUS_SIMULATION = originalEnv;
      });
    });

    describe('placeOrderWithRazorpay', () => {
      it('places Razorpay order successfully', async () => {
        mockApiClient.verifyRazorpayPayment.mockResolvedValueOnce({
          data: true,
          status: 200,
          statusText: 'OK'
        });
        mockApiClient.retryApiCall.mockResolvedValueOnce({
          data: mockOrder,
          status: 201,
          statusText: 'Created'
        });
        mockApiClient.getPaymentStatus.mockResolvedValueOnce({
          data: PaymentStatus.COMPLETED,
          status: 200,
          statusText: 'OK'
        });
        mockApiClient.startStatusSimulation.mockResolvedValueOnce({
          data: undefined,
          status: 200,
          statusText: 'OK'
        });

        // Mock environment variable
        const originalEnv = process.env.REACT_APP_ENABLE_STATUS_SIMULATION;
        process.env.REACT_APP_ENABLE_STATUS_SIMULATION = 'true';

        const result = await orderingService.placeOrderWithRazorpay(
          mockCreateOrderRequest,
          'pay_123',
          'sig_123'
        );

        expect(mockApiClient.verifyRazorpayPayment).toHaveBeenCalledWith('pay_123', 'consumer-456', 'sig_123');
        expect(result.order).toEqual(mockOrder);
        expect(result.payment.razorpayPaymentId).toBe('pay_123');
        expect(mockApiClient.startStatusSimulation).toHaveBeenCalledWith('order-123');

        // Restore environment variable
        process.env.REACT_APP_ENABLE_STATUS_SIMULATION = originalEnv;
      });

      it('throws error when payment verification fails', async () => {
        mockApiClient.verifyRazorpayPayment.mockResolvedValueOnce({
          data: false,
          status: 200,
          statusText: 'OK'
        });

        await expect(orderingService.placeOrderWithRazorpay(
          mockCreateOrderRequest,
          'pay_123',
          'invalid_sig'
        )).rejects.toThrow('Payment verification failed');
      });
    });
  });

  describe('Health and Monitoring', () => {
    describe('checkServiceHealth', () => {
      it('returns true when service is healthy', async () => {
        mockApiClient.checkApiHealth.mockResolvedValueOnce({
          data: { status: 'healthy' },
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.checkServiceHealth();

        expect(result).toBe(true);
      });

      it('returns false when service is unhealthy', async () => {
        mockApiClient.checkApiHealth.mockRejectedValueOnce(new Error('Service unavailable'));

        const result = await orderingService.checkServiceHealth();

        expect(result).toBe(false);
      });
    });

    describe('getServiceVersion', () => {
      it('returns version info when available', async () => {
        const mockVersion = { version: '1.0.0', build: 'abc123' };
        mockApiClient.getApiVersion.mockResolvedValueOnce({
          data: mockVersion,
          status: 200,
          statusText: 'OK'
        });

        const result = await orderingService.getServiceVersion();

        expect(result).toEqual(mockVersion);
      });

      it('returns null when version info unavailable', async () => {
        mockApiClient.getApiVersion.mockRejectedValueOnce(new Error('Not found'));

        const result = await orderingService.getServiceVersion();

        expect(result).toBeNull();
      });
    });
  });
});