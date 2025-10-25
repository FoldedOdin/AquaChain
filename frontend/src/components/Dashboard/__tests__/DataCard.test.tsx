/**
 * DataCard Component Tests
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DataCard } from '../DataCard';

describe('DataCard Component', () => {
  const mockAction = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('renders title and value correctly', () => {
      render(<DataCard title="Total Devices" value={42} />);
      
      expect(screen.getByText('Total Devices')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('renders string values correctly', () => {
      render(<DataCard title="Status" value="Active" />);
      
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('renders subtitle when provided', () => {
      render(<DataCard title="Temperature" value={25} subtitle="°C" />);
      
      expect(screen.getByText('°C')).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(
        <DataCard title="Test" value={1} className="custom-class" />
      );
      
      const card = container.firstChild;
      expect(card).toHaveClass('custom-class');
    });
  });

  describe('Loading State', () => {
    it('renders loading skeleton when loading is true', () => {
      const { container } = render(
        <DataCard title="Test" value={1} loading={true} />
      );
      
      expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
      expect(screen.queryByText('Test')).not.toBeInTheDocument();
    });

    it('does not render content when loading', () => {
      render(<DataCard title="Test" value={1} loading={true} />);
      
      expect(screen.queryByText('Test')).not.toBeInTheDocument();
      expect(screen.queryByText('1')).not.toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    it('renders upward trend correctly', () => {
      render(
        <DataCard
          title="Sales"
          value={100}
          trend={{ value: 15, direction: 'up', label: 'vs last month' }}
        />
      );
      
      expect(screen.getByText('15%')).toBeInTheDocument();
      expect(screen.getByText('vs last month')).toBeInTheDocument();
      expect(screen.getByText('15%')).toHaveClass('text-green-600');
    });

    it('renders downward trend correctly', () => {
      render(
        <DataCard
          title="Errors"
          value={5}
          trend={{ value: 20, direction: 'down' }}
        />
      );
      
      expect(screen.getByText('20%')).toBeInTheDocument();
      expect(screen.getByText('20%')).toHaveClass('text-red-600');
    });

    it('renders neutral trend correctly', () => {
      render(
        <DataCard
          title="Status"
          value={50}
          trend={{ value: 0, direction: 'neutral' }}
        />
      );
      
      expect(screen.getByText('0%')).toBeInTheDocument();
      expect(screen.getByText('0%')).toHaveClass('text-gray-600');
    });

    it('renders trend without label', () => {
      render(
        <DataCard
          title="Test"
          value={1}
          trend={{ value: 10, direction: 'up' }}
        />
      );
      
      expect(screen.getByText('10%')).toBeInTheDocument();
      expect(screen.queryByText('vs last month')).not.toBeInTheDocument();
    });
  });

  describe('Action Button', () => {
    it('renders action button when provided', () => {
      render(
        <DataCard
          title="Devices"
          value={10}
          action={{ label: 'View All', onClick: mockAction }}
        />
      );
      
      const button = screen.getByText('View All →');
      expect(button).toBeInTheDocument();
    });

    it('calls onClick handler when action button is clicked', () => {
      render(
        <DataCard
          title="Devices"
          value={10}
          action={{ label: 'View All', onClick: mockAction }}
        />
      );
      
      const button = screen.getByText('View All →');
      fireEvent.click(button);
      
      expect(mockAction).toHaveBeenCalledTimes(1);
    });

    it('does not render action button when not provided', () => {
      render(<DataCard title="Test" value={1} />);
      
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });
  });

  describe('Icon', () => {
    it('renders icon when provided', () => {
      const icon = <svg data-testid="test-icon" />;
      render(<DataCard title="Test" value={1} icon={icon} />);
      
      expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    });

    it('does not render icon container when icon not provided', () => {
      const { container } = render(<DataCard title="Test" value={1} />);
      
      expect(container.querySelector('.w-12.h-12')).not.toBeInTheDocument();
    });
  });

  describe('Memoization', () => {
    it('does not re-render when props are the same', () => {
      const { rerender } = render(<DataCard title="Test" value={1} />);
      const firstRender = screen.getByText('Test');
      
      rerender(<DataCard title="Test" value={1} />);
      const secondRender = screen.getByText('Test');
      
      expect(firstRender).toBe(secondRender);
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(<DataCard title="Test Metric" value={42} />);
      
      expect(screen.getByText('Test Metric')).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
    });

    it('maintains hover state styling', () => {
      const { container } = render(<DataCard title="Test" value={1} />);
      const card = container.firstChild;
      
      expect(card).toHaveClass('hover:shadow-md');
    });
  });
});
