import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock all external dependencies
jest.mock('react-router-dom', () => ({
  useNavigate: () => jest.fn(),
}));

jest.mock('../../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: {
      userId: 'admin-1',
      email: 'admin@test.com',
      role: 'admin',
      profile: { firstName: 'Admin', lastName: 'User' }
    },
    logout: jest.fn()
  })
}));

jest.mock('../../../hooks/useDashboardData', () => ({
  useDashboardData: () => ({
    data: null,
    isLoading: false,
    error: null
  })
}));

jest.mock('../../../hooks/useRealTimeUpdates', () => ({
  useRealTimeUpdates: () => ({
    isConnected: true
  })
}));

jest.mock('../../../hooks/useNotifications', () => ({
  useNotifications: () => ({
    notifications: []
  })
}));

jest.mock('../../../services/adminService', () => ({
  getAllUsers: jest.fn().mockResolvedValue([]),
  getSystemConfiguration: jest.fn().mockResolvedValue({}),
  getSystemHealthMetrics: jest.fn().mockResolvedValue({}),
  getPerformanceMetrics: jest.fn().mockResolvedValue([]),
}));

// Mock framer-motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
}));

// Mock dashboard components
jest.mock('../NotificationCenter', () => {
  return function MockNotificationCenter() {
    return <div data-testid="notification-center" />;
  };
});

jest.mock('../DataExportModal', () => {
  return function MockDataExportModal() {
    return <div data-testid="data-export-modal" />;
  };
});

import AdminDashboardRestructured from '../AdminDashboardRestructured';

describe('AdminDashboardRestructured - Basic Tests', () => {
  it('should render without crashing', () => {
    render(<AdminDashboardRestructured />);
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
  });

  it('should display admin role indicator', () => {
    render(<AdminDashboardRestructured />);
    expect(screen.getByText('Administrator')).toBeInTheDocument();
    expect(screen.getByText('System Administration & Oversight')).toBeInTheDocument();
  });

  it('should NOT display operational controls - inventory', () => {
    render(<AdminDashboardRestructured />);
    
    // Should NOT have inventory-related controls
    expect(screen.queryByText('Inventory')).not.toBeInTheDocument();
    expect(screen.queryByText('Stock Levels')).not.toBeInTheDocument();
    expect(screen.queryByText('Reorder Points')).not.toBeInTheDocument();
  });

  it('should NOT display operational controls - warehouse', () => {
    render(<AdminDashboardRestructured />);
    
    // Should NOT have warehouse-related controls
    expect(screen.queryByText('Warehouse')).not.toBeInTheDocument();
    expect(screen.queryByText('Receiving')).not.toBeInTheDocument();
    expect(screen.queryByText('Dispatch')).not.toBeInTheDocument();
  });

  it('should NOT display operational controls - supplier', () => {
    render(<AdminDashboardRestructured />);
    
    // Should NOT have supplier-related controls
    expect(screen.queryByText('Supplier')).not.toBeInTheDocument();
    expect(screen.queryByText('Supplier Profiles')).not.toBeInTheDocument();
    expect(screen.queryByText('Contract Management')).not.toBeInTheDocument();
  });

  it('should NOT display operational controls - procurement', () => {
    render(<AdminDashboardRestructured />);
    
    // Should NOT have procurement-related controls
    expect(screen.queryByText('Procurement')).not.toBeInTheDocument();
    expect(screen.queryByText('Purchase Orders')).not.toBeInTheDocument();
    expect(screen.queryByText('Approval Queue')).not.toBeInTheDocument();
  });

  it('should display admin-specific tabs', () => {
    render(<AdminDashboardRestructured />);
    
    // Should have admin-specific tabs
    expect(screen.getByText('System Overview')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('System Configuration')).toBeInTheDocument();
    expect(screen.getByText('Global Monitoring')).toBeInTheDocument();
    expect(screen.getByText('Security & Audit')).toBeInTheDocument();
  });

  it('should display system health metrics', () => {
    render(<AdminDashboardRestructured />);
    
    // Should display key system metrics
    expect(screen.getByText('Total Users')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('API Success Rate')).toBeInTheDocument();
    expect(screen.getByText('Active Alerts')).toBeInTheDocument();
  });
});