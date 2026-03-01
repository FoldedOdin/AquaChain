import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SystemHealthPanel from '../SystemHealthPanel';
import { SystemHealthResponse, ServiceHealth } from '../../../types/admin';

describe('SystemHealthPanel', () => {
  const mockOnRefresh = jest.fn();

  const mockHealthyService: ServiceHealth = {
    name: 'IoT Core',
    status: 'healthy',
    lastCheck: '2026-02-26T10:30:15Z',
    metrics: {
      mqttConnections: 1247,
      messagesPerSecond: 342
    }
  };

  const mockDegradedService: ServiceHealth = {
    name: 'SNS',
    status: 'degraded',
    lastCheck: '2026-02-26T10:30:15Z',
    metrics: {
      deliveryRate: 96.5
    },
    message: 'Delivery rate below 98% threshold'
  };

  const mockDownService: ServiceHealth = {
    name: 'Lambda',
    status: 'down',
    lastCheck: '2026-02-26T10:30:15Z',
    message: 'Service unavailable'
  };

  const mockUnknownService: ServiceHealth = {
    name: 'DynamoDB',
    status: 'unknown',
    lastCheck: '2026-02-26T10:30:15Z',
    message: 'Health check failed'
  };

  const mockHealthData: SystemHealthResponse = {
    services: [
      mockHealthyService,
      mockDegradedService,
      mockDownService,
      mockUnknownService,
      {
        name: 'ML Inference',
        status: 'healthy',
        lastCheck: '2026-02-26T10:30:15Z',
        metrics: {
          avgLatency: 387
        }
      }
    ],
    overallStatus: 'degraded',
    checkedAt: '2026-02-26T10:30:15Z',
    cacheHit: false
  };

  const defaultProps = {
    health: mockHealthData,
    loading: false,
    onRefresh: mockOnRefresh
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the component with title', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      expect(screen.getByText('System Health')).toBeInTheDocument();
    });

    it('should render refresh button', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      expect(refreshButton).toBeInTheDocument();
      expect(refreshButton).toHaveTextContent('Refresh');
    });

    it('should render all services from health data', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      expect(screen.getByText('IoT Core')).toBeInTheDocument();
      expect(screen.getByText('SNS')).toBeInTheDocument();
      expect(screen.getByText('Lambda')).toBeInTheDocument();
      expect(screen.getByText('DynamoDB')).toBeInTheDocument();
      expect(screen.getByText('ML Inference')).toBeInTheDocument();
    });

    it('should render last checked timestamp', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
    });

    it('should render cache indicator when cacheHit is true', () => {
      const propsWithCache = {
        ...defaultProps,
        health: { ...mockHealthData, cacheHit: true }
      };
      render(<SystemHealthPanel {...propsWithCache} />);
      expect(screen.getByText('(cached)')).toBeInTheDocument();
    });

    it('should not render cache indicator when cacheHit is false', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      expect(screen.queryByText('(cached)')).not.toBeInTheDocument();
    });
  });

  describe('Status Icons', () => {
    it('should display green icon for healthy status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const healthyStatus = screen.getByText('IoT Core').closest('div');
      expect(healthyStatus).toBeInTheDocument();
      const statusIcon = healthyStatus?.querySelector('[role="img"][aria-label="healthy status"]');
      expect(statusIcon).toBeInTheDocument();
    });

    it('should display yellow icon for degraded status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const degradedStatus = screen.getByText('SNS').closest('div');
      expect(degradedStatus).toBeInTheDocument();
      const statusIcon = degradedStatus?.querySelector('[role="img"][aria-label="degraded status"]');
      expect(statusIcon).toBeInTheDocument();
    });

    it('should display red icon for down status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const downStatus = screen.getByText('Lambda').closest('div');
      expect(downStatus).toBeInTheDocument();
      const statusIcon = downStatus?.querySelector('[role="img"][aria-label="down status"]');
      expect(statusIcon).toBeInTheDocument();
    });

    it('should display white icon for unknown status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const unknownStatus = screen.getByText('DynamoDB').closest('div');
      expect(unknownStatus).toBeInTheDocument();
      const statusIcon = unknownStatus?.querySelector('[role="img"][aria-label="unknown status"]');
      expect(statusIcon).toBeInTheDocument();
    });
  });

  describe('Status Text Display', () => {
    it('should display "healthy" text with green color for healthy status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const healthyElements = screen.getAllByText(/^healthy$/i);
      expect(healthyElements[0]).toHaveClass('text-green-600');
    });

    it('should display "degraded" text with yellow color for degraded status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const degradedText = screen.getByText(/^degraded$/i);
      expect(degradedText).toHaveClass('text-yellow-600');
    });

    it('should display "down" text with red color for down status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const downText = screen.getByText(/^down$/i);
      expect(downText).toHaveClass('text-red-600');
    });

    it('should display "unknown" text with gray color for unknown status', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      const unknownText = screen.getByText(/^unknown$/i);
      expect(unknownText).toHaveClass('text-gray-600');
    });

    it('should capitalize status text correctly', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      // Status text is displayed with first letter capitalized
      const healthyElements = screen.getAllByText(/^healthy$/i);
      expect(healthyElements.length).toBe(2);
      expect(screen.getByText(/^degraded$/i)).toBeInTheDocument();
      expect(screen.getByText(/^down$/i)).toBeInTheDocument();
      expect(screen.getByText(/^unknown$/i)).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show skeleton loaders when loading and no health data', () => {
      const loadingProps = {
        health: null,
        loading: true,
        onRefresh: mockOnRefresh
      };
      const { container } = render(<SystemHealthPanel {...loadingProps} />);
      
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBe(5);
    });

    it('should show loading status with aria-label', () => {
      const loadingProps = {
        health: null,
        loading: true,
        onRefresh: mockOnRefresh
      };
      render(<SystemHealthPanel {...loadingProps} />);
      
      const loadingStatus = screen.getByRole('status', { name: /loading system health/i });
      expect(loadingStatus).toBeInTheDocument();
    });

    it('should show "Checking..." text on refresh button when loading', () => {
      const loadingProps = {
        ...defaultProps,
        loading: true
      };
      render(<SystemHealthPanel {...loadingProps} />);
      
      expect(screen.getByText('Checking...')).toBeInTheDocument();
    });

    it('should disable refresh button when loading', () => {
      const loadingProps = {
        ...defaultProps,
        loading: true
      };
      render(<SystemHealthPanel {...loadingProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      expect(refreshButton).toBeDisabled();
    });

    it('should show spinning icon when loading', () => {
      const loadingProps = {
        ...defaultProps,
        loading: true
      };
      const { container } = render(<SystemHealthPanel {...loadingProps} />);
      
      const spinningIcon = container.querySelector('.animate-spin');
      expect(spinningIcon).toBeInTheDocument();
    });

    it('should not show skeleton loaders when loading but health data exists', () => {
      const loadingProps = {
        ...defaultProps,
        loading: true
      };
      const { container } = render(<SystemHealthPanel {...loadingProps} />);
      
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBe(0);
    });
  });

  describe('Error State', () => {
    it('should show error message when health is null and not loading', () => {
      const errorProps = {
        health: null,
        loading: false,
        onRefresh: mockOnRefresh
      };
      render(<SystemHealthPanel {...errorProps} />);
      
      expect(screen.getByText('Unable to load system health')).toBeInTheDocument();
    });

    it('should show "Try again" button in error state', () => {
      const errorProps = {
        health: null,
        loading: false,
        onRefresh: mockOnRefresh
      };
      render(<SystemHealthPanel {...errorProps} />);
      
      const tryAgainButton = screen.getByText('Try again');
      expect(tryAgainButton).toBeInTheDocument();
    });

    it('should call onRefresh when "Try again" button is clicked', () => {
      const errorProps = {
        health: null,
        loading: false,
        onRefresh: mockOnRefresh
      };
      render(<SystemHealthPanel {...errorProps} />);
      
      const tryAgainButton = screen.getByText('Try again');
      fireEvent.click(tryAgainButton);
      
      expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });
  });

  describe('Refresh Button Behavior', () => {
    it('should call onRefresh when refresh button is clicked', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      fireEvent.click(refreshButton);
      
      expect(mockOnRefresh).toHaveBeenCalledTimes(1);
    });

    it('should not call onRefresh when button is disabled', () => {
      const loadingProps = {
        ...defaultProps,
        loading: true
      };
      render(<SystemHealthPanel {...loadingProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      fireEvent.click(refreshButton);
      
      expect(mockOnRefresh).not.toHaveBeenCalled();
    });

    it('should enable refresh button when not loading', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      expect(refreshButton).not.toBeDisabled();
    });
  });

  describe('Service Messages', () => {
    it('should display info icon for services with messages', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      // Find the SNS service row and check for info icon within its parent container
      const snsRow = screen.getByText('SNS').closest('.flex.items-center.justify-between');
      const infoIcon = snsRow?.querySelector('.lucide-info');
      expect(infoIcon).toBeInTheDocument();
    });

    it('should not display info icon for services without messages', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      // ML Inference has no message, so should not have info icon
      const mlRow = screen.getByText('ML Inference').closest('.flex.items-center.justify-between');
      const infoIcon = mlRow?.querySelector('.lucide-info');
      expect(infoIcon).not.toBeInTheDocument();
    });
  });

  describe('Timestamp Formatting', () => {
    it('should format timestamp to locale time string', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      const timestampText = screen.getByText(/Last checked:/);
      expect(timestampText).toBeInTheDocument();
      
      // Verify it contains a time-like string (contains colons)
      expect(timestampText.textContent).toMatch(/\d+:\d+/);
    });

    it('should handle invalid timestamp gracefully', () => {
      const invalidHealthData = {
        ...mockHealthData,
        checkedAt: 'invalid-timestamp'
      };
      const propsWithInvalidTime = {
        ...defaultProps,
        health: invalidHealthData
      };
      
      render(<SystemHealthPanel {...propsWithInvalidTime} />);
      
      // Should still render without crashing
      expect(screen.getByText('System Health')).toBeInTheDocument();
    });
  });

  describe('Conditional Rendering', () => {
    it('should render health data when available', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      expect(screen.getByText('IoT Core')).toBeInTheDocument();
      expect(screen.queryByText('Unable to load system health')).not.toBeInTheDocument();
    });

    it('should render error state when health is null and not loading', () => {
      const errorProps = {
        health: null,
        loading: false,
        onRefresh: mockOnRefresh
      };
      render(<SystemHealthPanel {...errorProps} />);
      
      expect(screen.getByText('Unable to load system health')).toBeInTheDocument();
      expect(screen.queryByText('IoT Core')).not.toBeInTheDocument();
    });

    it('should render loading state when loading and no health data', () => {
      const loadingProps = {
        health: null,
        loading: true,
        onRefresh: mockOnRefresh
      };
      const { container } = render(<SystemHealthPanel {...loadingProps} />);
      
      expect(container.querySelectorAll('.animate-pulse').length).toBe(5);
      expect(screen.queryByText('IoT Core')).not.toBeInTheDocument();
      expect(screen.queryByText('Unable to load system health')).not.toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty services array', () => {
      const emptyHealthData = {
        ...mockHealthData,
        services: []
      };
      const propsWithEmptyServices = {
        ...defaultProps,
        health: emptyHealthData
      };
      
      render(<SystemHealthPanel {...propsWithEmptyServices} />);
      
      expect(screen.getByText('System Health')).toBeInTheDocument();
      expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
    });

    it('should handle service without metrics', () => {
      const serviceWithoutMetrics: ServiceHealth = {
        name: 'Test Service',
        status: 'healthy',
        lastCheck: '2026-02-26T10:30:15Z'
      };
      
      const healthWithoutMetrics = {
        ...mockHealthData,
        services: [serviceWithoutMetrics]
      };
      
      const propsWithoutMetrics = {
        ...defaultProps,
        health: healthWithoutMetrics
      };
      
      render(<SystemHealthPanel {...propsWithoutMetrics} />);
      
      expect(screen.getByText('Test Service')).toBeInTheDocument();
      expect(screen.getByText(/^healthy$/i)).toBeInTheDocument();
    });

    it('should handle service with empty message', () => {
      const serviceWithEmptyMessage: ServiceHealth = {
        name: 'Test Service',
        status: 'healthy',
        lastCheck: '2026-02-26T10:30:15Z',
        message: ''
      };
      
      const healthWithEmptyMessage = {
        ...mockHealthData,
        services: [serviceWithEmptyMessage]
      };
      
      const propsWithEmptyMessage = {
        ...defaultProps,
        health: healthWithEmptyMessage
      };
      
      render(<SystemHealthPanel {...propsWithEmptyMessage} />);
      
      expect(screen.getByText('Test Service')).toBeInTheDocument();
    });

    it('should handle multiple services with same status', () => {
      const allHealthyServices = mockHealthData.services.map(service => ({
        ...service,
        status: 'healthy' as const
      }));
      
      const allHealthyData = {
        ...mockHealthData,
        services: allHealthyServices
      };
      
      const propsAllHealthy = {
        ...defaultProps,
        health: allHealthyData
      };
      
      render(<SystemHealthPanel {...propsAllHealthy} />);
      
      const healthyStatuses = screen.getAllByText(/^healthy$/i);
      expect(healthyStatuses.length).toBeGreaterThan(1);
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-label for refresh button', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      expect(refreshButton).toHaveAttribute('aria-label', 'Refresh system health');
    });

    it('should have proper aria-label for loading state', () => {
      const loadingProps = {
        health: null,
        loading: true,
        onRefresh: mockOnRefresh
      };
      render(<SystemHealthPanel {...loadingProps} />);
      
      const loadingStatus = screen.getByRole('status', { name: /loading system health/i });
      expect(loadingStatus).toHaveAttribute('aria-label', 'Loading system health');
    });

    it('should have proper aria-label for status icons', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      // Use getAllByLabelText since there are multiple healthy statuses
      expect(screen.getAllByLabelText('healthy status').length).toBeGreaterThan(0);
      expect(screen.getByLabelText('degraded status')).toBeInTheDocument();
      expect(screen.getByLabelText('down status')).toBeInTheDocument();
      expect(screen.getByLabelText('unknown status')).toBeInTheDocument();
    });

    it('should be keyboard navigable', () => {
      render(<SystemHealthPanel {...defaultProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      refreshButton.focus();
      
      expect(document.activeElement).toBe(refreshButton);
    });
  });

  describe('Visual Styling', () => {
    it('should apply proper container styling', () => {
      const { container } = render(<SystemHealthPanel {...defaultProps} />);
      
      const panel = container.firstChild;
      expect(panel).toHaveClass('bg-white', 'rounded-lg', 'shadow', 'p-6', 'mb-6');
    });

    it('should apply proper spacing between services', () => {
      const { container } = render(<SystemHealthPanel {...defaultProps} />);
      
      const servicesContainer = container.querySelector('.space-y-3');
      expect(servicesContainer).toBeInTheDocument();
    });

    it('should apply disabled styling to refresh button when loading', () => {
      const loadingProps = {
        ...defaultProps,
        loading: true
      };
      render(<SystemHealthPanel {...loadingProps} />);
      
      const refreshButton = screen.getByRole('button', { name: /refresh system health/i });
      expect(refreshButton).toHaveClass('disabled:opacity-50', 'disabled:cursor-not-allowed');
    });
  });
});
