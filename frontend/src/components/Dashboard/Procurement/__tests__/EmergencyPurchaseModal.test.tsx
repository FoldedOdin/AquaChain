/**
 * EmergencyPurchaseModal Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useNotification } from '../../../../contexts/NotificationContext';
import EmergencyPurchaseModal from '../EmergencyPurchaseModal';

// Mock dependencies
jest.mock('../../../../contexts/NotificationContext');

const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;

const mockShowNotification = jest.fn();
const mockOnSubmit = jest.fn();
const mockOnClose = jest.fn();

describe('EmergencyPurchaseModal Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      showNotification: mockShowNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
  });

  it('renders modal header correctly', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByText('Emergency Purchase Request')).toBeInTheDocument();
    expect(screen.getByText('Submit high-priority procurement with expedited approval workflow')).toBeInTheDocument();
  });

  it('renders supplier information fields', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByLabelText(/Supplier ID/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Supplier Name/)).toBeInTheDocument();
  });

  it('renders initial item form', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByLabelText(/Item Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Quantity/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Unit Price/)).toBeInTheDocument();
  });

  it('allows adding additional items', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const addItemButton = screen.getByText('Add Item');
    fireEvent.click(addItemButton);
    
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('allows removing items when more than one exists', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Add a second item
    const addItemButton = screen.getByText('Add Item');
    fireEvent.click(addItemButton);
    
    // Remove button should now be visible
    const removeButtons = screen.getAllByRole('button', { name: /remove/i });
    expect(removeButtons).toHaveLength(2);
    
    fireEvent.click(removeButtons[0]);
    
    // Should only have one item left
    expect(screen.queryByText('Item 2')).not.toBeInTheDocument();
  });

  it('calculates item total price correctly', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const quantityInput = screen.getByLabelText(/Quantity/);
    const unitPriceInput = screen.getByLabelText(/Unit Price/);
    
    fireEvent.change(quantityInput, { target: { value: '5' } });
    fireEvent.change(unitPriceInput, { target: { value: '100' } });
    
    expect(screen.getByText('Total: $500')).toBeInTheDocument();
  });

  it('calculates grand total correctly', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const quantityInput = screen.getByLabelText(/Quantity/);
    const unitPriceInput = screen.getByLabelText(/Unit Price/);
    
    fireEvent.change(quantityInput, { target: { value: '5' } });
    fireEvent.change(unitPriceInput, { target: { value: '100' } });
    
    expect(screen.getByText('Grand Total: $500')).toBeInTheDocument();
  });

  it('renders emergency details fields', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByLabelText(/Budget Category/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Expected Delivery/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Emergency Reason/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Business Justification/)).toBeInTheDocument();
  });

  it('validates required fields on submission', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Supplier information is required',
        'error'
      );
    });
  });

  it('validates emergency reason is required', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Fill supplier info
    fireEvent.change(screen.getByLabelText(/Supplier ID/), { target: { value: 'SUP-001' } });
    fireEvent.change(screen.getByLabelText(/Supplier Name/), { target: { value: 'Test Supplier' } });
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Emergency reason is required',
        'error'
      );
    });
  });

  it('validates business justification is required', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Fill required fields except business justification
    fireEvent.change(screen.getByLabelText(/Supplier ID/), { target: { value: 'SUP-001' } });
    fireEvent.change(screen.getByLabelText(/Supplier Name/), { target: { value: 'Test Supplier' } });
    fireEvent.change(screen.getByLabelText(/Emergency Reason/), { target: { value: 'Critical equipment failure' } });
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Business justification is required',
        'error'
      );
    });
  });

  it('validates expected delivery date is required', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Fill required fields except delivery date
    fireEvent.change(screen.getByLabelText(/Supplier ID/), { target: { value: 'SUP-001' } });
    fireEvent.change(screen.getByLabelText(/Supplier Name/), { target: { value: 'Test Supplier' } });
    fireEvent.change(screen.getByLabelText(/Emergency Reason/), { target: { value: 'Critical equipment failure' } });
    fireEvent.change(screen.getByLabelText(/Business Justification/), { target: { value: 'Required for operations' } });
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Expected delivery date is required',
        'error'
      );
    });
  });

  it('validates at least one valid item is required', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Fill all required fields except item details
    fireEvent.change(screen.getByLabelText(/Supplier ID/), { target: { value: 'SUP-001' } });
    fireEvent.change(screen.getByLabelText(/Supplier Name/), { target: { value: 'Test Supplier' } });
    fireEvent.change(screen.getByLabelText(/Emergency Reason/), { target: { value: 'Critical equipment failure' } });
    fireEvent.change(screen.getByLabelText(/Business Justification/), { target: { value: 'Required for operations' } });
    fireEvent.change(screen.getByLabelText(/Expected Delivery/), { target: { value: '2024-12-31' } });
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'At least one valid item is required',
        'error'
      );
    });
  });

  it('submits valid emergency purchase request', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Fill all required fields
    fireEvent.change(screen.getByLabelText(/Supplier ID/), { target: { value: 'SUP-001' } });
    fireEvent.change(screen.getByLabelText(/Supplier Name/), { target: { value: 'Test Supplier' } });
    fireEvent.change(screen.getByLabelText(/Item Name/), { target: { value: 'Emergency Part' } });
    fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText(/Unit Price/), { target: { value: '1000' } });
    fireEvent.change(screen.getByLabelText(/Emergency Reason/), { target: { value: 'Critical equipment failure' } });
    fireEvent.change(screen.getByLabelText(/Business Justification/), { target: { value: 'Required for operations' } });
    fireEvent.change(screen.getByLabelText(/Expected Delivery/), { target: { value: '2024-12-31' } });
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        supplierId: 'SUP-001',
        items: [{
          itemId: '',
          itemName: 'Emergency Part',
          quantity: 1,
          unitPrice: 1000,
          totalPrice: 1000,
          specifications: ''
        }],
        totalAmount: 1000,
        budgetCategory: 'operations',
        emergencyReason: 'Critical equipment failure',
        businessJustification: 'Required for operations',
        expectedDelivery: '2024-12-31',
        alternativeOptions: undefined
      });
    });
  });

  it('handles close button click', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('handles cancel button click', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('displays risk warning', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    expect(screen.getByText('Emergency Purchase Risk Assessment')).toBeInTheDocument();
    expect(screen.getByText(/Emergency purchases bypass normal approval workflows/)).toBeInTheDocument();
  });

  it('sets minimum date for expected delivery', () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    const deliveryInput = screen.getByLabelText(/Expected Delivery/) as HTMLInputElement;
    const today = new Date().toISOString().split('T')[0];
    
    expect(deliveryInput.min).toBe(today);
  });

  it('includes alternative options when provided', async () => {
    render(
      <EmergencyPurchaseModal
        onSubmit={mockOnSubmit}
        onClose={mockOnClose}
      />
    );
    
    // Fill all required fields including alternative options
    fireEvent.change(screen.getByLabelText(/Supplier ID/), { target: { value: 'SUP-001' } });
    fireEvent.change(screen.getByLabelText(/Supplier Name/), { target: { value: 'Test Supplier' } });
    fireEvent.change(screen.getByLabelText(/Item Name/), { target: { value: 'Emergency Part' } });
    fireEvent.change(screen.getByLabelText(/Quantity/), { target: { value: '1' } });
    fireEvent.change(screen.getByLabelText(/Unit Price/), { target: { value: '1000' } });
    fireEvent.change(screen.getByLabelText(/Emergency Reason/), { target: { value: 'Critical equipment failure' } });
    fireEvent.change(screen.getByLabelText(/Business Justification/), { target: { value: 'Required for operations' } });
    fireEvent.change(screen.getByLabelText(/Expected Delivery/), { target: { value: '2024-12-31' } });
    fireEvent.change(screen.getByLabelText(/Alternative Options Considered/), { target: { value: 'Considered local suppliers but none available' } });
    
    const submitButton = screen.getByText('Submit Emergency Request');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          alternativeOptions: 'Considered local suppliers but none available'
        })
      );
    });
  });
});