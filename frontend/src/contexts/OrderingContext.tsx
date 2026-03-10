import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import { Order, OrderStatus, PaymentMethod, CreateOrderRequest } from '../types/ordering';

// Feature flag for orders service
const ORDERS_FEATURE_ENABLED = true;

// Ordering State Interface
interface OrderingState {
  currentOrder: Order | null;
  isLoading: boolean;
  error: string | null;
  paymentMethod: PaymentMethod | null;
  orderHistory: Order[];
  isProcessingPayment: boolean;
}

// Action Types
type OrderingAction =
  | { type: 'SET_PAYMENT_METHOD'; payload: PaymentMethod }
  | { type: 'START_ORDER_CREATION'; payload: CreateOrderRequest }
  | { type: 'ORDER_CREATED'; payload: Order }
  | { type: 'ORDER_UPDATED'; payload: Order }
  | { type: 'ORDER_CANCELLED'; payload: string }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_PROCESSING_PAYMENT'; payload: boolean }
  | { type: 'RESET_ORDER_FLOW' }
  | { type: 'LOAD_ORDER_HISTORY'; payload: Order[] };

// Initial State
const initialState: OrderingState = {
  currentOrder: null,
  isLoading: false,
  error: null,
  paymentMethod: null,
  orderHistory: [],
  isProcessingPayment: false,
};

// Reducer
const orderingReducer = (state: OrderingState, action: OrderingAction): OrderingState => {
  switch (action.type) {
    case 'SET_PAYMENT_METHOD':
      return {
        ...state,
        paymentMethod: action.payload,
        error: null,
      };

    case 'START_ORDER_CREATION':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'ORDER_CREATED':
      return {
        ...state,
        currentOrder: action.payload,
        isLoading: false,
        error: null,
        orderHistory: [action.payload, ...state.orderHistory],
      };

    case 'ORDER_UPDATED':
      return {
        ...state,
        currentOrder: action.payload,
        orderHistory: state.orderHistory.map(order =>
          order.id === action.payload.id ? action.payload : order
        ),
      };

    case 'ORDER_CANCELLED':
      return {
        ...state,
        currentOrder: null,
        isLoading: false,
        error: null,
      };

    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };

    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
        isProcessingPayment: false,
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };

    case 'SET_PROCESSING_PAYMENT':
      return {
        ...state,
        isProcessingPayment: action.payload,
      };

    case 'RESET_ORDER_FLOW':
      return {
        ...state,
        currentOrder: null,
        paymentMethod: null,
        isLoading: false,
        error: null,
        isProcessingPayment: false,
      };

    case 'LOAD_ORDER_HISTORY':
      return {
        ...state,
        orderHistory: action.payload,
      };

    default:
      return state;
  }
};

// Context Interface
interface OrderingContextType {
  state: OrderingState;
  setPaymentMethod: (method: PaymentMethod) => void;
  createOrder: (orderRequest: CreateOrderRequest) => Promise<void>;
  updateOrderStatus: (orderId: string, status: OrderStatus) => Promise<void>;
  cancelOrder: (orderId: string, reason: string) => Promise<void>;
  clearError: () => void;
  resetOrderFlow: () => void;
  loadOrderHistory: () => Promise<void>;
  processPayment: (paymentData: any) => Promise<void>;
}

// Create Context
const OrderingContext = createContext<OrderingContextType | undefined>(undefined);

// Provider Props
interface OrderingProviderProps {
  children: ReactNode;
}

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'https://vtqjfznspc.execute-api.ap-south-1.amazonaws.com/dev';

// Helper function to convert API order response to Order type with proper Date objects
const normalizeOrder = (apiOrder: any): Order | null => {
  // Safety check: ensure apiOrder exists
  if (!apiOrder) {
    console.error('normalizeOrder received undefined apiOrder');
    return null;
  }

  return {
    ...apiOrder,
    createdAt: new Date(apiOrder.createdAt),
    updatedAt: new Date(apiOrder.updatedAt),
    statusHistory: (apiOrder.statusHistory || []).map((update: any) => ({
      ...update,
      timestamp: new Date(update.timestamp)
    }))
  };
};

