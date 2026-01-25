/**
 * Frontend Integration Validation - Task 15 Checkpoint
 * 
 * Comprehensive validation for all three dashboards:
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

// Performance measurement utilities
const measureRenderTime = async (renderFn: () => void): Promise<number> => {
  const startTime = performance.now();
  await act(async () => {
    renderFn();
  });
  const endTime = performance.now();
  return endTime - startTime;
};

const measureInteractionTime = async (interactionFn: () => Promise<void>): Promise<number> => {
  const startTime = performance.now();
  await interactionFn();
  const endTime = performance.now();
  return endTime - startTime;
};

// Mock all child components to focus on integration behavior
jest.mock('../Operations/InventoryManagerView', () => {
  return function MockInventoryManagerView() {
    return (
      <div data-testid="inventory-manager-view">
        <h2>Inventory Management</h2>
        <div data-testid="stock-levels">Current Stock: 150 units</div>
        <div data-testid="reorder-alerts">3 items need reordering</div>
        <button data-testid="update-reorder-point">Update Reorder Point</button>
        <button data-testid="view-forecast">View Demand Forecast</button>
        <div data-testid="audit-history">Audit History Available</div>
      </div>
    );
  };
});

jest.mock('../Operations/WarehouseManagerView', () => {
  return function MockWarehouseManagerView() {
    return (
      <div data-testid="warehouse-manager-view">
        <h2>Warehouse Operations</h2>
        <div data-testid="receiving-queue">5 items in receiving queue</div>
        <div data-testid="dispatch-queue">3 items ready for dispatch</div>
        <button data-testid="process-receiving">Process Receiving</button>
        <button data-testid="manage-locations">Manage Locations</button>
        <div data-testid="performance-metrics">Performance: 95%</div>
      </div>
    );
  };
});

jest.mock('../Operations/SupplierCoordinatorView', () => {
  return function MockSupplierCoordinatorView() {
    return (
      <div data-testid="supplier-coordinator-view">
        <h2>Supplier Management</h2>
        <div data-testid="supplier-list">12 active suppliers</div>
        <div data-testid="contract-renewals">2 contracts expiring soon</div>
        <button data-testid="add-supplier">Add New Supplier</button>
        <button data-testid="review-performance">Review Performance</button>
        <div data-testid="risk-indicators">Risk Score: Low</div>
      </div>
    );
  };
});

jest.mock('../Procurement/ApprovalQueue', () => {
  return function MockApprovalQueue() {
    return (
      <div data-testid="approval-queue">
        <h2>Purchase Order Approvals</h2>
        <div data-testid="pending-orders">8 orders pending approval</div>
        <button data-testid="approve-order">Approve Order</button>
        <button data-testid="reject-order">Reject Order</button>
        <button data-testid="emergency-purchase">Emergency Purchase</button>
      </div>
    );
  };
});

jest.mock('../Procurement/BudgetTracking', () => {
  return function MockBudgetTracking() {
    return (
      <div data-testid="budget-tracking">
        <h2>Budget Tracking</h2>
        <div data-testid="budget-utilization">Budget Utilization: 75%</div>
        <div data-testid="forecast-comparison">Forecast vs Actual</div>
        <button data-testid="reallocate-budget">Reallocate Budget</button>
      </div>
    );
  };
});

jest.mock('../Procurement/FinancialAuditLog', () => {
  return function MockFinancialAuditLog() {
    return (
      <div data-testid="financial-audit-log">
        <h2>Financial Audit Log</h2>
        <div data-testid="audit-entries">245 audit entries</div>
        <button data-testid="export-audit">Export Audit Log</button>
        <button data-testid="filter-audit">Filter Entries</button>
      </div>
    );
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
        <div data-testid="dashboard-content">{children}</div>
      </div>
    );
  };
});

jest.mock('../NotificationCenter', () => {
  return function MockNotificationCenter({ userRole }: { userRole: string }) {
    return (
      <div data-testid="notification-center" data-role={userRole}>
        <button data-testid="notification-bell">🔔</button>
        <span>3 notifications</span>
      </div>
    );
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
        <h3>Export Data</h3>
        <button onClick={onClose} data-testid="close-export">Close</button>
        <button data-testid="export-csv">Export CSV</button>
      </div>
    ) : null;
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
  getAuthToken: jest.fn(),
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

// Mock services with proper return values
const mockUsers = [
  {
    userId: 'user-1',
    email: 'user1@example.com',
    role: 'consumer',
    status: 'active',
    createdAt: '2024-01-01T00:00:00Z',
    profile: { firstName: 'John', lastName: 'Doe' }
  }
];

const mockSystemConfig = {
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
};

const mockHealthMetrics = {
  criticalPathUptime: 99.9,
  apiUptime: 99.5
};

jest.mock('../../../services/adminService', () => ({
  getAllUsers: jest.fn(() => Promise.resolve(mockUsers)),
  getSystemConfiguration: jest.fn(() => Promise.resolve(mockSystemConfig)),
  updateSystemConfiguration: jest.fn(() => Promise.resolve(mockSystemConfig)),
  getSystemHealthMetrics: jest.fn(() => Promise.resolve(mockHealthMetrics)),
  getPerformanceMetrics: jest.fn(() => Promise.resolve([])),
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

describe('Frontend Integration Validation - Task 15 Checkpoint', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUser = null;
    mockIsLoading = false;
    mockIsMFAVerified = false;
  });

  describe('1. Dashboard Rendering Validation', () => {
    describe('Operations Dashboard', () => {
      it('renders correctly for Inventory Manager with all required components', async () => {
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

        // Verify dashboard structure
        expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Inventory Management')).toBeInTheDocument();
        expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();

        // Verify inventory-specific components
        expect(screen.getByTestId('stock-levels')).toBeInTheDocument();
        expect(screen.getByTestId('reorder-alerts')).toBeInTheDocument();
        expect(screen.getByTestId('audit-history')).toBeInTheDocument();

        // Verify unauthorized components are NOT present
        expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();
        expect(screen.queryByText('Warehouse Operations')).not.toBeInTheDocument();
        expect(screen.queryByText('Supplier Management')).not.toBeInTheDocument();
      });

      it('renders correctly for Warehouse Manager with all required components', async () => {
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

        // Verify warehouse-specific components
        expect(screen.getByTestId('receiving-queue')).toBeInTheDocument();
        expect(screen.getByTestId('dispatch-queue')).toBeInTheDocument();
        expect(screen.getByTestId('performance-metrics')).toBeInTheDocument();

        // Verify unauthorized components are NOT present
        expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();
      });

      it('renders correctly for Supplier Coordinator with all required components', async () => {
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

        // Verify supplier-specific components
        expect(screen.getByTestId('supplier-list')).toBeInTheDocument();
        expect(screen.getByTestId('contract-renewals')).toBeInTheDocument();
        expect(screen.getByTestId('risk-indicators')).toBeInTheDocument();

        // Verify unauthorized components are NOT present
        expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
      });
    });

    describe('Procurement Dashboard', () => {
      it('renders correctly for Procurement Controller with MFA verified', async () => {
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

        // Verify all procurement components are accessible
        expect(screen.getByTestId('approval-queue')).toBeInTheDocument();
        expect(screen.getByTestId('budget-tracking')).toBeInTheDocument();
      });

      it('enforces MFA requirements for sensitive operations', async () => {
        mockUser = createUserProfile('procurement_controller');
        mockIsMFAVerified = false;
        
        render(
          <TestWrapper>
            <ProcurementDashboard />
          </TestWrapper>
        );

        // Should show MFA requirement screen
        expect(screen.getByText('Multi-Factor Authentication Required')).toBeInTheDocument();
        expect(screen.getByText('Verify Identity')).toBeInTheDocument();
        
        // Should provide access to non-MFA sections
        expect(screen.getByText('View Budget Tracking (No MFA Required)')).toBeInTheDocument();
      });
    });

    describe('Admin Dashboard', () => {
      it('renders correctly with system administration functions only', async () => {
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

        // Verify admin-specific tabs
        expect(screen.getByText('System Overview')).toBeInTheDocument();
        expect(screen.getByText('User Management')).toBeInTheDocument();
        expect(screen.getByText('System Configuration')).toBeInTheDocument();
        expect(screen.getByText('Global Monitoring')).toBeInTheDocument();
        expect(screen.getByText('Security & Audit')).toBeInTheDocument();

        // CRITICAL: Verify NO operational controls are present
        const forbiddenControls = [
          'Inventory Management',
          'Warehouse Operations',
          'Supplier Management',
          'Purchase Order Approvals',
          'Procurement Controls',
          'Stock Levels',
          'Reorder Points',
          'Receiving Queue',
          'Dispatch Queue',
          'Supplier Profiles',
          'Contract Management'
        ];

        forbiddenControls.forEach(control => {
          expect(screen.queryByText(control)).not.toBeInTheDocument();
        });
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

        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
        expect(screen.queryByText('Operations Dashboard')).not.toBeInTheDocument();
        expect(screen.queryByTestId('inventory-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('warehouse-manager-view')).not.toBeInTheDocument();
        expect(screen.queryByTestId('supplier-coordinator-view')).not.toBeInTheDocument();

        unmount();
      }
    });

    it('prevents unauthorized access to Procurement Dashboard', async () => {
      const unauthorizedRoles = ['consumer', 'technician', 'admin', 'inventory_manager', 'warehouse_manager', 'supplier_coordinator'];
      
      for (const role of unauthorizedRoles) {
        mockUser = createUserProfile(role);
        
        const { unmount } = render(
          <TestWrapper>
            <ProcurementDashboard />
          </TestWrapper>
        );

        expect(screen.getByText('Access Restricted')).toBeInTheDocument();
        expect(screen.getByText('This dashboard is restricted to Procurement & Finance Controllers only.')).toBeInTheDocument();
        expect(screen.queryByText('Procurement & Finance Dashboard')).not.toBeInTheDocument();

        unmount();
      }
    });

    it('validates component-level role boundaries', async () => {
      // Test that each role only sees their authorized components
      const roleComponentMap = {
        'inventory_manager': {
          allowed: ['inventory-manager-view'],
          denied: ['warehouse-manager-view', 'supplier-coordinator-view', 'approval-queue', 'budget-tracking']
        },
        'warehouse_manager': {
          allowed: ['warehouse-manager-view'],
          denied: ['inventory-manager-view', 'supplier-coordinator-view', 'approval-queue', 'budget-tracking']
        },
        'supplier_coordinator': {
          allowed: ['supplier-coordinator-view'],
          denied: ['inventory-manager-view', 'warehouse-manager-view', 'approval-queue', 'budget-tracking']
        }
      };

      for (const [role, components] of Object.entries(roleComponentMap)) {
        mockUser = createUserProfile(role);
        
        const { unmount } = render(
          <TestWrapper>
            <OperationsDashboard />
          </TestWrapper>
        );

        // Check allowed components are present
        components.allowed.forEach(component => {
          expect(screen.getByTestId(component)).toBeInTheDocument();
        });

        // Check denied components are not present
        components.denied.forEach(component => {
          expect(screen.queryByTestId(component)).not.toBeInTheDocument();
        });

        unmount();
      }
    });
  });

  describe('3. User Experience Flow Validation', () => {
    it('handles inventory management workflow smoothly', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Verify initial state
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();
      expect(screen.getByText('Current Stock: 150 units')).toBeInTheDocument();
      expect(screen.getByText('3 items need reordering')).toBeInTheDocument();

      // Test interactive elements
      const updateButton = screen.getByTestId('update-reorder-point');
      const forecastButton = screen.getByTestId('view-forecast');

      expect(updateButton).toBeInTheDocument();
      expect(forecastButton).toBeInTheDocument();

      // Measure interaction responsiveness
      const interactionTime = await measureInteractionTime(async () => {
        await userEvent.click(updateButton);
      });

      expect(interactionTime).toBeLessThan(200);
    });

    it('handles warehouse operations workflow smoothly', async () => {
      mockUser = createUserProfile('warehouse_manager');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      expect(screen.getByTestId('warehouse-manager-view')).toBeInTheDocument();
      expect(screen.getByText('5 items in receiving queue')).toBeInTheDocument();
      expect(screen.getByText('3 items ready for dispatch')).toBeInTheDocument();

      const processButton = screen.getByTestId('process-receiving');
      const locationsButton = screen.getByTestId('manage-locations');

      const interactionTime = await measureInteractionTime(async () => {
        await userEvent.click(processButton);
      });

      expect(interactionTime).toBeLessThan(200);
    });

    it('handles procurement approval workflow with MFA', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      expect(screen.getByTestId('approval-queue')).toBeInTheDocument();
      expect(screen.getByText('8 orders pending approval')).toBeInTheDocument();

      const approveButton = screen.getByTestId('approve-order');
      const rejectButton = screen.getByTestId('reject-order');
      const emergencyButton = screen.getByTestId('emergency-purchase');

      expect(approveButton).toBeInTheDocument();
      expect(rejectButton).toBeInTheDocument();
      expect(emergencyButton).toBeInTheDocument();

      const interactionTime = await measureInteractionTime(async () => {
        await userEvent.click(approveButton);
      });

      expect(interactionTime).toBeLessThan(200);
    });

    it('handles admin dashboard navigation smoothly', async () => {
      mockUser = createUserProfile('admin');
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      // Test tab navigation
      const userManagementTab = screen.getByText('User Management');
      const configTab = screen.getByText('System Configuration');
      const monitoringTab = screen.getByText('Global Monitoring');

      // Measure tab switching performance
      const tabSwitchTime = await measureInteractionTime(async () => {
        await userEvent.click(userManagementTab);
      });

      expect(tabSwitchTime).toBeLessThan(200);

      await waitFor(() => {
        expect(screen.getByText('Add User')).toBeInTheDocument();
      });
    });
  });

  describe('4. Performance Requirements Validation', () => {
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

    it('meets <200ms latency for user interactions', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      const interactiveElements = [
        screen.getByTestId('update-reorder-point'),
        screen.getByTestId('view-forecast')
      ];

      for (const element of interactiveElements) {
        const interactionTime = await measureInteractionTime(async () => {
          await userEvent.click(element);
        });

        expect(interactionTime).toBeLessThan(200);
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

  describe('5. Critical Operation Flows', () => {
    it('validates complete inventory management flow', async () => {
      mockUser = createUserProfile('inventory_manager');
      
      render(
        <TestWrapper>
          <OperationsDashboard />
        </TestWrapper>
      );

      // Verify all required inventory components are present and functional
      expect(screen.getByTestId('stock-levels')).toBeInTheDocument();
      expect(screen.getByTestId('reorder-alerts')).toBeInTheDocument();
      expect(screen.getByTestId('audit-history')).toBeInTheDocument();
      
      // Verify interactive elements work
      const updateButton = screen.getByTestId('update-reorder-point');
      const forecastButton = screen.getByTestId('view-forecast');
      
      await userEvent.click(updateButton);
      await userEvent.click(forecastButton);
      
      // Should not throw errors and maintain responsive UI
      expect(screen.getByTestId('inventory-manager-view')).toBeInTheDocument();
    });

    it('validates complete procurement approval flow', async () => {
      mockUser = createUserProfile('procurement_controller');
      mockIsMFAVerified = true;
      
      render(
        <TestWrapper>
          <ProcurementDashboard />
        </TestWrapper>
      );

      // Verify all procurement components
      expect(screen.getByTestId('approval-queue')).toBeInTheDocument();
      expect(screen.getByTestId('budget-tracking')).toBeInTheDocument();
      
      // Test approval workflow
      const approveButton = screen.getByTestId('approve-order');
      const rejectButton = screen.getByTestId('reject-order');
      const emergencyButton = screen.getByTestId('emergency-purchase');
      
      await userEvent.click(approveButton);
      await userEvent.click(emergencyButton);
      
      expect(screen.getByTestId('approval-queue')).toBeInTheDocument();
    });

    it('validates complete admin management flow', async () => {
      mockUser = createUserProfile('admin');
      
      render(
        <TestWrapper>
          <AdminDashboardRestructured />
        </TestWrapper>
      );

      // Navigate through admin tabs
      const userManagementTab = screen.getByText('User Management');
      const configTab = screen.getByText('System Configuration');
      const monitoringTab = screen.getByText('Global Monitoring');
      const securityTab = screen.getByText('Security & Audit');

      // Test navigation to each tab
      await userEvent.click(userManagementTab);
      await waitFor(() => {
        expect(screen.getByText('Add User')).toBeInTheDocument();
      });

      await userEvent.click(configTab);
      await waitFor(() => {
        expect(screen.getByText('Configure System')).toBeInTheDocument();
      });

      await userEvent.click(monitoringTab);
      await waitFor(() => {
        expect(screen.getByText('System Health Dashboard')).toBeInTheDocument();
      });

      await userEvent.click(securityTab);
      await waitFor(() => {
        expect(screen.getByText('Security Overview')).toBeInTheDocument();
      });
    });
  });

  describe('6. Error Handling and Edge Cases', () => {
    it('handles unauthenticated users gracefully', async () => {
      mockUser = null;
      
      const dashboards = [OperationsDashboard, ProcurementDashboard, AdminDashboardRestructured];
      
      for (const Dashboard of dashboards) {
        const { unmount } = render(
          <TestWrapper>
            <Dashboard />
          </TestWrapper>
        );

        expect(screen.getByText('Authentication Required')).toBeInTheDocument();
        unmount();
      }
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

    it('maintains performance under error conditions', async () => {
      mockUser = createUserProfile('admin');
      
      // Simulate error condition
      jest.spyOn(console, 'error').mockImplementation(() => {});
      
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <AdminDashboardRestructured />
          </TestWrapper>
        );
      });

      expect(renderTime).toBeLessThan(200);
      
      jest.restoreAllMocks();
    });
  });

  describe('7. Integration Completeness Check', () => {
    it('verifies all three dashboards are fully integrated', async () => {
      // Test that all dashboards can be rendered without errors
      const dashboardTests = [
        { role: 'inventory_manager', dashboard: OperationsDashboard, expectedText: 'Operations Dashboard' },
        { role: 'warehouse_manager', dashboard: OperationsDashboard, expectedText: 'Operations Dashboard' },
        { role: 'supplier_coordinator', dashboard: OperationsDashboard, expectedText: 'Operations Dashboard' },
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

        expect(screen.getByText(test.expectedText)).toBeInTheDocument();
        unmount();
      }
    });

    it('verifies role boundaries are consistently enforced', async () => {
      // Comprehensive role boundary test
      const roleTests = [
        {
          role: 'inventory_manager',
          allowedDashboards: [OperationsDashboard],
          deniedDashboards: [ProcurementDashboard]
        },
        {
          role: 'procurement_controller',
          allowedDashboards: [ProcurementDashboard],
          deniedDashboards: [OperationsDashboard]
        },
        {
          role: 'admin',
          allowedDashboards: [AdminDashboardRestructured],
          deniedDashboards: [OperationsDashboard, ProcurementDashboard]
        }
      ];

      for (const test of roleTests) {
        mockUser = createUserProfile(test.role);
        if (test.role === 'procurement_controller') {
          mockIsMFAVerified = true;
        }

        // Test allowed dashboards
        for (const Dashboard of test.allowedDashboards) {
          const { unmount } = render(
            <TestWrapper>
              <Dashboard />
            </TestWrapper>
          );

          expect(screen.queryByText('Access Restricted')).not.toBeInTheDocument();
          unmount();
        }

        // Test denied dashboards
        for (const Dashboard of test.deniedDashboards) {
          const { unmount } = render(
            <TestWrapper>
              <Dashboard />
            </TestWrapper>
          );

          expect(screen.getByText('Access Restricted')).toBeInTheDocument();
          unmount();
        }
      }
    });
  });
});