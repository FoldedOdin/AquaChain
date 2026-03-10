import React, { useState } from 'react';
import { 
  XMarkIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';
import { Activity, Wifi, MapPin, Droplet } from 'lucide-react';

interface AddDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeviceAdded: () => void;
}

const AddDeviceModal: React.FC<AddDeviceModalProps> = ({ isOpen, onClose, onDeviceAdded }) => {
  const [step, setStep] = useState<'form' | 'success' | 'error'>('form');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Debug: Log when modal receives props
  console.log('🔍 AddDeviceModal received props:', { isOpen, step });

  // Form state
  const [deviceId, setDeviceId] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [location, setLocation] = useState('');
  const [waterSourceType, setWaterSourceType] = useState<'household' | 'industrial' | 'agricultural'>('household');
  const [pairingCode, setPairingCode] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!deviceId.trim()) {
      setErrorMessage('Device ID is required');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/devices/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        },
        body: JSON.stringify({
          deviceId: deviceId.trim(),
          deviceName: deviceName.trim() || `Device ${deviceId}`,
          location: location.trim() || 'Not specified',
          waterSourceType: waterSourceType,
          pairingCode: pairingCode.trim() || undefined
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.message || result.error || 'Failed to register device');
      }

      setStep('success');
      
      // Notify parent component after a short delay
      setTimeout(() => {
        onDeviceAdded();
        handleClose();
      }, 2000);

    } catch (error: any) {
      console.error('Device registration error:', error);
      setErrorMessage(error.message || 'Failed to register device. Please try again.');
      setStep('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form
    setStep('form');
    setDeviceId('');
    setDeviceName('');
    setLocation('');
    setWaterSourceType('household');
    setPairingCode('');
    setErrorMessage('');
    setIsSubmitting(false);
    onClose();
  };

  if (!isOpen) {
    console.log('🔍 AddDeviceModal not rendering - isOpen is false');
    return null;
  }

  console.log('🔍 AddDeviceModal rendering - isOpen is true');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden relative z-[10000]">
        {/* Header */}
        <div className="bg-gradient-to-r from-cyan-500 to-blue-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white bg-opacity-20 rounded-lg">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white">Register New Device</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6">
          {step === 'success' && (
            <div className="text-center py-12">
              <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Device Registered Successfully!</h3>
              <p className="text-gray-600 mb-4">
                Your device <strong>{deviceName || deviceId}</strong> has been added to your account.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left max-w-md mx-auto">
                <p className="text-sm text-blue-900 mb-2">
                  <strong>Next Steps:</strong>
                </p>
                <ul className="text-sm text-blue-800 space-y-1">
                  <li>• Your device will appear in the dashboard</li>
                  <li>• Data will start flowing once device connects</li>
                  <li>• You'll receive alerts for water quality issues</li>
                </ul>
              </div>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center py-12">
              <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Registration Failed</h3>
              <p className="text-gray-600 mb-4">{errorMessage}</p>
              <button
                onClick={() => setStep('form')}
                className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition"
              >
                Try Again
              </button>
            </div>
          )}

          {step === 'form' && (
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Device ID */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Device ID <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Activity className="w-5 h-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={deviceId}
                    onChange={(e) => setDeviceId(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                    placeholder="Enter device ID (e.g., AQ-001)"
                    required
                    maxLength={50}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Find this ID on your device or in the serial monitor
                </p>
              </div>

              {/* Device Name */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Device Name (Optional)
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Droplet className="w-5 h-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={deviceName}
                    onChange={(e) => setDeviceName(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                    placeholder="Kitchen Sink Monitor"
                    maxLength={100}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Give your device a friendly name for easy identification
                </p>
              </div>

              {/* Location */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Location / Description
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MapPin className="w-5 h-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                    placeholder="Kitchen, Bathroom, Garden, etc."
                    maxLength={200}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Where is this device installed?
                </p>
              </div>

              {/* Water Source Type */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Water Source Type
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['household', 'industrial', 'agricultural'] as const).map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setWaterSourceType(type)}
                      className={`p-3 text-sm font-medium rounded-lg border-2 transition ${
                        waterSourceType === type
                          ? 'border-cyan-500 bg-cyan-50 text-cyan-700'
                          : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Error Message */}
              {errorMessage && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {errorMessage}
                </div>
              )}

              {/* Form Actions */}
              <div className="bg-gray-50 px-6 py-4 flex items-center justify-end space-x-3">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !deviceId.trim()}
                  className="px-6 py-2 bg-cyan-500 text-white rounded-lg hover:bg-cyan-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isSubmitting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Registering...</span>
                    </>
                  ) : (
                    <>
                      <Activity className="w-4 h-4" />
                      <span>Register Device</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default AddDeviceModal;