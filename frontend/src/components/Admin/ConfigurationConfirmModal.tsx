import { useState, useEffect } from 'react';
import { SystemConfiguration } from '../../types/admin';

interface ConfigChange {
  field: string;
  oldValue: any;
  newValue: any;
  path: string;
}

interface ConfigurationConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  currentConfig: SystemConfiguration;
  newConfig: SystemConfiguration;
  isSaving: boolean;
}

const ConfigurationConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  currentConfig,
  newConfig,
  isSaving
}: ConfigurationConfirmModalProps) => {
  const [changes, setChanges] = useState<ConfigChange[]>([]);

  // Calculate changes when modal opens
  useEffect(() => {
    if (isOpen) {
      const detectedChanges = calculateChanges(currentConfig, newConfig);
      setChanges(detectedChanges);
    }
  }, [isOpen, currentConfig, newConfig]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Confirm Configuration Changes
          </h2>
        </div>

        {/* Warning Banner */}
        <div className="px-6 py-3 bg-yellow-50 border-b border-yellow-200">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-sm font-medium text-yellow-800">
                System-Wide Impact
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                Changes made here will affect ALL devices and users in the system immediately.
              </p>
            </div>
          </div>
        </div>

        {/* Changes List */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {changes.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No changes detected</p>
          ) : (
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700 mb-3">
                The following changes will be applied:
              </p>
              {changes.map((change, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                  <p className="text-sm font-medium text-gray-900 mb-2">
                    {formatFieldName(change.field)}
                  </p>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">Current:</span>
                      <span className="ml-2 font-medium text-red-600">
                        {formatValue(change.oldValue)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">New:</span>
                      <span className="ml-2 font-medium text-green-600">
                        {formatValue(change.newValue)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={isSaving}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isSaving || changes.length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Confirm Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper function to calculate changes between configs
function calculateChanges(oldConfig: SystemConfiguration, newConfig: SystemConfiguration): ConfigChange[] {
  const changes: ConfigChange[] = [];

  // Compare alert thresholds
  const oldThresholds = oldConfig.alertThresholds.global;
  const newThresholds = newConfig.alertThresholds.global;

  // pH thresholds - warning and critical levels
  if (oldThresholds.pH?.warning?.min !== newThresholds.pH?.warning?.min) {
    changes.push({
      field: 'pH Warning Minimum',
      oldValue: oldThresholds.pH?.warning?.min,
      newValue: newThresholds.pH?.warning?.min,
      path: 'alertThresholds.global.pH.warning.min'
    });
  }

  if (oldThresholds.pH?.warning?.max !== newThresholds.pH?.warning?.max) {
    changes.push({
      field: 'pH Warning Maximum',
      oldValue: oldThresholds.pH?.warning?.max,
      newValue: newThresholds.pH?.warning?.max,
      path: 'alertThresholds.global.pH.warning.max'
    });
  }

  if (oldThresholds.pH?.critical?.min !== newThresholds.pH?.critical?.min) {
    changes.push({
      field: 'pH Critical Minimum',
      oldValue: oldThresholds.pH?.critical?.min,
      newValue: newThresholds.pH?.critical?.min,
      path: 'alertThresholds.global.pH.critical.min'
    });
  }

  if (oldThresholds.pH?.critical?.max !== newThresholds.pH?.critical?.max) {
    changes.push({
      field: 'pH Critical Maximum',
      oldValue: oldThresholds.pH?.critical?.max,
      newValue: newThresholds.pH?.critical?.max,
      path: 'alertThresholds.global.pH.critical.max'
    });
  }

  // Turbidity thresholds
  if (oldThresholds.turbidity?.warning?.max !== newThresholds.turbidity?.warning?.max) {
    changes.push({
      field: 'Turbidity Warning Maximum',
      oldValue: oldThresholds.turbidity?.warning?.max,
      newValue: newThresholds.turbidity?.warning?.max,
      path: 'alertThresholds.global.turbidity.warning.max'
    });
  }

  if (oldThresholds.turbidity?.critical?.max !== newThresholds.turbidity?.critical?.max) {
    changes.push({
      field: 'Turbidity Critical Maximum',
      oldValue: oldThresholds.turbidity?.critical?.max,
      newValue: newThresholds.turbidity?.critical?.max,
      path: 'alertThresholds.global.turbidity.critical.max'
    });
  }

  // TDS thresholds
  if (oldThresholds.tds?.warning?.max !== newThresholds.tds?.warning?.max) {
    changes.push({
      field: 'TDS Warning Maximum',
      oldValue: oldThresholds.tds?.warning?.max,
      newValue: newThresholds.tds?.warning?.max,
      path: 'alertThresholds.global.tds.warning.max'
    });
  }

  if (oldThresholds.tds?.critical?.max !== newThresholds.tds?.critical?.max) {
    changes.push({
      field: 'TDS Critical Maximum',
      oldValue: oldThresholds.tds?.critical?.max,
      newValue: newThresholds.tds?.critical?.max,
      path: 'alertThresholds.global.tds.critical.max'
    });
  }

  // Temperature thresholds
  if (oldThresholds.temperature?.warning?.min !== newThresholds.temperature?.warning?.min) {
    changes.push({
      field: 'Temperature Warning Minimum',
      oldValue: oldThresholds.temperature?.warning?.min,
      newValue: newThresholds.temperature?.warning?.min,
      path: 'alertThresholds.global.temperature.warning.min'
    });
  }

  if (oldThresholds.temperature?.warning?.max !== newThresholds.temperature?.warning?.max) {
    changes.push({
      field: 'Temperature Warning Maximum',
      oldValue: oldThresholds.temperature?.warning?.max,
      newValue: newThresholds.temperature?.warning?.max,
      path: 'alertThresholds.global.temperature.warning.max'
    });
  }

  if (oldThresholds.temperature?.critical?.min !== newThresholds.temperature?.critical?.min) {
    changes.push({
      field: 'Temperature Critical Minimum',
      oldValue: oldThresholds.temperature?.critical?.min,
      newValue: newThresholds.temperature?.critical?.min,
      path: 'alertThresholds.global.temperature.critical.min'
    });
  }

  if (oldThresholds.temperature?.critical?.max !== newThresholds.temperature?.critical?.max) {
    changes.push({
      field: 'Temperature Critical Maximum',
      oldValue: oldThresholds.temperature?.critical?.max,
      newValue: newThresholds.temperature?.critical?.max,
      path: 'alertThresholds.global.temperature.critical.max'
    });
  }

  // WQI thresholds (if they exist)
  if (oldThresholds.wqi?.critical !== newThresholds.wqi?.critical) {
    changes.push({
      field: 'WQI Critical Threshold',
      oldValue: oldThresholds.wqi?.critical,
      newValue: newThresholds.wqi?.critical,
      path: 'alertThresholds.global.wqi.critical'
    });
  }

  if (oldThresholds.wqi?.warning !== newThresholds.wqi?.warning) {
    changes.push({
      field: 'WQI Warning Threshold',
      oldValue: oldThresholds.wqi?.warning,
      newValue: newThresholds.wqi?.warning,
      path: 'alertThresholds.global.wqi.warning'
    });
  }

  // Compare system limits
  const oldLimits = oldConfig.systemLimits;
  const newLimits = newConfig.systemLimits;

  if (oldLimits.maxDevicesPerUser !== newLimits.maxDevicesPerUser) {
    changes.push({
      field: 'Max Devices Per User',
      oldValue: oldLimits.maxDevicesPerUser,
      newValue: newLimits.maxDevicesPerUser,
      path: 'systemLimits.maxDevicesPerUser'
    });
  }

  if (oldLimits.maxConcurrentDevices !== newLimits.maxConcurrentDevices) {
    changes.push({
      field: 'Max Concurrent Devices',
      oldValue: oldLimits.maxConcurrentDevices,
      newValue: newLimits.maxConcurrentDevices,
      path: 'systemLimits.maxConcurrentDevices'
    });
  }

  if (oldLimits.dataRetentionDays !== newLimits.dataRetentionDays) {
    changes.push({
      field: 'Data Retention (days)',
      oldValue: oldLimits.dataRetentionDays,
      newValue: newLimits.dataRetentionDays,
      path: 'systemLimits.dataRetentionDays'
    });
  }

  if (oldLimits.auditRetentionYears !== newLimits.auditRetentionYears) {
    changes.push({
      field: 'Audit Retention (years)',
      oldValue: oldLimits.auditRetentionYears,
      newValue: newLimits.auditRetentionYears,
      path: 'systemLimits.auditRetentionYears'
    });
  }

  // Compare notification settings
  const oldNotif = oldConfig.notificationSettings;
  const newNotif = newConfig.notificationSettings;

  if (JSON.stringify(oldNotif.criticalAlertChannels) !== JSON.stringify(newNotif.criticalAlertChannels)) {
    changes.push({
      field: 'Critical Alert Channels',
      oldValue: oldNotif.criticalAlertChannels.join(', '),
      newValue: newNotif.criticalAlertChannels.join(', '),
      path: 'notificationSettings.criticalAlertChannels'
    });
  }

  if (oldNotif.rateLimits.smsPerHour !== newNotif.rateLimits.smsPerHour) {
    changes.push({
      field: 'SMS Rate Limit (per hour)',
      oldValue: oldNotif.rateLimits.smsPerHour,
      newValue: newNotif.rateLimits.smsPerHour,
      path: 'notificationSettings.rateLimits.smsPerHour'
    });
  }

  if (oldNotif.rateLimits.emailPerHour !== newNotif.rateLimits.emailPerHour) {
    changes.push({
      field: 'Email Rate Limit (per hour)',
      oldValue: oldNotif.rateLimits.emailPerHour,
      newValue: newNotif.rateLimits.emailPerHour,
      path: 'notificationSettings.rateLimits.emailPerHour'
    });
  }

  // Compare maintenance mode
  if (oldConfig.maintenanceMode.enabled !== newConfig.maintenanceMode.enabled) {
    changes.push({
      field: 'Maintenance Mode',
      oldValue: oldConfig.maintenanceMode.enabled ? 'Enabled' : 'Disabled',
      newValue: newConfig.maintenanceMode.enabled ? 'Enabled' : 'Disabled',
      path: 'maintenanceMode.enabled'
    });
  }

  if (oldConfig.maintenanceMode.message !== newConfig.maintenanceMode.message) {
    changes.push({
      field: 'Maintenance Message',
      oldValue: oldConfig.maintenanceMode.message || '(none)',
      newValue: newConfig.maintenanceMode.message || '(none)',
      path: 'maintenanceMode.message'
    });
  }

  return changes;
}

function formatFieldName(field: string): string {
  return field;
}

function formatValue(value: any): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  return String(value);
}

export default ConfigurationConfirmModal;
