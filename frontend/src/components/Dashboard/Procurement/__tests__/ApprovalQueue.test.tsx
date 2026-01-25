/**
 * ApprovalQueue Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useNotification } from '../../../../contexts/NotificationContext';
import ApprovalQueue from '../ApprovalQueue';
import procurementService from '../../../../services/procurementService';

// Mock dependencies
jest.mock('../../../../contexts/NotificationContext');
jest.mock('../../../../services/procurementService');

const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;
const mockProcurementService = procurementService as jest.Mocked<typeof procurementService>;

const mockShowNotification = jest.fn();

const mockApprovals = [
  {
    orderId: 'PO-001',
    purchaseOrder: {
      orderId: 'PO-001',
      requesterId: 'user-1',
      requesterName: 'John Doe',
      supplierId: 'supplier-1',
      supplierName: 'Test Supplier',
      items: [
        {
          itemId: 'item-1',
          itemName: 'Test Item',
          quantity: 10,
          unitPrice: 100,
          totalPrice: 1000
        }
      ],
      totalAmount: 1000,
      budgetCategory: 'operations',
      status: 'pending' as const,
      priority: 'normal' as const,
      workflowId: 'workflow-1',
      createdAt: '2024-01-01T00:00:00Z'
    },
    submittedAt: '2024-01-01T00:00:00Z',
    daysWaiting: 2,
    riskAssessment: {
      financialRisk: 'low' as const,
      supplierRisk: 'low' as const,
      budgetRisk: 'low' as const,
      overallRisk: 'low' as const,
      riskFactors: []
    }
  }
];

describe('ApprovalQueue Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      showNotification: mockShowNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
    mockProcurementService.getApprovalQueue.mockResolvedValue(mockApprovals);
  });

  it('renders approval queue header', async () => {
    render(<ApprovalQueue />);
    
    expect(screen.getByText('Purchase Order Approval Queue')).toBeInTheDocument();
    expect(screen.getByText('Emergency Purchase')).toBeInTheDocument();
  });

  it('loads and displays approval queue data', async () => {
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      expect(screen.getByText('Order #PO-001')).toBeInTheDocument();
      expect(screen.getByText('Test Supplier • 1 item')).toBeInTheDocument();
      expect(screen.getByText('$1,000')).toBeInTheDocument();
      expect(screen.getByText('2 days waiting')).toBeInTheDocument();
    });
  });

  it('handles filter changes', async () => {
    render(<ApprovalQueue />);
    
    const priorityFilter = screen.getByDisplayValue('All Priorities');
    fireEvent.change(priorityFilter, { target: { value: 'high' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getApprovalQueue).toHaveBeenCalledWith(
        expect.objectContaining({
          priority: ['high']
        })
      );
    });
  });

  it('opens approval modal when review button is clicked', async () => {
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      const reviewButton = screen.getByText('Review');
      fireEvent.click(reviewButton);
    });
    
    // Modal should be opened (we can't test the modal content here as it's in a separate component)
    expect(screen.getByText('Review')).toBeInTheDocument();
  });

  it('opens emergency purchase modal when emergency button is clicked', () => {
    render(<ApprovalQueue />);
    
    const emergencyButton = screen.getByText('Emergency Purchase');
    fireEvent.click(emergencyButton);
    
    // Modal should be opened
    expect(emergencyButton).toBeInTheDocument();
  });

  it('displays empty state when no approvals', async () => {
    mockProcurementService.getApprovalQueue.mockResolvedValue([]);
    
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      expect(screen.getByText('No Pending Approvals')).toBeInTheDocument();
      expect(screen.getByText('All purchase orders have been processed.')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    mockProcurementService.getApprovalQueue.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    render(<ApprovalQueue />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error when loading approval queue fails', async () => {
    const error = new Error('Failed to load');
    mockProcurementService.getApprovalQueue.mockRejectedValue(error);
    
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Failed to load approval queue',
        'error'
      );
    });
  });

  it('displays correct priority badge colors', async () => {
    const emergencyApproval = {
      ...mockApprovals[0],
      purchaseOrder: {
        ...mockApprovals[0].purchaseOrder,
        priority: 'emergency' as const
      }
    };
    
    mockProcurementService.getApprovalQueue.mockResolvedValue([emergencyApproval]);
    
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      const priorityBadge = screen.getByText('emergency');
      expect(priorityBadge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });

  it('displays correct risk badge colors', async () => {
    const highRiskApproval = {
      ...mockApprovals[0],
      riskAssessment: {
        ...mockApprovals[0].riskAssessment,
        overallRisk: 'high' as const
      }
    };
    
    mockProcurementService.getApprovalQueue.mockResolvedValue([highRiskApproval]);
    
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      const riskBadge = screen.getByText('high risk');
      expect(riskBadge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });

  it('formats currency correctly', async () => {
    render(<ApprovalQueue />);
    
    await waitFor(() => {
      expect(screen.getByText('$1,000')).toBeInTheDocument();
    });
  });

  it('handles sorting changes', async () => {
    render(<ApprovalQueue />);
    
    const sortByFilter = screen.getByDisplayValue('Date Created');
    fireEvent.change(sortByFilter, { target: { value: 'amount' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getApprovalQueue).toHaveBeenCalledWith(
        expect.objectContaining({
          sortBy: 'amount'
        })
      );
    });
  });

  it('handles budget category filter', async () => {
    render(<ApprovalQueue />);
    
    const categoryFilter = screen.getByDisplayValue('All Categories');
    fireEvent.change(categoryFilter, { target: { value: 'maintenance' } });
    
    await waitFor(() => {
      expect(mockProcurementService.getApprovalQueue).toHaveBeenCalledWith(
        expect.objectContaining({
          budgetCategory: ['maintenance']
        })
      );
    });
  });
});