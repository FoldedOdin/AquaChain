import React, { useState } from 'react';
import { TechnicianTask, MaintenanceReport, MaintenancePart, DiagnosticData } from '../../types';
import { technicianService } from '../../services/technicianService';

interface MaintenanceReportProps {
  task: TechnicianTask;
  onComplete: () => void;
  onCancel: () => void;
}

const MaintenanceReportComponent: React.FC<MaintenanceReportProps> = ({
  task,
  onComplete,
  onCancel
}) => {
  const [workPerformed, setWorkPerformed] = useState('');
  const [partsUsed, setPartsUsed] = useState<MaintenancePart[]>([]);
  const [diagnosticData, setDiagnosticData] = useState<DiagnosticData>({
    deviceStatus: 'operational',
    sensorReadings: {
      pH: { value: 7.0, status: 'normal' },
      turbidity: { value: 1.0, status: 'normal' },
      tds: { value: 150, status: 'normal' },
      temperature: { value: 25.0, status: 'normal' },
      humidity: { value: 60.0, status: 'normal' }
    },
    batteryLevel: 85,
    signalStrength: -65,
    calibrationStatus: 'current'
  });
  const [beforePhotos, setBeforePhotos] = useState<string[]>([]);
  const [afterPhotos, setAfterPhotos] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState('');
  const [nextMaintenanceDate, setNextMaintenanceDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const addPart = () => {
    setPartsUsed([...partsUsed, {
      partNumber: '',
      description: '',
      quantity: 1,
      cost: 0
    }]);
  };

  const updatePart = (index: number, field: keyof MaintenancePart, value: string | number) => {
    const updatedParts = [...partsUsed];
    updatedParts[index] = { ...updatedParts[index], [field]: value };
    setPartsUsed(updatedParts);
  };

  const removePart = (index: number) => {
    setPartsUsed(partsUsed.filter((_, i) => i !== index));
  };

  const updateSensorReading = (sensor: keyof DiagnosticData['sensorReadings'], field: 'value' | 'status', value: number | string) => {
    setDiagnosticData(prev => ({
      ...prev,
      sensorReadings: {
        ...prev.sensorReadings,
        [sensor]: {
          ...prev.sensorReadings[sensor],
          [field]: value
        }
      }
    }));
  };

  const handlePhotoUpload = async (event: React.ChangeEvent<HTMLInputElement>, type: 'before' | 'after') => {
    const files = event.target.files;
    if (!files) return;

    // Mock photo upload - in production this would upload to S3
    const mockUrls = Array.from(files).map((file, index) => 
      `https://example.com/photos/${task.taskId}_${type}_${Date.now()}_${index}.jpg`
    );

    if (type === 'before') {
      setBeforePhotos([...beforePhotos, ...mockUrls]);
    } else {
      setAfterPhotos([...afterPhotos, ...mockUrls]);
    }
  };

  const removePhoto = (url: string, type: 'before' | 'after') => {
    if (type === 'before') {
      setBeforePhotos(beforePhotos.filter(photo => photo !== url));
    } else {
      setAfterPhotos(afterPhotos.filter(photo => photo !== url));
    }
  };

  const handleSubmit = async () => {
    if (!workPerformed.trim()) {
      alert('Please describe the work performed');
      return;
    }

    setIsSubmitting(true);
    try {
      const report: Omit<MaintenanceReport, 'reportId' | 'completedAt'> = {
        taskId: task.taskId,
        deviceId: task.deviceId,
        technicianId: 'current-technician-id', // This would come from auth context
        workPerformed: workPerformed.trim(),
        partsUsed,
        diagnosticData,
        beforePhotos,
        afterPhotos,
        nextMaintenanceDate: nextMaintenanceDate || undefined,
        recommendations: recommendations.trim()
      };

      await technicianService.completeTask(task.taskId, report);
      onComplete();
    } catch (error) {
      console.error('Error submitting maintenance report:', error);
      alert('Failed to submit maintenance report. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Maintenance Report
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Complete the maintenance report for {task.customerInfo.name}
            </p>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-6">
          {/* Work Performed */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Work Performed *
            </label>
            <textarea
              value={workPerformed}
              onChange={(e) => setWorkPerformed(e.target.value)}
              rows={4}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Describe the maintenance work performed..."
            />
          </div>

          {/* Diagnostic Data */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">Device Diagnostics</h4>
            <div className="bg-gray-50 rounded-lg p-4 space-y-4">
              {/* Device Status */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                  Device Status
                </label>
                <select
                  value={diagnosticData.deviceStatus}
                  onChange={(e) => setDiagnosticData(prev => ({ ...prev, deviceStatus: e.target.value as DiagnosticData['deviceStatus'] }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="operational">Operational</option>
                  <option value="needs_repair">Needs Repair</option>
                  <option value="replaced">Replaced</option>
                </select>
              </div>

              {/* Sensor Readings */}
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                  Sensor Readings
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(diagnosticData.sensorReadings).map(([sensor, reading]) => (
                    <div key={sensor} className="bg-white p-3 rounded border">
                      <div className="text-sm font-medium text-gray-700 mb-2 capitalize">
                        {sensor === 'tds' ? 'TDS' : sensor}
                      </div>
                      <div className="space-y-2">
                        <input
                          type="number"
                          step="0.1"
                          value={reading.value}
                          onChange={(e) => updateSensorReading(sensor as keyof DiagnosticData['sensorReadings'], 'value', parseFloat(e.target.value))}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                        />
                        <select
                          value={reading.status}
                          onChange={(e) => updateSensorReading(sensor as keyof DiagnosticData['sensorReadings'], 'status', e.target.value)}
                          className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                        >
                          <option value="normal">Normal</option>
                          <option value="warning">Warning</option>
                          <option value="error">Error</option>
                        </select>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Battery and Signal */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Battery Level (%)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={diagnosticData.batteryLevel}
                    onChange={(e) => setDiagnosticData(prev => ({ ...prev, batteryLevel: parseInt(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Signal Strength (dBm)
                  </label>
                  <input
                    type="number"
                    value={diagnosticData.signalStrength}
                    onChange={(e) => setDiagnosticData(prev => ({ ...prev, signalStrength: parseInt(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">
                    Calibration Status
                  </label>
                  <select
                    value={diagnosticData.calibrationStatus}
                    onChange={(e) => setDiagnosticData(prev => ({ ...prev, calibrationStatus: e.target.value as DiagnosticData['calibrationStatus'] }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
                  >
                    <option value="current">Current</option>
                    <option value="needs_calibration">Needs Calibration</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Parts Used */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-700">Parts Used</h4>
              <button
                onClick={addPart}
                className="inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Add Part
              </button>
            </div>
            
            {partsUsed.length === 0 ? (
              <p className="text-sm text-gray-500 italic">No parts used</p>
            ) : (
              <div className="space-y-3">
                {partsUsed.map((part, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded-lg">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <input
                        type="text"
                        placeholder="Part Number"
                        value={part.partNumber}
                        onChange={(e) => updatePart(index, 'partNumber', e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 text-sm"
                      />
                      <input
                        type="text"
                        placeholder="Description"
                        value={part.description}
                        onChange={(e) => updatePart(index, 'description', e.target.value)}
                        className="border border-gray-300 rounded px-3 py-2 text-sm"
                      />
                      <input
                        type="number"
                        placeholder="Quantity"
                        min="1"
                        value={part.quantity}
                        onChange={(e) => updatePart(index, 'quantity', parseInt(e.target.value))}
                        className="border border-gray-300 rounded px-3 py-2 text-sm"
                      />
                      <div className="flex items-center space-x-2">
                        <input
                          type="number"
                          placeholder="Cost"
                          step="0.01"
                          value={part.cost || ''}
                          onChange={(e) => updatePart(index, 'cost', parseFloat(e.target.value))}
                          className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
                        />
                        <button
                          onClick={() => removePart(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Photos */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Before Photos */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Before Photos
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => handlePhotoUpload(e, 'before')}
                  className="hidden"
                  id="before-photos"
                />
                <label
                  htmlFor="before-photos"
                  className="cursor-pointer flex flex-col items-center justify-center text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span className="text-sm">Upload Before Photos</span>
                </label>
                
                {beforePhotos.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {beforePhotos.map((photo, index) => (
                      <div key={index} className="relative">
                        <div className="aspect-square bg-gray-200 rounded flex items-center justify-center">
                          <span className="text-xs text-gray-500">Photo {index + 1}</span>
                        </div>
                        <button
                          onClick={() => removePhoto(photo, 'before')}
                          className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* After Photos */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                After Photos
              </label>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  onChange={(e) => handlePhotoUpload(e, 'after')}
                  className="hidden"
                  id="after-photos"
                />
                <label
                  htmlFor="after-photos"
                  className="cursor-pointer flex flex-col items-center justify-center text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span className="text-sm">Upload After Photos</span>
                </label>
                
                {afterPhotos.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {afterPhotos.map((photo, index) => (
                      <div key={index} className="relative">
                        <div className="aspect-square bg-gray-200 rounded flex items-center justify-center">
                          <span className="text-xs text-gray-500">Photo {index + 1}</span>
                        </div>
                        <button
                          onClick={() => removePhoto(photo, 'after')}
                          className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Recommendations
            </label>
            <textarea
              value={recommendations}
              onChange={(e) => setRecommendations(e.target.value)}
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Any recommendations for the customer or future maintenance..."
            />
          </div>

          {/* Next Maintenance Date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Next Maintenance Date (Optional)
            </label>
            <input
              type="date"
              value={nextMaintenanceDate}
              onChange={(e) => setNextMaintenanceDate(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Submit Buttons */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              onClick={onCancel}
              disabled={isSubmitting}
              className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !workPerformed.trim()}
              className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Submitting...
                </>
              ) : (
                'Complete Task'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceReportComponent;