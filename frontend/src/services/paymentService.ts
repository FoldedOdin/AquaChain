/**
 * Payment Service Client
 * 
 * Integrates with existing Razorpay Lambda functions:
 * - POST /api/payments/create-razorpay-order
 * - POST /api/payments/verify-payment
 * - POST /api/payments/create-cod-payment
 * - GET /api/payments/payment-status
 */

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3000';

interface RazorpayOrderRequest {
  amount: number;
  currency?: string;
}

interface RazorpayOrderResponse {
  success: boolean;
  data: {
    paymentId: string;
    orderId: string;
    razorpayOrderId: string;
    amount: number;
    currency: string;
    key: string;
  };
}

interface VerifyPaymentRequest {
  paymentId: string;
  orderId: string;
  signature: string;
}

interface VerifyPaymentResponse {
  success: boolean;
  data: {
    verified: boolean;
    paymentId: string;
    status: string;
  };
}

interface CODPaymentRequest {
  orderId: string;
  amount: number;
}

interface CODPaymentResponse {
  success: boolean;
  data: {
    paymentId: string;
    orderId: string;
    status: string;
    paymentMethod: string;
  };
}

interface PaymentStatusResponse {
  success: boolean;
  data: {
    paymentId: string;
    orderId: string;
    status: string;
    amount: number;
    paymentMethod: string;
  };
}

class PaymentService {
  private getAuthToken(): string | null {
    return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  }

  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data?.message || data?.error || `Request failed with status ${response.status}`;
      throw new Error(errorMessage);
    }

    return data;
  }

  /**
   * Create a Razorpay order
   * Call this BEFORE opening Razorpay modal
   */
  async createRazorpayOrder(request: RazorpayOrderRequest): Promise<RazorpayOrderResponse> {
    console.log('💳 Creating Razorpay order:', request);
    
    const response = await this.makeRequest<RazorpayOrderResponse>(
      '/api/payments/create-razorpay-order',
      {
        method: 'POST',
        body: JSON.stringify({
          amount: request.amount,
          currency: request.currency || 'INR',
        }),
      }
    );

    console.log('✅ Razorpay order created:', response);
    return response;
  }

  /**
   * Verify Razorpay payment signature
   * Call this AFTER Razorpay payment success
   */
  async verifyPayment(request: VerifyPaymentRequest): Promise<VerifyPaymentResponse> {
    console.log('🔐 Verifying payment:', request);
    
    const response = await this.makeRequest<VerifyPaymentResponse>(
      '/api/payments/verify-payment',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    console.log('✅ Payment verified:', response);
    return response;
  }

  /**
   * Create COD payment record
   * Call this AFTER order is created
   */
  async createCODPayment(request: CODPaymentRequest): Promise<CODPaymentResponse> {
    console.log('💵 Creating COD payment:', request);
    
    const response = await this.makeRequest<CODPaymentResponse>(
      '/api/payments/create-cod-payment',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    console.log('✅ COD payment created:', response);
    return response;
  }

  /**
   * Get payment status by order ID
   */
  async getPaymentStatus(orderId: string): Promise<PaymentStatusResponse> {
    console.log('📊 Getting payment status for order:', orderId);
    
    const response = await this.makeRequest<PaymentStatusResponse>(
      `/api/payments/payment-status?orderId=${encodeURIComponent(orderId)}`,
      {
        method: 'GET',
      }
    );

    console.log('✅ Payment status:', response);
    return response;
  }
}

export const paymentService = new PaymentService();
export type {
  RazorpayOrderRequest,
  RazorpayOrderResponse,
  VerifyPaymentRequest,
  VerifyPaymentResponse,
  CODPaymentRequest,
  CODPaymentResponse,
  PaymentStatusResponse,
};
