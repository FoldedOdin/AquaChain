/**
 * Ordering Service
 * High-level service for managing the enhanced consumer ordering system
 */

import { apiClient } from './apiClient';
import { websocketService } from './websocketService';
import {
  CreateOrderRequest,
  Order,
  Payment,
  PaymentStatus,
  Technician,
  TechnicianAssignment,
  SimulationStatus,
  Location,
  RazorpayOrder,
  RazorpayError,
  OrderStatus,
  PaymentMethod,
  ApiResponse
} from '../types/ordering';

export class OrderingService {
  /**
   * Order Management
   */
  
  async createOrder(orderData: CreateOrderRequest): Promise<Order> {
    try {
      const response = await apiClient.retryApiCall(
        () => apiClient.createOrder(orderData),
        3,
        1000
      );
      
      if (!response.data) {
        throw new Error('No order data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error creating order:', error);
      throw new Error(`Failed to create order: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getOrder(orderId: string): Promise<Order> {
    try {
      const response = await apiClient.getOrder(orderId);
      
      if (!response.data) {
        throw new Error('Order not found');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching order:', error);
      throw new Error(`Failed to fetch order: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getOrdersByConsumer(consumerId: string): Promise<Order[]> {
    try {
      const response = await apiClient.getOrdersByConsumer(consumerId);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching consumer orders:', error);
      throw new Error(`Failed to fetch orders: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async updateOrderStatus(orderId: string, status: OrderStatus, metadata?: any): Promise<Order> {
    try {
      const response = await apiClient.updateOrderStatus(orderId, status, metadata);
      
      if (!response.data) {
        throw new Error('No order data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error updating order status:', error);
      throw new Error(`Failed to update order status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async cancelOrder(orderId: string, reason: string): Promise<Order> {
    try {
      const response = await apiClient.cancelOrder(orderId, reason);
      
      if (!response.data) {
        throw new Error('No order data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error cancelling order:', error);
      throw new Error(`Failed to cancel order: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Payment Processing
   */
  
  async createRazorpayOrder(amount: number, orderId: string): Promise<RazorpayOrder> {
    try {
      const response = await apiClient.createRazorpayOrder(amount, orderId);
      
      if (!response.data) {
        throw new Error('No Razorpay order data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error creating Razorpay order:', error);
      throw new Error(`Failed to create Razorpay order: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async verifyRazorpayPayment(paymentId: string, orderId: string, signature: string): Promise<boolean> {
    try {
      const response = await apiClient.verifyRazorpayPayment(paymentId, orderId, signature);
      return response.data || false;
    } catch (error) {
      console.error('Error verifying Razorpay payment:', error);
      throw new Error(`Failed to verify payment: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async createCODPayment(orderId: string, amount: number): Promise<Payment> {
    try {
      const response = await apiClient.createCODPayment(orderId, amount);
      
      if (!response.data) {
        throw new Error('No payment data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error creating COD payment:', error);
      throw new Error(`Failed to create COD payment: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getPaymentStatus(orderId: string): Promise<PaymentStatus> {
    try {
      const response = await apiClient.getPaymentStatus(orderId);
      return response.data || PaymentStatus.PENDING;
    } catch (error) {
      console.error('Error fetching payment status:', error);
      throw new Error(`Failed to fetch payment status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Technician Assignment
   */
  
  async assignTechnician(orderId: string, serviceLocation: Location): Promise<TechnicianAssignment> {
    try {
      const response = await apiClient.assignTechnician(orderId, serviceLocation);
      
      if (!response.data) {
        throw new Error('No technician assignment data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error assigning technician:', error);
      throw new Error(`Failed to assign technician: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getAvailableTechnicians(location: Location, radius: number = 50): Promise<Technician[]> {
    try {
      const response = await apiClient.getAvailableTechnicians(location, radius);
      return response.data || [];
    } catch (error) {
      console.error('Error fetching available technicians:', error);
      throw new Error(`Failed to fetch technicians: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Status Simulation
   */
  
  async startStatusSimulation(orderId: string): Promise<void> {
    try {
      await apiClient.startStatusSimulation(orderId);
    } catch (error) {
      console.error('Error starting status simulation:', error);
      throw new Error(`Failed to start simulation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async stopStatusSimulation(orderId: string): Promise<void> {
    try {
      await apiClient.stopStatusSimulation(orderId);
    } catch (error) {
      console.error('Error stopping status simulation:', error);
      throw new Error(`Failed to stop simulation: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getSimulationStatus(orderId: string): Promise<SimulationStatus> {
    try {
      const response = await apiClient.getSimulationStatus(orderId);
      
      if (!response.data) {
        throw new Error('No simulation status data received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Error fetching simulation status:', error);
      throw new Error(`Failed to fetch simulation status: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Real-time Updates
   */
  
  subscribeToOrderUpdates(orderId: string, onUpdate: (data: any) => void): () => void {
    const topic = `order-${orderId}`;
    
    const handleMessage = (data: any) => {
      try {
        // Filter for order-specific updates
        if (data.type === 'order_update' && data.orderId === orderId) {
          onUpdate(data);
        }
      } catch (error) {
        console.error('Error processing order update:', error);
      }
    };

    websocketService.connect(topic, handleMessage);
    
    // Return unsubscribe function
    return () => {
      websocketService.disconnect(topic, handleMessage);
    };
  }

  subscribeToOrderNotifications(consumerId: string, onNotification: (data: any) => void): () => void {
    const topic = `consumer-${consumerId}-orders`;
    
    const handleMessage = (data: any) => {
      try {
        // Filter for consumer-specific notifications
        if (data.type === 'order_notification' && data.consumerId === consumerId) {
          onNotification(data);
        }
      } catch (error) {
        console.error('Error processing order notification:', error);
      }
    };

    websocketService.connect(topic, handleMessage);
    
    // Return unsubscribe function
    return () => {
      websocketService.disconnect(topic, handleMessage);
    };
  }

  /**
   * Complete Order Flow Helpers
   */
  
  async placeOrderWithCOD(orderData: CreateOrderRequest): Promise<{ order: Order; payment: Payment }> {
    try {
      // Ensure payment method is COD
      const codOrderData = { ...orderData, paymentMethod: 'COD' as PaymentMethod };
      
      // Create the order
      const order = await this.createOrder(codOrderData);
      
      // Create COD payment record
      const payment = await this.createCODPayment(order.id, order.amount || 0);
      
      // Start status simulation if enabled
      if (process.env.REACT_APP_ENABLE_STATUS_SIMULATION === 'true') {
        await this.startStatusSimulation(order.id);
      }
      
      return { order, payment };
    } catch (error) {
      console.error('Error placing COD order:', error);
      throw error;
    }
  }

  async placeOrderWithRazorpay(
    orderData: CreateOrderRequest,
    paymentId: string,
    signature: string
  ): Promise<{ order: Order; payment: Payment }> {
    try {
      // Ensure payment method is ONLINE
      const onlineOrderData = { 
        ...orderData, 
        paymentMethod: 'ONLINE' as PaymentMethod,
        paymentId 
      };
      
      // Verify payment first
      const isPaymentValid = await this.verifyRazorpayPayment(paymentId, orderData.consumerId, signature);
      
      if (!isPaymentValid) {
        throw new Error('Payment verification failed');
      }
      
      // Create the order
      const order = await this.createOrder(onlineOrderData);
      
      // Get payment details
      const paymentStatus = await this.getPaymentStatus(order.id);
      
      // Create payment record (this should be handled by the backend)
      const payment: Payment = {
        id: paymentId,
        orderId: order.id,
        amount: order.amount || 0,
        paymentMethod: 'ONLINE',
        status: paymentStatus,
        razorpayPaymentId: paymentId,
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      // Start status simulation if enabled
      if (process.env.REACT_APP_ENABLE_STATUS_SIMULATION === 'true') {
        await this.startStatusSimulation(order.id);
      }
      
      return { order, payment };
    } catch (error) {
      console.error('Error placing Razorpay order:', error);
      throw error;
    }
  }

  /**
   * Health and Monitoring
   */
  
  async checkServiceHealth(): Promise<boolean> {
    try {
      const response = await apiClient.checkApiHealth();
      return response.status === 200;
    } catch (error) {
      console.error('Service health check failed:', error);
      return false;
    }
  }

  async getServiceVersion(): Promise<{ version: string; build: string } | null> {
    try {
      const response = await apiClient.getApiVersion();
      return response.data || null;
    } catch (error) {
      console.error('Failed to get service version:', error);
      return null;
    }
  }
}

// Export singleton instance
export const orderingService = new OrderingService();
export default orderingService;