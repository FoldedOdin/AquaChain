import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import MLSettingsSection from '../MLSettingsSection';

describe('MLSettingsSection', () => {
  const mockOnChange = jest.fn();
  const mockSetShowTooltip = jest.fn();

  const defaultProps = {
    mlSettings: {
      anomalyDetectionEnabled: true,
      modelVersion: 'v1.2',
      confidenceThreshold: 0.85,
      retrainingFrequencyDays: 30,
      driftDetectionEnabled: true,
      lastDriftScore: 0.023,
      lastDriftCheckAt: '2026-02-26T09:45:00Z'
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
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('ML Configuration')).toBeInTheDocument();
    });

    it('should render anomaly detection toggle', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Enable Anomaly Detection')).toBeInTheDocument();
      const checkbox = screen.getByRole('checkbox', { name: '' });
      expect(checkbox).toBeInTheDocument();
    });

    it('should render model version input', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Model Version')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('e.g., v1.2')).toBeInTheDocument();
    });

    it('should render confidence threshold slider', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText(/Confidence Threshold: 0.85/)).toBeInTheDocument();
      const slider = screen.getByRole('slider');
      expect(slider).toBeInTheDocument();
    });

    it('should render retraining frequency input', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Retraining Frequency (days)')).toBeInTheDocument();
      const input = screen.getByRole('spinbutton');
      expect(input).toBeInTheDocument();
    });

    it('should render drift detection toggle', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Enable Drift Detection')).toBeInTheDocument();
    });

    it('should render drift score when available', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Drift Monitoring')).toBeInTheDocument();
      expect(screen.getByText(/Last Drift Score:/)).toBeInTheDocument();
      expect(screen.getByText(/0.0230/)).toBeInTheDocument();
    });

    it('should not render drift score when not available', () => {
      const propsWithoutDrift = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          lastDriftScore: undefined,
          lastDriftCheckAt: undefined
        }
      };
      render(<MLSettingsSection {...propsWithoutDrift} />);
      expect(screen.queryByText('Drift Monitoring')).not.toBeInTheDocument();
    });

    it('should render all info icons for tooltips', () => {
      const { container } = render(<MLSettingsSection {...defaultProps} />);
      const infoButtons = container.querySelectorAll('button[type="button"]');
      expect(infoButtons.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('Edit Mode Behavior', () => {
    it('should enable all controls when editMode is true', () => {
      render(<MLSettingsSection {...defaultProps} editMode={true} />);
      
      const checkboxes = screen.getAllByRole('checkbox');
      checkboxes.forEach(checkbox => {
        expect(checkbox).not.toBeDisabled();
      });

      const textInput = screen.getByPlaceholderText('e.g., v1.2');
      expect(textInput).not.toBeDisabled();

      const slider = screen.getByRole('slider');
      expect(slider).not.toBeDisabled();

      const numberInput = screen.getByRole('spinbutton');
      expect(numberInput).not.toBeDisabled();
    });

    it('should disable all controls when editMode is false', () => {
      render(<MLSettingsSection {...defaultProps} editMode={false} />);
      
      const checkboxes = screen.getAllByRole('checkbox');
      checkboxes.forEach(checkbox => {
        expect(checkbox).toBeDisabled();
      });

      const textInput = screen.getByPlaceholderText('e.g., v1.2');
      expect(textInput).toBeDisabled();

      const slider = screen.getByRole('slider');
      expect(slider).toBeDisabled();

      const numberInput = screen.getByRole('spinbutton');
      expect(numberInput).toBeDisabled();
    });
  });

  describe('Input Values', () => {
    it('should display correct anomaly detection toggle state', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes[0]).toBeChecked();
    });

    it('should display correct model version value', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., v1.2 or latest');
      expect(input).toHaveValue('v1.2');
    });

    it('should display correct confidence threshold value', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const slider = screen.getByRole('slider');
      expect(slider).toHaveValue('0.85');
    });

    it('should display confidence threshold with 2 decimal places', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText(/Confidence Threshold: 0.85/)).toBeInTheDocument();
    });

    it('should display correct retraining frequency value', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(30);
    });

    it('should display correct drift detection toggle state', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes[1]).toBeChecked();
    });

    it('should display drift score with 4 decimal precision', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText(/0.0230/)).toBeInTheDocument();
    });

    it('should display last drift check timestamp', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
    });
  });

  describe('Toggle Controls', () => {
    it('should call onChange when anomaly detection toggle is clicked', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.anomalyDetectionEnabled', false);
    });

    it('should call onChange when drift detection toggle is clicked', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[1]);
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.driftDetectionEnabled', false);
    });

    it('should toggle anomaly detection from false to true', () => {
      const propsWithDisabled = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          anomalyDetectionEnabled: false
        }
      };
      render(<MLSettingsSection {...propsWithDisabled} />);
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[0]);
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.anomalyDetectionEnabled', true);
    });
  });

  describe('Slider Control', () => {
    it('should call onChange when slider value changes', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '0.90' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.confidenceThreshold', 0.90);
    });

    it('should update displayed value when slider changes', () => {
      const { rerender } = render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText(/Confidence Threshold: 0.85/)).toBeInTheDocument();
      
      const updatedProps = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          confidenceThreshold: 0.90
        }
      };
      rerender(<MLSettingsSection {...updatedProps} />);
      expect(screen.getByText(/Confidence Threshold: 0.90/)).toBeInTheDocument();
    });

    it('should handle minimum slider value (0.0)', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '0.0' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.confidenceThreshold', 0.0);
    });

    it('should handle maximum slider value (1.0)', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const slider = screen.getByRole('slider');
      fireEvent.change(slider, { target: { value: '1.0' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.confidenceThreshold', 1.0);
    });
  });

  describe('Number Input Validation', () => {
    it('should call onChange when retraining frequency changes', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      fireEvent.change(input, { target: { value: '45' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.retrainingFrequencyDays', 45);
    });

    it('should parse numeric values correctly', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      fireEvent.change(input, { target: { value: '7' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.retrainingFrequencyDays', 7);
      expect(typeof mockOnChange.mock.calls[0][1]).toBe('number');
    });

    it('should handle minimum valid value (1)', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      fireEvent.change(input, { target: { value: '1' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.retrainingFrequencyDays', 1);
    });

    it('should handle maximum valid value (365)', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      fireEvent.change(input, { target: { value: '365' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.retrainingFrequencyDays', 365);
    });

    it('should not call onChange for invalid numeric input', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      mockOnChange.mockClear();
      fireEvent.change(input, { target: { value: 'abc' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.retrainingFrequencyDays', NaN);
    });
  });

  describe('Warning Message Display', () => {
    it('should display warning when retraining frequency is less than 7 days', () => {
      const propsWithLowFrequency = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          retrainingFrequencyDays: 5
        }
      };
      render(<MLSettingsSection {...propsWithLowFrequency} />);
      expect(screen.getByText(/Frequent retraining may increase costs/)).toBeInTheDocument();
    });

    it('should not display warning when retraining frequency is 7 or more days', () => {
      const propsWithNormalFrequency = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          retrainingFrequencyDays: 7
        }
      };
      render(<MLSettingsSection {...propsWithNormalFrequency} />);
      expect(screen.queryByText(/Frequent retraining may increase costs/)).not.toBeInTheDocument();
    });

    it('should display warning icon with warning message', () => {
      const propsWithLowFrequency = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          retrainingFrequencyDays: 3
        }
      };
      render(<MLSettingsSection {...propsWithLowFrequency} />);
      const warningMessage = screen.getByText(/Frequent retraining may increase costs/);
      expect(warningMessage).toHaveClass('text-yellow-700');
    });
  });

  describe('Text Input', () => {
    it('should call onChange when model version changes', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., v1.2 or latest');
      fireEvent.change(input, { target: { value: 'v2.0' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.modelVersion', 'v2.0');
    });

    it('should handle empty model version', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., v1.2 or latest');
      fireEvent.change(input, { target: { value: '' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.modelVersion', '');
    });

    it('should handle special characters in model version', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., v1.2 or latest');
      fireEvent.change(input, { target: { value: 'v1.2-beta' } });
      expect(mockOnChange).toHaveBeenCalledWith('mlSettings.modelVersion', 'v1.2-beta');
    });
  });

  describe('Error Display', () => {
    it('should display anomaly detection error when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          'mlSettings.anomalyDetectionEnabled': 'Anomaly detection configuration error'
        }
      };
      render(<MLSettingsSection {...propsWithError} />);
      expect(screen.getByText('Anomaly detection configuration error')).toBeInTheDocument();
    });

    it('should display model version error when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          'mlSettings.modelVersion': 'Invalid model version'
        }
      };
      render(<MLSettingsSection {...propsWithError} />);
      expect(screen.getByText('Invalid model version')).toBeInTheDocument();
    });

    it('should display confidence threshold error when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          'mlSettings.confidenceThreshold': 'Confidence threshold must be between 0.0 and 1.0'
        }
      };
      render(<MLSettingsSection {...propsWithError} />);
      expect(screen.getByText('Confidence threshold must be between 0.0 and 1.0')).toBeInTheDocument();
    });

    it('should display retraining frequency error when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          'mlSettings.retrainingFrequencyDays': 'Retraining frequency must be between 1 and 365 days'
        }
      };
      render(<MLSettingsSection {...propsWithError} />);
      expect(screen.getByText('Retraining frequency must be between 1 and 365 days')).toBeInTheDocument();
    });

    it('should display drift detection error when present', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          'mlSettings.driftDetectionEnabled': 'Drift detection configuration error'
        }
      };
      render(<MLSettingsSection {...propsWithError} />);
      expect(screen.getByText('Drift detection configuration error')).toBeInTheDocument();
    });

    it('should display multiple errors simultaneously', () => {
      const propsWithMultipleErrors = {
        ...defaultProps,
        errors: {
          'mlSettings.modelVersion': 'Invalid model version',
          'mlSettings.confidenceThreshold': 'Invalid threshold',
          'mlSettings.retrainingFrequencyDays': 'Invalid frequency'
        }
      };
      render(<MLSettingsSection {...propsWithMultipleErrors} />);
      expect(screen.getByText('Invalid model version')).toBeInTheDocument();
      expect(screen.getByText('Invalid threshold')).toBeInTheDocument();
      expect(screen.getByText('Invalid frequency')).toBeInTheDocument();
    });

    it('should apply error styling to error messages', () => {
      const propsWithError = {
        ...defaultProps,
        errors: {
          'mlSettings.modelVersion': 'Error message'
        }
      };
      render(<MLSettingsSection {...propsWithError} />);
      const errorMessage = screen.getByText('Error message');
      expect(errorMessage).toHaveClass('text-red-600');
    });
  });

  describe('Tooltip Functionality', () => {
    it('should call setShowTooltip on mouse enter for anomaly detection tooltip', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const label = screen.getByText('Enable Anomaly Detection');
      const tooltipButton = label.parentElement?.querySelector('button');
      
      if (tooltipButton) {
        fireEvent.mouseEnter(tooltipButton);
        expect(mockSetShowTooltip).toHaveBeenCalledWith('anomaly-detection');
      }
    });

    it('should call setShowTooltip with null on mouse leave', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const label = screen.getByText('Enable Anomaly Detection');
      const tooltipButton = label.parentElement?.querySelector('button');
      
      if (tooltipButton) {
        fireEvent.mouseLeave(tooltipButton);
        expect(mockSetShowTooltip).toHaveBeenCalledWith(null);
      }
    });

    it('should display anomaly detection tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'anomaly-detection'
      };
      render(<MLSettingsSection {...propsWithTooltip} />);
      expect(screen.getByText(/ML-based identification of unusual water quality patterns/)).toBeInTheDocument();
    });

    it('should display model version tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'model-version'
      };
      render(<MLSettingsSection {...propsWithTooltip} />);
      expect(screen.getByText(/Current ML model version used for predictions/)).toBeInTheDocument();
    });

    it('should display confidence threshold tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'confidence-threshold'
      };
      render(<MLSettingsSection {...propsWithTooltip} />);
      expect(screen.getByText(/Minimum probability score/)).toBeInTheDocument();
      expect(screen.getByText(/Higher values increase reliability/)).toBeInTheDocument();
    });

    it('should display retraining frequency tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'retraining-frequency'
      };
      render(<MLSettingsSection {...propsWithTooltip} />);
      expect(screen.getByText(/How often ML models are retrained/)).toBeInTheDocument();
    });

    it('should display drift detection tooltip content when showTooltip matches', () => {
      const propsWithTooltip = {
        ...defaultProps,
        showTooltip: 'drift-detection'
      };
      render(<MLSettingsSection {...propsWithTooltip} />);
      expect(screen.getByText(/Monitor for model performance degradation/)).toBeInTheDocument();
    });

    it('should not display tooltip when showTooltip is null', () => {
      render(<MLSettingsSection {...defaultProps} showTooltip={null} />);
      expect(screen.queryByText(/ML-based identification/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Current ML model version/)).not.toBeInTheDocument();
    });
  });

  describe('Conditional Rendering', () => {
    it('should render drift score section when lastDriftScore is defined', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Drift Monitoring')).toBeInTheDocument();
      expect(screen.getByText(/Last Drift Score:/)).toBeInTheDocument();
    });

    it('should not render drift score section when lastDriftScore is undefined', () => {
      const propsWithoutDrift = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          lastDriftScore: undefined
        }
      };
      render(<MLSettingsSection {...propsWithoutDrift} />);
      expect(screen.queryByText('Drift Monitoring')).not.toBeInTheDocument();
    });

    it('should render drift score with timestamp when both are available', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText(/Last Drift Score:/)).toBeInTheDocument();
      expect(screen.getByText(/Last checked:/)).toBeInTheDocument();
    });

    it('should render drift score without timestamp when timestamp is missing', () => {
      const propsWithoutTimestamp = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          lastDriftCheckAt: undefined
        }
      };
      render(<MLSettingsSection {...propsWithoutTimestamp} />);
      expect(screen.getByText(/Last Drift Score:/)).toBeInTheDocument();
      expect(screen.queryByText(/Last checked:/)).not.toBeInTheDocument();
    });
  });

  describe('Visual Styling', () => {
    it('should apply proper styling to drift monitoring section', () => {
      const { container } = render(<MLSettingsSection {...defaultProps} />);
      const driftSection = container.querySelector('.bg-blue-50');
      expect(driftSection).toBeInTheDocument();
      expect(driftSection).toHaveClass('border-blue-200');
    });

    it('should apply proper spacing between sections', () => {
      const { container } = render(<MLSettingsSection {...defaultProps} />);
      const sections = container.querySelectorAll('.mb-4');
      expect(sections.length).toBeGreaterThan(0);
    });

    it('should use proper toggle switch styling', () => {
      const { container } = render(<MLSettingsSection {...defaultProps} />);
      const toggles = container.querySelectorAll('.peer-checked\\:bg-blue-600');
      expect(toggles.length).toBe(2);
    });
  });

  describe('Accessibility', () => {
    it('should have proper labels for all inputs', () => {
      render(<MLSettingsSection {...defaultProps} />);
      expect(screen.getByText('Enable Anomaly Detection')).toBeInTheDocument();
      expect(screen.getByText('Model Version')).toBeInTheDocument();
      expect(screen.getByText(/Confidence Threshold:/)).toBeInTheDocument();
      expect(screen.getByText('Retraining Frequency (days)')).toBeInTheDocument();
      expect(screen.getByText('Enable Drift Detection')).toBeInTheDocument();
    });

    it('should have proper input types', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const textInput = screen.getByPlaceholderText('e.g., v1.2 or latest');
      expect(textInput).toHaveAttribute('type', 'text');
      
      const slider = screen.getByRole('slider');
      expect(slider).toHaveAttribute('type', 'range');
      
      const numberInput = screen.getByRole('spinbutton');
      expect(numberInput).toHaveAttribute('type', 'number');
    });

    it('should have proper slider attributes', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const slider = screen.getByRole('slider');
      expect(slider).toHaveAttribute('min', '0');
      expect(slider).toHaveAttribute('max', '1');
      expect(slider).toHaveAttribute('step', '0.01');
    });

    it('should have proper number input attributes', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveAttribute('min', '1');
      expect(input).toHaveAttribute('max', '365');
    });

    it('should have keyboard accessible tooltip buttons', () => {
      render(<MLSettingsSection {...defaultProps} />);
      const label = screen.getByText('Enable Anomaly Detection');
      const tooltipButton = label.parentElement?.querySelector('button');
      expect(tooltipButton).toHaveAttribute('type', 'button');
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero drift score', () => {
      const propsWithZeroDrift = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          lastDriftScore: 0
        }
      };
      render(<MLSettingsSection {...propsWithZeroDrift} />);
      expect(screen.getByText(/0.0000/)).toBeInTheDocument();
    });

    it('should handle very small drift score', () => {
      const propsWithSmallDrift = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          lastDriftScore: 0.0001
        }
      };
      render(<MLSettingsSection {...propsWithSmallDrift} />);
      expect(screen.getByText(/0.0001/)).toBeInTheDocument();
    });

    it('should handle large drift score', () => {
      const propsWithLargeDrift = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          lastDriftScore: 0.9999
        }
      };
      render(<MLSettingsSection {...propsWithLargeDrift} />);
      expect(screen.getByText(/0.9999/)).toBeInTheDocument();
    });

    it('should handle empty model version string', () => {
      const propsWithEmptyVersion = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          modelVersion: ''
        }
      };
      render(<MLSettingsSection {...propsWithEmptyVersion} />);
      const input = screen.getByPlaceholderText('e.g., v1.2 or latest');
      expect(input).toHaveValue('');
    });

    it('should handle boundary retraining frequency (1 day)', () => {
      const propsWithMinFrequency = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          retrainingFrequencyDays: 1
        }
      };
      render(<MLSettingsSection {...propsWithMinFrequency} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(1);
      expect(screen.getByText(/Frequent retraining may increase costs/)).toBeInTheDocument();
    });

    it('should handle boundary retraining frequency (365 days)', () => {
      const propsWithMaxFrequency = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          retrainingFrequencyDays: 365
        }
      };
      render(<MLSettingsSection {...propsWithMaxFrequency} />);
      const input = screen.getByRole('spinbutton');
      expect(input).toHaveValue(365);
    });

    it('should handle all toggles disabled', () => {
      const propsWithAllDisabled = {
        ...defaultProps,
        mlSettings: {
          ...defaultProps.mlSettings,
          anomalyDetectionEnabled: false,
          driftDetectionEnabled: false
        }
      };
      render(<MLSettingsSection {...propsWithAllDisabled} />);
      const checkboxes = screen.getAllByRole('checkbox');
      checkboxes.forEach(checkbox => {
        expect(checkbox).not.toBeChecked();
      });
    });
  });
});
