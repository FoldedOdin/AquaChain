/**
 * Mock Payment Service for Local Development
 * Simulates Razorpay payment flow without backend
 */

export interface MockRazorpayOrder {
  razorpayOrderId: string;
  amount: number;
  currency: string;
}

export class MockPaymentService {
  /**
   * Create a mock Razorpay order
   */
  static async createRazorpayOrder(amount: number, orderId: string): Promise<MockRazorpayOrder> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));

    // Generate mock order ID
    const razorpayOrderId = `order_mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    console.log('Mock Payment: Creating Razorpay order', {
      amount,
      orderId,
      razorpayOrderId
    });

    return {
      razorpayOrderId,
      amount: amount * 100, // Convert to paise
      currency: 'INR'
    };
  }

  /**
   * Verify mock payment
   */
  static async verifyPayment(
    paymentId: string,
    orderId: string,
    signature: string
  ): Promise<boolean> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    console.log('Mock Payment: Verifying payment', {
      paymentId,
      orderId,
      signature
    });

    // Always return true for mock
    return true;
  }

  /**
   * Create mock COD payment
   */
  static async createCODPayment(orderId: string, amount: number): Promise<any> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 300));

    const paymentId = `cod_mock_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    console.log('Mock Payment: Creating COD payment', {
      orderId,
      amount,
      paymentId
    });

    return {
      paymentId,
      status: 'COD_PENDING',
      amount,
      orderId
    };
  }
}
