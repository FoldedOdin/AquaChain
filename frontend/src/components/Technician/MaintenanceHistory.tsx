import React, { useState, useEffect } from 'react';
import { MaintenanceReport, TechnicianTask } from '../../types';
import { technicianService } from '../../services/technicianService';

interface MaintenanceHistoryProps {
  deviceId?: string;
  technicianId?: string;
}

const MaintenanceHistory: React.FC<MaintenanceHistoryProps> = ({
  deviceId,
  technicianId
}) => {
  const [reports, setReports] = useState<MaintenanceReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedReport, setSelectedReport] = useState<MaintenanceReport | null>(null);

  useEffect(() => {
    loadMaintenanceHistory();
  }, [deviceId, technicianId]);

  const loadMaintenanceHistory = async () => {
    try {
      setLoading(true);
      // Mock data for development
      const mockReports: MaintenanceReport[] = [
        {
          reportId: 'RPT-001',
          taskId: 'TASK-001',
          deviceId: 'DEV-3421',
          technicianId: 'TECH-001',
          completedAt: '2025-10-18T16:30:00Z',
          workPerformed: 'Replaced pH sensor and recalibrated all sensors. Cleaned turbidity sensor housing.',
          partsUsed: [
            {
              partNumber: 'PH-SENSOR-V2',
              description: 'pH Sensor Module v2.1',
              quantity: 1,
              cost: 45.99
            },
            {
              partNumber: 'CLEAN-KIT',
              description: 'Sensor Cleaning Kit',
              quantity: 1,
              cost: 12.50
            }
          ],
          diagnosticData: {
            deviceStatus: 'operational',
            sensorReadings: {
              pH: { value: 7.2, status: 'normal' },
              turbidity: { value: 1.1, status: 'normal' },
              tds: { value: 148, status: 'normal' },
              temperature: { value: 24.8, status: 'normal' },
              humidity: { value: 65.2, status: 'normal' }
            },
            batteryLevel: 92,
            signalStrength: -58,
            calibrationStatus: 'current',
            lastCalibrationDate: '2025-10-18T16:30:00Z'
          },
          beforePhotos: ['photo1.jpg', 'photo2.jpg'],
          afterPhotos: ['photo3.jpg', 'photo4.jpg'],
          nextMaintenanceDate: '2026-04-18',
          recommendations: 'Monitor pH readings closely for the next week. Schedule routine maintenance in 6 months.'
        },
        {
          reportId: 'RPT-002',
          taskId: 'TASK-002',
          deviceId: 'DEV-3422',
          technicianId: 'TECH-001',
          completedAt: '2025-10-17T14:15:00Z',
          workPerformed: 'Routine maintenance check. All sensors functioning normally. Updated firmware to v2.1.3.',
          partsUsed: [],
          diagnosticData: {
            deviceStatus: 'operational',
            sensorReadings: {
              pH: { value: 7.0, status: 'normal' },
              turbidity: { value: 0.8, status: 'normal' },
              tds: { value: 152, status: 'normal' },
              temperature: { value: 25.1, status: 'normal' },
              humidity: { value: 62.8, status: 'normal' }
            },
            batteryLevel: 88,
            signalStrength: -62,
            calibrationStatus: 'current'
          },
          beforePhotos: ['photo5.jpg'],
          afterPhotos: ['photo6.jpg'],
          nextMaintenanceDate: '2026-04-17',
          recommendations: 'Device is in excellent condition. Continue regular monitoring.'
        }
      ];
      
      let filteredReports = mockReports;
      if (deviceId) {
        filteredReports = filteredReports.filter(r => r.deviceId === deviceId);
      }
      if (technicianId) {
        filteredReports = filteredReports.filter(r => r.technicianId === technicianId);
      }
      
      setReports(filteredReports);
    } catch (err) {
      setError('Failed to load maintenance history');
      console.error('Error loading maintenance history:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredReports = reports.filter(report =>
    report.workPerformed.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.deviceId.toLowerCase().includes(searchTerm.toLowerCase()) ||
    report.reportId.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'bg-green-100 text-green-800';
      case 'needs_repair':
        return 'bg-yellow-100 text-yellow-800';
      case 'replaced':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-sm text-red-700">{error}</div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Maintenance History
          </h3>
          <div className="flex items-center space-x-3">
            <input
              type="text"
              placeholder="Search reports..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        {filteredReports.length === 0 ? (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No maintenance reports</h3>
            <p className="mt-1 text-sm text-gray-500">
              {searchTerm ? 'No reports match your search.' : 'No maintenance reports found.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredReports.map((report) => (
              <div
                key={report.reportId}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                onClick={() => setSelectedReport(report)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-sm font-medium text-gray-900">
                        Report {report.reportId}
                      </h4>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(report.diagnosticData.deviceStatus)}`}>
                        {report.diagnosticData.deviceStatus.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">
                        Device: {report.deviceId}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                      {report.workPerformed}
                    </p>
                    
                    <div className="flex items-center text-xs text-gray-500 space-x-4">
                      <span>Completed: {formatDate(report.completedAt)}</span>
                      <span>Parts: {report.partsUsed.length}</span>
                      <span>Photos: {report.beforePhotos.length + report.afterPhotos.length}</span>
                      {report.nextMaintenanceDate && (
                        <span>Next: {new Date(report.nextMaintenanceDate).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="ml-4">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Report Detail Modal */}
        {selectedReport && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Maintenance Report {selectedReport.reportId}
                </h3>
                <button
                  onClick={() => setSelectedReport(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="max-h-96 overflow-y-auto space-y-4">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 uppercase">Device ID</label>
                    <p className="text-sm text-gray-900">{selectedReport.deviceId}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 uppercase">Completed</label>
                    <p className="text-sm text-gray-900">{formatDate(selectedReport.completedAt)}</p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 uppercase">Status</label>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(selectedReport.diagnosticData.deviceStatus)}`}>
                      {selectedReport.diagnosticData.deviceStatus.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Work Performed */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Work Performed</h4>
                  <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                    {selectedReport.workPerformed}
                  </p>
                </div>

                {/* Diagnostic Data */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Diagnostic Data</h4>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-3">
                      {Object.entries(selectedReport.diagnosticData.sensorReadings).map(([sensor, reading]) => (
                        <div key={sensor} className="text-center">
                          <div className="text-lg font-semibold text-gray-900">{reading.value}</div>
                          <div className="text-xs text-gray-500 capitalize">{sensor === 'tds' ? 'TDS' : sensor}</div>
                          <div className={`text-xs px-1 rounded ${
                            reading.status === 'normal' ? 'bg-green-100 text-green-800' :
                            reading.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {reading.status}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div>
                        <span className="text-gray-500">Battery:</span> {selectedReport.diagnosticData.batteryLevel}%
                      </div>
                      <div>
                        <span className="text-gray-500">Signal:</span> {selectedReport.diagnosticData.signalStrength} dBm
                      </div>
                      <div>
                        <span className="text-gray-500">Calibration:</span> {selectedReport.diagnosticData.calibrationStatus.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Parts Used */}
                {selectedReport.partsUsed.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Parts Used</h4>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="space-y-2">
                        {selectedReport.partsUsed.map((part, index) => (
                          <div key={index} className="flex justify-between items-center text-sm">
                            <div>
                              <span className="font-medium">{part.partNumber}</span> - {part.description}
                              <span className="text-gray-500 ml-2">Qty: {part.quantity}</span>
                            </div>
                            {part.cost && (
                              <span className="text-gray-900">${part.cost.toFixed(2)}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {selectedReport.recommendations && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Recommendations</h4>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                      {selectedReport.recommendations}
                    </p>
                  </div>
                )}

                {/* Next Maintenance */}
                {selectedReport.nextMaintenanceDate && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Next Maintenance</h4>
                    <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                      Scheduled for: {new Date(selectedReport.nextMaintenanceDate).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                      })}
                    </p>
                  </div>
                )}

                {/* Photos */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Documentation</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 uppercase mb-2">Before Photos ({selectedReport.beforePhotos.length})</h5>
                      <div className="grid grid-cols-2 gap-2">
                        {selectedReport.beforePhotos.map((photo, index) => (
                          <div key={index} className="aspect-square bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-xs text-gray-500">Photo {index + 1}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h5 className="text-xs font-medium text-gray-500 uppercase mb-2">After Photos ({selectedReport.afterPhotos.length})</h5>
                      <div className="grid grid-cols-2 gap-2">
                        {selectedReport.afterPhotos.map((photo, index) => (
                          <div key={index} className="aspect-square bg-gray-200 rounded flex items-center justify-center">
                            <span className="text-xs text-gray-500">Photo {index + 1}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MaintenanceHistory;