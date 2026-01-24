export interface WarehouseOverview {
  overview: {
    total_locations: number;
    occupied_locations: number;
    available_locations: number;
    occupancy_rate: number;
    inbound_shipments: number;
    outbound_orders: number;
  };
  inbound_queue: InboundShipment[];
  outbound_queue: OutboundOrder[];
  alerts: WarehouseAlert[];
}

export interface InboundShipment {
  po_id: string;
  supplier_id: string;
  expected_delivery?: string;
  status: 'scheduled' | 'arrived' | 'receiving' | 'completed';
  items?: Array<{
    item_id: string;
    name: string;
    quantity_expected: number;
    quantity_received?: number;
  }>;
  receiving_priority?: 'low' | 'normal' | 'high' | 'urgent';
  special_handling?: boolean;
  quality_check_required?: boolean;
}

export interface OutboundOrder {
  order_id: string;
  customer_id?: string;
  status: 'pending_fulfillment' | 'picking' | 'packing' | 'shipped' | 'delivered';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  items?: Array<{
    item_id: string;
    name: string;
    quantity: number;
    location_id?: string;
  }>;
  assigned_picker?: string;
  estimated_ship_date?: string;
  shipping_method?: string;
  tracking_number?: string;
}

export interface WarehouseAlert {
  alert_id: string;
  type: 'capacity' | 'quality' | 'safety' | 'equipment' | 'staffing';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  location?: string;
  created_at: string;
  acknowledged?: boolean;
  resolved?: boolean;
}

export interface WarehouseLocation {
  location_id: string;
  warehouse_id: string;
  zone: string;
  aisle?: string;
  shelf?: string;
  bin?: string;
  level?: number;
  capacity: number;
  current_usage: number;
  status: 'available' | 'occupied' | 'reserved' | 'maintenance' | 'temporary';
  location_type: 'storage' | 'receiving' | 'shipping' | 'quality' | 'returns';
  restrictions?: string[];
  temperature_controlled?: boolean;
  hazmat_approved?: boolean;
  last_inventory_check?: string;
  coordinates?: {
    x: number;
    y: number;
    z?: number;
  };
}

export interface PickList {
  pick_list_id: string;
  order_id: string;
  created_date: string;
  status: 'pending' | 'assigned' | 'picking' | 'completed' | 'cancelled';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  assigned_picker?: string;
  estimated_pick_time: number;
  actual_pick_time?: number;
  pick_items: PickListItem[];
  unavailable_items?: Array<{
    item_id: string;
    shortage_quantity: number;
  }>;
  notes?: string;
}

export interface PickListItem {
  item_id: string;
  item_name: string;
  location_id: string;
  zone: string;
  shelf?: string;
  quantity_to_pick: number;
  quantity_picked?: number;
  sequence: number;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  special_instructions?: string;
  picked_at?: string;
  condition?: 'good' | 'damaged' | 'expired';
}

export interface QualityCheck {
  qc_id: string;
  receiving_id: string;
  inspection_date: string;
  inspector: string;
  overall_status: 'passed' | 'failed' | 'partial';
  items_checked: QualityCheckItem[];
  defects_found?: QualityDefect[];
  photos?: string[];
  notes?: string;
  corrective_actions?: string[];
  follow_up_required?: boolean;
}

export interface QualityCheckItem {
  item_id: string;
  location_id: string;
  quantity_inspected: number;
  status: 'approved' | 'rejected' | 'conditional';
  quantity_approved?: number;
  quantity_rejected?: number;
  rejection_reason?: string;
  defect_codes?: string[];
  inspector_notes?: string;
}

export interface QualityDefect {
  defect_id: string;
  defect_code: string;
  defect_type: 'cosmetic' | 'functional' | 'safety' | 'specification';
  severity: 'minor' | 'major' | 'critical';
  description: string;
  affected_quantity: number;
  root_cause?: string;
  corrective_action?: string;
  supplier_notified?: boolean;
}

export interface ReceivingRecord {
  receiving_id: string;
  po_id: string;
  supplier_id: string;
  received_date: string;
  received_by: string;
  status: 'received' | 'quality_check' | 'put_away' | 'completed';
  items: Array<{
    item_id: string;
    quantity_expected: number;
    quantity_received: number;
    condition: 'good' | 'damaged' | 'expired';
    location_assigned?: string;
  }>;
  quality_check_required: boolean;
  quality_check_id?: string;
  discrepancies?: Array<{
    item_id: string;
    type: 'quantity' | 'quality' | 'specification';
    description: string;
    resolution?: string;
  }>;
  documents?: Array<{
    name: string;
    url: string;
    type: 'packing_slip' | 'invoice' | 'certificate' | 'photo';
  }>;
  notes?: string;
}

export interface WarehouseStaff {
  staff_id: string;
  name: string;
  role: 'picker' | 'receiver' | 'quality_inspector' | 'supervisor' | 'manager';
  shift: 'day' | 'evening' | 'night';
  status: 'active' | 'break' | 'offline';
  current_assignment?: {
    type: 'picking' | 'receiving' | 'quality_check' | 'put_away';
    reference_id: string;
    started_at: string;
  };
  performance_metrics?: {
    picks_per_hour: number;
    accuracy_rate: number;
    tasks_completed_today: number;
  };
  certifications?: string[];
  equipment_assigned?: string[];
}

export interface WarehouseAnalytics {
  timeRange: string;
  throughput: {
    items_received: number;
    items_shipped: number;
    orders_fulfilled: number;
    average_fulfillment_time: number;
  };
  efficiency: {
    space_utilization: number;
    pick_accuracy: number;
    on_time_shipments: number;
    labor_productivity: number;
  };
  quality: {
    defect_rate: number;
    return_rate: number;
    quality_incidents: number;
    supplier_quality_score: number;
  };
  trends: Array<{
    date: string;
    items_received: number;
    items_shipped: number;
    space_utilization: number;
    pick_accuracy: number;
  }>;
  bottlenecks: Array<{
    area: string;
    issue: string;
    impact: 'low' | 'medium' | 'high';
    recommendation: string;
  }>;
}

export interface InventoryMovement {
  movement_id: string;
  item_id: string;
  from_location?: string;
  to_location?: string;
  quantity: number;
  movement_type: 'receipt' | 'pick' | 'transfer' | 'adjustment' | 'return';
  reference_id?: string;
  performed_by: string;
  timestamp: string;
  reason?: string;
  notes?: string;
  status: 'pending' | 'completed' | 'cancelled';
}