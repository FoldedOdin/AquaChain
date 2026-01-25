/**
 * ApprovalModal Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useNotification } from '../../../../contexts/NotificationContext';
import ApprovalModal from '../ApprovalModal';
import procurementService from '../../../../services/procurementService';

// Mock dependencies
jest.mock('../../../../contexts/NotificationContext');
jest.mock('../../../../services/procurementService');

const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;
const mockProcurementService = procurementService as jest.Mocked<typeof procurementService>;

const mockShowNotification = jest.fn();
const mockOnApprove = jest.fn();
const mockOnClose = jest.fn();

const mockApproval = {
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
        totalPrice: 1000,
        specifications: 'Test specifications'
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
    riskFactors: ['No significant risks identified']
  }
};

const mockBudgetValidation = {
  isValid: true,
  availableBudget: 10000,
  requestedAmount: 1000,
  remainingAfterApproval: 9000,
  budgetUtilization: 10,
  warnings: []
};

const mockMLVariance = {
  forecastedSpend: 5000,
  actualSpend: 4500,
  variance: -500,
  variancePercentage: -10,
  trend: 'below_forecast' as const,
  confidence: 0.85
};

describe('ApprovalModal Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      showNotification: mockShowNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
    mockProcurementService.validateBudget.mockResolvedValue(mockBudgetValidation);
    mockProcurementService.getMLForecastVariance.mockResolvedValue(mockMLVariance);
  });

  it('renders modal header correctly', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByText('Purchase Order Approval - #PO-001')).toBeInTheDocument();
  });

  it('displays order details correctly', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Test Supplier')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('$1,000')).toBeInTheDocument();
      expect(screen.getByText('operations')).toBeInTheDocument();
      expect(screen.getByText('2 days')).toBeInTheDocument();
    });
  });

  it('displays items list correctly', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Items (1)')).toBeInTheDocument();
      expect(screen.getByText('Test Item')).toBeInTheDocument();
      expect(screen.getByText('Qty: 10 @ $100')).toBeInTheDocument();
    });
  });

  it('displays budget validation when valid', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Budget Validation')).toBeInTheDocument();
      expect(screen.getByText('$10,000')).toBeInTheDocument(); // Available budget
      expect(screen.getByText('$9,000')).toBeInTheDocument(); // Remaining after
      expect(screen.getByText('10.0%')).toBeInTheDocument(); // Utilization
    });
  });

  it('displays budget validation warnings when invalid', async () => {
    const invalidBudgetValidation = {
      ...mockBudgetValidation,
      isValid: false,
      warnings: ['Insufficient budget available']
    };
    
    mockProcurementService.validateBudget.mockResolvedValue(invalidBudgetValidation);
    
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Insufficient budget available')).toBeInTheDocument();
    });
  });

  it('displays ML forecast variance analysis', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('ML Forecast Analysis (Read-Only)')).toBeInTheDocument();
      expect(screen.getByText('$5,000')).toBeInTheDocument(); // Forecasted spend
      expect(screen.getByText('$4,500')).toBeInTheDocument(); // Actual spend
      expect(screen.getByText('-$500 (-10.0%)')).toBeInTheDocument(); // Variance
      expect(screen.getByText('85.0%')).toBeInTheDocument(); // Confidence
    });
  });

  it('displays risk assessment correctly', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(screen.getByText('Risk Assessment')).toBeInTheDocument();
      expect(screen.getAllByText('low')).toHaveLength(4); // All risk levels are low
      expect(screen.getByText('No significant risks identified')).toBeInTheDocument();
    });
  });

  it('allows selecting approve decision', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const approveButton = screen.getByText('Approve');
      fireEvent.click(approveButton);
      
      expect(approveButton).toHaveClass('bg-green-600');
    });
  });

  it('allows selecting reject decision', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const rejectButton = screen.getByText('Reject');
      fireEvent.click(rejectButton);
      
      expect(rejectButton).toHaveClass('bg-red-600');
    });
  });

  it('requires justification for submission', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const approveButton = screen.getByText('Approve');
      fireEvent.click(approveButton);
      
      const submitButton = screen.getByText('Submit Decision');
      fireEvent.click(submitButton);
      
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Justification is required',
        'error'
      );
    });
  });

  it('submits approval decision with justification', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const approveButton = screen.getByText('Approve');
      fireEvent.click(approveButton);
      
      const justificationTextarea = screen.getByPlaceholderText('Provide detailed justification for your decision...');
      fireEvent.change(justificationTextarea, { target: { value: 'Approved for business needs' } });
      
      const submitButton = screen.getByText('Submit Decision');
      fireEvent.click(submitButton);
      
      expect(mockOnApprove).toHaveBeenCalledWith({
        action: 'approve',
        justification: 'Approved for business needs',
        conditions: undefined
      });
    });
  });

  it('allows adding approval conditions', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const approveButton = screen.getByText('Approve');
      fireEvent.click(approveButton);
      
      const conditionInput = screen.getByPlaceholderText('Add a condition...');
      fireEvent.change(conditionInput, { target: { value: 'Delivery within 30 days' } });
      
      const addButton = screen.getByText('Add');
      fireEvent.click(addButton);
      
      expect(screen.getByText('Delivery within 30 days')).toBeInTheDocument();
    });
  });

  it('prevents approval when budget validation fails', async () => {
    const invalidBudgetValidation = {
      ...mockBudgetValidation,
      isValid: false
    };
    
    mockProcurementService.validateBudget.mockResolvedValue(invalidBudgetValidation);
    
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const approveButton = screen.getByText('Approve');
      expect(approveButton).toBeDisabled();
    });
  });

  it('handles close button click', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('handles cancel button click', async () => {
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);
      
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('shows loading state during validation data fetch', () => {
    mockProcurementService.validateBudget.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles validation data loading error', async () => {
    const error = new Error('Failed to load validation data');
    mockProcurementService.validateBudget.mockRejectedValue(error);
    
    render(
      <ApprovalModal
        approval={mockApproval}
        onApprove={mockOnApprove}
        onClose={mockOnClose}
      />
    );
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Failed to load budget validation data',
        'error'
      );
    });
  });
});