import React from 'react';
import { Info, AlertTriangle } from 'lucide-react';

interface MLSettingsSectionProps {
  mlSettings?: {
    anomalyDetectionEnabled: boolean;
    modelVersion: string;
    confidenceThreshold: number;
    retrainingFrequencyDays: number;
    driftDetectionEnabled: boolean;
    lastDriftScore?: number;
    lastDriftCheckAt?: string;
  };
  onChange: (field: string, value: any) => void;
  editMode: boolean;
  errors: Record<string, string>;
  showTooltip: string | null;
  setShowTooltip: (field: string | null) => void;
}

const MLSettingsSection: React.FC<MLSettingsSectionProps> = ({
  mlSettings,
  onChange,
  editMode,
  errors,
  showTooltip,
  setShowTooltip
}) => {
  // Default values if mlSettings is undefined
  const settings = mlSettings || {
    anomalyDetectionEnabled: true,
    modelVersion: 'latest',
    confidenceThreshold: 0.85,
    retrainingFrequencyDays: 30,
    driftDetectionEnabled: true
  };

  // Tooltip component matching existing pattern
  const Tooltip = ({ field, content }: { field: string; content: string }) => (
    <div className="relative inline-block">
      <button
        type="button"
        onMouseEnter={() => setShowTooltip(field)}
        onMouseLeave={() => setShowTooltip(null)}
        className="ml-1 text-gray-400 hover:text-gray-600 focus:outline-none"
      >
        <Info size={16} />
      </button>
      {showTooltip === field && (
        <div className="absolute z-10 w-64 p-2 mt-1 text-sm text-white bg-gray-900 rounded-lg shadow-lg -left-24">
          {content}
          <div className="absolute w-2 h-2 bg-gray-900 transform rotate-45 -top-1 left-1/2"></div>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        ML Configuration Settings
      </h3>

      <div className="space-y-6">
        {/* Anomaly Detection Toggle */}
        <div>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.anomalyDetectionEnabled}
              onChange={(e) => onChange('mlSettings.anomalyDetectionEnabled', e.target.checked)}
              disabled={!editMode}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:cursor-not-allowed"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">
              Enable Anomaly Detection
              <Tooltip
                field="anomaly-detection"
                content="When enabled, ML models analyze all incoming sensor readings for unusual patterns. Disabling skips anomaly analysis but continues WQI predictions."
              />
            </span>
          </label>
          {errors['mlSettings.anomalyDetectionEnabled'] && (
            <p className="text-red-600 text-sm mt-1">{errors['mlSettings.anomalyDetectionEnabled']}</p>
          )}
        </div>

        {/* Model Version */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Model Version
            <Tooltip
              field="model-version"
              content="Specifies which ML model version to use for predictions. Use 'latest' for the most recent model, or specify a version like 'v1.2' for a specific model."
            />
          </label>
          <input
            type="text"
            value={settings.modelVersion}
            onChange={(e) => onChange('mlSettings.modelVersion', e.target.value)}
            disabled={!editMode}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="e.g., v1.2 or latest"
          />
          {errors['mlSettings.modelVersion'] && (
            <p className="text-red-600 text-sm mt-1">{errors['mlSettings.modelVersion']}</p>
          )}
        </div>

        {/* Confidence Threshold Slider */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Confidence Threshold: {settings.confidenceThreshold.toFixed(2)}
            <Tooltip
              field="confidence-threshold"
              content="Minimum probability score (0.0-1.0) required for ML predictions to be accepted. Higher values increase reliability but may trigger more fallback calculations."
            />
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={settings.confidenceThreshold}
            onChange={(e) => onChange('mlSettings.confidenceThreshold', parseFloat(e.target.value))}
            disabled={!editMode}
            className="block w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0.0 (Low)</span>
            <span>0.5 (Medium)</span>
            <span>1.0 (High)</span>
          </div>
          {errors['mlSettings.confidenceThreshold'] && (
            <p className="text-red-600 text-sm mt-1">{errors['mlSettings.confidenceThreshold']}</p>
          )}
        </div>

        {/* Retraining Frequency */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Retraining Frequency (days)
            <Tooltip
              field="retraining-frequency"
              content="How often ML models are retrained (1-365 days). Balance model freshness with computational costs."
            />
          </label>
          <input
            type="number"
            min="1"
            max="365"
            value={settings.retrainingFrequencyDays}
            onChange={(e) => onChange('mlSettings.retrainingFrequencyDays', parseInt(e.target.value, 10))}
            disabled={!editMode}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          {settings.retrainingFrequencyDays < 7 && (
            <div className="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400 rounded-r">
              <div className="flex items-start">
                <AlertTriangle className="text-yellow-600 mr-2 flex-shrink-0 mt-0.5" size={16} />
                <p className="text-xs text-yellow-700">
                  Frequent retraining may increase costs
                </p>
              </div>
            </div>
          )}
          {errors['mlSettings.retrainingFrequencyDays'] && (
            <p className="text-red-600 text-sm mt-1">{errors['mlSettings.retrainingFrequencyDays']}</p>
          )}
        </div>

        {/* Drift Detection Toggle */}
        <div>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.driftDetectionEnabled}
              onChange={(e) => onChange('mlSettings.driftDetectionEnabled', e.target.checked)}
              disabled={!editMode}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:cursor-not-allowed"
            />
            <span className="ml-2 text-sm font-medium text-gray-700">
              Enable Drift Detection
              <Tooltip
                field="drift-detection"
                content="Monitor for model performance degradation over time due to changing data patterns. When enabled, drift scores are calculated every 100 predictions."
              />
            </span>
          </label>
          {errors['mlSettings.driftDetectionEnabled'] && (
            <p className="text-red-600 text-sm mt-1">{errors['mlSettings.driftDetectionEnabled']}</p>
          )}
        </div>

        {/* Drift Monitoring Status (conditional) */}
        {settings.lastDriftScore !== undefined && (
          <div className="border rounded-lg p-4 bg-gray-50">
            <h4 className="text-sm font-medium text-gray-900 mb-2">
              Drift Monitoring Status
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Last Drift Score:</span>
                <span className="font-mono font-medium text-gray-900">
                  {settings.lastDriftScore.toFixed(4)}
                </span>
              </div>
              {settings.lastDriftCheckAt && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Last Check:</span>
                  <span className="text-gray-900">
                    {new Date(settings.lastDriftCheckAt).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MLSettingsSection;
