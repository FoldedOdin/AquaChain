import { useState, useEffect } from 'react';
import { SystemConfiguration as SystemConfigType } from '../../types/admin';
import { getSystemConfiguration, updateSystemConfiguration } from '../../services/adminService';

const SystemConfiguration = () => {
  const [config, setConfig] = useState<SystemConfigType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<SystemConfigType | null>(null);

  useEffect(() => {
    loadConfiguration();
  }, []);

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

  const handleSave = async () => {
    if (!formData) return;

    setSaving(true);
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
    setFormData(config);
    setEditMode(false);
  };

  if (loading || !config || !formData) {
    return <div className="text-center py-8">Loading configuration...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
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
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
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

      <div className="space-y-6">
        {/* Alert Thresholds */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-4">Global Alert Thresholds</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">pH Min</label>
              <input
                type="number"
                step="0.1"
                value={formData.alertThresholds.global.pH.min}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      pH: { ...formData.alertThresholds.global.pH, min: parseFloat(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">pH Max</label>
              <input
                type="number"
                step="0.1"
                value={formData.alertThresholds.global.pH.max}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      pH: { ...formData.alertThresholds.global.pH, max: parseFloat(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Turbidity Max (NTU)</label>
              <input
                type="number"
                step="0.1"
                value={formData.alertThresholds.global.turbidity.max}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      turbidity: { max: parseFloat(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">TDS Max (ppm)</label>
              <input
                type="number"
                value={formData.alertThresholds.global.tds.max}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      tds: { max: parseInt(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Temperature Min (°C)</label>
              <input
                type="number"
                value={formData.alertThresholds.global.temperature.min}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      temperature: { ...formData.alertThresholds.global.temperature, min: parseInt(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Temperature Max (°C)</label>
              <input
                type="number"
                value={formData.alertThresholds.global.temperature.max}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      temperature: { ...formData.alertThresholds.global.temperature, max: parseInt(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">WQI Critical Threshold</label>
              <input
                type="number"
                value={formData.alertThresholds.global.wqi.critical}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      wqi: { ...formData.alertThresholds.global.wqi, critical: parseInt(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">WQI Warning Threshold</label>
              <input
                type="number"
                value={formData.alertThresholds.global.wqi.warning}
                onChange={(e) => setFormData({
                  ...formData,
                  alertThresholds: {
                    ...formData.alertThresholds,
                    global: {
                      ...formData.alertThresholds.global,
                      wqi: { ...formData.alertThresholds.global.wqi, warning: parseInt(e.target.value) }
                    }
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
          </div>
        </div>

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
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data Retention (days)</label>
              <input
                type="number"
                value={formData.systemLimits.dataRetentionDays}
                onChange={(e) => setFormData({
                  ...formData,
                  systemLimits: {
                    ...formData.systemLimits,
                    dataRetentionDays: parseInt(e.target.value)
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Audit Retention (years)</label>
              <input
                type="number"
                value={formData.systemLimits.auditRetentionYears}
                onChange={(e) => setFormData({
                  ...formData,
                  systemLimits: {
                    ...formData.systemLimits,
                    auditRetentionYears: parseInt(e.target.value)
                  }
                })}
                disabled={!editMode}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
              />
            </div>
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
    </div>
  );
};

export default SystemConfiguration;