// Provider Component
export const OrderingProvider: React.FC<OrderingProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(orderingReducer, initialState);

  // Get auth token
  const getAuthToken = useCallback(() => {
    return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  }, []);

  // API call helper
  const apiCall = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    console.log('🚀 API Call Starting:', { endpoint, method: options.method });
    
    const token = getAuthToken();
    
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          ...options.headers,
        },
      });

      console.log('📡 Response received:', { 
        endpoint, 
        status: response.status, 
        ok: response.ok,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      // Get response text first
      const responseText = await response.text();
      console.log('📄 Response text:', { endpoint, text: responseText, length: responseText.length });

      // Try to parse as JSON
      let data;
      try {
        data = responseText ? JSON.parse(responseText) : null;
        console.log('📦 Parsed data:', { endpoint, data, dataType: typeof data });
      } catch (parseError) {
        console.error('❌ JSON parse error:', { error: parseError, responseText });
        // If not JSON, treat the text as the error message
        if (!response.ok) {
          throw new Error(responseText || `Request failed with status ${response.status}`);
        }
        data = responseText;
      }

      if (!response.ok) {
        // Handle error responses
        console.error('❌ Response not OK:', { status: response.status, data });
        
        // Extract error message safely
        let errorMessage = 'Request failed';
        if (typeof data === 'string') {
          errorMessage = data || `Request failed with status ${response.status}`;
        } else if (data && typeof data === 'object') {
          // Backend returns { error: true, message: "...", code: "..." }
          errorMessage = data.message || data.errorMessage || data.error || `Request failed with status ${response.status}`;
          // If error is a boolean, use the message field instead
          if (typeof data.error === 'boolean' && data.message) {
            errorMessage = data.message;
          }
        }
        
        console.error('❌ Throwing error:', errorMessage);
        throw new Error(String(errorMessage)); // Ensure it's a string
      }

      // Handle different response formats
      console.log('✅ Response OK, validating format...');
      
      // Case 1: Backend returns { success: true, data: {...}, message: "..." }
      if (data && typeof data === 'object' && 'success' in data) {
        console.log('📋 Format: Object with success field', { success: data.success });
        if (data.success === false) {
          const errorMsg = data.error || data.message || 'Request failed';
          console.error('❌ Backend returned success=false:', errorMsg);
          throw new Error(String(errorMsg)); // Ensure it's a string
        }
        console.log('✅ Returning success response');
        return data; // Return the whole response object
      }

      // Case 2: Backend returns plain boolean (true)
      if (data === true || data === 'true') {
        console.log('📋 Format: Plain boolean true');
        return { success: true };
      }

      // Case 3: Backend returns plain data object
      console.log('📋 Format: Plain data object');
      return data;
      
    } catch (error) {
      console.error('❌ API Call failed:', { 
        endpoint, 
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined
      });
      throw error;
    }
  }, [getAuthToken]);

  // Set payment method
  const setPaymentMethod = useCallback((method: PaymentMethod) => {
    dispatch({ type: 'SET_PAYMENT_METHOD', payload: method });
  }, []);

  // Create order
  const createOrder = useCallback(async (orderRequest: CreateOrderRequest) => {
    // Check feature flag
    if (!ORDERS_FEATURE_ENABLED) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: 'Device ordering feature is currently being configured. Please contact support@aquachain.com to place an order.' 
      });
      return;
    }

    try {
      dispatch({ type: 'START_ORDER_CREATION', payload: orderRequest });

      const response = await apiCall('/api/orders', {
        method: 'POST',
        body: JSON.stringify(orderRequest),
      });

      console.log('Order API response:', response);

      // apiCall already returns the parsed body directly (not wrapped in { data: ... })
      // Backend returns { success: true, order: {...}, message: "..." }
      const apiOrder = response?.order || response;
      
      if (!apiOrder || !apiOrder.id) {
        console.error('Invalid API response structure:', response);
        throw new Error('Invalid API response: missing order data');
      }

      // Normalize the order response to convert string timestamps to Date objects
      const normalizedOrder = normalizeOrder(apiOrder);
      
      if (!normalizedOrder) {
        throw new Error('Failed to normalize order data');
      }

      dispatch({ type: 'ORDER_CREATED', payload: normalizedOrder });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create order';
      console.error('Failed to create COD order:', error);
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  }, [apiCall]);

  // Update order status
  const updateOrderStatus = useCallback(async (orderId: string, status: OrderStatus) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await apiCall(`/api/orders/${orderId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      });

      // Extract order from response - backend returns { success, data, message }
      const apiOrder = response?.data;
      
      if (!apiOrder) {
        throw new Error('Invalid API response: missing order data');
      }

      const normalizedOrder = normalizeOrder(apiOrder);
      
      if (!normalizedOrder) {
        throw new Error('Failed to normalize order data');
      }

      dispatch({ type: 'ORDER_UPDATED', payload: normalizedOrder });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update order status';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [apiCall]);

  // Cancel order
  const cancelOrder = useCallback(async (orderId: string, reason: string) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Use DELETE method with cancel_order Lambda
      await apiCall(`/api/orders/${orderId}`, {
        method: 'DELETE',
        body: JSON.stringify({ cancellationReason: reason }),
      });

      dispatch({ type: 'ORDER_CANCELLED', payload: orderId });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to cancel order';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [apiCall]);

  // Process payment
  const processPayment = useCallback(async (paymentData: any) => {
    try {
      dispatch({ type: 'SET_PROCESSING_PAYMENT', payload: true });

      const response = await apiCall('/api/payments/process', {
        method: 'POST',
        body: JSON.stringify(paymentData),
      });

      // Update order with payment information
      // Backend returns { success, data, message }
      const apiOrder = response?.data;
      
      if (apiOrder) {
        const normalizedOrder = normalizeOrder(apiOrder);
        if (normalizedOrder) {
          dispatch({ type: 'ORDER_UPDATED', payload: normalizedOrder });
        }
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Payment processing failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    } finally {
      dispatch({ type: 'SET_PROCESSING_PAYMENT', payload: false });
    }
  }, [apiCall]);

  // Load order history
  const loadOrderHistory = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await apiCall('/api/orders/history');
      
      // Backend returns { success, data, count }
      const orders = response?.data || [];
      
      dispatch({ type: 'LOAD_ORDER_HISTORY', payload: orders });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load order history';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [apiCall]);

  // Clear error
  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  // Reset order flow
  const resetOrderFlow = useCallback(() => {
    dispatch({ type: 'RESET_ORDER_FLOW' });
  }, []);

  const contextValue: OrderingContextType = {
    state,
    setPaymentMethod,
    createOrder,
    updateOrderStatus,
    cancelOrder,
    clearError,
    resetOrderFlow,
    loadOrderHistory,
    processPayment,
  };

  return (
    <OrderingContext.Provider value={contextValue}>
      {children}
    </OrderingContext.Provider>
  );
};

// Custom hook to use ordering context
export const useOrdering = (): OrderingContextType => {
  const context = useContext(OrderingContext);
  if (context === undefined) {
    throw new Error('useOrdering must be used within an OrderingProvider');
  }
  return context;
};

export default OrderingContext;