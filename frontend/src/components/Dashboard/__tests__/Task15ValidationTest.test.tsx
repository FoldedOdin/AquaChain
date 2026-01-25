/**
 * Task 15 Checkpoint Validation Test
 * 
 * Focused validation for the specific requirements of Task 15:
 * 1. Ensure all three dashboards render correctly for their respective roles
 * 2. Verify role boundaries are enforced in UI (no unauthorized components visible)
 * 3. Test user experience flows for all critical operations
 * 4. Validate <200ms perceived latency for all user interactions
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import OperationsDashboard from '../OperationsDashboard';
import ProcurementDashboard from '../ProcurementDashboard';
import AdminDashboardRestructured from '../AdminDashboardRestructured';
import { UserProfile } from '../../../types';

// Performance measurement
const measureRenderTime = async (renderFn: () => void): Promise<number> => {
  const startTime = performance.now();
  await act(async () => {
    renderFn();
  });
  const endTime = performance.now();
  return endTime - startTime;
};

// Mock all external dependencies
jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isLoading: mockIsLoading,
    isAuthenticated: !!mockUser,
    isMFAVerified: mockIsMFAVerified,
    requireMFA: jest.fn(),
    login: jest.fn(),
    logout: jest.fn(),
    getAuthToken: jest.fn(),
    refreshUser: jest.fn(),
  }),
}));

jest.mock('../../../contexts/NotificationContext', () => ({
  useNotification: () => ({
    showNotification: jest.fn(),
  }),
}));

jest.mock('../../../hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    data: { systemHealth: { uptime: 99.9, apiSuccess: 99.5 } },
    isLoading: false,
    error: null,
  }),
}));

jest.mock('../../../hooks/useRealTimeUpdates', () => ({
  useRealTimeUpdates: () => ({ isConnected: true }),
}));

jest.mock('../../../hooks/useNotifications', () => ({
  useNotifications: () => ({ notifications: [] }),
}));

jest.mock('../../../services/adminService', () => ({
  getAllUsers: jest.fn(() => Promise.resolve([])),
  getSystemConfiguration: jest.fn(() => Promise.resolve({
    alertThresholds: { global: { pH: { min: 6.5, max: 8.5 } } },
    systemLimits: { maxDevicesPerUser: 10 }
  })),
  updateSystemConfiguration: jest.fn(() => Promise.resolve({})),
  getSystemHealthMetrics: jest.fn(() => Promise.resolve({ criticalPathUptime: 99.9, apiUptime: 99.5 })),
  getPerformanceMetrics: jest.fn(() => Promise.resolve([])),
}));

// Mock child components with simple implementations
jest.mock('../Operations/InventoryManagerView', () => {
  return function MockInventoryManagerView() {
    return <div data-testid="inventory-manager-view">Inventory Manager Content</div>;
  };
});

jest.mock('../Operations/WarehouseManagerView', () => {
  return function MockWarehouseManagerView() {
    return <div data-testid="warehouse-manager-view">Warehouse Manager Content</div>;
  };
});

jest.mock('../Operations/SupplierCoordinatorView', () => {
  return function MockSupplierCoordinatorView() {
    return <div data-testid="supplier-coordinator-view">Supplier Coordinator Content</div>;
  };
});

jest.mock('../Procurement/ApprovalQueue', () => {
  return function MockApprovalQueue() {
    return <div data-testid="approval-queue">Approval Queue Content</div>;
  };
});

jest.mock('../Procurement/BudgetTracking', () => {
  return function MockBudgetTracking() {
    return <div data-testid="budget-tracking">Budget Tracking Content</div>;
  };
});

jest.mock('../Procurement/FinancialAuditLog', () => {
  return function MockFinancialAuditLog() {
    return <div data-testid="financial-audit-log">Financial Audit Log Content</div>;
  };
});

jest.mock('../DashboardLayout', () => {
  return function MockDashboardLayout({ children }: { children: React.ReactNode }) {
    return <div data-testid="dashboard-layout">{children}</div>;
  };
});

jest.mock('../NotificationCenter', () => {
  return function MockNotificationCenter() {
    return <div data-testid="notification-center">Notifications</div>;
  };
});

jest.mock('../DataExportModal', () => {
  return function MockDataExportModal({ isOpen }: { isOpen: boolean }) {
    return isOpen ? <div data-testid="data-export-modal">Export Modal</div> : null;
  };
});

// Test state variables
let mockUser: UserProfile | null = null;
let mockIsLoading = false;
let mockIsMFAVerified = false;

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

// Helper to create user profiles
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

describe('Task 15 Checkpoint Validation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUser = null;
    mockIsLoading = false;
    mockIsMFAVerified = false;
  });

  describe('1. Dashboard Rendering Validation', () => {
    it('Operations Dashboard renders correctly for Inventory Manager', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );
      });

      // Performance requirement: <200ms
      expect(renderTime).toBeLessThan(200);

      // Verify correct dashboard renders
      expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Inventory Management')).toBeInTheDocument();
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();

      // Verify unauthorized components are NOT present
      expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();
    });

    it('Operations Dashboard renders correctly for Warehouse Manager', async () => {
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

      // Verify unauthorized components are NOT present
      expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();
    });

    it('Operations Dashboard renders correctly for Supplier Coordinator', async () => {
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

      // Verify unauthorized components are NOT present
      expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
      expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
    });

    it('Procurement Dashboard renders correctly for Procurement Controller with MFA', async () => {
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
      expect(screen.getByTestId('approval-queue')).toBeInTheDocument();
    });

    it('Admin Dashboard renders correctly with system administration functions only', async () => {
      mockUser = createUserProfile('admin');
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <AdminDashboardRestructured />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      
      // Wait for component to fully render
      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      // Verify admin-specific tabs are present
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('User Management')).toBeInTheDocument();
      expect(screen.getByText('System Configuration')).toBeInTheDocument();

      // CRITICAL: Verify NO operational controls are present
      const forbiddenControls = [
        'Inventory Management',
        'Warehouse Operations',
        'Supplier Management',
        'Purchase Order Approvals'
      ];

      forbiddenControls.forEach(control => {
        expect(screen.queryByText(control)).not.toBeInTheDocument();
      });
    });
  });

  describe('2. Role Boundary Enforcement', () => {
    it('prevents unauthorized access to Operations Dashboard', async () => {
      const unauthorizedRoles = ['consumer', 'technician', 'admin', 'procurement_controller'];
      
      for (const role of unauthorizedRoles) {
        mockUser = createUserProfile(role);
        
        const { unmount } = render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );

        // Should show access restriction
        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
        expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();

        unmount();
      }
    });

    it('prevents unauthorized access to Procurement Dashboard', async () => {
      const unauthorizedRoles = ['consumer', 'technician', 'admin', 'inventory_manager'];
      
      for (const role of unauthorizedRoles) {
        mockUser = createUserProfile(role);
        
        const { unmount } = render(
          <TestWrapper>
            <ProcurementDashboard />
          </TestWrapper>
        );

        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
        expect(screen.queryByTestId('approval-queue')).not.toBeInTheDocument();

        unmount();
      }
    });

    it('enforces MFA requirements for sensitive operations', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = false;
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Should show MFA requirement
      expect(screen.getByText('Multi-Factor Authentication Required')).toBeInTheDocument();
    });
  });

  describe('3. User Experience Flow Validation', () => {
    it('handles tab switching in Operations Dashboard', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Verify initial state
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();
      
      // Since this user only has inventory_manager role, other tabs should not be available
      expect(screen.queryByText('Warehouse Operations')).not.toBeInTheDocument();
      expect(screen.queryByText('Supplier Management')).not.toBeInTheDocument();
    });

    it('handles admin dashboard navigation', async () => {
      mockUser = createUserProfile('admin');
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      });

      // Test tab navigation
      const userManagementTab = screen.getByText('User Management');
      expect(userManagementTab).toBeInTheDocument();

      // Click on tab
      userEvent.click(userManagementTab);

      // Should maintain responsive UI
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });
  });

  describe('4. Performance Requirements', () => {
    it('meets <200ms latency for all dashboard renders', async () => {
      const testCases = [
        { role: 'inventory_manager', component: OperationsDashboard },
        { role: 'warehouse_manager', component: OperationsDashboard },
        { role: 'supplier_coordinator', component: OperationsDashboard },
        { role: 'procurement_controller', component: ProcurementDashboard },
        { role: 'admin', component: AdminDashboardRestructured }
      ];

      for (const testCase of testCases) {
        mockUser = createUserProfile(testCase.role);
        if (testCase.role === 'procurement_controller') {
          mockIsMFAVerified = true;
        }

        const renderTime = await measureRenderTime(() => {
          render(
            <TestWrapper>
              <testCase.component />
            </TestWrapper>
          );
        });

        expect(renderTime).toBeLessThan(200);
      }
    });

    it('handles loading states efficiently', async () => {
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

  describe('5. Error Handling', () => {
    it('handles unauthenticated users gracefully', async () => {
      mockUser = null;
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Authentication Required')).toBeInTheDocument();
    });

    it('handles role changes during session', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      const { rerender } = render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();

      // Simulate role change
      mockUser = createUserProfile('warehouse_manager');
      
      rerender(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByTestId('warehouse-manager-view')).toBeInTheDocument();
      expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
    });
  });

  describe('6. Integration Completeness', () => {
    it('verifies all three dashboards can be rendered without errors', async () => {
      const dashboardTests = [
        { role: 'inventory_manager', dashboard: OperationsDashboard, expectedText: 'Operations Dashboard' },
        { role: 'procurement_controller', dashboard: ProcurementDashboard, expectedText: 'Procurement & Finance Dashboard' },
        { role: 'admin', dashboard: AdminDashboardRestructured, expectedText: 'Admin Dashboard' }
      ];

      for (const test of dashboardTests) {
        mockUser = createUserProfile(test.role);
        if (test.role === 'procurement_controller') {
          mockIsMFAVerified = true;
        }

        const { unmount } = render(
          <TestWrapper>
            <test.dashboard />
          </TestWrapper>
        );

        if (test.role === 'admin') {
          await waitFor(() => {
            expect(screen.getByText(test.expectedText)).toBeInTheDocument();
          });
        } else {
          expect(screen.getByText(test.expectedText)).toBeInTheDocument();
        }

        unmount();
      }
    });

    it('verifies role boundaries are consistently enforced', async () => {
      // Test that inventory managers cannot access procurement dashboard
      mockUser = createUserProfile('inventory_manager');
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Access Restricted')).toBeInTheDocument();
      expect(screen.queryByTestId('approval-queue')).not.toBeInTheDocument();
    });
  });
});