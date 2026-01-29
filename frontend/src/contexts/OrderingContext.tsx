import React, { createContext, useContext, useReducer, useCallback, ReactNode } from 'react';
import { Order, OrderStatus, PaymentMethod, CreateOrderRequest } from '../types/ordering';

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
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3002';

// Provider Component
export const OrderingProvider: React.FC<OrderingProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(orderingReducer, initialState);

  // Get auth token
  const getAuthToken = useCallback(() => {
    return localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  }, []);

  // API call helper
  const apiCall = useCallback(async (endpoint: string, options: RequestInit = {}) => {
    const token = getAuthToken();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Network error' }));
      throw new Error(error.error || error.message || 'Request failed');
    }

    return response.json();
  }, [getAuthToken]);

  // Set payment method
  const setPaymentMethod = useCallback((method: PaymentMethod) => {
    dispatch({ type: 'SET_PAYMENT_METHOD', payload: method });
  }, []);

  // Create order
  const createOrder = useCallback(async (orderRequest: CreateOrderRequest) => {
    try {
      dispatch({ type: 'START_ORDER_CREATION', payload: orderRequest });

      const response = await apiCall('/api/orders', {
        method: 'POST',
        body: JSON.stringify(orderRequest),
      });

      dispatch({ type: 'ORDER_CREATED', payload: response.order });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create order';
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

      dispatch({ type: 'ORDER_UPDATED', payload: response.order });
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

      await apiCall(`/api/orders/${orderId}/cancel`, {
        method: 'POST',
        body: JSON.stringify({ reason }),
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
      if (response.order) {
        dispatch({ type: 'ORDER_UPDATED', payload: response.order });
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
      dispatch({ type: 'LOAD_ORDER_HISTORY', payload: response.orders || [] });
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