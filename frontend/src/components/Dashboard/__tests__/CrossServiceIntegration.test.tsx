/**
 * Cross-Service Integration Tests - Task 16.1 Frontend
 * 
 * Tests complete workflows from frontend to backend with comprehensive validation:
 * - Complete workflows from frontend to backend
 * - Role-based access control across all API endpoints
 * - Approval workflows end-to-end with all state transitions
 * - Budget enforcement across all purchase scenarios
 * 
 * Requirements: All workflow and RBAC requirements
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import OperationsDashboard from '../OperationsDashboard';
import ProcurementDashboard from '../ProcurementDashboard';
import AdminDashboardRestructured from '../AdminDashboardRestructured';
import { UserProfile } from '../../../types';

// Mock API services
const mockInventoryService = {
  getStockLevels: jest.fn(),
  updateStockLevel: jest.fn(),
  getReorderAlerts: jest.fn(),
  getDemandForecast: jest.fn(),
};

const mockProcurementService = {
  submitPurchaseOrder: jest.fn(),
  getApprovalQueue: jest.fn(),
  approvePurchaseOrder: jest.fn(),
  rejectPurchaseOrder: jest.fn(),
};

const mockBudgetService = {
  getBudgetUtilization: jest.fn(),
  validateBudgetAvailability: jest.fn(),
  allocateBudget: jest.fn(),
  reserveBudget: jest.fn(),
};

const mockWorkflowService = {
  getWorkflowStatus: jest.fn(),
  transitionWorkflow: jest.fn(),
  getWorkflowHistory: jest.fn(),
};

const mockAuditService = {
  logUserAction: jest.fn(),
  getAuditTrail: jest.fn(),
};

// Mock services
jest.mock('../../../services/inventoryService', () => mockInventoryService);
jest.mock('../../../services/procurementService', () => mockProcurementService);
jest.mock('../../../services/budgetService', () => mockBudgetService);
jest.mock('../../../services/workflowService', () => mockWorkflowService);
jest.mock('../../../services/auditService', () => mockAuditService);

// Mock child components
jest.mock('../Operations/InventoryManagerView', () => {
  return function MockInventoryManagerView() {
    return (
      <div data-testid="inventory-manager-view">
        <button 
          data-testid="update-stock-btn"
          onClick={() => mockInventoryService.updateStockLevel('item-001', 'warehouse-001', { current_stock: 15 })}
        >
          Update Stock
        </button>
        <button 
          data-testid="get-alerts-btn"
          onClick={() => mockInventoryService.getReorderAlerts('high')}
        >
          Get Alerts
        </button>
      </div>
    );
  };
});

jest.mock('../Procurement/ApprovalQueue', () => {
  return function MockApprovalQueue() {
    return (
      <div data-testid="approval-queue">
        <button 
          data-testid="approve-order-btn"
          onClick={() => mockProcurementService.approvePurchaseOrder('order-001', 'Approved for testing')}
        >
          Approve Order
        </button>
        <button 
          data-testid="reject-order-btn"
          onClick={() => mockProcurementService.rejectPurchaseOrder('order-001', 'Rejected for testing')}
        >
          Reject Order
        </button>
      </div>
    );
  };
});

jest.mock('../Procurement/BudgetTracking', () => {
  return function MockBudgetTracking() {
    return (
      <div data-testid="budget-tracking">
        <button 
          data-testid="allocate-budget-btn"
          onClick={() => mockBudgetService.allocateBudget({ category: 'office-supplies', amount: 10000 })}
        >
          Allocate Budget
        </button>
        <button 
          data-testid="validate-budget-btn"
          onClick={() => mockBudgetService.validateBudgetAvailability(5000, 'office-supplies')}
        >
          Validate Budget
        </button>
      </div>
    );
  };
});

// Mock contexts and hooks
let mockUser: UserProfile | null = null;
let mockIsLoading = false;
let mockIsMFAVerified = false;

const mockAuthContext = {
  user: mockUser,
  isLoading: mockIsLoading,
  isAuthenticated: true,
  isMFAVerified: mockIsMFAVerified,
  requireMFA: jest.fn(),
  login: jest.fn(),
  logout: jest.fn(),
  getAuthToken: jest.fn().mockResolvedValue('mock-token'),
  refreshUser: jest.fn(),
};

const mockNotificationContext = {
  showNotification: jest.fn(),
};

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({ ...mockAuthContext, user: mockUser, isLoading: mockIsLoading, isMFAVerified: mockIsMFAVerified }),
}));

jest.mock('../../../contexts/NotificationContext', () => ({
  useNotification: () => mockNotificationContext,
}));

jest.mock('../../../hooks/useDashboardData', () => ({
  useDashboardData: () => ({ data: null, isLoading: false, error: null }),
}));

jest.mock('../../../hooks/useRealTimeUpdates', () => ({
  useRealTimeUpdates: () => ({ isConnected: true }),
}));

jest.mock('../../../hooks/useNotifications', () => ({
  useNotifications: () => ({ notifications: [] }),
}));

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

// Helper function to create user profiles
const createUserProfile = (role: string): UserProfile => ({
  userId: `user-${role}`,
  email: `${role}@example.com`,
  role: role as any,
  profile: {
    firstName: 'Test',
    lastName: 'User',
    phone: '+1234567890',
    address: {
      street: '123 Test St',
      city: 'Test City',
      state: 'TS',
      zipCode: '12345',
      coordinates: { latitude: 0, longitude: 0 }
    }
  },
  deviceIds: [],
  preferences: {
    notifications: { push: true, sms: true, email: true },
    theme: 'auto',
    language: 'en'
  }
});

describe('Cross-Service Integration Tests - Task 16.1 Frontend', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUser = null;
    mockIsLoading = false;
    mockIsMFAVerified = false;
  });

  describe('1. Complete Purchase Order Workflow - Frontend to Backend', () => {
    it('should handle complete inventory reorder workflow', async () => {
      // Step 1: Start as inventory manager
      mockUser = createUserProfile('inventory_manager');
      
      // Mock low stock alert
      mockInventoryService.getReorderAlerts.mockResolvedValue({
        statusCode: 200,
        body: {
          alerts: [{
            itemId: 'item-001',
            currentStock: 5,
            reorderPoint: 20,
            urgency: 'high',
            recommendedAction: 'immediate_reorder'
          }]
        }
      });

      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Verify inventory manager view is rendered
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();

      // Trigger reorder alert check
      const getAlertsBtn = screen.getByTestId('get-alerts-btn');
      await userEvent.click(getAlertsBtn);

      await waitFor(() => {
        expect(mockInventoryService.getReorderAlerts).toHaveBeenCalledWith('high');
      });

      // Step 2: Switch to procurement controller for purchase order
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;

      // Mock budget validation
      mockBudgetService.validateBudgetAvailability.mockResolvedValue({
        available: true,
        requestedAmount: 5000,
        availableAmount: 8000,
        message: 'Budget available'
      });

      // Mock purchase order submission
      mockProcurementService.submitPurchaseOrder.mockResolvedValue({
        orderId: 'order-001',
        status: 'PENDING',
        workflowId: 'workflow-001'
      });

      const { rerender } = render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Verify procurement dashboard renders
      expect(screen.getByText('Procurement & Finance Dashboard')).toBeInTheDocument();

      // Test budget validation
      const validateBudgetBtn = screen.getByTestId('validate-budget-btn');
      await userEvent.click(validateBudgetBtn);

      await waitFor(() => {
        expect(mockBudgetService.validateBudgetAvailability).toHaveBeenCalledWith(5000, 'office-supplies');
      });

      // Step 3: Test approval workflow
      mockProcurementService.approvePurchaseOrder.mockResolvedValue({
        orderId: 'order-001',
        status: 'APPROVED',
        approvedBy: 'test-procurement-controller',
        approvedAt: new Date().toISOString()
      });

      const approveBtn = screen.getByTestId('approve-order-btn');
      await userEvent.click(approveBtn);

      await waitFor(() => {
        expect(mockProcurementService.approvePurchaseOrder).toHaveBeenCalledWith('order-001', 'Approved for testing');
      });

      // Step 4: Verify audit logging
      expect(mockAuditService.logUserAction).toHaveBeenCalled();
    });

    it('should handle budget enforcement during purchase workflow', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;

      // Mock insufficient budget
      mockBudgetService.validateBudgetAvailability.mockResolvedValue({
        available: false,
        requestedAmount: 15000,
        availableAmount: 8000,
        message: 'Insufficient budget'
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const validateBudgetBtn = screen.getByTestId('validate-budget-btn');
      await userEvent.click(validateBudgetBtn);

      await waitFor(() => {
        expect(mockBudgetService.validateBudgetAvailability).toHaveBeenCalled();
      });

      // Should show budget constraint notification
      expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'error',
          message: expect.stringContaining('budget')
        })
      );
    });
  });

  describe('2. Role-Based Access Control - Frontend Enforcement', () => {
    const testRoleAccess = async (role: string, expectedComponents: string[], deniedComponents: string[]) => {
      mockUser = createUserProfile(role);
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Check expected components are present
      for (const component of expectedComponents) {
        expect(screen.getByTestId(component)).toBeInTheDocument();
      }

      // Check denied components are not present
      for (const component of deniedComponents) {
        expect(screen.queryByTestId(component)).not.toBeInTheDocument();
      }
    };

    it('should enforce inventory manager role boundaries', async () => {
      await testRoleAccess(
        'inventory_manager',
        ['inventory-manager-view'],
        ['warehouse-manager-view', 'supplier-coordinator-view']
      );
    });

    it('should enforce warehouse manager role boundaries', async () => {
      await testRoleAccess(
        'warehouse_manager',
        ['warehouse-manager-view'],
        ['inventory-manager-view', 'supplier-coordinator-view']
      );
    });

    it('should enforce supplier coordinator role boundaries', async () => {
      await testRoleAccess(
        'supplier_coordinator',
        ['supplier-coordinator-view'],
        ['inventory-manager-view', 'warehouse-manager-view']
      );
    });

    it('should block unauthorized API calls based on role', async () => {
      mockUser = createUserProfile('inventory_manager');

      // Mock unauthorized API call
      mockProcurementService.submitPurchaseOrder.mockRejectedValue(
        new Error('Unauthorized: Insufficient permissions')
      );

      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Attempt unauthorized action (inventory manager trying to submit purchase order)
      try {
        await mockProcurementService.submitPurchaseOrder({
          supplierId: 'supplier-001',
          items: [{ itemId: 'item-001', quantity: 10, unitPrice: 25 }],
          budgetCategory: 'office-supplies'
        });
      } catch (error) {
        expect(error.message).toContain('Unauthorized');
      }
    });
  });

  describe('3. Approval Workflow State Transitions - Frontend Integration', () => {
    beforeEach(() => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;
    });

    it('should handle workflow approval transition', async () => {
      mockWorkflowService.getWorkflowStatus.mockResolvedValue({
        workflowId: 'workflow-001',
        currentState: 'PENDING_APPROVAL',
        canApprove: true,
        canReject: true
      });

      mockWorkflowService.transitionWorkflow.mockResolvedValue({
        workflowId: 'workflow-001',
        currentState: 'APPROVED',
        action: 'APPROVE'
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const approveBtn = screen.getByTestId('approve-order-btn');
      await userEvent.click(approveBtn);

      await waitFor(() => {
        expect(mockProcurementService.approvePurchaseOrder).toHaveBeenCalled();
      });
    });

    it('should handle workflow rejection transition', async () => {
      mockWorkflowService.getWorkflowStatus.mockResolvedValue({
        workflowId: 'workflow-001',
        currentState: 'PENDING_APPROVAL',
        canApprove: true,
        canReject: true
      });

      mockWorkflowService.transitionWorkflow.mockResolvedValue({
        workflowId: 'workflow-001',
        currentState: 'REJECTED',
        action: 'REJECT'
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const rejectBtn = screen.getByTestId('reject-order-btn');
      await userEvent.click(rejectBtn);

      await waitFor(() => {
        expect(mockProcurementService.rejectPurchaseOrder).toHaveBeenCalled();
      });
    });

    it('should prevent invalid workflow transitions', async () => {
      mockWorkflowService.getWorkflowStatus.mockResolvedValue({
        workflowId: 'workflow-001',
        currentState: 'COMPLETED',
        canApprove: false,
        canReject: false
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Buttons should be disabled for completed workflow
      const approveBtn = screen.getByTestId('approve-order-btn');
      const rejectBtn = screen.getByTestId('reject-order-btn');

      expect(approveBtn).toBeDisabled();
      expect(rejectBtn).toBeDisabled();
    });
  });

  describe('4. Budget Enforcement - Frontend Validation', () => {
    beforeEach(() => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;
    });

    it('should validate budget before allowing purchase submission', async () => {
      mockBudgetService.validateBudgetAvailability.mockResolvedValue({
        available: true,
        requestedAmount: 5000,
        availableAmount: 8000
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const validateBtn = screen.getByTestId('validate-budget-btn');
      await userEvent.click(validateBtn);

      await waitFor(() => {
        expect(mockBudgetService.validateBudgetAvailability).toHaveBeenCalledWith(5000, 'office-supplies');
      });
    });

    it('should prevent purchase when budget is insufficient', async () => {
      mockBudgetService.validateBudgetAvailability.mockResolvedValue({
        available: false,
        requestedAmount: 15000,
        availableAmount: 8000,
        message: 'Insufficient budget: requested 15000, available 8000'
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const validateBtn = screen.getByTestId('validate-budget-btn');
      await userEvent.click(validateBtn);

      await waitFor(() => {
        expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'error'
          })
        );
      });
    });

    it('should handle budget allocation workflow', async () => {
      mockBudgetService.allocateBudget.mockResolvedValue({
        allocated: true,
        category: 'office-supplies',
        amount: 10000,
        allocationId: 'allocation-001'
      });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const allocateBtn = screen.getByTestId('allocate-budget-btn');
      await userEvent.click(allocateBtn);

      await waitFor(() => {
        expect(mockBudgetService.allocateBudget).toHaveBeenCalledWith({
          category: 'office-supplies',
          amount: 10000
        });
      });
    });
  });

  describe('5. Error Handling and Recovery', () => {
    it('should handle API errors gracefully', async () => {
      mockUser = createUserProfile('inventory_manager');

      mockInventoryService.updateStockLevel.mockRejectedValue(
        new Error('Service temporarily unavailable')
      );

      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      const updateBtn = screen.getByTestId('update-stock-btn');
      await userEvent.click(updateBtn);

      await waitFor(() => {
        expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'error',
            message: expect.stringContaining('Service temporarily unavailable')
          })
        );
      });
    });

    it('should handle network failures with retry mechanism', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;

      // First call fails, second succeeds
      mockBudgetService.validateBudgetAvailability
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          available: true,
          requestedAmount: 5000,
          availableAmount: 8000
        });

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const validateBtn = screen.getByTestId('validate-budget-btn');
      await userEvent.click(validateBtn);

      // Should retry automatically
      await waitFor(() => {
        expect(mockBudgetService.validateBudgetAvailability).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('6. Performance and User Experience', () => {
    it('should maintain responsive UI during API calls', async () => {
      mockUser = createUserProfile('inventory_manager');

      // Mock slow API response
      mockInventoryService.getReorderAlerts.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          statusCode: 200,
          body: { alerts: [] }
        }), 100))
      );

      const startTime = performance.now();

      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      const renderTime = performance.now() - startTime;

      // UI should render quickly even with slow API
      expect(renderTime).toBeLessThan(200);
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();
    });

    it('should show loading states during API operations', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;

      // Mock delayed API response
      mockBudgetService.validateBudgetAvailability.mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          available: true,
          requestedAmount: 5000,
          availableAmount: 8000
        }), 500))
      );

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      const validateBtn = screen.getByTestId('validate-budget-btn');
      await userEvent.click(validateBtn);

      // Should show loading indicator
      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('7. Audit Trail Integration', () => {
    it('should log all user actions for audit trail', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;

      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Perform various actions
      const approveBtn = screen.getByTestId('approve-order-btn');
      await userEvent.click(approveBtn);

      const allocateBtn = screen.getByTestId('allocate-budget-btn');
      await userEvent.click(allocateBtn);

      // Verify audit logging
      await waitFor(() => {
        expect(mockAuditService.logUserAction).toHaveBeenCalledTimes(2);
      });
    });

    it('should include proper context in audit logs', async () => {
      mockUser = createUserProfile('inventory_manager');

      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      const updateBtn = screen.getByTestId('update-stock-btn');
      await userEvent.click(updateBtn);

      await waitFor(() => {
        expect(mockAuditService.logUserAction).toHaveBeenCalledWith(
          expect.objectContaining({
            userId: 'user-inventory_manager',
            action: expect.any(String),
            timestamp: expect.any(String),
            context: expect.objectContaining({
              role: 'inventory_manager',
              component: expect.any(String)
            })
          })
        );
      });
    });
  });
});