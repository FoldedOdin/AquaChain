import React, { useState } from 'react';
import { Wifi, Check, AlertCircle, Loader2, QrCode } from 'lucide-react';

interface DevicePairingProps {
  userId: string;
  onPairingComplete: (deviceId: string) => void;
}

interface PairingState {
  step: 'input' | 'validating' | 'success' | 'error';
  deviceId: string;
  deviceName: string;
  error: string | null;
}

export default function DevicePairing({ userId, onPairingComplete }: DevicePairingProps) {
  const [state, setState] = useState<PairingState>({
    step: 'input',
    deviceId: '',
    deviceName: '',
    error: null
  });

  const handleDeviceIdChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    // Auto-format as ESP32-XXXXXX
    if (value.length <= 12) {
      setState(prev => ({ ...prev, deviceId: value }));
    }
  };

  const handleDeviceNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setState(prev => ({ ...prev, deviceName: e.target.value }));
  };

  const validateDeviceId = (deviceId: string): boolean => {
    // Format: ESP32-XXXXXX (6 alphanumeric characters)
    const regex = /^ESP32-[A-Z0-9]{6}$/;
    return regex.test(deviceId);
  };

  const handlePairDevice = async () => {
    if (!validateDeviceId(state.deviceId)) {
      setState(prev => ({
        ...prev,
        error: 'Invalid device ID format. Expected: ESP32-XXXXXX'
      }));
      return;
    }

    if (!state.deviceName.trim()) {
      setState(prev => ({
        ...prev,
        error: 'Please enter a device name'
      }));
      return;
    }

    setState(prev => ({ ...prev, step: 'validating', error: null }));

    try {
      const response = await fetch('/api/v1/devices/pair', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          deviceId: state.deviceId,
          userId: userId,
          deviceName: state.deviceName
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to pair device');
      }

      setState(prev => ({ ...prev, step: 'success' }));
      
      // Notify parent component
      setTimeout(() => {
        onPairingComplete(state.deviceId);
      }, 2000);

    } catch (error) {
      setState(prev => ({
        ...prev,
        step: 'error',
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      }));
    }
  };

  const handleReset = () => {
    setState({
      step: 'input',
      deviceId: '',
      deviceName: '',
      error: null
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-md mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-blue-100 rounded-lg">
          <Wifi className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Pair New Device</h2>
          <p className="text-sm text-gray-600">Connect your AquaChain sensor</p>
        </div>
      </div>

      {state.step === 'input' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Device ID
            </label>
            <input
              type="text"
              value={state.deviceId}
              onChange={handleDeviceIdChange}
              placeholder="ESP32-ABC123"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxLength={12}
            />
            <p className="mt-1 text-xs text-gray-500">
              Find this on the device label or QR code
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Device Name
            </label>
            <input
              type="text"
              value={state.deviceName}
              onChange={handleDeviceNameChange}
              placeholder="Kitchen Sensor"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              maxLength={50}
            />
            <p className="mt-1 text-xs text-gray-500">
              Give your device a friendly name
            </p>
          </div>

          {state.error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{state.error}</p>
            </div>
          )}

          <button
            onClick={handlePairDevice}
            disabled={!state.deviceId || !state.deviceName}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Pair Device
          </button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">or</span>
            </div>
          </div>

          <button
            onClick={() => alert('QR code scanner coming soon!')}
            className="w-full py-3 border-2 border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
          >
            <QrCode className="w-5 h-5" />
            Scan QR Code
          </button>
        </div>
      )}

      {state.step === 'validating' && (
        <div className="py-8 text-center">
          <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-700 font-medium">Pairing device...</p>
          <p className="text-sm text-gray-500 mt-2">This may take a few seconds</p>
        </div>
      )}

      {state.step === 'success' && (
        <div className="py-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <p className="text-gray-900 font-semibold text-lg mb-2">Device Paired Successfully!</p>
          <p className="text-gray-600 mb-1">{state.deviceName}</p>
          <p className="text-sm text-gray-500">{state.deviceId}</p>
        </div>
      )}

      {state.step === 'error' && (
        <div className="py-8 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <p className="text-gray-900 font-semibold text-lg mb-2">Pairing Failed</p>
          <p className="text-gray-600 mb-6">{state.error}</p>
          <button
            onClick={handleReset}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
