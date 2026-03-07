/**
 * Device Actions Component
 * Action buttons for device management
 * 
 * Actions:
 * - View Device: Navigate to device detail page
 * - Restart Device: Restart the device (with confirmation)
 * - Calibrate Sensor: Calibrate device sensors (with modal)
 * - Disable Device: Disable the device (with confirmation)
 * 
 * Read-only mode disables all actions except View
 */

import React, { useState } from "react";
import { Eye, RotateCw, Settings, XCircle } from "lucide-react";
import { toast } from "react-toastify";
import { Device } from "../../types/device";
import ConfirmationModal from "./modals/ConfirmationModal";
import CalibrateSensorModal from "./modals/CalibrateSensorModal";

interface DeviceActionsProps {
  device: Device;
  readOnly: boolean;
}

const DeviceActions: React.FC<DeviceActionsProps> = ({ device, readOnly }) => {
  const [showRestartModal, setShowRestartModal] = useState(false);
  const [showCalibrateModal, setShowCalibrateModal] = useState(false);
  const [showDisableModal, setShowDisableModal] = useState(false);

  const handleViewDevice = () => {
    // Navigate to device detail page
    window.location.href = `/devices/${device.deviceId}`;
  };

  const handleRestartDevice = () => {
    toast.success(`Device ${device.deviceId} restart initiated`, {
      position: "top-right",
      autoClose: 5000,
    });
    setShowRestartModal(false);
  };

  const handleCalibrateDevice = (sensors: string[]) => {
    toast.success(
      `Calibration started for ${device.deviceId}: ${sensors.join(", ")}`,
      {
        position: "top-right",
        autoClose: 5000,
      }
    );
    setShowCalibrateModal(false);
  };

  const handleDisableDevice = () => {
    toast.warning(`Device ${device.deviceId} has been disabled`, {
      position: "top-right",
      autoClose: 5000,
    });
    setShowDisableModal(false);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        <button
          onClick={handleViewDevice}
          className="p-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 transition-colors"
          title="View Device"
          aria-label={`View device ${device.deviceId}`}
        >
          <Eye size={16} />
        </button>

        {!readOnly && (
          <>
            <button
              onClick={() => setShowRestartModal(true)}
              className="p-1 text-orange-600 hover:text-orange-800 dark:text-orange-400 dark:hover:text-orange-300 transition-colors"
              title="Restart Device"
              aria-label={`Restart device ${device.deviceId}`}
            >
              <RotateCw size={16} />
            </button>

            <button
              onClick={() => setShowCalibrateModal(true)}
              className="p-1 text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300 transition-colors"
              title="Calibrate Sensor"
              aria-label={`Calibrate sensors for device ${device.deviceId}`}
            >
              <Settings size={16} />
            </button>

            <button
              onClick={() => setShowDisableModal(true)}
              className="p-1 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 transition-colors"
              title="Disable Device"
              aria-label={`Disable device ${device.deviceId}`}
            >
              <XCircle size={16} />
            </button>
          </>
        )}
      </div>

      {/* Modals */}
      {showRestartModal && (
        <ConfirmationModal
          title="Restart Device"
          message={`Are you sure you want to restart ${device.deviceId}? The device will be offline for approximately 30 seconds.`}
          confirmLabel="Restart"
          confirmVariant="warning"
          onConfirm={handleRestartDevice}
          onCancel={() => setShowRestartModal(false)}
        />
      )}

      {showCalibrateModal && (
        <CalibrateSensorModal
          deviceId={device.deviceId}
          onConfirm={handleCalibrateDevice}
          onCancel={() => setShowCalibrateModal(false)}
        />
      )}

      {showDisableModal && (
        <ConfirmationModal
          title="Disable Device"
          message={`Are you sure you want to disable ${device.deviceId}? This will stop all data collection and alerts for this device.`}
          confirmLabel="Disable"
          confirmVariant="danger"
          onConfirm={handleDisableDevice}
          onCancel={() => setShowDisableModal(false)}
        />
      )}
    </>
  );
};

export default DeviceActions;
