import {
  Shipment,
  ShipmentListItem,
  CreateShipmentRequest,
  CreateShipmentResponse,
  ShipmentStatusResponse
} from '../types/shipment';

// API Base URL
const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';

/**
 * Get authentication token from localStorage
 */
const getAuthToken = (): string => {
  const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
  if (!token) {
    throw new Error('No authentication token found');
  }
  return token;
};

/**
 * Get all shipments with optional filtering
 */
export const getAllShipments = async (filters?: {
  status?: string;
  search?: string;
}): Promise<ShipmentListItem[]> => {
  try {
    const token = getAuthToken();
    
    // Build query parameters
    const params = new URLSearchParams();
    if (filters?.status) {
      params.append('status', filters.status);
    }
    if (filters?.search) {
      params.append('search', filters.search);
    }
    
    const url = `${API_BASE_URL}/api/shipments${params.toString() ? `?${params.toString()}` : ''}`;
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch shipments');
    }

    const data = await response.json();
    
    // Transform and calculate delayed status
    const now = new Date();
    return (data.shipments || []).map((shipment: Shipment) => {
      const estimatedDelivery = new Date(shipment.estimated_delivery);
      const isDelayed = estimatedDelivery < now && 
        !['delivered', 'returned', 'cancelled'].includes(shipment.internal_status);
      
      return {
        shipment_id: shipment.shipment_id,
        order_id: shipment.order_id,
        tracking_number: shipment.tracking_number,
        courier_name: shipment.courier_name,
        internal_status: shipment.internal_status,
        estimated_delivery: shipment.estimated_delivery,
        created_at: shipment.created_at,
        updated_at: shipment.updated_at,
        is_delayed: isDelayed,
        destination: {
          contact_name: shipment.destination.contact_name,
          address: shipment.destination.address
        }
      };
    });
  } catch (error) {
    console.error('Error fetching shipments:', error);
    throw error;
  }
};

/**
 * Get shipment details by shipment ID
 */
export const getShipmentById = async (shipmentId: string): Promise<ShipmentStatusResponse> => {
  try {
    const token = getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/shipments/${shipmentId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch shipment details');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching shipment details:', error);
    throw error;
  }
};

/**
 * Get shipment details by order ID
 */
export const getShipmentByOrderId = async (orderId: string): Promise<ShipmentStatusResponse> => {
  try {
    const token = getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/shipments?orderId=${orderId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch shipment details');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching shipment details:', error);
    throw error;
  }
};

/**
 * Create a new shipment
 */
export const createShipment = async (request: CreateShipmentRequest): Promise<CreateShipmentResponse> => {
  try {
    const token = getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/shipments`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to create shipment');
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error creating shipment:', error);
    throw error;
  }
};

/**
 * Get stale shipments (no updates for 7+ days)
 */
export const getStaleShipments = async (): Promise<ShipmentListItem[]> => {
  try {
    const allShipments = await getAllShipments();
    
    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    return allShipments.filter(shipment => {
      const updatedAt = new Date(shipment.updated_at);
      const isStale = updatedAt < sevenDaysAgo;
      const isActive = !['delivered', 'returned', 'cancelled'].includes(shipment.internal_status);
      
      return isStale && isActive;
    });
  } catch (error) {
    console.error('Error fetching stale shipments:', error);
    throw error;
  }
};

/**
 * Format date for display
 */
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Calculate days since last update
 */
export const daysSinceUpdate = (dateString: string): number => {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  return diffDays;
};
