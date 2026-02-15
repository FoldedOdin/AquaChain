/**
 * Enhanced Consumer Ordering System Types
 * TypeScript interfaces for orders, payments, technicians, and simulations
 */

// Core enums
export enum OrderStatus {
  PENDING_PAYMENT = 'PENDING_PAYMENT',
  PENDING_CONFIRMATION = 'PENDING_CONFIRMATION',
  ORDER_PLACED = 'ORDER_PLACED',
  SHIPPED = 'SHIPPED',
  OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY',
  DELIVERED = 'DELIVERED',
  CANCELLED = 'CANCELLED',
  FAILED = 'FAILED'
}

export enum PaymentStatus {
  PENDING = 'PENDING',
  COD_PENDING = 'COD_PENDING',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED'
}

export type PaymentMethod = 'COD' | 'ONLINE';

// Location and address interfaces
export interface Location {
  latitude: number;
  longitude: number;
  address: string;
  city: string;
  state: string;
  pincode: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  landmark?: string;
}

export interface ContactInfo {
  name: string;
  phone: string;
  email: string;
  alternatePhone?: string;
}

// Status update interface
export interface StatusUpdate {
  status: OrderStatus | string;
  timestamp: Date;
  message: string;
  metadata?: Record<string, any>;
}

// Order interfaces
export interface CreateOrderRequest {
  consumerId: string;
  deviceType: string;
  serviceType: string;
  paymentMethod: PaymentMethod;
  deliveryAddress: Address;
  contactInfo: ContactInfo;
  specialInstructions?: string;
  amount?: number;
  paymentId?: string;
}

export interface Order {
  id: string;
  consumerId: string;
  deviceType: string;
  serviceType: string;
  paymentMethod: PaymentMethod;
  status: OrderStatus | string;
  amount?: number;
  deliveryAddress: Address;
  contactInfo: ContactInfo;
  assignedTechnician?: string;
  paymentId?: string;
  createdAt: Date;
  updatedAt: Date;
  statusHistory: StatusUpdate[];
  specialInstructions?: string;
}

// Payment interfaces
export interface RazorpayOrder {
  id: string;
  amount: number;
  currency: string;
  receipt: string;
  status: string;
}

export interface RazorpayError {
  code: string;
  description: string;
  source: string;
  step: string;
  reason: string;
}

export interface Payment {
  id: string;
  orderId: string;
  amount: number;
  paymentMethod: PaymentMethod;
  status: PaymentStatus;
  razorpayPaymentId?: string;
  razorpayOrderId?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Technician interfaces
export interface Technician {
  id: string;
  name: string;
  phone: string;
  email: string;
  location: Location;
  available: boolean;
  skills: string[];
  rating: number;
}

export interface TechnicianAssignment {
  orderId: string;
  technicianId: string;
  assignedAt: Date;
  estimatedArrival?: Date;
  distance: number; // in kilometers
}

// Simulation interfaces
export interface SimulationStatus {
  orderId: string;
  currentStatus: OrderStatus;
  nextStatus?: OrderStatus;
  nextTransitionAt?: Date;
  isActive: boolean;
}

// Frontend component prop interfaces
export interface PaymentMethodSelectorProps {
  onMethodSelect: (method: PaymentMethod) => void;
  disabled?: boolean;
}

export interface PaymentMethodOption {
  id: PaymentMethod;
  name: string;
  description: string;
  icon: string;
}

export interface CODConfirmationTimerProps {
  onConfirm: () => void;
  onCancel: () => void;
  countdownSeconds: number;
}

export interface TimerState {
  remainingSeconds: number;
  isActive: boolean;
  progress: number; // 0-100 for progress bar
}

export interface RazorpayCheckoutProps {
  orderId: string;
  amount: number;
  onSuccess: (paymentId: string) => void;
  onFailure: (error: RazorpayError) => void;
  customerInfo: ContactInfo;
}

export interface OrderStatusTrackerProps {
  orderId: string;
  currentStatus: OrderStatus | string;
  statusHistory: StatusUpdate[];
  estimatedDelivery?: Date;
  demoMode?: boolean; // Enable auto-progression for demo purposes
  progressInterval?: number; // Interval in seconds (default: 20)
}

// Service interfaces for backend integration
export interface OrderManagementService {
  createOrder(request: CreateOrderRequest): Promise<Order>;
  updateOrderStatus(orderId: string, status: OrderStatus, metadata?: any): Promise<Order>;
  getOrder(orderId: string): Promise<Order>;
  getOrdersByConsumer(consumerId: string): Promise<Order[]>;
  cancelOrder(orderId: string, reason: string): Promise<Order>;
}

export interface PaymentService {
  createRazorpayOrder(amount: number, orderId: string): Promise<RazorpayOrder>;
  verifyPayment(paymentId: string, orderId: string, signature: string): Promise<boolean>;
  createCODPayment(orderId: string, amount: number): Promise<Payment>;
  getPaymentStatus(orderId: string): Promise<PaymentStatus>;
  handlePaymentWebhook(payload: any, signature: string): Promise<void>;
}

export interface TechnicianAssignmentService {
  assignTechnician(orderId: string, serviceLocation: Location): Promise<TechnicianAssignment>;
  getAvailableTechnicians(location: Location, radius: number): Promise<Technician[]>;
  updateTechnicianAvailability(technicianId: string, available: boolean): Promise<void>;
}

export interface StatusSimulatorService {
  startSimulation(orderId: string): Promise<void>;
  stopSimulation(orderId: string): Promise<void>;
  getSimulationStatus(orderId: string): Promise<SimulationStatus>;
}

// API response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface OrderResponse extends ApiResponse<Order> {}
export interface PaymentResponse extends ApiResponse<Payment> {}
export interface TechnicianResponse extends ApiResponse<Technician[]> {}
export interface SimulationResponse extends ApiResponse<SimulationStatus> {}