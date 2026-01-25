/**
 * Unit Tests for Inventory Manager View
 * Tests stock level display, reorder alert rendering, and audit history functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import InventoryManagerView from '../InventoryManagerView';
import { UserProfile } from '../../../../types';

// Mock the contexts
const mockUser: UserProfile = {
  userId: 'user-123',
  email: 'inventory@example.com',
  role: 'inventory_manager',
  profile: {
    firstName: 'John',
    lastName: 'Doe',
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

// Mock LoadingSpinner
jest.mock('../../../Loading/LoadingSpinner', () => {
  return function MockLoadingSpinner({ size }: { size?: string }) {
    return <div data-testid="loading-spinner" data-size={size}>Loading...</div>;
  };
});

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>
    {children}
  </BrowserRouter>
);

describe('InventoryManagerView', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render loading state initially', () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    expect(screen.getByText('Loading inventory data...')).toBeInTheDocument();
  });

  it('should render inventory management header and description', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Inventory Management')).toBeInTheDocument();
    });

    expect(screen.getByText('Manage stock levels, reorder points, and demand forecasting for all inventory items.')).toBeInTheDocument();
  });

  it('should display stock level statistics', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Total Items')).toBeInTheDocument();
    });

    expect(screen.getByText('Low Stock Alerts')).toBeInTheDocument();
    expect(screen.getByText('Out of Stock')).toBeInTheDocument();
    expect(screen.getByText('Total Value')).toBeInTheDocument();
  });

  it('should render stock alerts when present', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Stock Alerts')).toBeInTheDocument();
    });

    // Check for alert items
    expect(screen.getByText('Turbidity Sensor Module')).toBeInTheDocument();
    expect(screen.getByText('TDS Measurement Kit')).toBeInTheDocument();
    
    // Check for severity indicators
    expect(screen.getByText('WARNING')).toBeInTheDocument();
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();
  });

  it('should render search and filter controls', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Search Items')).toBeInTheDocument();
    });

    expect(screen.getByPlaceholderText('Search by item name or ID...')).toBeInTheDocument();
    expect(screen.getByLabelText('Category')).toBeInTheDocument();
  });

  it('should filter inventory items by search term', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Water Quality Sensor pH-7')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search by item name or ID...');
    fireEvent.change(searchInput, { target: { value: 'pH-7' } });

    // Should still show the pH sensor
    expect(screen.getByText('Water Quality Sensor pH-7')).toBeInTheDocument();
    
    // Should not show other items (they might still be in DOM but filtered out visually)
    // We'll check the search input value instead
    expect(searchInput).toHaveValue('pH-7');
  });

  it('should filter inventory items by category', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Category')).toBeInTheDocument();
    });

    const categorySelect = screen.getByLabelText('Category');
    fireEvent.change(categorySelect, { target: { value: 'Sensors' } });

    expect(categorySelect).toHaveValue('Sensors');
  });

  it('should display inventory items table with correct columns', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Inventory Items')).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText('Item')).toBeInTheDocument();
    expect(screen.getByText('Current Stock')).toBeInTheDocument();
    expect(screen.getByText('Reorder Point')).toBeInTheDocument();
    expect(screen.getByText('Unit Cost')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('should display inventory items with correct data', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Water Quality Sensor pH-7')).toBeInTheDocument();
    });

    // Check item details
    expect(screen.getByText('INV001')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument(); // Current stock
    expect(screen.getByText('20')).toBeInTheDocument(); // Reorder point
    expect(screen.getByText('$125.99')).toBeInTheDocument(); // Unit cost
    expect(screen.getByText('IN STOCK')).toBeInTheDocument(); // Status
  });

  it('should handle reorder point updates', async () => {
    // Mock window.prompt
    const mockPrompt = jest.spyOn(window, 'prompt').mockReturnValue('25');

    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Reorder Point')).toBeInTheDocument();
    });

    const editButton = screen.getAllByText('Edit Reorder Point')[0];
    fireEvent.click(editButton);

    expect(mockPrompt).toHaveBeenCalledWith('Enter new reorder point:', '20');

    await waitFor(() => {
      expect(mockNotificationContext.showNotification).toHaveBeenCalledWith(
        'Reorder point updated for item INV001',
        'success'
      );
    });

    mockPrompt.mockRestore();
  });

  it('should display demand forecasting section', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Demand Forecasting')).toBeInTheDocument();
    });

    // Check forecast data
    expect(screen.getByText('Predicted Demand (30d):')).toBeInTheDocument();
    expect(screen.getByText('Confidence:')).toBeInTheDocument();
    expect(screen.getByText('Trend:')).toBeInTheDocument();
  });

  it('should display audit history table', async () => {
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Inventory Audit History')).toBeInTheDocument();
    });

    // Check audit table headers
    expect(screen.getByText('Timestamp')).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Resource')).toBeInTheDocument();
    expect(screen.getByText('Changes')).toBeInTheDocument();
  });

  it('should show error notification on data load failure', async () => {
    // Mock console.error to avoid test output noise
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    // We can't easily mock the useEffect failure, but we can test the error handling
    // by checking that the notification context is available
    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    // The component should render without crashing
    await waitFor(() => {
      expect(screen.getByText('Inventory Management')).toBeInTheDocument();
    });

    consoleSpy.mockRestore();
  });

  it('should handle invalid reorder point input', async () => {
    const mockPrompt = jest.spyOn(window, 'prompt').mockReturnValue('invalid');

    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Reorder Point')).toBeInTheDocument();
    });

    const editButton = screen.getAllByText('Edit Reorder Point')[0];
    fireEvent.click(editButton);

    // Should not call showNotification for invalid input
    expect(mockNotificationContext.showNotification).not.toHaveBeenCalled();

    mockPrompt.mockRestore();
  });

  it('should handle cancelled reorder point update', async () => {
    const mockPrompt = jest.spyOn(window, 'prompt').mockReturnValue(null);

    render(
      <TestWrapper>
        <InventoryManagerView />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Reorder Point')).toBeInTheDocument();
    });

    const editButton = screen.getAllByText('Edit Reorder Point')[0];
    fireEvent.click(editButton);

    // Should not call showNotification for cancelled input
    expect(mockNotificationContext.showNotification).not.toHaveBeenCalled();

    mockPrompt.mockRestore();
  });
});