import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { 
  Activity, 
  Droplet, 
  MapPin, 
  Thermometer,
  Beaker,
  Eye
} from 'lucide-react';

interface DemoDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDemoDeviceAdded: () => void;
}

const DemoDeviceModal: React.FC<DemoDeviceModalProps> = ({
  isOpen,
  onClose,
  onDemoDeviceAdded
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Demo device data with realistic water quality readings
  const demoDevice = {
    device_id: `demo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    name: 'Demo Water Monitor',
    location: 'Kitchen Sink - Demo Location',
    status: 'active',
    type: 'ESP32-WQ-Monitor',
    installation_date: new Date().toISOString(),
    last_reading: new Date().toISOString(),
    readings: {
      pH: 7.2,
      turbidity: 2.1,
      tds: 145,
      temperature: 22.5,
      timestamp: new Date().toISOString()
    },
    metadata: {
      isDemo: true,
      description: 'This is a demonstration device with simulated water quality data'
    }
  };

  const handleAddDemoDevice = async () => {
    setIsAdding(true);
    setError(null);

    try {
      const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
      
      const response = await fetch('http://localhost:3002/api/devices/demo', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(demoDevice)
      });

      if (response.ok) {
        setIsSuccess(true);
        // Call the callback to refresh dashboard data
        setTimeout(() => {
          onDemoDeviceAdded();
          onClose();
          setIsSuccess(false);
        }, 2000);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to add demo device');
      }
    } catch (err) {
      console.error('Error adding demo device:', err);
      setError(err instanceof Error ? err.message : 'Failed to add demo device');
    } finally {
      setIsAdding(false);
    }
  };

  const handleClose = () => {
    if (!isAdding) {
      onClose();
      setError(null);
      setIsSuccess(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-cyan-600 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="w-6 h-6 text-white" />
              <h2 className="text-xl font-bold text-white">Add Demo Device</h2>
            </div>
            <button
              onClick={handleClose}
              disabled={isAdding}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition disabled:opacity-50"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {isSuccess ? (
              <div className="text-center py-8">
                <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Demo Device Added!</h3>
                <p className="text-gray-600">
                  Your demo water quality monitor has been successfully added to your dashboard.
                </p>
              </div>
            ) : (
              <>
                <div className="mb-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <div className="flex items-start gap-3">
                      <Activity className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <h3 className="font-semibold text-blue-900 mb-1">Demo Device Preview</h3>
                        <p className="text-sm text-blue-800">
                          This will add a demonstration water quality monitor with simulated data to help you explore the dashboard features.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Device Preview Card */}
                  <div className="bg-white border-2 border-gray-200 rounded-lg p-6">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        <Droplet className="w-6 h-6 text-green-600" />
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900">{demoDevice.name}</h4>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <MapPin className="w-4 h-4" />
                          <span>{demoDevice.location}</span>
                        </div>
                      </div>
                      <div className="ml-auto">
                        <span className="inline-flex items-center gap-2 px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                          Online
                        </span>
                      </div>
                    </div>

                    {/* Sample Readings */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-blue-50 rounded-lg p-3 text-center">
                        <Beaker className="w-5 h-5 text-blue-600 mx-auto mb-1" />
                        <div className="text-lg font-bold text-blue-900">{demoDevice.readings.pH}</div>
                        <div className="text-xs text-blue-700">pH Level</div>
                      </div>
                      <div className="bg-green-50 rounded-lg p-3 text-center">
                        <Eye className="w-5 h-5 text-green-600 mx-auto mb-1" />
                        <div className="text-lg font-bold text-green-900">{demoDevice.readings.turbidity}</div>
                        <div className="text-xs text-green-700">Turbidity (NTU)</div>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-3 text-center">
                        <Droplet className="w-5 h-5 text-purple-600 mx-auto mb-1" />
                        <div className="text-lg font-bold text-purple-900">{demoDevice.readings.tds}</div>
                        <div className="text-xs text-purple-700">TDS (ppm)</div>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-3 text-center">
                        <Thermometer className="w-5 h-5 text-orange-600 mx-auto mb-1" />
                        <div className="text-lg font-bold text-orange-900">{demoDevice.readings.temperature}°C</div>
                        <div className="text-xs text-orange-700">Temperature</div>
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <div className="flex items-start gap-2">
                        <ExclamationTriangleIcon className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-amber-900">Demo Device Notice</p>
                          <p className="text-xs text-amber-800 mt-1">
                            This device generates simulated data for demonstration purposes. 
                            You can remove it anytime from your device list.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
                      <p className="text-sm font-medium text-red-900">Error</p>
                    </div>
                    <p className="text-sm text-red-800 mt-1">{error}</p>
                  </div>
                )}

                {/* Features List */}
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 mb-3">What you'll get:</h4>
                  <ul className="space-y-2">
                    <li className="flex items-center gap-3">
                      <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">Real-time water quality monitoring simulation</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">Interactive charts and historical data</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">Water Quality Index (WQI) calculations</span>
                    </li>
                    <li className="flex items-center gap-3">
                      <CheckCircleIcon className="w-5 h-5 text-green-600 flex-shrink-0" />
                      <span className="text-sm text-gray-700">Alert notifications for parameter changes</span>
                    </li>
                  </ul>
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          {!isSuccess && (
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
              <button
                onClick={handleClose}
                disabled={isAdding}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddDemoDevice}
                disabled={isAdding}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isAdding ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Adding Demo Device...</span>
                  </>
                ) : (
                  <>
                    <Activity className="w-4 h-4" />
                    <span>Add Demo Device</span>
                  </>
                )}
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default DemoDeviceModal;