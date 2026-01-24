export interface InventoryItem {
  item_id: string;
  location_id: string;
  name: string;
  description?: string;
  category: string;
  current_stock: number;
  pending_stock?: number;
  quarantine_stock?: number;
  reorder_point?: number;
  reorder_quantity?: number;
  safety_stock?: number;
  unit_cost?: number;
  supplier_id?: string;
  supplier_info?: {
    name: string;
    contact_email: string;
    lead_time_days: number;
  };
  stock_status: 'normal' | 'low' | 'critical' | 'out';
  days_of_supply?: number;
  auto_reorder?: boolean;
  last_received?: string;
  last_picked?: string;
  created_at: string;
  updated_at: string;
  status: 'active' | 'inactive' | 'discontinued';
}

export interface InventoryAlert {
  item_id: string;
  name: string;
  current_stock: number;
  reorder_point: number;
  safety_stock?: number;
  days_of_supply: number;
  location_id: string;
  supplier_id?: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  alert_type: 'low_stock' | 'out_of_stock' | 'overstock' | 'expired';
  created_at: string;
}

export interface InventoryMetrics {
  totalItems: number;
  lowStockCount: number;
  outOfStockCount: number;
  totalValue: number;
  turnoverRate?: number;
  averageDaysOfSupply?: number;
  stockAccuracy?: number;
}

export interface CreateInventoryItemRequest {
  name: string;
  description?: string;
  category: string;
  current_stock: number;
  reorder_point?: number;
  reorder_quantity?: number;
  safety_stock?: number;
  unit_cost?: number;
  supplier_id?: string;
  location_id: string;
  auto_reorder?: boolean;
}

export interface UpdateInventoryItemRequest {
  name?: string;
  description?: string;
  category?: string;
  current_stock?: number;
  reorder_point?: number;
  reorder_quantity?: number;
  safety_stock?: number;
  unit_cost?: number;
  supplier_id?: string;
  auto_reorder?: boolean;
  status?: 'active' | 'inactive' | 'discontinued';
}

export interface InventoryTransaction {
  transaction_id: string;
  item_id: string;
  location_id: string;
  transaction_type: 'receipt' | 'issue' | 'adjustment' | 'transfer';
  quantity: number;
  reference_id?: string; // PO ID, Order ID, etc.
  reason?: string;
  performed_by: string;
  timestamp: string;
  notes?: string;
}

export interface InventoryForecast {
  item_id: string;
  forecast_date: string;
  predicted_demand: number;
  confidence_level: number;
  seasonal_factor?: number;
  trend_factor?: number;
  recommended_stock_level: number;
  model_version: string;
}

export interface StockMovement {
  movement_id: string;
  item_id: string;
  from_location?: string;
  to_location?: string;
  quantity: number;
  movement_type: 'inbound' | 'outbound' | 'transfer' | 'adjustment';
  reference_document?: string;
  moved_by: string;
  movement_date: string;
  status: 'pending' | 'completed' | 'cancelled';
}

export interface InventoryAnalytics {
  timeRange: string;
  totalTransactions: number;
  totalValue: number;
  topMovingItems: Array<{
    item_id: string;
    name: string;
    total_movement: number;
    movement_value: number;
  }>;
  categoryBreakdown: Array<{
    category: string;
    item_count: number;
    total_value: number;
    avg_turnover: number;
  }>;
  stockLevelTrends: Array<{
    date: string;
    total_items: number;
    low_stock_items: number;
    out_of_stock_items: number;
  }>;
  supplierPerformance: Array<{
    supplier_id: string;
    supplier_name: string;
    items_supplied: number;
    avg_lead_time: number;
    on_time_delivery_rate: number;
  }>;
}