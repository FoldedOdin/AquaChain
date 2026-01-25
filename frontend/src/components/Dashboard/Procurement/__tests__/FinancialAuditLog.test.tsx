/**
 * FinancialAuditLog Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useNotification } from '../../../../contexts/NotificationContext';
import FinancialAuditLog from '../FinancialAuditLog';
import procurementService from '../../../../services/procurementService';

// Mock dependencies
jest.mock('../../../../contexts/NotificationContext');
jest.mock('../../../../services/procurementService');

const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;
const mockProcurementService = procurementService as jest.Mocked<typeof procurementService>;

const mockShowNotification = jest.fn();

const mockAuditEntries = [
  {
    auditId: 'audit-1',
    orderId: 'PO-001',
    action: 'approve',
    performedBy: 'John Controller',
    performedAt: '2024-01-15T10:30:00Z',
    amount: 1000,
    budgetCategory: 'operations',
    ipAddress: '192.168.1.100',
    details: {
      justification: 'Approved for business needs',
      conditions: ['Delivery within 30 days']
    }
  },
  {
    auditId: 'audit-2',
    orderId: 'PO-002',
    action: 'reject',
    performedBy: 'Jane Controller',
    performedAt: '2024-01-14T14:15:00Z',
    amount: 5000,
    budgetCategory: 'maintenance',
    ipAddress: '192.168.1.101',
    details: {
      justification: 'Insufficient budget available'
    }
  }
];

// Mock URL.createObjectURL and related functions
global.URL.createObjectURL = jest.fn(() => 'mock-blob-url');
global.URL.revokeObjectURL = jest.fn();

// Mock document.createElement and appendChild/removeChild
const mockLink = {
  href: '',
  download: '',
  click: jest.fn()
};

const originalCreateElement = document.createElement;
document.createElement = jest.fn((tagName) => {
  if (tagName === 'a') {
    return mockLink as any;
  }
  return originalCreateElement.call(document, tagName);
});

const originalAppendChild = document.body.appendChild;
const originalRemoveChild = document.body.removeChild;
document.body.appendChild = jest.fn();
document.body.removeChild = jest.fn();

describe('FinancialAuditLog Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      showNotification: mockShowNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
    mockProcurementService.getFinancialAuditLog.mockResolvedValue(mockAuditEntries);
    mockProcurementService.exportAuditData.mockResolvedValue(new Blob(['test data'], { type: 'text/csv' }));
  });

  afterAll(() => {
    document.createElement = originalCreateElement;
    document.body.appendChild = originalAppendChild;
    document.body.removeChild = originalRemoveChild;
  });

  it('renders audit log header', async () => {
    render(<FinancialAuditLog />);
    
    expect(screen.getByText('Financial Audit Log')).toBeInTheDocument();
    expect(screen.getByText('Comprehensive audit trail of all financial transactions and decisions')).toBeInTheDocument();
  });

  it('renders export buttons', () => {
    render(<FinancialAuditLog />);
    
    expect(screen.getByText('Export CSV')).toBeInTheDocument();
    expect(screen.getByText('Export Excel')).toBeInTheDocument();
    expect(screen.getByText('Export PDF')).toBeInTheDocument();
  });

  it('renders filter controls', () => {
    render(<FinancialAuditLog />);
    
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    expect(screen.getByLabelText('Order ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Budget Category')).toBeInTheDocument();
    expect(screen.getByLabelText('Performed By')).toBeInTheDocument();
    expect(screen.getByLabelText('Action')).toBeInTheDocument();
  });

  it('loads and displays audit entries', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(screen.getByText('PO-001')).toBeInTheDocument();
      expect(screen.getByText('PO-002')).toBeInTheDocument();
      expect(screen.getByText('John Controller')).toBeInTheDocument();
      expect(screen.getByText('Jane Controller')).toBeInTheDocument();
      expect(screen.getByText('$1,000')).toBeInTheDocument();
      expect(screen.getByText('$5,000')).toBeInTheDocument();
    });
  });

  it('displays action badges with correct colors', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const approveBadge = screen.getByText('approve');
      const rejectBadge = screen.getByText('reject');
      
      expect(approveBadge).toHaveClass('bg-green-100', 'text-green-800');
      expect(rejectBadge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });

  it('formats dates correctly', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(screen.getByText('Jan 15, 2024, 10:30 AM')).toBeInTheDocument();
      expect(screen.getByText('Jan 14, 2024, 02:15 PM')).toBeInTheDocument();
    });
  });

  it('displays IP addresses in monospace font', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const ipAddress = screen.getByText('192.168.1.100');
      expect(ipAddress).toHaveClass('font-mono');
    });
  });

  it('handles filter changes', async () => {
    render(<FinancialAuditLog />);
    
    const orderIdFilter = screen.getByLabelText('Order ID');
    fireEvent.change(orderIdFilter, { target: { value: 'PO-001' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getFinancialAuditLog).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          orderId: 'PO-001'
        })
      );
    });
  });

  it('handles budget category filter', async () => {
    render(<FinancialAuditLog />);
    
    const categoryFilter = screen.getByLabelText('Budget Category');
    fireEvent.change(categoryFilter, { target: { value: 'operations' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getFinancialAuditLog).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          budgetCategory: 'operations'
        })
      );
    });
  });

  it('handles action filter', async () => {
    render(<FinancialAuditLog />);
    
    const actionFilter = screen.getByLabelText('Action');
    fireEvent.change(actionFilter, { target: { value: 'approve' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getFinancialAuditLog).toHaveBeenCalledWith(
        expect.any(Object),
        expect.objectContaining({
          action: 'approve'
        })
      );
    });
  });

  it('clears all filters when clear button is clicked', async () => {
    render(<FinancialAuditLog />);
    
    // Set some filters first
    const orderIdFilter = screen.getByLabelText('Order ID');
    fireEvent.change(orderIdFilter, { target: { value: 'PO-001' } });
    
    // Clear filters
    const clearButton = screen.getByText('Clear All Filters');
    fireEvent.click(clearButton);
    
    expect(orderIdFilter).toHaveValue('');
  });

  it('displays results summary', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(screen.getByText('Showing 2 audit entries')).toBeInTheDocument();
    });
  });

  it('handles CSV export', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const csvButton = screen.getByText('Export CSV');
      fireEvent.click(csvButton);
      
      expect(mockProcurementService.exportAuditData).toHaveBeenCalledWith(
        expect.any(Object),
        'csv'
      );
    });
  });

  it('handles Excel export', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const excelButton = screen.getByText('Export Excel');
      fireEvent.click(excelButton);
      
      expect(mockProcurementService.exportAuditData).toHaveBeenCalledWith(
        expect.any(Object),
        'xlsx'
      );
    });
  });

  it('handles PDF export', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const pdfButton = screen.getByText('Export PDF');
      fireEvent.click(pdfButton);
      
      expect(mockProcurementService.exportAuditData).toHaveBeenCalledWith(
        expect.any(Object),
        'pdf'
      );
    });
  });

  it('disables export buttons when no data', async () => {
    mockProcurementService.getFinancialAuditLog.mockResolvedValue([]);
    
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(screen.getByText('Export CSV')).toBeDisabled();
      expect(screen.getByText('Export Excel')).toBeDisabled();
      expect(screen.getByText('Export PDF')).toBeDisabled();
    });
  });

  it('displays empty state when no audit entries', async () => {
    mockProcurementService.getFinancialAuditLog.mockResolvedValue([]);
    
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(screen.getByText('No Audit Entries Found')).toBeInTheDocument();
      expect(screen.getByText('No financial audit entries match the selected criteria.')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    mockProcurementService.getFinancialAuditLog.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    render(<FinancialAuditLog />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error when loading audit log fails', async () => {
    const error = new Error('Failed to load audit log');
    mockProcurementService.getFinancialAuditLog.mockRejectedValue(error);
    
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Failed to load financial audit log',
        'error'
      );
    });
  });

  it('handles export error', async () => {
    const error = new Error('Export failed');
    mockProcurementService.exportAuditData.mockRejectedValue(error);
    
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const csvButton = screen.getByText('Export CSV');
      fireEvent.click(csvButton);
    });
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Failed to export audit data',
        'error'
      );
    });
  });

  it('shows exporting state during export', async () => {
    // Make export take some time
    mockProcurementService.exportAuditData.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(new Blob()), 100))
    );
    
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const csvButton = screen.getByText('Export CSV');
      fireEvent.click(csvButton);
      
      expect(screen.getByText('Exporting...')).toBeInTheDocument();
    });
  });

  it('displays audit trail integrity notice', () => {
    render(<FinancialAuditLog />);
    
    expect(screen.getByText('Audit Trail Integrity')).toBeInTheDocument();
    expect(screen.getByText(/cryptographically secured and tamper-evident/)).toBeInTheDocument();
  });

  it('handles date range filters', async () => {
    render(<FinancialAuditLog />);
    
    const startDateFilter = screen.getByLabelText('Start Date');
    const endDateFilter = screen.getByLabelText('End Date');
    
    fireEvent.change(startDateFilter, { target: { value: '2024-01-01' } });
    fireEvent.change(endDateFilter, { target: { value: '2024-01-31' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getFinancialAuditLog).toHaveBeenCalledWith(
        { start: '2024-01-01', end: '2024-01-31' },
        expect.any(Object)
      );
    });
  });

  it('displays details for complex audit entries', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      const detailsButton = screen.getByText('View Details');
      fireEvent.click(detailsButton);
      
      expect(screen.getByText('Approved for business needs')).toBeInTheDocument();
    });
  });

  it('formats currency amounts correctly', async () => {
    render(<FinancialAuditLog />);
    
    await waitFor(() => {
      expect(screen.getByText('$1,000')).toBeInTheDocument();
      expect(screen.getByText('$5,000')).toBeInTheDocument();
    });
  });
});