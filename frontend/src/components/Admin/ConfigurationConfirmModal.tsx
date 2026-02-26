import { useState } from 'react';
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
  useState(() => {
    if (isOpen) {
      const detectedChanges = calculateChanges(currentConfig, newConfig);
      setChanges(detectedChanges);
    }
  });

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

  if (oldThresholds.pH.min !== newThresholds.pH.min) {
    changes.push({
      field: 'pH Minimum',
      oldValue: oldThresholds.pH.min,
      newValue: newThresholds.pH.min,
      path: 'alertThresholds.global.pH.min'
    });
  }

  if (oldThresholds.pH.max !== newThresholds.pH.max) {
    changes.push({
      field: 'pH Maximum',
      oldValue: oldThresholds.pH.max,
      newValue: newThresholds.pH.max,
      path: 'alertThresholds.global.pH.max'
    });
  }

  if (oldThresholds.turbidity.max !== newThresholds.turbidity.max) {
    changes.push({
      field: 'Turbidity Maximum',
      oldValue: oldThresholds.turbidity.max,
      newValue: newThresholds.turbidity.max,
      path: 'alertThresholds.global.turbidity.max'
    });
  }

  if (oldThresholds.tds.max !== newThresholds.tds.max) {
    changes.push({
      field: 'TDS Maximum',
      oldValue: oldThresholds.tds.max,
      newValue: newThresholds.tds.max,
      path: 'alertThresholds.global.tds.max'
    });
  }

  if (oldThresholds.temperature.min !== newThresholds.temperature.min) {
    changes.push({
      field: 'Temperature Minimum',
      oldValue: oldThresholds.temperature.min,
      newValue: newThresholds.temperature.min,
      path: 'alertThresholds.global.temperature.min'
    });
  }

  if (oldThresholds.temperature.max !== newThresholds.temperature.max) {
    changes.push({
      field: 'Temperature Maximum',
      oldValue: oldThresholds.temperature.max,
      newValue: newThresholds.temperature.max,
      path: 'alertThresholds.global.temperature.max'
    });
  }

  if (oldThresholds.wqi.critical !== newThresholds.wqi.critical) {
    changes.push({
      field: 'WQI Critical Threshold',
      oldValue: oldThresholds.wqi.critical,
      newValue: newThresholds.wqi.critical,
      path: 'alertThresholds.global.wqi.critical'
    });
  }

  if (oldThresholds.wqi.warning !== newThresholds.wqi.warning) {
    changes.push({
      field: 'WQI Warning Threshold',
      oldValue: oldThresholds.wqi.warning,
      newValue: newThresholds.wqi.warning,
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
