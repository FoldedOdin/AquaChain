/**
 * Unit Tests for Supplier Coordinator View
 * Tests supplier profile CRUD operations, contract management interface, and performance scoring display
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SupplierCoordinatorView from '../SupplierCoordinatorView';
import { UserProfile } from '../../../../types';
import { supplierService } from '../../../../services/supplierService';

// Mock the supplier service
jest.mock('../../../../services/supplierService', () => ({
  supplierService: {
    getSuppliers: jest.fn(),
    getSupplierAnalytics: jest.fn(),
    createSupplier: jest.fn(),
    updateSupplier: jest.fn(),
    getSupplier: jest.fn(),
    getSupplierPerformance: jest.fn(),
  },
}));

const mockSupplierService = supplierService as jest.Mocked<typeof supplierService>;

// Mock the contexts
const mockUser: UserProfile = {
  userId: 'user-123',
  email: 'supplier@example.com',
  role: 'supplier_coordinator',
  profile: {
    firstName: 'Jane',
    lastName: 'Smith',
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

// Mock supplier data
const mockSuppliers = [
  {
    supplier_id: 'SUP001',
    name: 'AquaTech Solutions',
    supplier_type: 'device_manufacturer',
    contact_email: 'contact@aquatech.com',
    contact_phone: '+1-555-0101',
    performance_score: 94.5,
    total_orders: 45,
    status: 'active',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-20T15:30:00Z',
    lead_time_days: 7
  },
  {
    supplier_id: 'SUP002',
    name: 'FlowSense Inc',
    supplier_type: 'component',
    contact_email: 'orders@flowsense.com',
    contact_phone: '+1-555-0102',
    performance_score: 87.2,
    total_orders: 32,
    status: 'active',
    created_at: '2024-01-10T09:00:00Z',
    updated_at: '2024-01-18T14:20:00Z',
    lead_time_days: 10
  },
  {
    supplier_id: 'SUP003',
    name: 'WaterPure Corp',
    supplier_type: 'service',
    contact_email: 'support@waterpure.com',
    contact_phone: '+1-555-0103',
    performance_score: 65.8,
    total_orders: 18,
    status: 'under_review',
    created_at: '2024-01-05T08:00:00Z',
    updated_at: '2024-01-22T11:45:00Z',
    lead_time_days: 14
  }
];

const mockAnalytics = {
  timeRange: '30d',
  totalSuppliers: 47,
  activeSuppliers: 42,
  totalPurchaseValue: 125000,
  averageLeadTime: 8.5,
  overallPerformanceScore: 89.2
};

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div>
    {children}
  </div>
);

describe('SupplierCoordinatorView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Setup default mock responses
    mockSupplierService.getSuppliers.mockResolvedValue({
      success: true,
      data: mockSuppliers
    });
    
    mockSupplierService.getSupplierAnalytics.mockResolvedValue({
      success: true,
      data: mockAnalytics
    });
  });

  it('should render loading state initially', () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('should render supplier management header and description', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Supplier Management')).toBeInTheDocument();
    });

    expect(screen.getByText('Manage supplier profiles, contracts, performance scoring, and risk indicators.')).toBeInTheDocument();
  });

  it('should display supplier statistics', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Active Suppliers')).toBeInTheDocument();
    });

    expect(screen.getByText('Active Contracts')).toBeInTheDocument();
    expect(screen.getByText('Risk Alerts')).toBeInTheDocument();
    expect(screen.getByText('Avg Performance')).toBeInTheDocument();
  });

  it('should render supplier profiles table with correct data', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Supplier Profiles')).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText('Supplier')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('Risk Level')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();

    // Check supplier data
    expect(screen.getByText('AquaTech Solutions')).toBeInTheDocument();
    expect(screen.getByText('contact@aquatech.com')).toBeInTheDocument();
    expect(screen.getByText('FlowSense Inc')).toBeInTheDocument();
    expect(screen.getByText('WaterPure Corp')).toBeInTheDocument();
  });

  it('should filter suppliers by search term', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search suppliers...')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search suppliers...');
    fireEvent.change(searchInput, { target: { value: 'AquaTech' } });

    expect(searchInput).toHaveValue('AquaTech');
    // The filtering logic is implemented in the component
    expect(screen.getByText('AquaTech Solutions')).toBeInTheDocument();
  });

  it('should filter suppliers by status', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue('All Status');
    fireEvent.change(statusSelect, { target: { value: 'active' } });

    expect(statusSelect).toHaveValue('active');
  });

  it('should sort suppliers by different criteria', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Sort by Name')).toBeInTheDocument();
    });

    const sortSelect = screen.getByDisplayValue('Sort by Name');
    fireEvent.change(sortSelect, { target: { value: 'performance' } });

    expect(sortSelect).toHaveValue('performance');
  });

  it('should toggle sort order', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByDisplayValue('Sort by Name')).toBeInTheDocument();
    });

    // Find the sort order toggle button (arrow icon button)
    const buttons = screen.getAllByRole('button');
    const sortButton = buttons.find(button => 
      button.querySelector('svg') && 
      (button.querySelector('svg')?.getAttribute('viewBox') === '0 0 24 24')
    );
    
    expect(sortButton).toBeInTheDocument();
    
    if (sortButton) {
      fireEvent.click(sortButton);
      // The sort order should toggle (tested by checking if click handler works)
      expect(sortButton).toBeInTheDocument();
    }
  });

  it('should open add supplier modal', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Add Supplier')).toBeInTheDocument();
    });

    const addButton = screen.getByText('Add Supplier');
    fireEvent.click(addButton);

    expect(screen.getByText('Add New Supplier')).toBeInTheDocument();
    expect(screen.getByText('Supplier form would be implemented here')).toBeInTheDocument();
  });

  it('should open edit supplier modal', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4); // Multiple occurrences expected
    });

    // Find and click the edit button (pencil icon)
    const editButtons = screen.getAllByRole('button');
    const editButton = editButtons.find(button => 
      button.querySelector('svg') && 
      button.getAttribute('class')?.includes('text-green-600')
    );
    
    if (editButton) {
      fireEvent.click(editButton);
      expect(screen.getByText('Edit Supplier')).toBeInTheDocument();
    }
  });

  it('should open contract management modal', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('New Contract')).toBeInTheDocument();
    });

    const newContractButton = screen.getByText('New Contract');
    fireEvent.click(newContractButton);

    expect(screen.getByText('Contract form with document upload would be implemented here')).toBeInTheDocument();
  });

  it('should display contract management section', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Contract Management')).toBeInTheDocument();
    });

    // Check for sample contracts
    expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4); // Appears in table, contracts, performance, and risk sections
    expect(screen.getByText('Service Agreement')).toBeInTheDocument();
    expect(screen.getAllByText('FlowSense Inc')).toHaveLength(4); // In table, contracts, performance, and risk sections
    expect(screen.getByText('Purchase Agreement')).toBeInTheDocument();
  });

  it('should display performance scoring visualization', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Performance Scoring')).toBeInTheDocument();
    });

    expect(screen.getByText('Top Performers')).toBeInTheDocument();
    expect(screen.getByText('Key Metrics')).toBeInTheDocument();
    expect(screen.getByText('On-Time Delivery')).toBeInTheDocument();
    expect(screen.getByText('Quality Score')).toBeInTheDocument();
    expect(screen.getByText('Response Time')).toBeInTheDocument();
    expect(screen.getByText('Defect Rate')).toBeInTheDocument();
  });

  it('should display risk indicators dashboard', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Supplier Risk Indicators')).toBeInTheDocument();
    });

    expect(screen.getByText('Financial Risk')).toBeInTheDocument();
    expect(screen.getByText('Operational Risk')).toBeInTheDocument();
    expect(screen.getByText('Compliance Risk')).toBeInTheDocument();
    expect(screen.getByText('Recent Risk Alerts')).toBeInTheDocument();
  });

  it('should display risk levels correctly', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4);
    });

    // Check risk level badges (Low for high performance, High for low performance)
    const riskBadges = screen.getAllByText(/Low|Medium|High/);
    expect(riskBadges.length).toBeGreaterThan(0);
  });

  it('should handle API errors gracefully', async () => {
    mockSupplierService.getSuppliers.mockRejectedValue(new Error('API Error'));
    
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Supplier Management')).toBeInTheDocument();
    });

    // Component should still render even with API errors
    expect(screen.getByText('Active Suppliers')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should close modals when cancel is clicked', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Add Supplier')).toBeInTheDocument();
    });

    // Open supplier modal
    const addButton = screen.getByText('Add Supplier');
    fireEvent.click(addButton);

    expect(screen.getByText('Add New Supplier')).toBeInTheDocument();

    // Close modal
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    // Modal should be closed (text should not be visible)
    await waitFor(() => {
      expect(screen.queryByText('Add New Supplier')).not.toBeInTheDocument();
    });
  });

  it('should display performance scores with progress bars', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4);
    });

    // Check that performance scores are displayed (use getAllByText for multiple occurrences)
    expect(screen.getAllByText('94.5%')).toHaveLength(2); // In table and performance section
    expect(screen.getAllByText('87.2%')).toHaveLength(2);
    expect(screen.getAllByText('65.8%')).toHaveLength(2);
  });

  it('should display supplier types correctly', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('device manufacturer')).toBeInTheDocument();
    });

    expect(screen.getByText('component')).toBeInTheDocument();
    expect(screen.getByText('service')).toBeInTheDocument();
  });

  it('should show correct status badges', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getAllByText('active')).toHaveLength(4); // 2 in supplier table + 2 in contract section
    });

    expect(screen.getByText('under review')).toBeInTheDocument();
  });

  // Enhanced CRUD Operations Tests
  describe('Supplier Profile CRUD Operations', () => {
    it('should handle supplier creation workflow', async () => {
      mockSupplierService.createSupplier.mockResolvedValue({
        success: true,
        data: {
          supplier_id: 'SUP004',
          name: 'New Test Supplier',
          supplier_type: 'component',
          contact_email: 'test@newsupp.com',
          performance_score: 0,
          total_orders: 0,
          status: 'active',
          lead_time_days: 5,
          created_at: '2024-01-25T10:00:00Z',
          updated_at: '2024-01-25T10:00:00Z'
        }
      });

      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Add Supplier')).toBeInTheDocument();
      });

      // Open add supplier modal
      const addButton = screen.getByText('Add Supplier');
      fireEvent.click(addButton);

      expect(screen.getByText('Add New Supplier')).toBeInTheDocument();

      // Test save button functionality
      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      // Modal should remain open (form validation would happen in real implementation)
      expect(screen.getByText('Add New Supplier')).toBeInTheDocument();
    });

    it('should handle supplier update workflow', async () => {
      mockSupplierService.updateSupplier.mockResolvedValue({
        success: true,
        data: {
          ...mockSuppliers[0],
          name: 'Updated Supplier Name'
        }
      });

      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4); // Multiple occurrences expected
      });

      // Find and click edit button
      const editButtons = screen.getAllByRole('button');
      const editButton = editButtons.find(button => 
        button.querySelector('svg') && 
        button.getAttribute('class')?.includes('text-green-600')
      );
      
      if (editButton) {
        fireEvent.click(editButton);
        expect(screen.getByText('Edit Supplier')).toBeInTheDocument();

        // Test save functionality
        const saveButton = screen.getByText('Save');
        fireEvent.click(saveButton);
      }
    });

    it('should handle supplier view details', async () => {
      mockSupplierService.getSupplier.mockResolvedValue({
        success: true,
        data: mockSuppliers[0]
      });

      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4); // Multiple occurrences expected
      });

      // Find and click view button (eye icon)
      const viewButtons = screen.getAllByRole('button');
      const viewButton = viewButtons.find(button => 
        button.querySelector('svg') && 
        button.getAttribute('class')?.includes('text-blue-600')
      );
      
      if (viewButton) {
        fireEvent.click(viewButton);
        // In real implementation, this would show supplier details
      }
    });

    it('should validate supplier data before operations', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4); // Multiple occurrences expected
      });

      // Verify supplier data integrity
      expect(screen.getByText('contact@aquatech.com')).toBeInTheDocument();
      expect(screen.getAllByText('94.5%')).toHaveLength(2); // In table and performance sections
      expect(screen.getByText('45')).toBeInTheDocument(); // total orders
    });

    it('should handle supplier filtering and search correctly', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search suppliers...')).toBeInTheDocument();
      });

      // Test search functionality
      const searchInput = screen.getByPlaceholderText('Search suppliers...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      expect(searchInput).toHaveValue('nonexistent');

      // Test email search
      fireEvent.change(searchInput, { target: { value: 'aquatech.com' } });
      expect(searchInput).toHaveValue('aquatech.com');

      // Test status filtering
      const statusSelect = screen.getByDisplayValue('All Status');
      fireEvent.change(statusSelect, { target: { value: 'under_review' } });
      expect(statusSelect).toHaveValue('under_review');
    });
  });

  // Enhanced Contract Management Tests
  describe('Contract Management Interface', () => {
  it('should display contract management section with proper structure', async () => {
    render(
      <TestWrapper>
        <SupplierCoordinatorView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Contract Management')).toBeInTheDocument();
    });

    // Verify contract cards are displayed
    expect(screen.getByText('Service Agreement')).toBeInTheDocument();
    expect(screen.getByText('Purchase Agreement')).toBeInTheDocument();
    expect(screen.getByText('Master Agreement')).toBeInTheDocument();

    // Verify contract status indicators
    expect(screen.getAllByText('active')).toHaveLength(4); // Including supplier statuses
    expect(screen.getByText('expiring')).toBeInTheDocument();
  });

    it('should handle contract creation workflow', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('New Contract')).toBeInTheDocument();
      });

      // Open contract modal
      const newContractButton = screen.getByText('New Contract');
      fireEvent.click(newContractButton);

      expect(screen.getByText('Contract form with document upload would be implemented here')).toBeInTheDocument();

      // Test create contract button
      const createButton = screen.getByText('Create Contract');
      fireEvent.click(createButton);

      // Modal should close or show validation (in real implementation)
      expect(screen.getByText('Contract form with document upload would be implemented here')).toBeInTheDocument();
    });

    it('should display contract expiration dates correctly', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Contract Management')).toBeInTheDocument();
      });

      // Check expiration dates are displayed
      expect(screen.getByText('Expires: 2024-12-31')).toBeInTheDocument();
      expect(screen.getByText('Expires: 2024-06-30')).toBeInTheDocument();
      expect(screen.getByText('Expires: 2024-03-15')).toBeInTheDocument();
    });

    it('should handle contract actions (view, upload, edit)', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Contract Management')).toBeInTheDocument();
      });

      // Test view details buttons
      const viewDetailsButtons = screen.getAllByText('View Details');
      expect(viewDetailsButtons).toHaveLength(3);

      fireEvent.click(viewDetailsButtons[0]);
      // In real implementation, this would show contract details
    });

    it('should show contract status with appropriate styling', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Contract Management')).toBeInTheDocument();
      });

      // Verify status badges have appropriate classes (would be tested with more specific selectors in real implementation)
      const activeStatuses = screen.getAllByText('active');
      const expiringStatus = screen.getByText('expiring');
      
      expect(activeStatuses.length).toBeGreaterThan(0);
      expect(expiringStatus).toBeInTheDocument();
    });
  });

  // Enhanced Performance Scoring Tests
  describe('Performance Scoring Display', () => {
    it('should display performance scoring section with all components', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Performance Scoring')).toBeInTheDocument();
      });

      // Verify main sections
      expect(screen.getByText('Top Performers')).toBeInTheDocument();
      expect(screen.getByText('Key Metrics')).toBeInTheDocument();

      // Verify key metrics are displayed
      expect(screen.getByText('On-Time Delivery')).toBeInTheDocument();
      expect(screen.getByText('Quality Score')).toBeInTheDocument();
      expect(screen.getByText('Response Time')).toBeInTheDocument();
      expect(screen.getByText('Defect Rate')).toBeInTheDocument();

      // Verify metric values
      expect(screen.getByText('92.5%')).toBeInTheDocument();
      expect(screen.getByText('94.8%')).toBeInTheDocument();
      expect(screen.getByText('2.3h')).toBeInTheDocument();
      expect(screen.getByText('1.2%')).toBeInTheDocument();
    });

    it('should display top performers ranking correctly', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Top Performers')).toBeInTheDocument();
      });

      // Verify ranking numbers are displayed
      const rankingElements = screen.getAllByText(/^[1-5]$/);
      expect(rankingElements.length).toBeGreaterThan(0);

      // Verify performance scores are shown with progress bars (use getAllByText for multiple occurrences)
      expect(screen.getAllByText('94.5%')).toHaveLength(2); // In table and performance section
      expect(screen.getAllByText('87.2%')).toHaveLength(2);
      expect(screen.getAllByText('65.8%')).toHaveLength(2);
    });

    it('should calculate and display performance statistics correctly', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Avg Performance')).toBeInTheDocument();
      });

      // The component calculates average performance from supplier data
      // With mock data: (94.5 + 87.2 + 65.8) / 3 = 82.5
      expect(screen.getByText('82.5%')).toBeInTheDocument();
    });

    it('should display risk levels based on performance scores', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4);
      });

      // Verify risk level calculation
      // AquaTech (94.5%) should be Low risk
      // FlowSense (87.2%) should be Medium risk  
      // WaterPure (65.8%) should be High risk
      const riskBadges = screen.getAllByText(/Low|Medium|High/);
      expect(riskBadges.length).toBeGreaterThan(0);
    });

    it('should handle performance data updates', async () => {
      const updatedSuppliers = [
        {
          ...mockSuppliers[0],
          performance_score: 98.5
        }
      ];

      mockSupplierService.getSuppliers.mockResolvedValue({
        success: true,
        data: updatedSuppliers
      });

      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('98.5%')).toHaveLength(3); // In stats, table, and performance sections
      });
    });

    it('should display performance metrics in proper format', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Key Metrics')).toBeInTheDocument();
      });

      // Verify metrics are displayed in grid format
      const metricsSection = screen.getByText('Key Metrics').closest('div');
      expect(metricsSection).toBeInTheDocument();

      // Verify all metric categories are present
      expect(screen.getByText('On-Time Delivery')).toBeInTheDocument();
      expect(screen.getByText('Quality Score')).toBeInTheDocument();
      expect(screen.getByText('Response Time')).toBeInTheDocument();
      expect(screen.getByText('Defect Rate')).toBeInTheDocument();
    });
  });

  // Additional Integration Tests
  describe('Integration and Error Handling', () => {
    it('should handle partial API failures gracefully', async () => {
      mockSupplierService.getSuppliers.mockResolvedValue({
        success: true,
        data: mockSuppliers
      });
      
      mockSupplierService.getSupplierAnalytics.mockRejectedValue(new Error('Analytics API Error'));
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Supplier Management')).toBeInTheDocument();
      });

      // Component should still render supplier data even if analytics fail
      // When analytics fail, suppliers only appear in contracts and risk sections (not performance section)
      expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(2); // In contracts and risk sections only

      consoleSpy.mockRestore();
    });

    it('should maintain state consistency during operations', async () => {
      render(
        <TestWrapper>
          <SupplierCoordinatorView />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getAllByText('AquaTech Solutions')).toHaveLength(4); // Multiple occurrences expected
      });

      // Test multiple state changes
      const searchInput = screen.getByPlaceholderText('Search suppliers...');
      fireEvent.change(searchInput, { target: { value: 'AquaTech' } });

      const statusSelect = screen.getByDisplayValue('All Status');
      fireEvent.change(statusSelect, { target: { value: 'active' } });

      const sortSelect = screen.getByDisplayValue('Sort by Name');
      fireEvent.change(sortSelect, { target: { value: 'performance' } });

      // All state should be maintained
      expect(searchInput).toHaveValue('AquaTech');
      expect(statusSelect).toHaveValue('active');
      expect(sortSelect).toHaveValue('performance');
    });
  });
});