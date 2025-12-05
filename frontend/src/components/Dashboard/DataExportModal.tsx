import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  DocumentArrowDownIcon,
  CalendarIcon,
  ChartBarIcon,
  TableCellsIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

interface DataExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  userRole: 'consumer' | 'technician' | 'admin';
}

const DataExportModal: React.FC<DataExportModalProps> = ({ isOpen, onClose, userRole }) => {
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'pdf' | 'json'>('csv');
  const [selectedDateRange, setSelectedDateRange] = useState<'7d' | '30d' | '90d' | 'custom'>('30d');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [selectedDataTypes, setSelectedDataTypes] = useState<string[]>([]);
  const [isExporting, setIsExporting] = useState(false);

  // Define available data types based on user role
  const getAvailableDataTypes = () => {
    switch (userRole) {
      case 'consumer':
        return [
          { id: 'water-quality', label: 'Water Quality Metrics', description: 'pH, chlorine, turbidity levels' },
          { id: 'usage', label: 'Water Usage Data', description: 'Daily and monthly consumption' },
          { id: 'alerts', label: 'Safety Alerts', description: 'Notifications and warnings' }
        ];
      case 'technician':
        return [
          { id: 'equipment-status', label: 'Equipment Status', description: 'Sensor health and performance' },
          { id: 'maintenance-logs', label: 'Maintenance Logs', description: 'Service history and tasks' },
          { id: 'calibration-data', label: 'Calibration Data', description: 'Sensor calibration records' },
          { id: 'field-reports', label: 'Field Reports', description: 'Inspection and repair reports' }
        ];
      case 'admin':
        return [
          { id: 'system-overview', label: 'System Overview', description: 'Complete system metrics' },
          { id: 'user-activity', label: 'User Activity', description: 'User login and usage statistics' },
          { id: 'compliance-reports', label: 'Compliance Reports', description: 'EPA and regulatory compliance data' },
          { id: 'audit-logs', label: 'Audit Logs', description: 'System access and change logs' },
          { id: 'performance-metrics', label: 'Performance Metrics', description: 'System performance and uptime' }
        ];
      default:
        return [];
    }
  };

  const availableDataTypes = getAvailableDataTypes();

  const handleDataTypeToggle = (dataTypeId: string) => {
    setSelectedDataTypes(prev => 
      prev.includes(dataTypeId) 
        ? prev.filter(id => id !== dataTypeId)
        : [...prev, dataTypeId]
    );
  };

  const handleExport = async () => {
    if (selectedDataTypes.length === 0) {
      alert('Please select at least one data type to export.');
      return;
    }

    setIsExporting(true);
    
    try {
      // Simulate export process
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const exportData = {
        format: selectedFormat,
        dateRange: selectedDateRange,
        customDates: selectedDateRange === 'custom' ? { start: customStartDate, end: customEndDate } : null,
        dataTypes: selectedDataTypes,
        exportedAt: new Date().toISOString(),
        userRole
      };

      let blob: Blob;
      let mimeType: string;
      let fileExtension: string;

      switch (selectedFormat) {
        case 'csv':
          // Generate CSV
          const csvContent = generateCSV(exportData);
          blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
          mimeType = 'text/csv';
          fileExtension = 'csv';
          break;

        case 'pdf':
          // Generate HTML-based PDF (can be printed to PDF)
          const htmlContent = generateHTMLReport(exportData);
          blob = new Blob([htmlContent], { type: 'text/html' });
          mimeType = 'text/html';
          fileExtension = 'html';
          // Open in new window for printing
          const printWindow = window.open('', '_blank');
          if (printWindow) {
            printWindow.document.write(htmlContent);
            printWindow.document.close();
            setTimeout(() => {
              printWindow.print();
            }, 500);
          }
          setIsExporting(false);
          onClose();
          return; // Skip the download part

        case 'json':
        default:
          // Generate JSON
          blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
          mimeType = 'application/json';
          fileExtension = 'json';
          break;
      }

      // Create download
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `aquachain-export-${userRole}-${Date.now()}.${fileExtension}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setIsExporting(false);
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
      setIsExporting(false);
    }
  };

  const generateCSV = (data: any): string => {
    const headers = ['Data Type', 'Date Range', 'Exported At', 'User Role'];
    const rows = data.dataTypes.map((type: string) => [
      type,
      getDateRangeLabel(),
      new Date(data.exportedAt).toLocaleString(),
      data.userRole
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row: string[]) => row.join(','))
    ].join('\n');

    return csvContent;
  };

  const generateHTMLReport = (data: any): string => {
    const exportDate = new Date(data.exportedAt).toLocaleString();
    const dateRange = getDateRangeLabel();
    
    // Get full data type labels
    const selectedTypes = availableDataTypes
      .filter(dt => data.dataTypes.includes(dt.id))
      .map(dt => `<tr><td style="padding: 8px; border: 1px solid #ddd;">${dt.label}</td><td style="padding: 8px; border: 1px solid #ddd;">${dt.description}</td></tr>`)
      .join('');
    
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AquaChain Data Export Report</title>
  <style>
    @media print {
      body { margin: 0; }
      .no-print { display: none; }
    }
    body {
      font-family: Arial, sans-serif;
      max-width: 800px;
      margin: 40px auto;
      padding: 20px;
      color: #333;
    }
    .header {
      text-align: center;
      border-bottom: 3px solid #3b82f6;
      padding-bottom: 20px;
      margin-bottom: 30px;
    }
    .header h1 {
      color: #1e40af;
      margin: 0 0 10px 0;
    }
    .header p {
      color: #6b7280;
      margin: 5px 0;
    }
    .section {
      margin: 30px 0;
    }
    .section h2 {
      color: #1e40af;
      border-bottom: 2px solid #e5e7eb;
      padding-bottom: 10px;
      margin-bottom: 15px;
    }
    .info-grid {
      display: grid;
      grid-template-columns: 200px 1fr;
      gap: 10px;
      margin: 15px 0;
    }
    .info-label {
      font-weight: bold;
      color: #4b5563;
    }
    .info-value {
      color: #1f2937;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
    }
    th {
      background-color: #3b82f6;
      color: white;
      padding: 12px;
      text-align: left;
      font-weight: 600;
    }
    td {
      padding: 10px;
      border: 1px solid #e5e7eb;
    }
    tr:nth-child(even) {
      background-color: #f9fafb;
    }
    .footer {
      margin-top: 50px;
      padding-top: 20px;
      border-top: 2px solid #e5e7eb;
      text-align: center;
      color: #6b7280;
      font-size: 14px;
    }
    .print-button {
      background-color: #3b82f6;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 16px;
      margin: 20px 0;
    }
    .print-button:hover {
      background-color: #2563eb;
    }
  </style>
</head>
<body>
  <div class="no-print" style="text-align: center;">
    <button class="print-button" onclick="window.print()">🖨️ Print / Save as PDF</button>
  </div>

  <div class="header">
    <h1>🌊 AquaChain Data Export Report</h1>
    <p>Water Quality Monitoring System</p>
  </div>

  <div class="section">
    <h2>Export Information</h2>
    <div class="info-grid">
      <div class="info-label">Export Date:</div>
      <div class="info-value">${exportDate}</div>
      
      <div class="info-label">User Role:</div>
      <div class="info-value">${data.userRole.charAt(0).toUpperCase() + data.userRole.slice(1)}</div>
      
      <div class="info-label">Date Range:</div>
      <div class="info-value">${dateRange}</div>
      
      ${data.customDates ? `
      <div class="info-label">Custom Start:</div>
      <div class="info-value">${data.customDates.start}</div>
      
      <div class="info-label">Custom End:</div>
      <div class="info-value">${data.customDates.end}</div>
      ` : ''}
    </div>
  </div>

  <div class="section">
    <h2>Selected Data Types</h2>
    <table>
      <thead>
        <tr>
          <th>Data Type</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        ${selectedTypes}
      </tbody>
    </table>
  </div>

  <div class="section">
    <h2>Report Summary</h2>
    <p>This report contains ${data.dataTypes.length} data type(s) exported from the AquaChain Water Quality Monitoring System.</p>
    <p>The data covers the period: <strong>${dateRange}</strong></p>
    <p>For detailed data analysis and visualization, please access the AquaChain dashboard.</p>
  </div>

  <div class="footer">
    <p><strong>AquaChain</strong> - Advanced Water Quality Monitoring</p>
    <p>Generated on ${exportDate}</p>
    <p style="margin-top: 10px; font-size: 12px;">
      This is an automated report. For questions or support, please contact your system administrator.
    </p>
  </div>

  <script>
    // Auto-print on load (optional)
    // window.onload = function() { window.print(); };
  </script>
</body>
</html>`;
  };

  const getDateRangeLabel = () => {
    switch (selectedDateRange) {
      case '7d': return 'Last 7 days';
      case '30d': return 'Last 30 days';
      case '90d': return 'Last 90 days';
      case 'custom': return 'Custom range';
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-50"
            onClick={onClose}
          />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              {/* Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <DocumentArrowDownIcon className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900">Export Data</h2>
                      <p className="text-sm text-gray-600">Download your data in various formats</p>
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                {/* Format Selection */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Export Format</h3>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      onClick={() => setSelectedFormat('csv')}
                      className={`p-4 border rounded-lg transition-colors duration-200 ${
                        selectedFormat === 'csv'
                          ? 'border-blue-500 bg-blue-50 text-blue-900'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <TableCellsIcon className="w-6 h-6 mx-auto mb-2" />
                      <div className="text-sm font-medium">CSV</div>
                      <div className="text-xs text-gray-600">Spreadsheet format</div>
                    </button>

                    <button
                      onClick={() => setSelectedFormat('pdf')}
                      className={`p-4 border rounded-lg transition-colors duration-200 ${
                        selectedFormat === 'pdf'
                          ? 'border-blue-500 bg-blue-50 text-blue-900'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <DocumentTextIcon className="w-6 h-6 mx-auto mb-2" />
                      <div className="text-sm font-medium">PDF</div>
                      <div className="text-xs text-gray-600">Report format</div>
                    </button>

                    <button
                      onClick={() => setSelectedFormat('json')}
                      className={`p-4 border rounded-lg transition-colors duration-200 ${
                        selectedFormat === 'json'
                          ? 'border-blue-500 bg-blue-50 text-blue-900'
                          : 'border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <ChartBarIcon className="w-6 h-6 mx-auto mb-2" />
                      <div className="text-sm font-medium">JSON</div>
                      <div className="text-xs text-gray-600">Data format</div>
                    </button>
                  </div>
                </div>

                {/* Date Range Selection */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Date Range</h3>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {['7d', '30d', '90d', 'custom'].map((range) => (
                      <button
                        key={range}
                        onClick={() => setSelectedDateRange(range as any)}
                        className={`p-3 border rounded-lg text-sm transition-colors duration-200 ${
                          selectedDateRange === range
                            ? 'border-blue-500 bg-blue-50 text-blue-900'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        {range === '7d' && 'Last 7 days'}
                        {range === '30d' && 'Last 30 days'}
                        {range === '90d' && 'Last 90 days'}
                        {range === 'custom' && 'Custom range'}
                      </button>
                    ))}
                  </div>

                  {selectedDateRange === 'custom' && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                        <input
                          type="date"
                          value={customStartDate}
                          onChange={(e) => setCustomStartDate(e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                        <input
                          type="date"
                          value={customEndDate}
                          onChange={(e) => setCustomEndDate(e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Data Type Selection */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Data to Export</h3>
                  <div className="space-y-2">
                    {availableDataTypes.map((dataType) => (
                      <label
                        key={dataType.id}
                        className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDataTypes.includes(dataType.id)}
                          onChange={() => handleDataTypeToggle(dataType.id)}
                          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{dataType.label}</div>
                          <div className="text-sm text-gray-600">{dataType.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Export Summary */}
                {selectedDataTypes.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Export Summary</h4>
                    <div className="text-sm text-blue-800 space-y-1">
                      <div>Format: {selectedFormat.toUpperCase()}</div>
                      <div>Date Range: {getDateRangeLabel()}</div>
                      <div>Data Types: {selectedDataTypes.length} selected</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-6 border-t border-gray-200 bg-gray-50 rounded-b-xl">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    {selectedDataTypes.length} data type{selectedDataTypes.length !== 1 ? 's' : ''} selected
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={onClose}
                      className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors duration-200"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleExport}
                      disabled={selectedDataTypes.length === 0 || isExporting}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center gap-2"
                    >
                      {isExporting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          <span>Exporting...</span>
                        </>
                      ) : (
                        <>
                          <DocumentArrowDownIcon className="w-4 h-4" />
                          <span>Export Data</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default DataExportModal;