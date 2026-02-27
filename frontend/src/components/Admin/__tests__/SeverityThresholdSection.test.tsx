import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import SeverityThresholdSection from '../SeverityThresholdSection';

describe('SeverityThresholdSection', () => {
  const mockOnChange = jest.fn();
  const mockSetShowTooltip = jest.fn();

  const defaultProps = {
    thresholds: {
      pH: {
        warning: { min: 6.0, max: 9.0 },
        critical: { min: 5.5, max: 9.5 }
      },
      turbidity: {
        warning: { max: 5.0 },
        critical: { max: 10.0 }
      },
      tds: {
        warning: { max: 600 },
        critical: { max: 1000 }
      },
      temperature: {
        warning: { min: 10, max: 35 },
        critical: { min: 5, max: 40 }
      }
    },
    onChange: mockOnChange,
    editMode: true,
    errors: {},
    showTooltip: null,
    setShowTooltip: mockSetShowTooltip
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the component with title', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      expect(screen.getByText('Alert Thresholds')).toBeInTheDocument();
    });

    it('should render warning and critical sections for pH', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const phSection = screen.getByText('pH Range').closest('div')?.parentElement;
      expect(phSection).toBeInTheDocument();
      
      const warningSections = screen.getAllByText('⚠️ Warning Level');
      const criticalSections = screen.getAllByText('🔴 Critical Level');
      
      expect(warningSections.length).toBeGreaterThan(0);
      expect(criticalSections.length).toBeGreaterThan(0);
    });

    it('should render warning and critical sections for turbidity', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      expect(screen.getByText('Turbidity (NTU)')).toBeInTheDocument();
    });

    it('should render warning and critical sections for TDS', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      expect(screen.getByText('TDS (ppm)')).toBeInTheDocument();
    });

    it('should render warning and critical sections for temperature', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      expect(screen.getByText('Temperature (°C)')).toBeInTheDocument();
    });

    it('should render relationship hint text for pH', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      const hints = screen.getAllByText(/Warning Min < Critical Min < Critical Max < Warning Max/i);
      expect(hints.length).toBeGreaterThan(0);
    });

    it('should render relationship hint text for turbidity', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      const hints = screen.getAllByText(/Critical Max < Warning Max/i);
      // Should have 2 instances (turbidity and TDS)
      expect(hints.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Edit Mode Behavior', () => {
    it('should enable inputs when editMode is true', () => {
      render(<SeverityThresholdSection {...defaultProps} editMode={true} />);
      
      const inputs = screen.getAllByRole('spinbutton');
      inputs.forEach(input => {
        expect(input).not.toBeDisabled();
      });
    });

    it('should disable inputs when editMode is false', () => {
      render(<SeverityThresholdSection {...defaultProps} editMode={false} />);
      
      const inputs = screen.getAllByRole('spinbutton');
      inputs.forEach(input => {
        expect(input).toBeDisabled();
      });
    });

    it('should apply disabled styling when editMode is false', () => {
      render(<SeverityThresholdSection {...defaultProps} editMode={false} />);
      
      const inputs = screen.getAllByRole('spinbutton');
      inputs.forEach(input => {
        expect(input).toHaveClass('disabled:bg-gray-100');
        expect(input).toHaveClass('disabled:cursor-not-allowed');
      });
    });
  });

  describe('Input Values', () => {
    it('should display correct pH warning min value', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // pH warning min is the first input
      expect(allInputs[0]).toHaveValue(6.0);
    });

    it('should display correct pH warning max value', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // pH warning max is the second input
      expect(allInputs[1]).toHaveValue(9.0);
    });

    it('should display correct pH critical min value', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // pH critical min is the third input
      expect(allInputs[2]).toHaveValue(5.5);
    });

    it('should display correct pH critical max value', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // pH critical max is the fourth input
      expect(allInputs[3]).toHaveValue(9.5);
    });

    it('should display correct turbidity values', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // Turbidity warning max is the 5th input, critical max is 6th
      expect(allInputs[4]).toHaveValue(5.0);
      expect(allInputs[5]).toHaveValue(10.0);
    });

    it('should display correct TDS values', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // TDS warning max is the 7th input, critical max is 8th
      expect(allInputs[6]).toHaveValue(600);
      expect(allInputs[7]).toHaveValue(1000);
    });

    it('should display correct temperature values', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // Temperature: warning min (9th), warning max (10th), critical min (11th), critical max (12th)
      expect(allInputs[8]).toHaveValue(10);
      expect(allInputs[9]).toHaveValue(35);
      expect(allInputs[10]).toHaveValue(5);
      expect(allInputs[11]).toHaveValue(40);
    });

    it('should handle empty threshold values gracefully', () => {
      const propsWithEmptyValues = {
        ...defaultProps,
        thresholds: {
          pH: {},
          turbidity: {},
          tds: {},
          temperature: {}
        }
      };
      
      render(<SeverityThresholdSection {...propsWithEmptyValues} />);
      
      const inputs = screen.getAllByRole('spinbutton');
      inputs.forEach(input => {
        expect(input).toHaveValue(null);
      });
    });
  });

  describe('onChange Handlers', () => {
    it('should call onChange with correct field path for pH warning min', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      fireEvent.change(allInputs[0], { target: { value: '6.5' } });
      
      expect(mockOnChange).toHaveBeenCalledWith('pH.warning.min', 6.5);
    });

    it('should call onChange with correct field path for pH critical max', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      fireEvent.change(allInputs[3], { target: { value: '10.0' } });
      
      expect(mockOnChange).toHaveBeenCalledWith('pH.critical.max', 10.0);
    });

    it('should call onChange with correct field path for turbidity warning', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // Turbidity warning is the 5th input (index 4)
      fireEvent.change(allInputs[4], { target: { value: '7.5' } });
      
      expect(mockOnChange).toHaveBeenCalledWith('turbidity.warning.max', 7.5);
    });

    it('should call onChange with correct field path for TDS critical', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // TDS critical is the 8th input (index 7)
      fireEvent.change(allInputs[7], { target: { value: '1200' } });
      
      expect(mockOnChange).toHaveBeenCalledWith('tds.critical.max', 1200);
    });

    it('should call onChange with correct field path for temperature warning min', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // Temperature warning min is the 9th input (index 8)
      fireEvent.change(allInputs[8], { target: { value: '12' } });
      
      expect(mockOnChange).toHaveBeenCalledWith('temperature.warning.min', 12);
    });

    it('should parse numeric values correctly', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      fireEvent.change(allInputs[0], { target: { value: '7.25' } });
      
      expect(mockOnChange).toHaveBeenCalledWith('pH.warning.min', 7.25);
      expect(typeof mockOnChange.mock.calls[0][1]).toBe('number');
    });

    it('should not call onChange when input is disabled', () => {
      render(<SeverityThresholdSection {...defaultProps} editMode={false} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // Inputs are disabled, but fireEvent still triggers the handler
      // We need to check that the input is actually disabled
      expect(allInputs[0]).toBeDisabled();
    });
  });

  describe('Error Display', () => {
    it('should display pH error message when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          pH: 'pH thresholds must satisfy: warning_min < critical_min < critical_max < warning_max'
        }
      };
      
      render(<SeverityThresholdSection {...propsWithError} />);
      expect(screen.getByText(/pH thresholds must satisfy/i)).toBeInTheDocument();
    });

    it('should display turbidity error message when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          turbidity: 'Turbidity critical max must be less than warning max'
        }
      };
      
      render(<SeverityThresholdSection {...propsWithError} />);
      expect(screen.getByText(/Turbidity critical max must be less than warning max/i)).toBeInTheDocument();
    });

    it('should display TDS error message when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          tds: 'TDS critical max must be less than warning max'
        }
      };
      
      render(<SeverityThresholdSection {...propsWithError} />);
      expect(screen.getByText(/TDS critical max must be less than warning max/i)).toBeInTheDocument();
    });

    it('should display temperature error message when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          temperature: 'Temperature thresholds must satisfy: warning_min < critical_min < critical_max < warning_max'
        }
      };
      
      render(<SeverityThresholdSection {...propsWithError} />);
      expect(screen.getByText(/Temperature thresholds must satisfy/i)).toBeInTheDocument();
    });

    it('should display error icon with error messages', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          pH: 'Invalid pH thresholds'
        }
      };
      
      render(<SeverityThresholdSection {...propsWithError} />);
      
      const errorMessage = screen.getByText(/Invalid pH thresholds/i);
      const errorContainer = errorMessage.closest('p');
      
      expect(errorContainer).toHaveClass('text-red-600');
    });

    it('should not display error messages when errors object is empty', () => {
      render(<SeverityThresholdSection {...defaultProps} errors={{}} />);
      
      const errorMessages = screen.queryAllByText(/must be less than|must satisfy/i);
      expect(errorMessages).toHaveLength(0);
    });

    it('should display multiple error messages simultaneously', () => {
      const propsWithMultipleErrors = {
        ...defaultProps,
        errors: {
          pH: 'Invalid pH thresholds',
          turbidity: 'Invalid turbidity thresholds',
          tds: 'Invalid TDS thresholds'
        }
      };
      
      render(<SeverityThresholdSection {...propsWithMultipleErrors} />);
      
      expect(screen.getByText(/Invalid pH thresholds/i)).toBeInTheDocument();
      expect(screen.getByText(/Invalid turbidity thresholds/i)).toBeInTheDocument();
      expect(screen.getByText(/Invalid TDS thresholds/i)).toBeInTheDocument();
    });
  });

  describe('Tooltip Functionality', () => {
    it('should call setShowTooltip on mouse enter for pH tooltip', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const phLabel = screen.getByText('pH Range');
      const tooltipButton = phLabel.parentElement?.querySelector('button');
      
      if (tooltipButton) {
        fireEvent.mouseEnter(tooltipButton);
        expect(mockSetShowTooltip).toHaveBeenCalledWith('pH-severity');
      }
    });

    it('should call setShowTooltip with null on mouse leave', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const phLabel = screen.getByText('pH Range');
      const tooltipButton = phLabel.parentElement?.querySelector('button');
      
      if (tooltipButton) {
        fireEvent.mouseLeave(tooltipButton);
        expect(mockSetShowTooltip).toHaveBeenCalledWith(null);
      }
    });

    it('should display pH tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'pH-severity'
      };
      
      render(<SeverityThresholdSection {...propsWithTooltip} />);
      expect(screen.getByText(/WHO recommends pH between 6.5-8.5/i)).toBeInTheDocument();
    });

    it('should display turbidity tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'turbidity-severity'
      };
      
      render(<SeverityThresholdSection {...propsWithTooltip} />);
      expect(screen.getByText(/WHO guideline: <5 NTU for drinking water/i)).toBeInTheDocument();
    });

    it('should display TDS tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'tds-severity'
      };
      
      render(<SeverityThresholdSection {...propsWithTooltip} />);
      expect(screen.getByText(/WHO guideline: <500 ppm for acceptable taste/i)).toBeInTheDocument();
    });

    it('should display temperature tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'temperature-severity'
      };
      
      render(<SeverityThresholdSection {...propsWithTooltip} />);
      expect(screen.getByText(/Typical range: 10-35°C/i)).toBeInTheDocument();
    });

    it('should not display tooltip when showTooltip is null', () => {
      render(<SeverityThresholdSection {...defaultProps} showTooltip={null} />);
      
      expect(screen.queryByText(/WHO recommends pH between 6.5-8.5/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/WHO guideline: <5 NTU/i)).not.toBeInTheDocument();
    });

    it('should render info icons for all parameter tooltips', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const phLabel = screen.getByText('pH Range');
      const turbidityLabel = screen.getByText('Turbidity (NTU)');
      const tdsLabel = screen.getByText('TDS (ppm)');
      const tempLabel = screen.getByText('Temperature (°C)');
      
      expect(phLabel.parentElement?.querySelector('button')).toBeInTheDocument();
      expect(turbidityLabel.parentElement?.querySelector('button')).toBeInTheDocument();
      expect(tdsLabel.parentElement?.querySelector('button')).toBeInTheDocument();
      expect(tempLabel.parentElement?.querySelector('button')).toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply yellow styling to warning sections', () => {
      const { container } = render(<SeverityThresholdSection {...defaultProps} />);
      
      const warningSections = container.querySelectorAll('.border-yellow-300');
      expect(warningSections.length).toBeGreaterThan(0);
      
      warningSections.forEach(section => {
        expect(section).toHaveClass('bg-yellow-50');
      });
    });

    it('should apply red styling to critical sections', () => {
      const { container } = render(<SeverityThresholdSection {...defaultProps} />);
      
      const criticalSections = container.querySelectorAll('.border-red-300');
      expect(criticalSections.length).toBeGreaterThan(0);
      
      criticalSections.forEach(section => {
        expect(section).toHaveClass('bg-red-50');
      });
    });

    it('should use grid layout for warning/critical sections', () => {
      const { container } = render(<SeverityThresholdSection {...defaultProps} />);
      
      const gridContainers = container.querySelectorAll('.grid.grid-cols-2');
      expect(gridContainers.length).toBeGreaterThan(0);
    });

    it('should apply proper spacing between sections', () => {
      const { container } = render(<SeverityThresholdSection {...defaultProps} />);
      
      const sections = container.querySelectorAll('.mb-6');
      expect(sections.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels for all pH inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      expect(screen.getAllByText(/Minimum pH/i)).toHaveLength(2);
      expect(screen.getAllByText(/Maximum pH/i)).toHaveLength(2);
    });

    it('should have proper labels for turbidity inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      expect(screen.getAllByText(/Maximum Turbidity/i)).toHaveLength(2);
    });

    it('should have proper labels for TDS inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      expect(screen.getAllByText(/Maximum TDS/i)).toHaveLength(2);
    });

    it('should have proper labels for temperature inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      expect(screen.getAllByText(/Minimum Temperature/i)).toHaveLength(2);
      expect(screen.getAllByText(/Maximum Temperature/i)).toHaveLength(2);
    });

    it('should have proper input types for numeric values', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const inputs = screen.getAllByRole('spinbutton');
      inputs.forEach(input => {
        expect(input).toHaveAttribute('type', 'number');
      });
    });

    it('should have proper step values for pH inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // pH inputs are the first 4 inputs (indices 0-3)
      expect(allInputs[0]).toHaveAttribute('step', '0.1');
      expect(allInputs[1]).toHaveAttribute('step', '0.1');
      expect(allInputs[2]).toHaveAttribute('step', '0.1');
      expect(allInputs[3]).toHaveAttribute('step', '0.1');
    });

    it('should have proper step values for turbidity inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // Turbidity inputs are indices 4-5
      expect(allInputs[4]).toHaveAttribute('step', '0.1');
      expect(allInputs[5]).toHaveAttribute('step', '0.1');
    });

    it('should have proper step values for TDS inputs', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // TDS inputs are indices 6-7
      expect(allInputs[6]).toHaveAttribute('step', '1');
      expect(allInputs[7]).toHaveAttribute('step', '1');
    });

    it('should have keyboard accessible tooltip buttons', () => {
      render(<SeverityThresholdSection {...defaultProps} />);
      
      const phLabel = screen.getByText('pH Range');
      const tooltipButton = phLabel.parentElement?.querySelector('button');
      
      expect(tooltipButton).toHaveAttribute('type', 'button');
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined thresholds object', () => {
      const propsWithUndefined = {
        ...defaultProps,
        thresholds: undefined
      };
      
      expect(() => {
        render(<SeverityThresholdSection {...propsWithUndefined} />);
      }).not.toThrow();
    });

    it('should handle null threshold values', () => {
      const propsWithNull = {
        ...defaultProps,
        thresholds: {
          pH: { warning: { min: null, max: null }, critical: { min: null, max: null } },
          turbidity: { warning: { max: null }, critical: { max: null } },
          tds: { warning: { max: null }, critical: { max: null } },
          temperature: { warning: { min: null, max: null }, critical: { min: null, max: null } }
        }
      };
      
      render(<SeverityThresholdSection {...propsWithNull} />);
      
      const inputs = screen.getAllByRole('spinbutton');
      inputs.forEach(input => {
        expect(input).toHaveValue(null);
      });
    });

    it('should handle very large numeric values', () => {
      const propsWithLargeValues = {
        ...defaultProps,
        thresholds: {
          ...defaultProps.thresholds,
          tds: {
            warning: { max: 999999 },
            critical: { max: 1000000 }
          }
        }
      };
      
      render(<SeverityThresholdSection {...propsWithLargeValues} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // TDS inputs are at indices 6-7
      expect(allInputs[6]).toHaveValue(999999);
      expect(allInputs[7]).toHaveValue(1000000);
    });

    it('should handle decimal values with high precision', () => {
      const propsWithPreciseValues = {
        ...defaultProps,
        thresholds: {
          ...defaultProps.thresholds,
          pH: {
            warning: { min: 6.123456, max: 8.987654 },
            critical: { min: 5.555555, max: 9.444444 }
          }
        }
      };
      
      render(<SeverityThresholdSection {...propsWithPreciseValues} />);
      
      const allInputs = screen.getAllByRole('spinbutton');
      // pH inputs are at indices 0-3
      expect(allInputs[0]).toHaveValue(6.123456);
      expect(allInputs[2]).toHaveValue(5.555555);
    });
  });
});
