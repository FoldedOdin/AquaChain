// Shipment tracking types

export interface ShipmentTimeline {
  status: string;
  timestamp: string;
  location: string;
  description: string;
}

export interface WebhookEvent {
  event_id: string;
  received_at: string;
  courier_status: string;
  raw_payload: string;
}

export interface RetryConfig {
  max_retries: number;
  retry_count: number;
  last_retry_at: string | null;
}

export interface ShipmentDestination {
  address: string;
  pincode: string;
  contact_name: string;
  contact_phone: string;
}

export interface ShipmentMetadata {
  package_weight: string;
  declared_value: number;
  insurance: boolean;
}

export interface Shipment {
  shipment_id: string;
  order_id: string;
  device_id: string;
  tracking_number: string;
  courier_name: string;
  courier_service_type: string;
  internal_status: 'shipment_created' | 'picked_up' | 'in_transit' | 'out_for_delivery' | 'delivered' | 'delivery_failed' | 'returned' | 'cancelled' | 'lost';
  external_status: string;
  destination: ShipmentDestination;
  timeline: ShipmentTimeline[];
  webhook_events: WebhookEvent[];
  retry_config: RetryConfig;
  metadata: ShipmentMetadata;
  estimated_delivery: string;
  delivered_at: string | null;
  failed_at: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ShipmentListItem {
  shipment_id: string;
  order_id: string;
  tracking_number: string;
  courier_name: string;
  internal_status: Shipment['internal_status'];
  estimated_delivery: string;
  created_at: string;
  updated_at: string;
  is_delayed: boolean;
  destination: {
    contact_name: string;
    address: string;
  };
}

export interface ShipmentProgress {
  percentage: number;
  current_status: string;
  status_message: string;
  status_color: string;
  is_completed: boolean;
}

export interface CreateShipmentRequest {
  order_id: string;
  courier_name: string;
  service_type: string;
  destination: ShipmentDestination;
  package_details: {
    weight: string;
    declared_value: number;
    insurance: boolean;
  };
}

export interface CreateShipmentResponse {
  success: boolean;
  shipment_id: string;
  tracking_number: string;
  estimated_delivery: string;
}

export interface ShipmentStatusResponse {
  success: boolean;
  shipment: Shipment;
  progress: ShipmentProgress;
}

export interface CourierContact {
  name: string;
  phone: string;
  email: string;
  tracking_url: string;
}

export const COURIER_CONTACTS: Record<string, CourierContact> = {
  Delhivery: {
    name: 'Delhivery',
    phone: '+91-124-4646444',
    email: 'support@delhivery.com',
    tracking_url: 'https://www.delhivery.com/track/package/'
  },
  BlueDart: {
    name: 'BlueDart',
    phone: '+91-22-28394444',
    email: 'customercare@bluedart.com',
    tracking_url: 'https://www.bluedart.com/tracking/'
  },
  DTDC: {
    name: 'DTDC',
    phone: '+91-22-30916000',
    email: 'care@dtdc.com',
    tracking_url: 'https://www.dtdc.in/tracking.asp'
  }
};

export const STATUS_COLORS: Record<Shipment['internal_status'], string> = {
  shipment_created: 'bg-blue-100 text-blue-800',
  picked_up: 'bg-indigo-100 text-indigo-800',
  in_transit: 'bg-purple-100 text-purple-800',
  out_for_delivery: 'bg-yellow-100 text-yellow-800',
  delivered: 'bg-green-100 text-green-800',
  delivery_failed: 'bg-red-100 text-red-800',
  returned: 'bg-gray-100 text-gray-800',
  cancelled: 'bg-gray-100 text-gray-800',
  lost: 'bg-red-100 text-red-800'
};

export const STATUS_ICONS: Record<Shipment['internal_status'], string> = {
  shipment_created: '📦',
  picked_up: '🚚',
  in_transit: '🛣️',
  out_for_delivery: '🚛',
  delivered: '✅',
  delivery_failed: '❌',
  returned: '↩️',
  cancelled: '🚫',
  lost: '❓'
};

export const STATUS_LABELS: Record<Shipment['internal_status'], string> = {
  shipment_created: 'Shipment Created',
  picked_up: 'Picked Up',
  in_transit: 'In Transit',
  out_for_delivery: 'Out for Delivery',
  delivered: 'Delivered',
  delivery_failed: 'Delivery Failed',
  returned: 'Returned',
  cancelled: 'Cancelled',
  lost: 'Lost'
};
