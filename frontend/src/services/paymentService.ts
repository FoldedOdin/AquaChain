/**
 * Payment Service
 * Handles all payment-related API calls to AquaChain backend
 */

import { apiClient } from './apiClient';

export interface RazorpayOrderResponse {
  success: boolean;
  data: {
    paymentId: string;
    razorpayOrder: {
      id: string;
      amount: number;
      currency: string;
      receipt: string;
      status: string;
    };
  };
  error?: string;
}

export interface PaymentVerificationResponse {
  success: boolean;
  data: {
    paymentId: string;
    status: string;
    verified: boolean;
  };
  error?: string;
}

export interface CODPaymentResponse {
  success: boolean;
  data: {
    paymentId: string;
    status: string;
  };
  error?: string;
}

export interface PaymentStatusResponse {
  success: boolean;
  data: {
    paymentId: string;
    status: string;
    paymentMethod: string;
    amount: number;
    createdAt: string;
    updatedAt: string;
  } | {
    status: string;
    message: string;
  };
  error?: string;
}

export class PaymentService {
  /**
   * Create a Razorpay order for online payment
   * @param amount - Amount in INR (will be converted to paise internally)
   * @param orderId - Your order ID
   * @returns Razorpay order details
   */
  static async createRazorpayOrder(amount: number, orderId: string): Promise<RazorpayOrderResponse> {
    try {
      const response = await apiClient.post<RazorpayOrderResponse>(
        '/api/payments/create-razorpay-order',
        {
          amount: amount,
          orderId: orderId,
          currency: 'INR'
        }
      );

      return response.data;
    } catch (error: any) {
      console.error('Failed to create Razorpay order:', error);
      throw new Error(error.message || 'Failed to create payment order');
    }
  }

  /**
   * Verify Razorpay payment after successful payment
   * @param paymentId - Razorpay payment ID
   * @param orderId - Razorpay order ID
   * @param signature - Razorpay signature
   * @returns Verification result
   */
  static async verifyPayment(
    paymentId: string,
    orderId: string,
    signature: string
  ): Promise<PaymentVerificationResponse> {
    try {
      const response = await apiClient.post<PaymentVerificationResponse>(
        '/api/payments/verify-payment',
        {
          paymentId,
          orderId,
          signature
        }
      );

      return response.data;
    } catch (error: any) {
      console.error('Failed to verify payment:', error);
      throw new Error(error.message || 'Payment verification failed');
    }
  }

  /**
   * Create a COD payment record
   * @param orderId - Your order ID
   * @param amount - Amount in INR
   * @returns COD payment details
   */
  static async createCODPayment(orderId: string, amount: number): Promise<CODPaymentResponse> {
    try {
      const response = await apiClient.post<CODPaymentResponse>(
        '/api/payments/create-cod-payment',
        {
          orderId,
          amount
        }
      );

      return response.data;
    } catch (error: any) {
      console.error('Failed to create COD payment:', error);
      throw new Error(error.message || 'Failed to create COD payment');
    }
  }

  /**
   * Get payment status for an order
   * @param orderId - Your order ID
   * @returns Payment status details
   */
  static async getPaymentStatus(orderId: string): Promise<PaymentStatusResponse> {
    try {
      const response = await apiClient.get<PaymentStatusResponse>(
        `/api/payments/payment-status?orderId=${orderId}`
      );

      return response.data;
    } catch (error: any) {
      console.error('Failed to get payment status:', error);
      throw new Error(error.message || 'Failed to get payment status');
    }
  }
}

export default PaymentService;
