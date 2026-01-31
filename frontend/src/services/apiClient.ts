/**
 * API Client
 * Centralized HTTP client for making API requests with authentication
 */

import { 
  CreateOrderRequest, 
  Order, 
  Payment, 
  PaymentStatus, 
  Technician, 
  TechnicianAssignment, 
  SimulationStatus,
  Location,
  RazorpayOrder
} from '../types/ordering';
import { websocketService } from './websocketService';

export interface ApiResponse<T = unknown> {
  data: T;
  status: number;
  statusText: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
  }

  /**
   * Get authentication token from localStorage
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('aquachain_token');
  }

  /**
   * Get authorization headers
   */
  private getAuthHeaders(): HeadersInit {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response, expectBlob = false): Promise<ApiResponse<T>> {
    if (!response.ok) {
      // For error responses, try to get JSON error message first
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData?.error || errorData?.message || errorMessage;
      } catch {
        // If JSON parsing fails, use statusText
      }

      const error: ApiError = {
        message: errorMessage,
        status: response.status,
        code: response.status.toString()
      };
      throw error;
    }

    let data: T;

    if (expectBlob) {
      data = (await response.blob()) as unknown as T;
    } else {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else if (contentType && contentType.includes('text/')) {
        data = (await response.text()) as unknown as T;
      } else {
        data = (await response.blob()) as unknown as T;
      }
    }

    return {
      data,
      status: response.status,
      statusText: response.statusText
    };
  }

  /**
   * Make GET request
   */
  async get<T = unknown>(url: string, options?: RequestInit & { expectBlob?: boolean }): Promise<ApiResponse<T>> {
    const { expectBlob, ...fetchOptions } = options || {};
    
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
      ...fetchOptions
    });

    return this.handleResponse<T>(response, expectBlob);
  }

  /**
   * Make POST request
   */
  async post<T = unknown>(url: string, data?: unknown, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make PUT request
   */
  async put<T = unknown>(url: string, data?: unknown, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make PATCH request
   */
  async patch<T = unknown>(url: string, data?: unknown, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'PATCH',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make DELETE request
   */
  async delete<T = unknown>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Upload file
   */
  async upload<T = unknown>(url: string, file: File, options?: RequestInit): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getAuthToken();
    const headers: HeadersInit = {
      ...(token && { 'Authorization': `Bearer ${token}` })
    };

    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'POST',
      headers,
      body: formData,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Download file
   */
  async download(url: string, filename?: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'GET',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  }
}

/**
 * Enhanced API Client with Order Management
 * Extends the base ApiClient with order-specific endpoints
 */
class EnhancedApiClient extends ApiClient {
  /**
   * Order Management API calls
   */
  
  // Create a new order
  async createOrder(orderData: CreateOrderRequest): Promise<ApiResponse<Order>> {
    return this.post('/api/orders', orderData);
  }

  // Get order by ID
  async getOrder(orderId: string): Promise<ApiResponse<Order>> {
    return this.get(`/api/orders/${orderId}`);
  }

  // Get orders by consumer ID
  async getOrdersByConsumer(consumerId: string): Promise<ApiResponse<Order[]>> {
    return this.get(`/api/orders/consumer/${consumerId}`);
  }

  // Update order status
  async updateOrderStatus(orderId: string, status: string, metadata?: Record<string, unknown>): Promise<ApiResponse<Order>> {
    return this.post(`/api/orders/${orderId}/status`, { status, metadata });
  }

  // Cancel order
  async cancelOrder(orderId: string, reason: string): Promise<ApiResponse<Order>> {
    return this.post(`/api/orders/${orderId}/cancel`, { reason });
  }

  /**
   * Payment Processing API calls
   */
  
  // Create Razorpay order
  async createRazorpayOrder(amount: number, orderId: string): Promise<ApiResponse<RazorpayOrder>> {
    return this.post('/api/payments/razorpay/create', { amount, orderId });
  }

  // Verify Razorpay payment
  async verifyRazorpayPayment(paymentId: string, orderId: string, signature: string): Promise<ApiResponse<boolean>> {
    return this.post('/api/payments/razorpay/verify', { paymentId, orderId, signature });
  }

  // Create COD payment
  async createCODPayment(orderId: string, amount: number): Promise<ApiResponse<Payment>> {
    return this.post('/api/payments/cod/create', { orderId, amount });
  }

  // Get payment status
  async getPaymentStatus(orderId: string): Promise<ApiResponse<PaymentStatus>> {
    return this.get(`/api/payments/status/${orderId}`);
  }

  /**
   * Technician Assignment API calls
   */
  
  // Assign technician to order
  async assignTechnician(orderId: string, serviceLocation: Location): Promise<ApiResponse<TechnicianAssignment>> {
    return this.post(`/api/technicians/assign`, { orderId, serviceLocation });
  }

  // Get available technicians
  async getAvailableTechnicians(location: Location, radius = 50): Promise<ApiResponse<Technician[]>> {
    return this.post('/api/technicians/available', { location, radius });
  }

  // Update technician availability
  async updateTechnicianAvailability(technicianId: string, available: boolean): Promise<ApiResponse<void>> {
    return this.patch(`/api/technicians/${technicianId}/availability`, { available });
  }

  /**
   * Status Simulator API calls
   */
  
  // Start order status simulation
  async startStatusSimulation(orderId: string): Promise<ApiResponse<void>> {
    return this.post(`/api/simulator/start`, { orderId });
  }

  // Stop order status simulation
  async stopStatusSimulation(orderId: string): Promise<ApiResponse<void>> {
    return this.post(`/api/simulator/stop`, { orderId });
  }

  // Get simulation status
  async getSimulationStatus(orderId: string): Promise<ApiResponse<SimulationStatus>> {
    return this.get(`/api/simulator/status/${orderId}`);
  }

  /**
   * WebSocket Connection Management
   */
  
  // Get WebSocket connection URL
  getWebSocketUrl(): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.REACT_APP_WEBSOCKET_ENDPOINT || 
                   `${wsProtocol}//${window.location.host}/ws`;
    return wsHost;
  }

  // Connect to order updates WebSocket
  connectToOrderUpdates(orderId: string, onMessage: (data: unknown) => void): void {
    websocketService.connect(`order-${orderId}`, onMessage);
  }

  // Disconnect from order updates WebSocket
  disconnectFromOrderUpdates(orderId: string, onMessage?: (data: unknown) => void): void {
    websocketService.disconnect(`order-${orderId}`, onMessage);
  }

  // Connect to general order notifications
  connectToOrderNotifications(consumerId: string, onMessage: (data: unknown) => void): void {
    websocketService.connect(`consumer-${consumerId}-orders`, onMessage);
  }

  // Disconnect from general order notifications
  disconnectFromOrderNotifications(consumerId: string, onMessage?: (data: unknown) => void): void {
    websocketService.disconnect(`consumer-${consumerId}-orders`, onMessage);
  }

  /**
   * Error Handling and Retry Logic
   */
  
  // Retry API call with exponential backoff
  async retryApiCall<T>(
    apiCall: () => Promise<ApiResponse<T>>,
    maxRetries = 3,
    baseDelay = 1000
  ): Promise<ApiResponse<T>> {
    let lastError: ApiError | undefined;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall();
      } catch (error) {
        lastError = error as ApiError;
        
        // Don't retry on client errors (4xx)
        if (lastError.status && lastError.status >= 400 && lastError.status < 500) {
          throw lastError;
        }
        
        // Don't retry on the last attempt
        if (attempt === maxRetries) {
          throw lastError;
        }
        
        // Calculate delay with exponential backoff
        const delay = baseDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        
        console.log(`Retrying API call (attempt ${attempt + 2}/${maxRetries + 1}) after ${delay}ms`);
      }
    }
    
    throw new Error(lastError?.message || 'API call failed after retries');
  }

  // Check API health
  async checkApiHealth(): Promise<ApiResponse<{ status: string; timestamp: string }>> {
    return this.get('/api/health');
  }

  // Get API version info
  async getApiVersion(): Promise<ApiResponse<{ version: string; build: string }>> {
    return this.get('/api/version');
  }
}

// Export singleton instance
export const apiClient = new EnhancedApiClient();
export default apiClient;