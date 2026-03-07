/**
 * Calibrate Sensor Modal Component
 * Modal for selecting sensors to calibrate
 * 
 * Allows selection of multiple sensors:
 * - pH Sensor
 * - Turbidity Sensor
 * - TDS Sensor
 * - Temperature Sensor
 */

import React, { useState } from "react";
import { X, Settings } from "lucide-react";

interface CalibrateSensorModalProps {
  deviceId: string;
  onConfirm: (sensors: string[]) => void;
  onCancel: () => void;
}

const AVAILABLE_SENSORS = [
  { id: "pH", label: "pH Sensor", description: "Calibrate pH measurement" },
  {
    id: "turbidity",
    label: "Turbidity Sensor",
    description: "Calibrate turbidity measurement",
  },
  { id: "tds", label: "TDS Sensor", description: "Calibrate TDS measurement" },
  {
    id: "temperature",
    label: "Temperature Sensor",
    description: "Calibrate temperature measurement",
  },
];

const CalibrateSensorModal: React.FC<CalibrateSensorModalProps> = ({
  deviceId,
  onConfirm,
  onCancel,
}) => {
  const [selectedSensors, setSelectedSensors] = useState<string[]>([]);

  const handleToggleSensor = (sensorId: string) => {
    setSelectedSensors((prev) =>
      prev.includes(sensorId)
        ? prev.filter((id) => id !== sensorId)
        : [...prev, sensorId]
    );
  };

  const handleConfirm = () => {
    if (selectedSensors.length === 0) {
      return; // Don't allow confirmation without selecting sensors
    }
    onConfirm(selectedSensors);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="text-purple-600 dark:text-purple-400">
              <Settings size={24} />
            </div>
            <h2
              id="modal-title"
              className="text-lg font-semibold text-gray-900 dark:text-white"
            >
              Calibrate Sensors
            </h2>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="p-6">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Select sensors to calibrate for device <strong>{deviceId}</strong>
          </p>

          <div className="space-y-3">
            {AVAILABLE_SENSORS.map((sensor) => (
              <label
                key={sensor.id}
                className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedSensors.includes(sensor.id)}
                  onChange={() => handleToggleSensor(sensor.id)}
                  className="mt-1 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <div className="flex-1">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {sensor.label}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {sensor.description}
                  </div>
                </div>
              </label>
            ))}
          </div>

          {selectedSensors.length === 0 && (
            <p className="mt-4 text-sm text-orange-600 dark:text-orange-400">
              Please select at least one sensor to calibrate.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={selectedSensors.length === 0}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start Calibration
          </button>
        </div>
      </div>
    </div>
  );
};

export default CalibrateSensorModal;
