/**
 * AlertPanel Component Tests
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AlertPanel, Alert } from '../AlertPanel';

describe('AlertPanel Component', () => {
  const mockOnDismiss = jest.fn();
  const mockOnAcknowledge = jest.fn();

  const mockAlerts: Alert[] = [
    {
      id: '1',
      type: 'error',
      title: 'Critical Error',
      message: 'System failure detected',
      timestamp: new Date('2024-01-01T12:00:00Z').toISOString(),
      acknowledged: false,
      dismissible: true
    },
    {
      id: '2',
      type: 'warning',
      title: 'Warning',
      message: 'High temperature detected',
      timestamp: new Date('2024-01-01T11:00:00Z').toISOString(),
      acknowledged: false,
      dismissible: true
    },
    {
      id: '3',
      type: 'info',
      title: 'Information',
      message: 'System update available',
      timestamp: new Date('2024-01-01T10:00:00Z').toISOString(),
      acknowledged: true,
      dismissible: true
    }
  ];

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders alerts correctly', () => {
      render(<AlertPanel alerts={mockAlerts} />);
      
      expect(screen.getByText('Critical Error')).toBeInTheDocument();
      expect(screen.getByText('Warning')).toBeInTheDocument();
      expect(screen.getByText('Information')).toBeInTheDocument();
    });

    it('displays alert count', () => {
      render(<AlertPanel alerts={mockAlerts} />);
      
      expect(screen.getByText('3 active alerts')).toBeInTheDocument();
    });

    it('displays singular alert text for one alert', () => {
      render(<AlertPanel alerts={[mockAlerts[0]]} />);
      
      expect(screen.getByText('1 active alert')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <AlertPanel alerts={mockAlerts} className="custom-class" />
      );
      
      const panel = container.firstChild;
      expect(panel).toHaveClass('custom-class');
    });
  });

  describe('Empty State', () => {
    it('renders empty state when no alerts', () => {
      render(<AlertPanel alerts={[]} />);
      
      expect(screen.getByText('No alerts')).toBeInTheDocument();
      expect(screen.getByText('All systems are operating normally')).toBeInTheDocument();
    });

    it('does not show alert count in empty state', () => {
      render(<AlertPanel alerts={[]} />);
      
      expect(screen.queryByText(/active alert/)).not.toBeInTheDocument();
    });
  });

  describe('Alert Types', () => {
    it('renders error alerts with correct styling', () => {
      const errorAlert: Alert = {
        id: '1',
        type: 'error',
        title: 'Error',
        message: 'Error message',
        timestamp: new Date().toISOString()
      };
      
      const { container } = render(<AlertPanel alerts={[errorAlert]} />);
      
      expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
    });

    it('renders warning alerts with correct styling', () => {
      const warningAlert: Alert = {
        id: '1',
        type: 'warning',
        title: 'Warning',
        message: 'Warning message',
        timestamp: new Date().toISOString()
      };
      
      const { container } = render(<AlertPanel alerts={[warningAlert]} />);
      
      expect(container.querySelector('.bg-yellow-50')).toBeInTheDocument();
    });

    it('renders success alerts with correct styling', () => {
      const successAlert: Alert = {
        id: '1',
        type: 'success',
        title: 'Success',
        message: 'Success message',
        timestamp: new Date().toISOString()
      };
      
      const { container } = render(<AlertPanel alerts={[successAlert]} />);
      
      expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
    });

    it('renders info alerts with correct styling', () => {
      const infoAlert: Alert = {
        id: '1',
        type: 'info',
        title: 'Info',
        message: 'Info message',
        timestamp: new Date().toISOString()
      };
      
      const { container } = render(<AlertPanel alerts={[infoAlert]} />);
      
      expect(container.querySelector('.bg-blue-50')).toBeInTheDocument();
    });
  });

  describe('Alert Actions', () => {
    it('calls onDismiss when dismiss button is clicked', () => {
      render(
        <AlertPanel
          alerts={[mockAlerts[0]]}
          onDismiss={mockOnDismiss}
        />
      );
      
      const dismissButtons = screen.getAllByTitle('Dismiss');
      fireEvent.click(dismissButtons[0]);
      
      expect(mockOnDismiss).toHaveBeenCalledWith('1');
    });

    it('calls onAcknowledge when acknowledge button is clicked', () => {
      render(
        <AlertPanel
          alerts={[mockAlerts[0]]}
          onAcknowledge={mockOnAcknowledge}
        />
      );
      
      const acknowledgeButtons = screen.getAllByTitle('Acknowledge');
      fireEvent.click(acknowledgeButtons[0]);
      
      expect(mockOnAcknowledge).toHaveBeenCalledWith('1');
    });

    it('does not show acknowledge button for acknowledged alerts', () => {
      const acknowledgedAlert: Alert = {
        ...mockAlerts[0],
        acknowledged: true
      };
      
      render(
        <AlertPanel
          alerts={[acknowledgedAlert]}
          onAcknowledge={mockOnAcknowledge}
        />
      );
      
      expect(screen.queryByTitle('Acknowledge')).not.toBeInTheDocument();
    });

    it('does not show dismiss button when dismissible is false', () => {
      const nonDismissibleAlert: Alert = {
        ...mockAlerts[0],
        dismissible: false
      };
      
      render(
        <AlertPanel
          alerts={[nonDismissibleAlert]}
          onDismiss={mockOnDismiss}
        />
      );
      
      expect(screen.queryByTitle('Dismiss')).not.toBeInTheDocument();
    });

    it('does not render action buttons when callbacks not provided', () => {
      render(<AlertPanel alerts={[mockAlerts[0]]} />);
      
      expect(screen.queryByTitle('Dismiss')).not.toBeInTheDocument();
      expect(screen.queryByTitle('Acknowledge')).not.toBeInTheDocument();
    });
  });

  describe('Acknowledged State', () => {
    it('applies opacity to acknowledged alerts', () => {
      const acknowledgedAlert: Alert = {
        ...mockAlerts[0],
        acknowledged: true
      };
      
      const { container } = render(<AlertPanel alerts={[acknowledgedAlert]} />);
      
      expect(container.querySelector('.opacity-60')).toBeInTheDocument();
    });

    it('does not apply opacity to unacknowledged alerts', () => {
      const { container } = render(<AlertPanel alerts={[mockAlerts[0]]} />);
      
      expect(container.querySelector('.opacity-60')).not.toBeInTheDocument();
    });
  });

  describe('Max Alerts', () => {
    it('limits displayed alerts to maxAlerts', () => {
      const manyAlerts = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        type: 'info' as const,
        title: `Alert ${i}`,
        message: `Message ${i}`,
        timestamp: new Date().toISOString()
      }));
      
      render(<AlertPanel alerts={manyAlerts} maxAlerts={5} />);
      
      expect(screen.getByText('Alert 0')).toBeInTheDocument();
      expect(screen.getByText('Alert 4')).toBeInTheDocument();
      expect(screen.queryByText('Alert 5')).not.toBeInTheDocument();
    });

    it('shows overflow message when alerts exceed maxAlerts', () => {
      const manyAlerts = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        type: 'info' as const,
        title: `Alert ${i}`,
        message: `Message ${i}`,
        timestamp: new Date().toISOString()
      }));
      
      render(<AlertPanel alerts={manyAlerts} maxAlerts={10} />);
      
      expect(screen.getByText('+5 more alerts')).toBeInTheDocument();
    });

    it('uses default maxAlerts of 10', () => {
      const manyAlerts = Array.from({ length: 15 }, (_, i) => ({
        id: `${i}`,
        type: 'info' as const,
        title: `Alert ${i}`,
        message: `Message ${i}`,
        timestamp: new Date().toISOString()
      }));
      
      render(<AlertPanel alerts={manyAlerts} />);
      
      expect(screen.getByText('Alert 9')).toBeInTheDocument();
      expect(screen.queryByText('Alert 10')).not.toBeInTheDocument();
    });
  });

  describe('Timestamp Formatting', () => {
    it('formats recent timestamps correctly', () => {
      const recentAlert: Alert = {
        id: '1',
        type: 'info',
        title: 'Recent',
        message: 'Message',
        timestamp: new Date(Date.now() - 30000).toISOString() // 30 seconds ago
      };
      
      render(<AlertPanel alerts={[recentAlert]} />);
      
      expect(screen.getByText('Just now')).toBeInTheDocument();
    });
  });

  describe('Memoization', () => {
    it('does not re-render when props are the same', () => {
      const { rerender } = render(<AlertPanel alerts={mockAlerts} />);
      const firstRender = screen.getByText('Critical Error');
      
      rerender(<AlertPanel alerts={mockAlerts} />);
      const secondRender = screen.getByText('Critical Error');
      
      expect(firstRender).toBe(secondRender);
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(<AlertPanel alerts={mockAlerts} />);
      
      expect(screen.getByText('Alerts')).toBeInTheDocument();
    });

    it('has scrollable container for many alerts', () => {
      const { container } = render(<AlertPanel alerts={mockAlerts} />);
      
      expect(container.querySelector('.overflow-y-auto')).toBeInTheDocument();
    });
  });
});
