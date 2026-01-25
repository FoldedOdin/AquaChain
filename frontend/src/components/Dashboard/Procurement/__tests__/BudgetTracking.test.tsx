/**
 * BudgetTracking Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useNotification } from '../../../../contexts/NotificationContext';
import BudgetTracking from '../BudgetTracking';
import budgetService from '../../../../services/budgetService';

// Mock dependencies
jest.mock('../../../../contexts/NotificationContext');
jest.mock('../../../../services/budgetService');

const mockUseNotification = useNotification as jest.MockedFunction<typeof useNotification>;
const mockBudgetService = budgetService as jest.Mocked<typeof budgetService>;

const mockShowNotification = jest.fn();

const mockBudgetData = [
  {
    category: 'operations',
    period: '2024-01',
    allocatedAmount: 10000,
    utilizedAmount: 7500,
    remainingAmount: 2500,
    utilizationPercentage: 75,
    projectedSpend: 8000
  },
  {
    category: 'maintenance',
    period: '2024-01',
    allocatedAmount: 5000,
    utilizedAmount: 4500,
    remainingAmount: 500,
    utilizationPercentage: 90,
    projectedSpend: 4800
  }
];

const mockForecastComparison = [
  {
    category: 'operations',
    forecastedAmount: 8000,
    actualAmount: 7500,
    variance: -500,
    variancePercentage: -6.25,
    trend: 'below_forecast' as const,
    confidence: 0.85
  },
  {
    category: 'maintenance',
    forecastedAmount: 4000,
    actualAmount: 4500,
    variance: 500,
    variancePercentage: 12.5,
    trend: 'above_forecast' as const,
    confidence: 0.92
  }
];

const mockBudgetAlerts = [
  {
    alertId: 'alert-1',
    budgetCategory: 'maintenance',
    message: 'Budget utilization approaching limit',
    severity: 'warning' as const,
    currentUtilization: 90,
    threshold: 85,
    createdAt: '2024-01-15T00:00:00Z'
  }
];

describe('BudgetTracking Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseNotification.mockReturnValue({
      showNotification: mockShowNotification,
      notifications: [],
      removeNotification: jest.fn()
    });
    mockBudgetService.getBudgetUtilization.mockResolvedValue(mockBudgetData);
    mockBudgetService.getSpendForecastComparison.mockResolvedValue(mockForecastComparison);
    mockBudgetService.getBudgetAlerts.mockResolvedValue(mockBudgetAlerts);
  });

  it('renders budget tracking header', async () => {
    render(<BudgetTracking />);
    
    expect(screen.getByText('Budget Tracking & Financial Oversight')).toBeInTheDocument();
    expect(screen.getByText('Monitor budget allocation, utilization, and spend forecasts')).toBeInTheDocument();
  });

  it('displays period selector with current month selected', async () => {
    render(<BudgetTracking />);
    
    const periodSelect = screen.getByDisplayValue(/2024/); // Should show current year
    expect(periodSelect).toBeInTheDocument();
  });

  it('loads and displays budget alerts', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('Budget Alerts')).toBeInTheDocument();
      expect(screen.getByText('maintenance')).toBeInTheDocument();
      expect(screen.getByText('Budget utilization approaching limit')).toBeInTheDocument();
      expect(screen.getByText('90.0%')).toBeInTheDocument();
    });
  });

  it('displays budget utilization data correctly', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('Budget Utilization by Category')).toBeInTheDocument();
      expect(screen.getByText('operations')).toBeInTheDocument();
      expect(screen.getByText('maintenance')).toBeInTheDocument();
      expect(screen.getByText('$10,000')).toBeInTheDocument(); // Allocated amount
      expect(screen.getByText('$7,500')).toBeInTheDocument(); // Utilized amount
      expect(screen.getByText('$2,500')).toBeInTheDocument(); // Remaining amount
    });
  });

  it('displays utilization percentages with correct colors', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      const operationsUtilization = screen.getByText('75.0%');
      const maintenanceUtilization = screen.getByText('90.0%');
      
      expect(operationsUtilization).toHaveClass('text-yellow-600'); // 75% should be yellow
      expect(maintenanceUtilization).toHaveClass('text-red-600'); // 90% should be red
    });
  });

  it('displays spend vs forecast comparison table', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('Spend vs Forecast Comparison')).toBeInTheDocument();
      expect(screen.getByText('$8,000')).toBeInTheDocument(); // Forecasted amount
      expect(screen.getByText('-6.2%')).toBeInTheDocument(); // Variance percentage
      expect(screen.getByText('below forecast')).toBeInTheDocument(); // Trend
      expect(screen.getByText('85.0%')).toBeInTheDocument(); // Confidence
    });
  });

  it('displays variance colors correctly', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      const negativeVariance = screen.getByText('-6.2%');
      const positiveVariance = screen.getByText('+12.5%');
      
      expect(negativeVariance).toHaveClass('text-green-600'); // Negative variance is good (green)
      expect(positiveVariance).toHaveClass('text-red-600'); // Positive variance is bad (red)
    });
  });

  it('displays summary cards with totals', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Allocated')).toBeInTheDocument();
      expect(screen.getByText('Total Utilized')).toBeInTheDocument();
      expect(screen.getByText('Total Remaining')).toBeInTheDocument();
      expect(screen.getByText('$15,000')).toBeInTheDocument(); // Total allocated (10000 + 5000)
      expect(screen.getByText('$12,000')).toBeInTheDocument(); // Total utilized (7500 + 4500)
      expect(screen.getByText('$3,000')).toBeInTheDocument(); // Total remaining (2500 + 500)
    });
  });

  it('handles period change', async () => {
    render(<BudgetTracking />);
    
    const periodSelect = screen.getByDisplayValue(/2024/);
    fireEvent.change(periodSelect, { target: { value: '2023-12' } });
    
    await waitFor(() => {
      expect(mockBudgetService.getBudgetUtilization).toHaveBeenCalledWith(
        expect.objectContaining({
          start: '2023-12-01',
          end: '2023-12-31'
        })
      );
    });
  });

  it('displays empty state when no budget data', async () => {
    mockBudgetService.getBudgetUtilization.mockResolvedValue([]);
    
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('No Budget Data')).toBeInTheDocument();
      expect(screen.getByText('No budget data available for the selected period.')).toBeInTheDocument();
    });
  });

  it('displays empty state when no forecast data', async () => {
    mockBudgetService.getSpendForecastComparison.mockResolvedValue([]);
    
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('No Forecast Data')).toBeInTheDocument();
      expect(screen.getByText('No forecast comparison data available for the selected period.')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    mockBudgetService.getBudgetUtilization.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    
    render(<BudgetTracking />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error when loading budget data fails', async () => {
    const error = new Error('Failed to load budget data');
    mockBudgetService.getBudgetUtilization.mockRejectedValue(error);
    
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(mockShowNotification).toHaveBeenCalledWith(
        'Failed to load budget data',
        'error'
      );
    });
  });

  it('displays alert severity colors correctly', async () => {
    const criticalAlert = {
      ...mockBudgetAlerts[0],
      severity: 'critical' as const
    };
    
    mockBudgetService.getBudgetAlerts.mockResolvedValue([criticalAlert]);
    
    render(<BudgetTracking />);
    
    await waitFor(() => {
      const alertCard = screen.getByText('maintenance').closest('div');
      expect(alertCard).toHaveClass('bg-red-100', 'text-red-800', 'border-red-200');
    });
  });

  it('formats currency correctly', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.getByText('$10,000')).toBeInTheDocument();
      expect(screen.getByText('$7,500')).toBeInTheDocument();
      expect(screen.getByText('$2,500')).toBeInTheDocument();
    });
  });

  it('displays progress bars with correct colors', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      const progressBars = screen.getAllByRole('progressbar', { hidden: true });
      
      // Operations (75%) should be yellow
      expect(progressBars[0]).toHaveClass('bg-yellow-500');
      
      // Maintenance (90%) should be red
      expect(progressBars[1]).toHaveClass('bg-red-500');
    });
  });

  it('does not display budget alerts section when no alerts', async () => {
    mockBudgetService.getBudgetAlerts.mockResolvedValue([]);
    
    render(<BudgetTracking />);
    
    await waitFor(() => {
      expect(screen.queryByText('Budget Alerts')).not.toBeInTheDocument();
    });
  });

  it('displays trend badges with correct colors', async () => {
    render(<BudgetTracking />);
    
    await waitFor(() => {
      const belowForecastBadge = screen.getByText('below forecast');
      const aboveForecastBadge = screen.getByText('above forecast');
      
      expect(belowForecastBadge).toHaveClass('bg-green-100', 'text-green-800');
      expect(aboveForecastBadge).toHaveClass('bg-red-100', 'text-red-800');
    });
  });
});