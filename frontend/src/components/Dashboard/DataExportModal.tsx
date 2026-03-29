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

export interface ExportReading {
  timestamp: string;
  pH?: number;
  turbidity?: number;
  tds?: number;
  temperature?: number;
  wqi?: number;
  quality?: string;
}

export interface ExportAlert {
  timestamp?: string;
  created_at?: string;
  alert_type?: string;
  type?: string;
  severity?: string;
  message?: string;
  status?: string;
  acknowledged?: boolean;
}

export interface ExportDeviceInfo {
  device_id?: string;
  name?: string;
  location?: string | { lat?: number; lng?: number };
  installation_date?: string;
  status?: string;
}

interface DataExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  userRole: 'consumer' | 'technician' | 'admin';
  readings?: ExportReading[];
  alerts?: ExportAlert[];
  deviceInfo?: ExportDeviceInfo;
}

const DataExportModal: React.FC<DataExportModalProps> = ({
  isOpen,
  onClose,
  userRole,
  readings = [],
  alerts = [],
  deviceInfo,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'pdf' | 'json'>('csv');
  const [selectedDateRange, setSelectedDateRange] = useState<'7d' | '30d' | '90d' | 'custom'>('30d');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [selectedDataTypes, setSelectedDataTypes] = useState<string[]>([]);
  const [isExporting, setIsExporting] = useState(false);

  const getAvailableDataTypes = () => {
    switch (userRole) {
      case 'consumer':
        return [
          { id: 'water-quality', label: 'Water Quality Metrics', description: 'pH, chlorine, turbidity levels' },
          { id: 'usage', label: 'Water Usage Data', description: 'Daily and monthly consumption' },
          { id: 'alerts', label: 'Safety Alerts', description: 'Notifications and warnings' },
        ];
      case 'technician':
        return [
          { id: 'equipment-status', label: 'Equipment Status', description: 'Sensor health and performance' },
          { id: 'maintenance-logs', label: 'Maintenance Logs', description: 'Service history and tasks' },
          { id: 'calibration-data', label: 'Calibration Data', description: 'Sensor calibration records' },
          { id: 'field-reports', label: 'Field Reports', description: 'Inspection and repair reports' },
        ];
      case 'admin':
        return [
          { id: 'system-overview', label: 'System Overview', description: 'Complete system metrics' },
          { id: 'user-activity', label: 'User Activity', description: 'User login and usage statistics' },
          { id: 'compliance-reports', label: 'Compliance Reports', description: 'EPA and regulatory compliance data' },
          { id: 'audit-logs', label: 'Audit Logs', description: 'System access and change logs' },
          { id: 'performance-metrics', label: 'Performance Metrics', description: 'System performance and uptime' },
        ];
      default:
        return [];
    }
  };

  const availableDataTypes = getAvailableDataTypes();

  const handleDataTypeToggle = (id: string) => {
    setSelectedDataTypes(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    );
  };

  const getDateRangeLabel = () => {
    switch (selectedDateRange) {
      case '7d': return 'Last 7 days';
      case '30d': return 'Last 30 days';
      case '90d': return 'Last 90 days';
      case 'custom': return `${customStartDate} to ${customEndDate}`;
    }
  };

  // Filter readings by selected date range
  const getFilteredReadings = (): ExportReading[] => {
    if (!readings.length) return [];
    const now = new Date();
    let cutoff: Date | null = null;
    if (selectedDateRange === '7d') cutoff = new Date(now.getTime() - 7 * 86400000);
    else if (selectedDateRange === '30d') cutoff = new Date(now.getTime() - 30 * 86400000);
    else if (selectedDateRange === '90d') cutoff = new Date(now.getTime() - 90 * 86400000);
    else if (selectedDateRange === 'custom' && customStartDate) cutoff = new Date(customStartDate);
    if (!cutoff) return readings;
    const endCutoff = selectedDateRange === 'custom' && customEndDate ? new Date(customEndDate) : now;
    return readings.filter(r => {
      const d = new Date(r.timestamp);
      return d >= cutoff! && d <= endCutoff;
    });
  };

  const getFilteredAlerts = (): ExportAlert[] => {
    if (!alerts.length) return [];
    const now = new Date();
    let cutoff: Date | null = null;
    if (selectedDateRange === '7d') cutoff = new Date(now.getTime() - 7 * 86400000);
    else if (selectedDateRange === '30d') cutoff = new Date(now.getTime() - 30 * 86400000);
    else if (selectedDateRange === '90d') cutoff = new Date(now.getTime() - 90 * 86400000);
    else if (selectedDateRange === 'custom' && customStartDate) cutoff = new Date(customStartDate);
    if (!cutoff) return alerts;
    const endCutoff = selectedDateRange === 'custom' && customEndDate ? new Date(customEndDate) : now;
    return alerts.filter(a => {
      const ts = a.timestamp || a.created_at || '';
      if (!ts) return true;
      const d = new Date(ts);
      return d >= cutoff! && d <= endCutoff;
    });
  };

  const computeSummary = (filteredReadings: ExportReading[], filteredAlerts: ExportAlert[]) => {
    const wqiValues = filteredReadings.map(r => r.wqi).filter((v): v is number => v !== undefined);
    const avgWqi = wqiValues.length ? Math.round(wqiValues.reduce((a, b) => a + b, 0) / wqiValues.length) : null;
    const minWqi = wqiValues.length ? Math.min(...wqiValues) : null;
    const maxWqi = wqiValues.length ? Math.max(...wqiValues) : null;
    const criticalAlerts = filteredAlerts.filter(a => (a.severity || '').toLowerCase() === 'critical').length;
    const warningAlerts = filteredAlerts.filter(a => (a.severity || '').toLowerCase() === 'warning').length;
    return { avgWqi, minWqi, maxWqi, totalAlerts: filteredAlerts.length, criticalAlerts, warningAlerts };
  };

  const getWqiLabel = (wqi: number | null): string => {
    if (wqi === null) return 'N/A';
    if (wqi >= 90) return 'Excellent';
    if (wqi >= 70) return 'Good';
    if (wqi >= 50) return 'Fair';
    if (wqi >= 25) return 'Poor';
    return 'Very Poor';
  };

  const generateInsights = (
    filteredReadings: ExportReading[],
    filteredAlerts: ExportAlert[],
    summary: ReturnType<typeof computeSummary>
  ): string[] => {
    const insights: string[] = [];
    if (summary.avgWqi !== null) {
      insights.push(`Average Water Quality Index is ${summary.avgWqi} (${getWqiLabel(summary.avgWqi)}) over the selected period.`);
    }
    if (summary.minWqi !== null && summary.minWqi < 50) {
      insights.push(`Water quality dropped to a minimum of ${summary.minWqi} (${getWqiLabel(summary.minWqi)}) — review alerts for that period.`);
    }
    if (summary.criticalAlerts > 0) {
      insights.push(`${summary.criticalAlerts} critical alert(s) detected. Immediate attention may be required.`);
    }
    if (summary.totalAlerts === 0) {
      insights.push('No alerts recorded in this period — system operating normally.');
    }
    const highTurbidity = filteredReadings.filter(r => (r.turbidity ?? 0) > 5);
    if (highTurbidity.length > 0) {
      insights.push(`${highTurbidity.length} reading(s) showed turbidity above 5 NTU threshold.`);
    }
    const highTds = filteredReadings.filter(r => (r.tds ?? 0) > 500);
    if (highTds.length > 0) {
      insights.push(`${highTds.length} reading(s) showed TDS above 500 ppm threshold.`);
    }
    if (insights.length === 0) {
      insights.push('All parameters within normal ranges for the selected period.');
    }
    return insights;
  };

  const generateCSV = (): string => {
    const filteredReadings = getFilteredReadings();
    const filteredAlerts = getFilteredAlerts();
    const includeReadings = selectedDataTypes.includes('water-quality') || selectedDataTypes.includes('equipment-status') || selectedDataTypes.includes('system-overview');
    const includeAlerts = selectedDataTypes.includes('alerts') || selectedDataTypes.includes('compliance-reports');

    const sections: string[] = [];

    if (includeReadings && filteredReadings.length > 0) {
      sections.push('WATER QUALITY READINGS');
      sections.push('Timestamp,pH,Turbidity (NTU),TDS (ppm),Temperature (°C),WQI,Status');
      filteredReadings.forEach(r => {
        sections.push([
          r.timestamp,
          r.pH ?? '',
          r.turbidity ?? '',
          r.tds ?? '',
          r.temperature ?? '',
          r.wqi ?? '',
          r.quality ?? getWqiLabel(r.wqi ?? null),
        ].join(','));
      });
      sections.push('');
    }

    if (includeAlerts && filteredAlerts.length > 0) {
      sections.push('ALERTS');
      sections.push('Timestamp,Type,Severity,Message,Status');
      filteredAlerts.forEach(a => {
        sections.push([
          a.timestamp || a.created_at || '',
          a.alert_type || a.type || '',
          a.severity || '',
          `"${(a.message || '').replace(/"/g, '""')}"`,
          a.status || (a.acknowledged ? 'Acknowledged' : 'Active'),
        ].join(','));
      });
      sections.push('');
    }

    if (sections.length === 0) {
      sections.push('Export Date,Date Range,Role');
      sections.push(`${new Date().toLocaleString()},${getDateRangeLabel()},${userRole}`);
    }

    return sections.join('\n');
  };

  const generateHTMLReport = (): string => {
    const filteredReadings = getFilteredReadings();
    const filteredAlerts = getFilteredAlerts();
    const summary = computeSummary(filteredReadings, filteredAlerts);
    const insights = generateInsights(filteredReadings, filteredAlerts, summary);
    const exportDate = new Date().toLocaleString();
    const dateRange = getDateRangeLabel();
    const includeReadings = selectedDataTypes.includes('water-quality') || selectedDataTypes.includes('equipment-status') || selectedDataTypes.includes('system-overview');
    const includeAlerts = selectedDataTypes.includes('alerts') || selectedDataTypes.includes('compliance-reports');

    const deviceId = deviceInfo?.device_id || 'N/A';
    const deviceName = deviceInfo?.name || deviceId;
    const deviceLocation = typeof deviceInfo?.location === 'string'
      ? deviceInfo.location
      : deviceInfo?.location
        ? `${(deviceInfo.location as any).lat ?? ''}, ${(deviceInfo.location as any).lng ?? ''}`
        : 'N/A';

    const readingsRows = filteredReadings.map(r => `
      <tr>
        <td>${new Date(r.timestamp).toLocaleString()}</td>
        <td>${r.pH?.toFixed(2) ?? '-'}</td>
        <td>${r.turbidity?.toFixed(1) ?? '-'}</td>
        <td>${r.tds?.toFixed(0) ?? '-'}</td>
        <td>${r.temperature?.toFixed(1) ?? '-'}</td>
        <td><span class="wqi-badge ${getWqiBadgeClass(r.wqi ?? null)}">${r.wqi ?? '-'}</span></td>
        <td>${r.quality || getWqiLabel(r.wqi ?? null)}</td>
      </tr>`).join('');

    const alertRows = filteredAlerts.map(a => `
      <tr>
        <td>${a.timestamp || a.created_at ? new Date(a.timestamp || a.created_at || '').toLocaleString() : '-'}</td>
        <td>${a.alert_type || a.type || '-'}</td>
        <td><span class="severity-${(a.severity || 'info').toLowerCase()}">${a.severity || '-'}</span></td>
        <td>${a.message || '-'}</td>
        <td>${a.status || (a.acknowledged ? 'Acknowledged' : 'Active')}</td>
      </tr>`).join('');

    const insightItems = insights.map(i => `<p>• ${i}</p>`).join('');

    return buildHTMLTemplate({
      exportDate, dateRange, deviceId, deviceName, deviceLocation,
      summary, includeReadings, includeAlerts,
      readingsRows, alertRows, insightItems,
      readingsCount: filteredReadings.length,
      alertsCount: filteredAlerts.length,
    });
  };

  const getWqiBadgeClass = (wqi: number | null): string => {
    if (wqi === null) return '';
    if (wqi >= 70) return 'wqi-good';
    if (wqi >= 50) return 'wqi-fair';
    return 'wqi-poor';
  };

  const buildHTMLTemplate = ({
    exportDate, dateRange, deviceId, deviceName, deviceLocation,
    summary, includeReadings, includeAlerts,
    readingsRows, alertRows, insightItems,
    readingsCount, alertsCount,
  }: {
    exportDate: string; dateRange: string; deviceId: string; deviceName: string; deviceLocation: string;
    summary: ReturnType<typeof computeSummary>;
    includeReadings: boolean; includeAlerts: boolean;
    readingsRows: string; alertRows: string; insightItems: string;
    readingsCount: number; alertsCount: number;
  }): string => `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>AquaChain Water Quality Report</title>
  <style>
    @media print { .no-print { display: none; } body { margin: 0; } }
    * { box-sizing: border-box; }
    body { font-family: Inter, Arial, sans-serif; margin: 0; padding: 40px; color: #1f2937; background: #fff; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #e5e7eb; padding-bottom: 16px; margin-bottom: 24px; }
    .header h1 { color: #2563eb; margin: 0 0 4px 0; font-size: 24px; }
    .header p { color: #6b7280; margin: 2px 0; font-size: 13px; }
    .cards { display: flex; gap: 12px; margin-bottom: 28px; flex-wrap: wrap; }
    .card { flex: 1; min-width: 120px; padding: 14px 16px; border-radius: 10px; background: #f3f4f6; text-align: center; }
    .card .label { font-size: 12px; color: #6b7280; margin-bottom: 4px; }
    .card .value { font-size: 22px; font-weight: 700; color: #111827; }
    .card.critical .value { color: #dc2626; }
    .card.good .value { color: #16a34a; }
    .card.warning .value { color: #d97706; }
    .section { margin-bottom: 32px; }
    .section h2 { font-size: 16px; font-weight: 600; color: #1e40af; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; margin-bottom: 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { background: #2563eb; color: #fff; padding: 9px 10px; text-align: left; font-weight: 600; }
    td { padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
    tr:nth-child(even) td { background: #f9fafb; }
    .wqi-badge { padding: 2px 8px; border-radius: 12px; font-weight: 600; font-size: 12px; }
    .wqi-good { background: #dcfce7; color: #15803d; }
    .wqi-fair { background: #fef9c3; color: #854d0e; }
    .wqi-poor { background: #fee2e2; color: #b91c1c; }
    .severity-critical { color: #dc2626; font-weight: 700; }
    .severity-warning { color: #d97706; font-weight: 600; }
    .severity-info { color: #2563eb; }
    .insights { background: #eef2ff; padding: 14px 18px; border-radius: 10px; }
    .insights p { margin: 4px 0; font-size: 13px; color: #1e40af; }
    .footer { margin-top: 40px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 16px; }
    .print-btn { background: #2563eb; color: #fff; border: none; padding: 10px 22px; border-radius: 6px; cursor: pointer; font-size: 14px; margin-bottom: 20px; }
    .no-data { color: #9ca3af; font-style: italic; font-size: 13px; padding: 12px 0; }
  </style>
</head>
<body>
  <div class="no-print" style="text-align:center">
    <button class="print-btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
  </div>
  <div class="header">
    <div>
      <h1>💧 AquaChain Water Quality Report</h1>
      <p>Water Quality Monitoring System</p>
      <p>Device: <strong>${deviceName}</strong> &nbsp;|&nbsp; Location: ${deviceLocation}</p>
    </div>
    <div style="text-align:right">
      <p><strong>Generated:</strong> ${exportDate}</p>
      <p><strong>Period:</strong> ${dateRange}</p>
      <p><strong>Role:</strong> ${userRole.charAt(0).toUpperCase() + userRole.slice(1)}</p>
    </div>
  </div>

  <div class="cards">
    <div class="card ${summary.avgWqi !== null && summary.avgWqi >= 70 ? 'good' : summary.avgWqi !== null && summary.avgWqi >= 50 ? '' : 'critical'}">
      <div class="label">Avg WQI</div>
      <div class="value">${summary.avgWqi ?? 'N/A'}</div>
    </div>
    <div class="card critical">
      <div class="label">Min WQI</div>
      <div class="value">${summary.minWqi ?? 'N/A'}</div>
    </div>
    <div class="card good">
      <div class="label">Max WQI</div>
      <div class="value">${summary.maxWqi ?? 'N/A'}</div>
    </div>
    <div class="card warning">
      <div class="label">Total Alerts</div>
      <div class="value">${summary.totalAlerts}</div>
    </div>
    <div class="card critical">
      <div class="label">Critical</div>
      <div class="value">${summary.criticalAlerts}</div>
    </div>
  </div>

  ${includeReadings ? `
  <div class="section">
    <h2>📊 Water Quality Data (${readingsCount} readings)</h2>
    ${readingsCount > 0 ? `
    <table>
      <thead><tr><th>Timestamp</th><th>pH</th><th>Turbidity (NTU)</th><th>TDS (ppm)</th><th>Temp (°C)</th><th>WQI</th><th>Status</th></tr></thead>
      <tbody>${readingsRows}</tbody>
    </table>` : '<p class="no-data">No readings available for the selected period.</p>'}
  </div>` : ''}

  ${includeAlerts ? `
  <div class="section">
    <h2>🚨 Alerts (${alertsCount})</h2>
    ${alertsCount > 0 ? `
    <table>
      <thead><tr><th>Timestamp</th><th>Type</th><th>Severity</th><th>Message</th><th>Status</th></tr></thead>
      <tbody>${alertRows}</tbody>
    </table>` : '<p class="no-data">No alerts for the selected period.</p>'}
  </div>` : ''}

  <div class="section">
    <h2>🧠 Insights</h2>
    <div class="insights">${insightItems}</div>
  </div>

  <div class="section">
    <h2>📍 Device Info</h2>
    <table>
      <tbody>
        <tr><td><strong>Device ID</strong></td><td>${deviceId}</td></tr>
        <tr><td><strong>Location</strong></td><td>${deviceLocation}</td></tr>
        <tr><td><strong>Report Period</strong></td><td>${dateRange}</td></tr>
        <tr><td><strong>Generated</strong></td><td>${exportDate}</td></tr>
      </tbody>
    </table>
  </div>

  <div class="footer">
    <p>AquaChain — Advanced Water Quality Monitoring System</p>
    <p>This report was generated automatically. For questions, contact your system administrator.</p>
  </div>
</body>
</html>`;

  const handleExport = async () => {
    if (selectedDataTypes.length === 0) {
      alert('Please select at least one data type to export.');
      return;
    }
    setIsExporting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));

      if (selectedFormat === 'pdf') {
        const html = generateHTMLReport();
        const win = window.open('', '_blank');
        if (win) {
          win.document.write(html);
          win.document.close();
          setTimeout(() => win.print(), 600);
        }
        setIsExporting(false);
        onClose();
        return;
      }

      let content: string;
      let mimeType: string;
      let ext: string;

      if (selectedFormat === 'csv') {
        content = generateCSV();
        mimeType = 'text/csv;charset=utf-8;';
        ext = 'csv';
      } else {
        const filteredReadings = getFilteredReadings();
        const filteredAlerts = getFilteredAlerts();
        const summary = computeSummary(filteredReadings, filteredAlerts);
        const exportPayload = {
          exportedAt: new Date().toISOString(),
          dateRange: getDateRangeLabel(),
          userRole,
          device: deviceInfo || null,
          summary,
          readings: selectedDataTypes.includes('water-quality') ? filteredReadings : [],
          alerts: selectedDataTypes.includes('alerts') ? filteredAlerts : [],
        };
        content = JSON.stringify(exportPayload, null, 2);
        mimeType = 'application/json';
        ext = 'json';
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `aquachain-export-${userRole}-${Date.now()}.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setIsExporting(false);
      onClose();
    } catch (err) {
      console.error('Export failed:', err);
      alert('Export failed. Please try again.');
      setIsExporting(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50" onClick={onClose} />
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
                  <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 transition-colors duration-200">
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-6">
                {/* Format */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Export Format</h3>
                  <div className="grid grid-cols-3 gap-3">
                    {(['csv', 'pdf', 'json'] as const).map(fmt => (
                      <button
                        key={fmt}
                        onClick={() => setSelectedFormat(fmt)}
                        className={`p-4 border rounded-lg transition-colors duration-200 ${selectedFormat === fmt ? 'border-blue-500 bg-blue-50 text-blue-900' : 'border-gray-200 hover:bg-gray-50'}`}
                      >
                        {fmt === 'csv' && <TableCellsIcon className="w-6 h-6 mx-auto mb-2" />}
                        {fmt === 'pdf' && <DocumentTextIcon className="w-6 h-6 mx-auto mb-2" />}
                        {fmt === 'json' && <ChartBarIcon className="w-6 h-6 mx-auto mb-2" />}
                        <div className="text-sm font-medium">{fmt.toUpperCase()}</div>
                        <div className="text-xs text-gray-600">
                          {fmt === 'csv' ? 'Spreadsheet format' : fmt === 'pdf' ? 'Report format' : 'Data format'}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Date Range */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Date Range</h3>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {(['7d', '30d', '90d', 'custom'] as const).map(range => (
                      <button
                        key={range}
                        onClick={() => setSelectedDateRange(range)}
                        className={`p-3 border rounded-lg text-sm transition-colors duration-200 ${selectedDateRange === range ? 'border-blue-500 bg-blue-50 text-blue-900' : 'border-gray-200 hover:bg-gray-50'}`}
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
                        <input type="date" value={customStartDate} onChange={e => setCustomStartDate(e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                        <input type="date" value={customEndDate} onChange={e => setCustomEndDate(e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                      </div>
                    </div>
                  )}
                </div>

                {/* Data Types */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Data to Export</h3>
                  <div className="space-y-2">
                    {availableDataTypes.map(dt => (
                      <label key={dt.id} className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input type="checkbox" checked={selectedDataTypes.includes(dt.id)} onChange={() => handleDataTypeToggle(dt.id)}
                          className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded" />
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{dt.label}</div>
                          <div className="text-sm text-gray-600">{dt.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                {selectedDataTypes.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Export Summary</h4>
                    <div className="text-sm text-blue-800 space-y-1">
                      <div>Format: {selectedFormat.toUpperCase()}</div>
                      <div>Date Range: {getDateRangeLabel()}</div>
                      <div>Data Types: {selectedDataTypes.length} selected</div>
                      {readings.length > 0 && <div>Available readings: {getFilteredReadings().length}</div>}
                      {alerts.length > 0 && <div>Available alerts: {getFilteredAlerts().length}</div>}
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
                    <button onClick={onClose} className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors duration-200">
                      Cancel
                    </button>
                    <button
                      onClick={handleExport}
                      disabled={selectedDataTypes.length === 0 || isExporting}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center gap-2"
                    >
                      {isExporting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
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
