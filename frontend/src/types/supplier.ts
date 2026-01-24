export interface Supplier {
  supplier_id: string;
  name: string;
  supplier_type: 'device_manufacturer' | 'component' | 'service' | 'logistics';
  contact_email: string;
  contact_phone?: string;
  address?: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
  };
  website?: string;
  tax_id?: string;
  payment_terms?: string;
  lead_time_days: number;
  minimum_order_value?: number;
  performance_score: number;
  total_orders: number;
  on_time_deliveries: number;
  quality_issues: number;
  status: 'active' | 'inactive' | 'under_review' | 'suspended';
  api_endpoint?: string;
  api_credentials?: boolean;
  certifications?: string[];
  capabilities?: string[];
  created_at: string;
  updated_at: string;
  performance_metrics?: SupplierMetrics;
}

export interface SupplierMetrics {
  total_orders: number;
  on_time_delivery_rate: number;
  quality_score: number;
  average_lead_time: number;
  total_value: number;
  delivered_orders: number;
  pending_orders: number;
  cost_savings?: number;
  defect_rate?: number;
  response_time?: number;
}

export interface PurchaseOrder {
  po_id: string;
  supplier_id: string;
  supplier_info?: {
    name: string;
    contact_email: string;
    lead_time_days: number;
  };
  items: PurchaseOrderItem[];
  total_amount: string;
  currency: string;
  status: 'pending' | 'approved' | 'shipped' | 'delivered' | 'cancelled';
  approval_status: 'pending' | 'pending_approval' | 'auto_approved' | 'approved' | 'rejected';
  created_date: string;
  updated_at: string;
  expected_delivery?: string;
  actual_delivery_date?: string;
  created_by: string;
  approved_by?: string;
  delivery_address?: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
  };
  special_instructions?: string;
  terms_and_conditions?: string;
  status_history?: Array<{
    status: string;
    timestamp: string;
    notes?: string;
    changed_by?: string;
  }>;
  receiving_id?: string;
  quality_issues?: number;
  notes?: string;
}

export interface PurchaseOrderItem {
  item_id: string;
  name: string;
  description?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  unit_of_measure?: string;
  expected_delivery_date?: string;
  quantity_received?: number;
  quantity_rejected?: number;
  location_id?: string;
  specifications?: Record<string, any>;
}

export interface CreateSupplierRequest {
  name: string;
  supplier_type: 'device_manufacturer' | 'component' | 'service' | 'logistics';
  contact_email: string;
  contact_phone?: string;
  address?: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
  };
  website?: string;
  tax_id?: string;
  payment_terms?: string;
  lead_time_days: number;
  minimum_order_value?: number;
  certifications?: string[];
  capabilities?: string[];
}

export interface CreatePurchaseOrderRequest {
  supplier_id: string;
  items: Array<{
    item_id: string;
    name: string;
    description?: string;
    quantity: number;
    unit_price: number;
    specifications?: Record<string, any>;
  }>;
  delivery_address?: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
    country: string;
  };
  special_instructions?: string;
  requested_delivery_date?: string;
  created_by: string;
}

export interface SupplierPerformanceReport {
  supplier_id: string;
  supplier_name: string;
  reporting_period: {
    start_date: string;
    end_date: string;
  };
  metrics: SupplierMetrics;
  orders_summary: {
    total_orders: number;
    total_value: number;
    average_order_value: number;
    on_time_orders: number;
    late_orders: number;
    cancelled_orders: number;
  };
  quality_metrics: {
    defect_rate: number;
    return_rate: number;
    quality_incidents: number;
    corrective_actions: number;
  };
  financial_metrics: {
    payment_terms_compliance: number;
    cost_variance: number;
    price_stability: number;
  };
  recommendations: string[];
  risk_assessment: {
    overall_risk: 'low' | 'medium' | 'high';
    financial_risk: 'low' | 'medium' | 'high';
    operational_risk: 'low' | 'medium' | 'high';
    quality_risk: 'low' | 'medium' | 'high';
  };
}

export interface SupplierContract {
  contract_id: string;
  supplier_id: string;
  contract_type: 'master_agreement' | 'purchase_agreement' | 'service_agreement';
  start_date: string;
  end_date: string;
  auto_renewal: boolean;
  payment_terms: string;
  delivery_terms: string;
  quality_requirements: string[];
  pricing_structure: {
    type: 'fixed' | 'variable' | 'tiered';
    details: Record<string, any>;
  };
  sla_requirements?: {
    delivery_time: number;
    quality_threshold: number;
    response_time: number;
  };
  penalties?: {
    late_delivery: number;
    quality_issues: number;
    non_compliance: number;
  };
  status: 'draft' | 'active' | 'expired' | 'terminated';
  created_by: string;
  approved_by?: string;
  documents?: Array<{
    name: string;
    url: string;
    type: string;
  }>;
}

export interface SupplierAnalytics {
  timeRange: string;
  totalSuppliers: number;
  activeSuppliers: number;
  totalPurchaseValue: number;
  averageLeadTime: number;
  overallPerformanceScore: number;
  topPerformers: Array<{
    supplier_id: string;
    name: string;
    performance_score: number;
    total_value: number;
  }>;
  categoryBreakdown: Array<{
    supplier_type: string;
    count: number;
    total_value: number;
    avg_performance: number;
  }>;
  performanceTrends: Array<{
    date: string;
    avg_performance: number;
    on_time_delivery: number;
    quality_score: number;
  }>;
  riskAnalysis: {
    high_risk_suppliers: number;
    single_source_items: number;
    contract_renewals_due: number;
  };
}