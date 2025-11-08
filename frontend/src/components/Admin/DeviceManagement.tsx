import { useState, useEffect } from 'react';
import { DeviceRegistration } from '../../types/admin';
import { getAllDevices, registerDevice, updateDevice } from '../../services/adminService';

const DeviceManagement = () => {
  const [devices, setDevices] = useState<DeviceRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive' | 'maintenance'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState<DeviceRegistration | null>(null);

  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    try {
      const data = await getAllDevices();
      setDevices(data);
    } catch (error) {
      console.error('Error loading devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDevices = devices.filter(device => {
    const matchesFilter = filter === 'all' || device.status === filter;
    const matchesSearch = searchTerm === '' || 
      device.deviceId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.serialNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.location.address.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleRegisterDevice = async (deviceData: Partial<DeviceRegistration>) => {
    try {
      const newDevice = await registerDevice(deviceData);
      setDevices([...devices, newDevice]);
      setShowRegisterModal(false);
    } catch (error) {
      console.error('Error registering device:', error);
      alert('Failed to register device');
    }
  };

  const handleUpdateDevice = async (deviceId: string, updates: Partial<DeviceRegistration>) => {
    try {
      const updatedDevice = await updateDevice(deviceId, updates);
      setDevices(devices.map(d => d.deviceId === deviceId ? updatedDevice : d));
      setEditingDevice(null);
    } catch (error) {
      console.error('Error updating device:', error);
      alert('Failed to update device');
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'maintenance': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading devices...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Device Management</h2>
        <button
          onClick={() => setShowRegisterModal(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          + Register Device
        </button>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex gap-2">
          {(['all', 'active', 'inactive', 'maintenance'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search devices..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
        />
      </div>

      {/* Device Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Total Devices</div>
          <div className="text-2xl font-bold">{devices.length}</div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Active</div>
          <div className="text-2xl font-bold text-green-600">
            {devices.filter(d => d.status === 'active').length}
          </div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Maintenance</div>
          <div className="text-2xl font-bold text-yellow-600">
            {devices.filter(d => d.status === 'maintenance').length}
          </div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Inactive</div>
          <div className="text-2xl font-bold text-gray-600">
            {devices.filter(d => d.status === 'inactive').length}
          </div>
        </div>
      </div>

      {/* Device Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Serial Number</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned To</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredDevices.map((device) => (
              <tr key={device.deviceId} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{device.deviceId}</div>
                  <div className="text-xs text-gray-500">FW: {device.firmwareVersion}</div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">{device.serialNumber}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{device.model}</td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(device.status)}`}>
                    {device.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {device.assignedTo || <span className="text-gray-400">Unassigned</span>}
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-700">{device.location.address}</div>
                  <div className="text-xs text-gray-500">
                    {device.location.latitude.toFixed(4)}, {device.location.longitude.toFixed(4)}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingDevice(device)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => {
                        const newStatus = device.status === 'active' ? 'inactive' : 'active';
                        handleUpdateDevice(device.deviceId, { status: newStatus });
                      }}
                      className="text-green-600 hover:text-green-800 text-sm font-medium"
                    >
                      {device.status === 'active' ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredDevices.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No devices found matching your criteria
        </div>
      )}

      {/* Register/Edit Device Modal */}
      {(showRegisterModal || editingDevice) && (
        <DeviceFormModal
          device={editingDevice}
          onSave={(deviceData) => {
            if (editingDevice) {
              handleUpdateDevice(editingDevice.deviceId, deviceData);
            } else {
              handleRegisterDevice(deviceData);
            }
          }}
          onCancel={() => {
            setShowRegisterModal(false);
            setEditingDevice(null);
          }}
        />
      )}
    </div>
  );
};

interface DeviceFormModalProps {
  device: DeviceRegistration | null;
  onSave: (deviceData: Partial<DeviceRegistration>) => void;
  onCancel: () => void;
}

const DeviceFormModal = ({ device, onSave, onCancel }: DeviceFormModalProps) => {
  const [formData, setFormData] = useState({
    serialNumber: device?.serialNumber || '',
    model: device?.model || 'AquaChain Pro v2',
    firmwareVersion: device?.firmwareVersion || '2.1.5',
    status: device?.status || 'active',
    assignedTo: device?.assignedTo || '',
    address: device?.location.address || '',
    latitude: device?.location.latitude || 0,
    longitude: device?.location.longitude || 0,
    readingInterval: device?.configuration.readingInterval || 30,
    pHMin: device?.configuration.alertThresholds.pH.min || 6.5,
    pHMax: device?.configuration.alertThresholds.pH.max || 8.5,
    turbidityMax: device?.configuration.alertThresholds.turbidity.max || 5.0,
    tdsMax: device?.configuration.alertThresholds.tds.max || 500,
    tempMin: device?.configuration.alertThresholds.temperature.min || 0,
    tempMax: device?.configuration.alertThresholds.temperature.max || 40
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      serialNumber: formData.serialNumber,
      model: formData.model,
      firmwareVersion: formData.firmwareVersion,
      status: formData.status as any,
      assignedTo: formData.assignedTo || undefined,
      location: {
        latitude: formData.latitude,
        longitude: formData.longitude,
        address: formData.address
      },
      configuration: {
        readingInterval: formData.readingInterval,
        alertThresholds: {
          pH: { min: formData.pHMin, max: formData.pHMax },
          turbidity: { max: formData.turbidityMax },
          tds: { max: formData.tdsMax },
          temperature: { min: formData.tempMin, max: formData.tempMax }
        }
      }
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 my-8">
        <h3 className="text-lg font-semibold mb-4">
          {device ? 'Edit Device' : 'Register New Device'}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Serial Number</label>
              <input
                type="text"
                value={formData.serialNumber}
                onChange={(e) => setFormData({ ...formData, serialNumber: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
              <input
                type="text"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Firmware Version</label>
              <input
                type="text"
                value={formData.firmwareVersion}
                onChange={(e) => setFormData({ ...formData, firmwareVersion: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'inactive' | 'maintenance' })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="maintenance">Maintenance</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Assigned To (User ID)</label>
            <input
              type="text"
              value={formData.assignedTo}
              onChange={(e) => setFormData({ ...formData, assignedTo: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Optional"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                required
              />
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-3">Configuration</h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reading Interval (seconds)</label>
                <input
                  type="number"
                  value={formData.readingInterval}
                  onChange={(e) => setFormData({ ...formData, readingInterval: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
            </div>

            <h5 className="font-medium text-gray-700 mt-4 mb-2">Alert Thresholds</h5>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">pH Min</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.pHMin}
                  onChange={(e) => setFormData({ ...formData, pHMin: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">pH Max</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.pHMax}
                  onChange={(e) => setFormData({ ...formData, pHMax: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Turbidity Max (NTU)</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.turbidityMax}
                  onChange={(e) => setFormData({ ...formData, turbidityMax: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">TDS Max (ppm)</label>
                <input
                  type="number"
                  value={formData.tdsMax}
                  onChange={(e) => setFormData({ ...formData, tdsMax: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Temp Min (°C)</label>
                <input
                  type="number"
                  value={formData.tempMin}
                  onChange={(e) => setFormData({ ...formData, tempMin: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Temp Max (°C)</label>
                <input
                  type="number"
                  value={formData.tempMax}
                  onChange={(e) => setFormData({ ...formData, tempMax: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              {device ? 'Update' : 'Register'}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DeviceManagement;
