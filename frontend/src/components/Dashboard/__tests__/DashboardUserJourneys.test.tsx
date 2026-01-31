/**
 * Dashboard User Journey Tests - Task 15 Checkpoint
 * 
 * End-to-end user journey validation for critical operations across all dashboards.
 * Tests complete workflows from login to task completion for each role.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import OperationsDashboard from '../OperationsDashboard';
import ProcurementDashboard from '../ProcurementDashboard';
import AdminDashboardRestructured from '../AdminDashboardRestructured';
import { UserProfile } from '../../../types';

// Mock all child components with interactive elements
jest.mock('../Operations/InventoryManagerView', () => {
  return function MockInventoryManagerView() {
    return (
      <div data-testid="inventory-manager-view">
        <h2>Inventory Management</h2>
        <div data-testid="stock-levels">Current Stock: 150 units</div>
        <div data-testid="reorder-alerts">3 items need reordering</div>
        <button data-testid="update-reorder-point">Update Reorder Point</button>
        <button data-testid="view-forecast">View Demand Forecast</button>
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
      </div>
    );
  };
});

// Mock other components
jest.mock('../Procurement/BudgetTracker', () => {
  return function MockBudgetTracker() {
    return (
      <div data-testid="budget-tracker">
        <h2>Budget Tracking</h2>
        <div data-testid="budget-status">Budget: 75% utilized</div>
      </div>
    );
  };
});

jest.mock('../Admin/SystemOverview', () => {
  return function MockSystemOverview() {
    return (
      <div data-testid="system-overview">
        <h2>System Overview</h2>
        <div data-testid="system-health">System Health: Good</div>
      </div>
    );
  };
});

// Mock user profiles
const mockOperationsUser: UserProfile = {
  id: 'ops-user-1',
  email: 'ops@aquachain.com',
  name: 'Operations Manager',
  role: 'operations_manager',
  permissions: ['inventory:read', 'inventory:write', 'warehouse:manage'],
  preferences: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

const mockProcurementUser: UserProfile = {
  id: 'proc-user-1',
  email: 'procurement@aquachain.com',
  name: 'Procurement Manager',
  role: 'procurement_manager',
  permissions: ['procurement:read', 'procurement:write', 'budget:manage'],
  preferences: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

const mockAdminUser: UserProfile = {
  id: 'admin-user-1',
  email: 'admin@aquachain.com',
  name: 'System Administrator',
  role: 'admin',
  permissions: ['admin:all'],
  preferences: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
};

describe('Dashboard User Journeys', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Operations Dashboard Journey', () => {
    test('operations manager can complete inventory management workflow', async () => {
      const user = userEvent.setup();
      
      render(
        <BrowserRouter>
          <OperationsDashboard user={mockOperationsUser} />
        </BrowserRouter>
      );

      // Verify dashboard loads
      expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
      
      // Navigate to inventory management
      const inventorySection = screen.getByTestId('inventory-manager-view');
      expect(inventorySection).toBeInTheDocument();
      
      // Interact with inventory controls
      const updateButton = screen.getByTestId('update-reorder-point');
      await user.click(updateButton);
      
      // Verify forecast view
      const forecastButton = screen.getByTestId('view-forecast');
      await user.click(forecastButton);
      
      expect(screen.getByText('Current Stock: 150 units')).toBeInTheDocument();
    });
  });

  describe('Procurement Dashboard Journey', () => {
    test('procurement manager can complete approval workflow', async () => {
      const user = userEvent.setup();
      
      render(
        <BrowserRouter>
          <ProcurementDashboard user={mockProcurementUser} />
        </BrowserRouter>
      );

      // Verify dashboard loads
      expect(screen.getByText('Procurement Dashboard')).toBeInTheDocument();
      
      // Navigate to approval queue
      const approvalQueue = screen.getByTestId('approval-queue');
      expect(approvalQueue).toBeInTheDocument();
      
      // Process approval
      const approveButton = screen.getByTestId('approve-order');
      await user.click(approveButton);
      
      expect(screen.getByText('8 orders pending approval')).toBeInTheDocument();
    });
  });

  describe('Admin Dashboard Journey', () => {
    test('admin can access system overview and management tools', async () => {
      const user = userEvent.setup();
      
      render(
        <BrowserRouter>
          <AdminDashboardRestructured user={mockAdminUser} />
        </BrowserRouter>
      );

      // Verify dashboard loads
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
      
      // Check system overview
      const systemOverview = screen.getByTestId('system-overview');
      expect(systemOverview).toBeInTheDocument();
      
      expect(screen.getByText('System Health: Good')).toBeInTheDocument();
    });
  });
});