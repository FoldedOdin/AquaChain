import { useState, useEffect, useMemo } from 'react';
import { SystemConfiguration as SystemConfigType, SystemHealthResponse } from '../../types/admin';
import { 
  getSystemConfiguration, 
  updateSystemConfiguration,
  validateConfiguration,
  getSystemHealth
} from '../../services/adminService';
import ConfigurationConfirmModal from './ConfigurationConfirmModal';
import SeverityThresholdSection from './SeverityThresholdSection';
import MLSettingsSection from './MLSettingsSection';
import SystemHealthPanel from './SystemHealthPanel';
import { AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';

const SystemConfiguration = () => {
  const [config, setConfig] = useState<SystemConfigType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<SystemConfigType | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [showTooltip, setShowTooltip] = useState<string | null>(null);

  // Phase 3c: System health state
  const [systemHealth, setSystemHealth] = useState<SystemHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState(false);

  // Calculate unsaved changes count
  const unsavedChangesCount = useMemo(() => {
    if (!config || !formData || !editMode) return 0;
    
    let changes = 0;
    const checkChanges = (obj1: any, obj2: any, path = ''): void => {
      Object.keys(obj1).forEach(key => {
        const newPath = path ? `${path}.${key}` : key;
        if (typeof obj1[key] === 'object' && obj1[key] !== null && !Array.isArray(obj1[key])) {
          checkChanges(obj1[key], obj2[key], newPath);
        } else if (JSON.stringify(obj1[key]) !== JSON.stringify(obj2[key])) {
          changes++;
        }
      });
    };
    checkChanges(config, formData);
    return changes;
  }, [config, formData, editMode]);

  useEffect(() => {
    loadConfiguration();
  }, []);

  // Phase 3c: Auto-refresh health status every 30 seconds when in edit mode
  useEffect(() => {
    if (editMode) {
      // Load health immediately when entering edit mode
      loadSystemHealth();
      
      // Set up 30-second auto-refresh interval
      const interval = setInterval(loadSystemHealth, 30000);
      
      // Cleanup interval on unmount or when exiting edit mode
      return () => clearInterval(interval);
    }
  }, [editMode]);

  const loadConfiguration = async () => {
    try {
      const data = await getSystemConfiguration();
      setConfig(data);
      setFormData(data);
    } catch (error) {
      console.error('Error loading configuration:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSystemHealth = async () => {
    setHealthLoading(true);
    try {
      const health = await getSystemHealth();
      setSystemHealth(health);
    } catch (error) {
      console.error('Failed to load system health:', error);
      // Don't throw - allow configuration to continue working even if health check fails
    } finally {
      setHealthLoading(false);
    }
  };

  const handleSaveClick = async () => {
    if (!formData) return;

    // Validate configuration before showing confirmation
    const validation = await validateConfiguration(formData);
    
    if (!validation.valid) {
      setValidationErrors(validation.errors);
      alert('Configuration has validation errors. Please fix them before saving.');
      return;
    }

    setValidationErrors([]);
    setShowConfirmModal(true);
  };

  const handleConfirmSave = async () => {
    if (!formData) return;

    setSaving(true);
    setShowConfirmModal(false);
    
    try {
      const updated = await updateSystemConfiguration(formData);
      setConfig(updated);
      setFormData(updated);
      setEditMode(false);
      alert('Configuration updated successfully');
    } catch (error) {
      console.error('Error updating configuration:', error);
      alert('Failed to update configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (unsavedChangesCount > 0) {
      if (!window.confirm(`You have ${unsavedChangesCount} unsaved change(s). Are you sure you want to discard them?`)) {
        return;
      }
    }
    setFormData(config);
    setEditMode(false);
    setValidationErrors([]);
    setFieldErrors({});
  };

  // Handle nested threshold changes (e.g., "pH.warning.min")
  const handleThresholdChange = (field: string, value: any) => {
    if (!formData) return;

    const parts = field.split('.');
    const updatedThresholds = { ...formData.alertThresholds };
    
    // Navigate to the nested object and update the value
    let current: any = updatedThresholds.global;
    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current[part]) {
        current[part] = {};
      }
      // Create a copy to maintain immutability
      current[part] = { ...current[part] };
      current = current[part];
    }
    
    // Set the final value
    current[parts[parts.length - 1]] = value;
    
    setFormData({
      ...formData,
      alertThresholds: updatedThresholds
    });

    // Real-time validation for the field
    if (editMode) {
      const validationError = validateField(field, value);
      setFieldErrors(prev => {
        const updated = { ...prev };
        if (validationError) {
          updated[field] = validationError;
        } else {
          delete updated[field];
        }
        return updated;
      });
    }
  };

  // Handle ML settings changes (e.g., "mlSettings.confidenceThreshold")
  const handleMLSettingsChange = (field: string, value: any) => {
    if (!formData) return;

    const parts = field.split('.');
    if (parts[0] !== 'mlSettings') return;

    // Initialize mlSettings if it doesn't exist
    const updatedMLSettings = formData.mlSettings ? { ...formData.mlSettings } : {
      anomalyDetectionEnabled: true,
      modelVersion: 'latest',
      confidenceThreshold: 0.85,
      retrainingFrequencyDays: 30,
      driftDetectionEnabled: true
    };

    // Update the specific field
    const fieldName = parts[1] as keyof typeof updatedMLSettings;
    (updatedMLSettings as any)[fieldName] = value;

    setFormData({
      ...formData,
      mlSettings: updatedMLSettings
    });

    // Real-time validation for the field
    if (editMode) {
      const validationError = validateField(field, value);
      setFieldErrors(prev => {
        const updated = { ...prev };
        if (validationError) {
          updated[field] = validationError;
        } else {
          delete updated[field];
        }
        return updated;
      });
    }
  };

  // Real-time field validation
  const validateField = (field: string, value: any): string | null => {
    switch (field) {
      case 'pH.min':
        if (value < 0 || value > 14) return 'pH must be between 0 and 14';
        if (formData?.alertThresholds?.global?.pH?.max !== undefined && value >= formData.alertThresholds.global.pH.max) {
          return 'pH min must be less than pH max';
        }
        break;
      case 'pH.max':
        if (value < 0 || value > 14) return 'pH must be between 0 and 14';
        if (formData?.alertThresholds?.global?.pH?.min !== undefined && value <= formData.alertThresholds.global.pH.min) {
          return 'pH max must be greater than pH min';
        }
        break;
      case 'turbidity.max':
        if (value < 0) return 'Turbidity cannot be negative';
        if (value > 100) return 'Turbidity max should not exceed 100 NTU';
        break;
      case 'tds.max':
        if (value < 0) return 'TDS cannot be negative';
        if (value > 5000) return 'TDS max should not exceed 5000 ppm';
        break;
      case 'temperature.min':
        if (value < -10 || value > 100) return 'Temperature must be between -10°C and 100°C';
        if (formData?.alertThresholds?.global?.temperature?.max !== undefined && value >= formData.alertThresholds.global.temperature.max) {
          return 'Temperature min must be less than max';
        }
        break;
      case 'temperature.max':
        if (value < -10 || value > 100) return 'Temperature must be between -10°C and 100°C';
        if (formData?.alertThresholds?.global?.temperature?.min !== undefined && value <= formData.alertThresholds.global.temperature.min) {
          return 'Temperature max must be greater than min';
        }
        break;
      case 'dataRetentionDays':
        if (value < 30) return 'Data retention must be at least 30 days';
        if (value > 3650) return 'Data retention should not exceed 10 years';
        break;
      case 'auditRetentionYears':
        if (value < 1) return 'Audit retention must be at least 1 year';
        if (value > 10) return 'Audit retention should not exceed 10 years';
        break;
      case 'mlSettings.confidenceThreshold':
        if (value < 0 || value > 1) return 'Confidence threshold must be between 0.0 and 1.0';
        break;
      case 'mlSettings.retrainingFrequencyDays':
        if (value < 1) return 'Retraining frequency must be at least 1 day';
        if (value > 365) return 'Retraining frequency should not exceed 365 days';
        break;
      case 'mlSettings.modelVersion':
        if (!value || value.trim() === '') return 'Model version cannot be empty';
        break;
    }
    return null;
  };

  // Tooltip content with WHO standards
  const getTooltipContent = (field: string): string => {
    const tooltips: Record<string, string> = {
      'pH': 'WHO recommends pH between 6.5-8.5 for drinking water. Values outside this range may indicate contamination or treatment issues.',
      'turbidity': 'WHO guideline: <5 NTU for drinking water. Higher values indicate suspended particles that may harbor pathogens.',
      'tds': 'WHO guideline: <500 ppm for acceptable taste. Higher values may indicate dissolved minerals or contaminants.',
      'temperature': 'Typical range: 10-35°C. Extreme temperatures may affect water quality and indicate system issues.',
      'wqi': 'Water Quality Index: 0-25 (Excellent), 26-50 (Good), 51-75 (Poor), 76-100 (Very Poor), >100 (Unsuitable)',
      'dataRetention': 'Minimum 30 days required for trend analysis and compliance. Longer retention enables better historical analysis.',
      'auditRetention': 'Minimum 1 year required for GDPR compliance. Longer retention recommended for regulatory audits.'
    };
    return tooltips[field] || '';
  };

  if (loading || !config || !formData) {
    return <div className="text-center py-8">Loading configuration...</div>;
  }

  // Tooltip component
  const Tooltip = ({ field, children }: { field: string; children: React.ReactNode }) => (
    <div className="relative inline-block">
      {children}
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
          {getTooltipContent(field)}
          <div className="absolute w-2 h-2 bg-gray-900 transform rotate-45 -top-1 left-1/2"></div>
        </div>
      )}
    </div>
  );

  // Input field with validation
  const ValidatedInput = ({ 
    label, 
    field, 
    value, 
    onChange, 
    type = 'number',
    step,
    tooltip
  }: { 
    label: string; 
    field: string; 
    value: any; 
    onChange: (value: any) => void;
    type?: string;
    step?: string;
    tooltip?: string;
  }) => {
    const error = fieldErrors[field];
    const hasError = !!error;

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = type === 'number' ? parseFloat(e.target.value) : e.target.value;
      onChange(newValue);
      
      // Real-time validation
      if (editMode) {
        const validationError = validateField(field, newValue);
        setFieldErrors(prev => {
          const updated = { ...prev };
          if (validationError) {
            updated[field] = validationError;
          } else {
            delete updated[field];
          }
          return updated;
        });
      }
    };

    return (
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {tooltip ? (
            <Tooltip field={tooltip}>
              <span>{label}</span>
            </Tooltip>
          ) : (
            label
          )}
        </label>
        <input
          type={type}
          step={step}
          value={value}
          onChange={handleChange}
          disabled={!editMode}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 disabled:bg-gray-100 ${
            hasError 
              ? 'border-red-500 focus:ring-red-500' 
              : 'border-gray-300 focus:ring-blue-500'
          }`}
        />
        {hasError && (
          <div className="flex items-center mt-1 text-xs text-red-600">
            <XCircle size={12} className="mr-1" />
            {error}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 pb-24">
      {/* Global Impact Warning Banner */}
      {editMode && (
        <div className="mb-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg">
          <div className="flex items-start">
            <AlertTriangle className="text-yellow-600 mr-3 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <h4 className="text-sm font-semibold text-yellow-800 mb-1">
                Global Configuration Warning
              </h4>
              <p className="text-sm text-yellow-700">
                Changes made here affect <strong>ALL devices and users</strong> in the system. 
                Invalid configurations may disrupt monitoring and alerting for all customers.
                Please review carefully before saving.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">System Configuration</h2>
        {!editMode ? (
          <button
            onClick={() => setEditMode(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Edit Configuration
          </button>
        ) : (
          <div className="flex items-center gap-3">
            {unsavedChangesCount > 0 && (
              <span className="px-3 py-1 bg-orange-100 text-orange-800 text-sm font-medium rounded-full">
                {unsavedChangesCount} unsaved change{unsavedChangesCount !== 1 ? 's' : ''}
              </span>
            )}
            <button
              onClick={handleSaveClick}
              disabled={saving || Object.keys(fieldErrors).length > 0}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <button
              onClick={handleCancel}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* Phase 3c: System Health Indicators - Display only when in edit mode */}
      {editMode && (
        <SystemHealthPanel 
          health={systemHealth} 
          loading={healthLoading}
          onRefresh={loadSystemHealth}
        />
      )}

      <div className="space-y-6">
        {/* Alert Thresholds - Phase 3a Severity Thresholds */}
        <SeverityThresholdSection
          thresholds={formData.alertThresholds.global}
          onChange={handleThresholdChange}
          editMode={editMode}
          errors={fieldErrors}
          showTooltip={showTooltip}
          setShowTooltip={setShowTooltip}
        />

        {/* ML Settings - Phase 3b */}
        <MLSettingsSection
          mlSettings={formData.mlSettings}
          onChange={handleMLSettingsChange}
          editMode={editMode}
          errors={fieldErrors}
          showTooltip={showTooltip}
          setShowTooltip={setShowTooltip}
        />

        {/* Notification Settings */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Notification Settings</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Critical Alert Channels</label>
              <div className="flex gap-4">
                {(['sms', 'email', 'push'] as const).map((channel) => (
                  <label key={channel} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.notificationSettings.criticalAlertChannels.includes(channel)}
                      onChange={(e) => {
                        const channels = e.target.checked
                          ? [...formData.notificationSettings.criticalAlertChannels, channel]
                          : formData.notificationSettings.criticalAlertChannels.filter(c => c !== channel);
                        setFormData({
                          ...formData,
                          notificationSettings: {
                            ...formData.notificationSettings,
                            criticalAlertChannels: channels
                          }
                        });
                      }}
                      disabled={!editMode}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700 capitalize">{channel}</span>
                  </label>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">SMS Rate Limit (per hour)</label>
                <input
                  type="number"
                  value={formData.notificationSettings.rateLimits.smsPerHour}
                  onChange={(e) => setFormData({
                    ...formData,
                    notificationSettings: {
                      ...formData.notificationSettings,
                      rateLimits: {
                        ...formData.notificationSettings.rateLimits,
                        smsPerHour: parseInt(e.target.value)
                      }
                    }
                  })}
                  disabled={!editMode}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email Rate Limit (per hour)</label>
                <input
                  type="number"
                  value={formData.notificationSettings.rateLimits.emailPerHour}
                  onChange={(e) => setFormData({
                    ...formData,
                    notificationSettings: {
                      ...formData.notificationSettings,
                      rateLimits: {
                        ...formData.notificationSettings.rateLimits,
                        emailPerHour: parseInt(e.target.value)
                      }
                    }
                  })}
                  disabled={!editMode}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>
        </div>

        {/* System Limits */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-4">System Limits</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Devices Per User</label>
              <input
                type="number"
                value={formData.systemLimits.maxDevicesPerUser}
                onChange={(e) => setFormData({
                  ...formData,
                  systemLimits: {
                    ...formData.systemLimits,
                    maxDevicesPerUser: parseInt(e.target.value)
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Concurrent Devices</label>
              <input
                type="number"
                value={formData.systemLimits.maxConcurrentDevices}
                onChange={(e) => setFormData({
                  ...formData,
                  systemLimits: {
                    ...formData.systemLimits,
                    maxConcurrentDevices: parseInt(e.target.value)
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <ValidatedInput
              label="Data Retention (days)"
              field="dataRetentionDays"
              value={formData.systemLimits.dataRetentionDays}
              onChange={(value) => setFormData({
                ...formData,
                systemLimits: {
                  ...formData.systemLimits,
                  dataRetentionDays: value
                }
              })}
              tooltip="dataRetention"
            />
            <ValidatedInput
              label="Audit Retention (years)"
              field="auditRetentionYears"
              value={formData.systemLimits.auditRetentionYears}
              onChange={(value) => setFormData({
                ...formData,
                systemLimits: {
                  ...formData.systemLimits,
                  auditRetentionYears: value
                }
              })}
              tooltip="auditRetention"
            />
          </div>
        </div>

        {/* Maintenance Mode */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Maintenance Mode</h3>
          <div className="space-y-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.maintenanceMode.enabled}
                onChange={(e) => setFormData({
                  ...formData,
                  maintenanceMode: {
                    ...formData.maintenanceMode,
                    enabled: e.target.checked
                  }
                })}
                disabled={!editMode}
                className="mr-2"
              />
              <span className="text-sm font-medium text-gray-700">Enable Maintenance Mode</span>
            </label>
            {formData.maintenanceMode.enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Maintenance Message</label>
                <textarea
                  value={formData.maintenanceMode.message || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    maintenanceMode: {
                      ...formData.maintenanceMode,
                      message: e.target.value
                    }
                  })}
                  disabled={!editMode}
                  rows={3}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  placeholder="System is under maintenance. Please check back later."
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <h4 className="text-sm font-medium text-red-800 mb-2">Validation Errors:</h4>
          <ul className="list-disc list-inside text-sm text-red-700">
            {validationErrors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Sticky Save Bar */}
      {editMode && unsavedChangesCount > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-orange-400 shadow-lg z-50">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center">
              <AlertTriangle className="text-orange-600 mr-3" size={20} />
              <div>
                <p className="text-sm font-semibold text-gray-900">
                  You have {unsavedChangesCount} unsaved change{unsavedChangesCount !== 1 ? 's' : ''}
                </p>
                <p className="text-xs text-gray-600">
                  Changes will not be applied until you save
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleCancel}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors text-sm font-medium"
              >
                Discard Changes
              </button>
              <button
                onClick={handleSaveClick}
                disabled={saving || Object.keys(fieldErrors).length > 0}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium flex items-center"
              >
                {saving ? (
                  <>
                    <span className="animate-spin mr-2">⏳</span>
                    Saving...
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} className="mr-2" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {config && formData && (
        <ConfigurationConfirmModal
          isOpen={showConfirmModal}
          onClose={() => setShowConfirmModal(false)}
          onConfirm={handleConfirmSave}
          currentConfig={config}
          newConfig={formData}
          isSaving={saving}
        />
      )}
    </div>
  );
};

export default SystemConfiguration;
