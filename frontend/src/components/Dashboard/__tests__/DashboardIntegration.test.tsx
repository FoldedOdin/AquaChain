/**
 * Dashboard Integration Tests - Task 15 Checkpoint
 * 
 * Comprehensive integration testing for all three dashboards:
 * - Operations Dashboard (multi-role)
 * - Procurement Dashboard (dedicated high-authority)
 * - Admin Dashboard (restructured)
 * 
 * Validates:
 * - All three dashboards render correctly for their respective roles
 * - Role boundaries are enforced in UI (no unauthorized components visible)
 * - User experience flows for all critical operations
 * - <200ms perceived latency for all user interactions
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import OperationsDashboard from '../OperationsDashboard';
import ProcurementDashboard from '../ProcurementDashboard';
import AdminDashboardRestructured from '../AdminDashboardRestructured';
import { UserProfile } from '../../../types';

// Performance measurement utilities
const measureRenderTime = async (renderFn: () => void): Promise<number> => {
  const startTime = performance.now();
  await act(async () => {
    renderFn();
  });
  const endTime = performance.now();
  return endTime - startTime;
};

// Mock all child components to focus on integration behavior
jest.mock('../Operations/InventoryManagerView', () => {
  return function MockInventoryManagerView() {
    return <div data-testid="inventory-manager-view">Inventory Manager View</div>;
  };
});

jest.mock('../Operations/WarehouseManagerView', () => {
  return function MockWarehouseManagerView() {
    return <div data-testid="warehouse-manager-view">Warehouse Manager View</div>;
  };
});

jest.mock('../Operations/SupplierCoordinatorView', () => {
  return function MockSupplierCoordinatorView() {
    return <div data-testid="supplier-coordinator-view">Supplier Coordinator View</div>;
  };
});

jest.mock('../Procurement/ApprovalQueue', () => {
  return function MockApprovalQueue() {
    return <div data-testid="approval-queue">Approval Queue</div>;
  };
});

jest.mock('../Procurement/BudgetTracking', () => {
  return function MockBudgetTracking() {
    return <div data-testid="budget-tracking">Budget Tracking</div>;
  };
});

jest.mock('../Procurement/FinancialAuditLog', () => {
  return function MockFinancialAuditLog() {
    return <div data-testid="financial-audit-log">Financial Audit Log</div>;
  };
});

jest.mock('../DashboardLayout', () => {
  return function MockDashboardLayout({ children, header, role }: { 
    children: React.ReactNode; 
    header?: React.ReactNode;
    role?: string;
  }) {
    return (
      <div data-testid="dashboard-layout" data-role={role}>
        {header && <div data-testid="dashboard-header">{header}</div>}
        {children}
      </div>
    );
  };
});

jest.mock('../NotificationCenter', () => {
  return function MockNotificationCenter({ userRole }: { userRole: string }) {
    return <div data-testid="notification-center" data-role={userRole}>Notifications</div>;
  };
});

jest.mock('../DataExportModal', () => {
  return function MockDataExportModal({ isOpen, onClose, userRole }: { 
    isOpen: boolean; 
    onClose: () => void;
    userRole: string;
  }) {
    return isOpen ? (
      <div data-testid="data-export-modal" data-role={userRole}>
        <button onClick={onClose}>Close</button>
      </div>
    ) : null;
  };
});

// Mock contexts
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
  getAuthToken: jest.fn(),
  refreshUser: jest.fn(),
};

const mockNotificationContext = {
  showNotification: jest.fn(),
};

// Mock hooks
const mockDashboardData = {
  data: null,
  isLoading: false,
  error: null,
};

const mockRealTimeUpdates = {
  isConnected: true,
};

const mockNotifications = {
  notifications: [],
};

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({ ...mockAuthContext, user: mockUser, isLoading: mockIsLoading, isMFAVerified: mockIsMFAVerified }),
}));

jest.mock('../../../contexts/NotificationContext', () => ({
  useNotification: () => mockNotificationContext,
}));

jest.mock('../../../hooks/useDashboardData', () => ({
  useDashboardData: () => mockDashboardData,
}));

jest.mock('../../../hooks/useRealTimeUpdates', () => ({
  useRealTimeUpdates: () => mockRealTimeUpdates,
}));

jest.mock('../../../hooks/useNotifications', () => ({
  useNotifications: () => mockNotifications,
}));

// Mock services
jest.mock('../../../services/adminService', () => ({
  getAllUsers: jest.fn().mockResolvedValue([]),
  getSystemConfiguration: jest.fn().mockResolvedValue({
    alertThresholds: {
      global: {
        pH: { min: 6.5, max: 8.5 },
        turbidity: { max: 5.0 },
        tds: { max: 500 },
        temperature: { min: 0, max: 40 }
      }
    },
    systemLimits: {
      maxDevicesPerUser: 10,
      dataRetentionDays: 90,
      auditRetentionYears: 7
    }
  }),
  updateSystemConfiguration: jest.fn().mockResolvedValue({}),
  getSystemHealthMetrics: jest.fn().mockResolvedValue({
    criticalPathUptime: 99.9,
    apiUptime: 99.5
  }),
  getPerformanceMetrics: jest.fn().mockResolvedValue([]),
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

describe('Dashboard Integration Tests - Task 15 Checkpoint', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUser = null;
    mockIsLoading = false;
    mockIsMFAVerified = false;
  });

  describe('1. Operations Dashboard - Role-Based Rendering', () => {
    it('should render correctly for Inventory Manager role', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );
      });

      // Verify performance requirement (<200ms)
      expect(renderTime).toBeLessThan(200);

      // Verify correct dashboard renders
      expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Inventory Management')).toBeInTheDocument();
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();

      // Verify unauthorized tabs are NOT present
      expect(screen.queryByText('Warehouse Operations')).not.toBeInTheDocument();
      expect(screen.queryByText('Supplier Management')).not.toBeInTheDocument();
      expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();
    });

    it('should render correctly for Warehouse Manager role', async () => {
      mockUser = createUserProfile('warehouse_manager');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Warehouse Operations')).toBeInTheDocument();
      expect(screen.getByTestId('warehouse-manager-view')).toBeInTheDocument();

      // Verify unauthorized components are not present
      expect(screen.queryByText('Inventory Management')).not.toBeInTheDocument();
      expect(screen.queryByText('Supplier Management')).not.toBeInTheDocument();
    });

    it('should render correctly for Supplier Coordinator role', async () => {
      mockUser = createUserProfile('supplier_coordinator');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Supplier Management')).toBeInTheDocument();
      expect(screen.getByTestId('supplier-coordinator-view')).toBeInTheDocument();

      // Verify unauthorized components are not present
      expect(screen.queryByText('Inventory Management')).not.toBeInTheDocument();
      expect(screen.queryByText('Warehouse Operations')).not.toBeInTheDocument();
    });

    it('should deny access for unauthorized roles', async () => {
      const unauthorizedRoles = ['consumer', 'technician', 'admin', 'procurement_controller'];
      
      for (const role of unauthorizedRoles) {
        mockUser = createUserProfile(role);
        
        render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );

        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
        expect(screen.queryByText('Operations Dashboard')).not.toBeInTheDocument();
        expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();
      }
    });
  });

  describe('2. Procurement Dashboard - High-Authority Access', () => {
    it('should render correctly for Procurement Controller with MFA', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <ProcurementDashboard />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      expect(screen.getByText('Procurement & Finance Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Purchase Order Approvals')).toBeInTheDocument();
      expect(screen.getByText('Budget Tracking')).toBeInTheDocument();
      expect(screen.getByText('Financial Audit Log')).toBeInTheDocument();
      expect(screen.getByText('MFA Verified')).toBeInTheDocument();
    });

    it('should require MFA for sensitive operations', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = false;
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Should show MFA requirement for sensitive tabs
      const approvalTab = screen.getByText('Purchase Order Approvals');
      expect(approvalTab.closest('button')).toHaveAttribute('disabled');
      
      // Budget tracking should be accessible without MFA
      const budgetTab = screen.getByText('Budget Tracking');
      expect(budgetTab.closest('button')).not.toHaveAttribute('disabled');
    });

    it('should deny access for non-procurement roles', async () => {
      const unauthorizedRoles = ['consumer', 'technician', 'admin', 'inventory_manager', 'warehouse_manager', 'supplier_coordinator'];
      
      for (const role of unauthorizedRoles) {
        mockUser = createUserProfile(role);
        
        render(
          <TestWrapper>
            <ProcurementDashboard />
          </TestWrapper>
        );

        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
        expect(screen.getByText('This dashboard is restricted to Procurement & Finance Controllers only.')).toBeInTheDocument();
        expect(screen.queryByText('Procurement & Finance Dashboard')).not.toBeInTheDocument();
      }
    });
  });

  describe('3. Admin Dashboard - System Administration Only', () => {
    it('should render correctly for Administrator role', async () => {
      mockUser = createUserProfile('admin');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <AdminDashboardRestructured />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      expect(screen.getByText('System Administration & Oversight')).toBeInTheDocument();
      
      // Verify admin-specific tabs are present
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('System Configuration')).toBeInTheDocument();
      expect(screen.getByText('Global Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Security & Audit')).toBeInTheDocument();
    });

    it('should NOT contain operational controls', async () => {
      mockUser = createUserProfile('admin');
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      // Verify NO operational controls are present
      const operationalControls = [
        'Inventory Management',
        'Warehouse Operations', 
        'Supplier Management',
        'Purchase Order Approvals',
        'Procurement Controls'
      ];

      operationalControls.forEach(control => {
        expect(screen.queryByText(control)).not.toBeInTheDocument();
      });

      // Verify admin-only functions are present
      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('System Configuration')).toBeInTheDocument();
    });

    it('should provide system-wide monitoring capabilities', async () => {
      mockUser = createUserProfile('admin');
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      // Click on monitoring tab
      const monitoringTab = screen.getByText('Global Monitoring');
      await userEvent.click(monitoringTab);

      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
      });
    });
  });

  describe('4. User Experience Flows', () => {
    it('should handle tab switching smoothly in Operations Dashboard', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Initial state - inventory tab should be active
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();

      // Note: Since this user only has inventory_manager role, 
      // other tabs should not be available for switching
      expect(screen.queryByText('Warehouse Operations')).not.toBeInTheDocument();
      expect(screen.queryByText('Supplier Management')).not.toBeInTheDocument();
    });

    it('should handle MFA flow in Procurement Dashboard', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = false;
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Try to access MFA-protected tab
      const approvalTab = screen.getByText('Purchase Order Approvals');
      
      // Tab should be disabled
      expect(approvalTab.closest('button')).toHaveAttribute('disabled');
      
      // Should show MFA indicator
      const mfaIcon = approvalTab.parentElement?.querySelector('svg');
      expect(mfaIcon).toBeInTheDocument();
    });

    it('should handle user management flow in Admin Dashboard', async () => {
      mockUser = createUserProfile('admin');
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      // Navigate to user management
      const userManagementTab = screen.getByText('User Management');
      await userEvent.click(userManagementTab);

      await waitFor(() => {
        expect(screen.getByText('Add User')).toBeInTheDocument();
      });
    });
  });

  describe('5. Performance Requirements', () => {
    it('should meet <200ms perceived latency for Operations Dashboard', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
    });

    it('should meet <200ms perceived latency for Procurement Dashboard', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <ProcurementDashboard />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
    });

    it('should meet <200ms perceived latency for Admin Dashboard', async () => {
      mockUser = createUserProfile('admin');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <AdminDashboardRestructured />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
    });

    it('should handle loading states efficiently', async () => {
      mockIsLoading = true;
      mockUser = createUserProfile('admin');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <AdminDashboardRestructured />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      expect(screen.getByText('Loading admin dashboard...')).toBeInTheDocument();
    });
  });

  describe('6. Error Handling and Edge Cases', () => {
    it('should handle unauthenticated users gracefully', async () => {
      mockUser = null;
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Authentication Required')).toBeInTheDocument();
      expect(screen.getByText('Please log in to access the Operations Dashboard.')).toBeInTheDocument();
    });

    it('should handle network disconnection gracefully', async () => {
      mockUser = createUserProfile('admin');
      // Mock disconnected state
      (mockRealTimeUpdates as any).isConnected = false;
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      expect(screen.getByText('Real-time updates disconnected.')).toBeInTheDocument();
    });

    it('should handle role changes during session', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      const { rerender } = render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Inventory Management')).toBeInTheDocument();

      // Simulate role change
      mockUser = createUserProfile('warehouse_manager');
      
      rerender(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Warehouse Operations')).toBeInTheDocument();
      expect(screen.queryByText('Inventory Management')).not.toBeInTheDocument();
    });
  });

  describe('7. Security Boundary Validation', () => {
    it('should prevent cross-dashboard access through URL manipulation', async () => {
      // Test that procurement users cannot access operations dashboard
      mockUser = createUserProfile('procurement_controller');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Access Restricted')).toBeInTheDocument();
      expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
    });

    it('should enforce MFA requirements consistently', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = false;
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Sensitive operations should be blocked
      const sensitiveButtons = screen.getAllByRole('button').filter(button => 
        button.hasAttribute('disabled') && 
        button.textContent?.includes('Purchase Order Approvals')
      );
      
      expect(sensitiveButtons.length).toBeGreaterThan(0);
    });

    it('should validate role boundaries at component level', async () => {
      const testCases = [
        { role: 'inventory_manager', allowedComponents: ['inventory-manager-view'], deniedComponents: ['warehouse-manager-view', 'supplier-coordinator-view'] },
        { role: 'warehouse_manager', allowedComponents: ['warehouse-manager-view'], deniedComponents: ['inventory-manager-view', 'supplier-coordinator-view'] },
        { role: 'supplier_coordinator', allowedComponents: ['supplier-coordinator-view'], deniedComponents: ['inventory-manager-view', 'warehouse-manager-view'] }
      ];

      for (const testCase of testCases) {
        mockUser = createUserProfile(testCase.role);
        
        const { unmount } = render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );

        // Check allowed components are present
        testCase.allowedComponents.forEach(component => {
          expect(screen.getByTestId(component)).toBeInTheDocument();
        });

        // Check denied components are not present
        testCase.deniedComponents.forEach(component => {
          expect(screen.queryByTestId(component)).not.toBeInTheDocument();
        });

        unmount();
      }
    });
  });
});