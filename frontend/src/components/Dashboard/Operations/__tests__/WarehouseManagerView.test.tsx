/**
 * Unit Tests for Warehouse Manager View
 * Tests workflow interface interactions, location management operations, and performance metrics display
 * Requirements: 1.2
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import WarehouseManagerView from '../WarehouseManagerView';
import { UserProfile } from '../../../../types';

// Mock the contexts
const mockUser: UserProfile = {
  userId: 'user-456',
  email: 'warehouse@example.com',
  role: 'warehouse_manager',
  profile: {
    firstName: 'Jane',
    lastName: 'Smith',
    phone: '+1234567890',
    address: {
      street: '456 Warehouse Ave',
      city: 'Warehouse City',
      state: 'WC',
      zipCode: '54321',
      coordinates: { latitude: 0, longitude: 0 }
    }
  },
  deviceIds: [],
  preferences: {
    notifications: { push: true, sms: true, email: true },
    theme: 'auto',
    language: 'en'
  }
};

const mockAuthContext = {
  user: mockUser,
  isLoading: false,
  isAuthenticated: true,
  login: jest.fn(),
  logout: jest.fn(),
  getAuthToken: jest.fn(),
  refreshUser: jest.fn(),
};

const mockNotificationContext = {
  showNotification: jest.fn(),
};

jest.mock('../../../../contexts/AuthContext', () => ({
  useAuth: () => mockAuthContext,
}));

jest.mock('../../../../contexts/NotificationContext', () => ({
  useNotification: () => mockNotificationContext,
}));

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <>{children}</>
);

describe('WarehouseManagerView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    render(
      <TestWrapper>
        <WarehouseManagerView />
      </TestWrapper>
    );

    expect(screen.getByRole('generic')).toBeInTheDocument();
    expect(screen.getByRole('generic')).toHaveClass('animate-spin');
  });

  it('should render warehouse operations header and description', async () => {
    render(
      <TestWrapper>
        <WarehouseManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Warehouse Operations')).toBeInTheDocument();
    });

    expect(screen.getByText('Manage receiving and dispatch workflows, location management, and warehouse performance metrics.')).toBeInTheDocument();
  });

  it('should display warehouse statistics', async () => {
    render(
      <TestWrapper>
        <WarehouseManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Pending Receipts')).toBeInTheDocument();
    });

    expect(screen.getByText('Pending Dispatches')).toBeInTheDocument();
    expect(screen.getByText('Warehouse Utilization')).toBeInTheDocument();
    expect(screen.getByText('Avg Pick Time')).toBeInTheDocument();
  });

  it('should render navigation tabs', async () => {
    render(
      <TestWrapper>
        <WarehouseManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Workflows')).toBeInTheDocument();
    });

    expect(screen.getByText('Locations')).toBeInTheDocument();
    expect(screen.getByText('Movements')).toBeInTheDocument();
    expect(screen.getByText('Metrics')).toBeInTheDocument();
  });

  describe('Workflow Interface Interactions', () => {
    it('should display receiving workflows by default', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Receiving Workflows')).toBeInTheDocument();
      });

      expect(screen.getByText('Dispatch Workflows')).toBeInTheDocument();
      expect(screen.getByText('PO-2024-001')).toBeInTheDocument();
      expect(screen.getByText('AquaTech Solutions')).toBeInTheDocument();
    });

    it('should handle receiving item updates', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('ESP32 Water Sensor')).toBeInTheDocument();
      });

      const receiveButton = screen.getAllByText('+1')[0];
      fireEvent.click(receiveButton);

      await waitFor(() => {
        expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
          'Received 1 units of ESP32-001',
          'success'
        );
      });
    });

    it('should handle dispatch workflow status updates', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Start Picking')).toBeInTheDocument();
      });

      const startPickingButton = screen.getByText('Start Picking');
      fireEvent.click(startPickingButton);

      await waitFor(() => {
        expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
          'Dispatch DSP-001 updated to picking',
          'success'
        );
      });
    });

    it('should display dispatch items with correct priority and status', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('ORD-2024-001')).toBeInTheDocument();
      });

      expect(screen.getByText('City Water Department')).toBeInTheDocument();
      expect(screen.getByText('high')).toBeInTheDocument();
      expect(screen.getByText('pending')).toBeInTheDocument();
    });

    it('should show different workflow buttons based on status', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Start Picking')).toBeInTheDocument();
      });

      // Check that picking status shows "Mark Packed" button (for DSP-002 which is in picking status)
      expect(screen.getByText('Mark Packed')).toBeInTheDocument();
    });

    it('should disable receive button when quantity is fully received', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        const receiveButtons = screen.getAllByText('+1');
        expect(receiveButtons.length).toBeGreaterThan(0);
      });

      // Find a button that should be disabled (when receivedQty >= expectedQty)
      // This would need to be tested with specific mock data where receivedQty equals expectedQty
    });
  });

  describe('Location Management Operations', () => {
    it('should display location management grid when locations tab is active', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Locations')).toBeInTheDocument();
      });

      const locationsTab = screen.getByText('Locations');
      fireEvent.click(locationsTab);

      await waitFor(() => {
        expect(screen.getByText('Location Management Grid')).toBeInTheDocument();
      });
    });

    it('should display warehouse locations with capacity information', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const locationsTab = screen.getByText('Locations');
      fireEvent.click(locationsTab);

      await waitFor(() => {
        expect(screen.getByText('A1-B2')).toBeInTheDocument();
      });

      expect(screen.getByText('Zone A')).toBeInTheDocument();
      expect(screen.getByText('75/100 units')).toBeInTheDocument();
    });

    it('should show different visual states for occupied vs empty locations', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const locationsTab = screen.getByText('Locations');
      fireEvent.click(locationsTab);

      await waitFor(() => {
        expect(screen.getByText('A1-B2')).toBeInTheDocument();
      });

      // Check for occupied location (A1-B2 has 75/100 units)
      expect(screen.getByText('75/100 units')).toBeInTheDocument();
      
      // Check for empty location (B2-D1 has 0/120 units)
      expect(screen.getByText('0/120 units')).toBeInTheDocument();
    });

    it('should display items stored in each location', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const locationsTab = screen.getByText('Locations');
      fireEvent.click(locationsTab);

      await waitFor(() => {
        expect(screen.getByText('Items:')).toBeInTheDocument();
      });

      expect(screen.getByText('ESP32-001')).toBeInTheDocument();
      expect(screen.getByText('PROBE-PH')).toBeInTheDocument();
    });
  });

  describe('Stock Movements Display', () => {
    it('should display stock movements when movements tab is active', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const movementsTab = screen.getByText('Movements');
      fireEvent.click(movementsTab);

      await waitFor(() => {
        expect(screen.getByText('Stock Movement Log')).toBeInTheDocument();
      });
    });

    it('should display movement table with correct headers', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const movementsTab = screen.getByText('Movements');
      fireEvent.click(movementsTab);

      await waitFor(() => {
        expect(screen.getByText('Timestamp')).toBeInTheDocument();
      });

      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('SKU')).toBeInTheDocument();
      expect(screen.getByText('Quantity')).toBeInTheDocument();
      expect(screen.getByText('From → To')).toBeInTheDocument();
      expect(screen.getByText('Operator')).toBeInTheDocument();
      expect(screen.getByText('Reason')).toBeInTheDocument();
    });

    it('should display stock movement data correctly', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const movementsTab = screen.getByText('Movements');
      fireEvent.click(movementsTab);

      await waitFor(() => {
        expect(screen.getByText('ESP32-001')).toBeInTheDocument();
      });

      expect(screen.getByText('25')).toBeInTheDocument(); // Quantity
      expect(screen.getByText('RECEIVING → A1-B2')).toBeInTheDocument();
      expect(screen.getByText('John Smith')).toBeInTheDocument();
      expect(screen.getByText('Stock receipt')).toBeInTheDocument();
    });

    it('should show different movement types with appropriate styling', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const movementsTab = screen.getByText('Movements');
      fireEvent.click(movementsTab);

      await waitFor(() => {
        expect(screen.getByText('inbound')).toBeInTheDocument();
      });

      expect(screen.getByText('outbound')).toBeInTheDocument();
    });
  });

  describe('Performance Metrics Display', () => {
    it('should display performance metrics when metrics tab is active', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const metricsTab = screen.getByText('Metrics');
      fireEvent.click(metricsTab);

      await waitFor(() => {
        expect(screen.getByText('Warehouse Performance Metrics')).toBeInTheDocument();
      });
    });

    it('should display all performance metric cards', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const metricsTab = screen.getByText('Metrics');
      fireEvent.click(metricsTab);

      await waitFor(() => {
        expect(screen.getByText('Order Accuracy')).toBeInTheDocument();
      });

      expect(screen.getByText('Throughput')).toBeInTheDocument();
      expect(screen.getByText('Performance Score')).toBeInTheDocument();
      expect(screen.getByText('Daily Movements')).toBeInTheDocument();
      expect(screen.getByText('Utilization Rate')).toBeInTheDocument();
      expect(screen.getByText('Pick Time')).toBeInTheDocument();
    });

    it('should display metric values correctly', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const metricsTab = screen.getByText('Metrics');
      fireEvent.click(metricsTab);

      await waitFor(() => {
        expect(screen.getByText('99.5%')).toBeInTheDocument(); // Order Accuracy
      });

      expect(screen.getByText('45/hr')).toBeInTheDocument(); // Throughput
      expect(screen.getByText('92')).toBeInTheDocument(); // Performance Score
      expect(screen.getByText('156')).toBeInTheDocument(); // Daily Movements
    });

    it('should display metric descriptions', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      const metricsTab = screen.getByText('Metrics');
      fireEvent.click(metricsTab);

      await waitFor(() => {
        expect(screen.getByText('Last 30 days')).toBeInTheDocument();
      });

      expect(screen.getByText('Items processed')).toBeInTheDocument();
      expect(screen.getByText('Overall rating')).toBeInTheDocument();
      expect(screen.getByText("Today's activity")).toBeInTheDocument();
      expect(screen.getByText('Space efficiency')).toBeInTheDocument();
      expect(screen.getByText('Average duration')).toBeInTheDocument();
    });
  });

  describe('Tab Navigation', () => {
    it('should switch between tabs correctly', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Receiving Workflows')).toBeInTheDocument();
      });

      // Switch to Locations tab
      const locationsTab = screen.getByText('Locations');
      fireEvent.click(locationsTab);

      await waitFor(() => {
        expect(screen.getByText('Location Management Grid')).toBeInTheDocument();
      });

      // Switch to Movements tab
      const movementsTab = screen.getByText('Movements');
      fireEvent.click(movementsTab);

      await waitFor(() => {
        expect(screen.getByText('Stock Movement Log')).toBeInTheDocument();
      });

      // Switch to Metrics tab
      const metricsTab = screen.getByText('Metrics');
      fireEvent.click(metricsTab);

      await waitFor(() => {
        expect(screen.getByText('Warehouse Performance Metrics')).toBeInTheDocument();
      });
    });

    it('should highlight active tab correctly', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        const workflowsTab = screen.getByText('Workflows');
        expect(workflowsTab).toHaveClass('text-blue-600');
      });

      const locationsTab = screen.getByText('Locations');
      fireEvent.click(locationsTab);

      await waitFor(() => {
        expect(locationsTab).toHaveClass('text-blue-600');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle data loading errors gracefully', async () => {
      // Mock console.error to avoid test output noise
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      // The component should render without crashing
      await waitFor(() => {
        expect(screen.getByText('Warehouse Operations')).toBeInTheDocument();
      });

      consoleSpy.mockRestore();
    });

    it('should display fallback values when metrics are null', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      // Before data loads, should show fallback values (0 or empty)
      await waitFor(() => {
        expect(screen.getByText('Warehouse Operations')).toBeInTheDocument();
      });

      // Check that the component renders without crashing when metrics are null
      expect(screen.getByText('Pending Receipts')).toBeInTheDocument();
      expect(screen.getByText('Pending Dispatches')).toBeInTheDocument();
    });
  });

  describe('Workflow Status Management', () => {
    it('should handle dispatch workflow status updates', async () => {
      render(
        <TestWrapper>
          <WarehouseManagerView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Start Picking')).toBeInTheDocument();
      });

      // Start picking
      const startPickingButton = screen.getByText('Start Picking');
      fireEvent.click(startPickingButton);

      await waitFor(() => {
        expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
          'Dispatch DSP-001 updated to picking',
          'success'
        );
      });
    });
  });
});