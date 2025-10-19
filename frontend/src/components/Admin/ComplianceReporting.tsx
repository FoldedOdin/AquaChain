import { useState } from 'react';
import { ComplianceReport } from '../../types/admin';
import { generateComplianceReport } from '../../services/adminService';

const ComplianceReporting = () => {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 30);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });

  const handleGenerateReport = async () => {
    setLoading(true);
    try {
      const newReport = await generateComplianceReport(startDate, endDate);
      setReport(newReport);
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Failed to generate compliance report');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = () => {
    if (!report) return;
    
    // In a real implementation, this would generate and download a PDF
    alert('PDF export functionality would be implemented here');
    console.log('Exporting report:', report);
  };

  const handleExportCSV = () => {
    if (!report) return;
    
    // In a real implementation, this would generate and download a CSV
    alert('CSV export functionality would be implemented here');
    console.log('Exporting report:', report);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-6">Compliance Reporting</h2>

      {/* Report Generation Controls */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Generate Compliance Report</h3>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm text-gray-600 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm text-gray-600 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleGenerateReport}
              disabled={loading}
              className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Generating...' : 'Generate Report'}
            </button>
          </div>
        </div>
      </div>

      {/* Report Display */}
      {report && (
        <div className="space-y-6">
          {/* Report Header */}
          <div className="border-b pb-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="text-lg font-semibold">Compliance Report</h3>
                <p className="text-sm text-gray-600">Report ID: {report.reportId}</p>
                <p className="text-sm text-gray-600">
                  Period: {new Date(report.period.startDate).toLocaleDateString()} - {new Date(report.period.endDate).toLocaleDateString()}
                </p>
                <p className="text-sm text-gray-600">
                  Generated: {new Date(report.generatedAt).toLocaleString()}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleExportPDF}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm"
                >
                  Export PDF
                </button>
                <button
                  onClick={handleExportCSV}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                >
                  Export CSV
                </button>
              </div>
            </div>
          </div>

          {/* Summary Section */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Summary</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Total Readings</div>
                <div className="text-2xl font-bold text-blue-600">
                  {report.summary.totalReadings.toLocaleString()}
                </div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Devices Monitored</div>
                <div className="text-2xl font-bold text-green-600">
                  {report.summary.devicesMonitored}
                </div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Alerts Generated</div>
                <div className="text-2xl font-bold text-yellow-600">
                  {report.summary.alertsGenerated}
                </div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Compliance Rate</div>
                <div className={`text-2xl font-bold ${
                  report.summary.complianceRate >= 99.5 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {report.summary.complianceRate.toFixed(2)}%
                </div>
              </div>
            </div>
          </div>

          {/* Ledger Verification Section */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Ledger Verification</h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Total Ledger Entries</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {report.ledgerVerification.totalEntries.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Verified Entries</div>
                  <div className="text-lg font-semibold text-green-600">
                    {report.ledgerVerification.verifiedEntries.toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Hash Chain Status</div>
                  <div className="flex items-center">
                    {report.ledgerVerification.hashChainIntact ? (
                      <>
                        <span className="text-green-600 text-xl mr-2">✓</span>
                        <span className="text-lg font-semibold text-green-600">Intact</span>
                      </>
                    ) : (
                      <>
                        <span className="text-red-600 text-xl mr-2">✗</span>
                        <span className="text-lg font-semibold text-red-600">Compromised</span>
                      </>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Last Verification</div>
                  <div className="text-lg font-semibold text-gray-900">
                    {new Date(report.ledgerVerification.lastVerificationDate).toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Data Integrity Section */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">Data Integrity</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Missing Readings</div>
                <div className={`text-2xl font-bold ${
                  report.dataIntegrity.missingReadings === 0 ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {report.dataIntegrity.missingReadings}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {((report.dataIntegrity.missingReadings / report.summary.totalReadings) * 100).toFixed(3)}%
                </div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Duplicate Readings</div>
                <div className={`text-2xl font-bold ${
                  report.dataIntegrity.duplicateReadings === 0 ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {report.dataIntegrity.duplicateReadings}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {((report.dataIntegrity.duplicateReadings / report.summary.totalReadings) * 100).toFixed(3)}%
                </div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Invalid Readings</div>
                <div className={`text-2xl font-bold ${
                  report.dataIntegrity.invalidReadings === 0 ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {report.dataIntegrity.invalidReadings}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {((report.dataIntegrity.invalidReadings / report.summary.totalReadings) * 100).toFixed(3)}%
                </div>
              </div>
            </div>
          </div>

          {/* Uptime Metrics Section */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3">System Uptime Metrics</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Critical Path Uptime</div>
                <div className={`text-2xl font-bold ${
                  report.uptimeMetrics.criticalPathUptime >= 99.5 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {report.uptimeMetrics.criticalPathUptime.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">Target: 99.5%</div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">API Uptime</div>
                <div className={`text-2xl font-bold ${
                  report.uptimeMetrics.apiUptime >= 99.0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {report.uptimeMetrics.apiUptime.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">Target: 99.0%</div>
              </div>
              <div className="border rounded-lg p-4">
                <div className="text-sm text-gray-600 mb-1">Notification Uptime</div>
                <div className={`text-2xl font-bold ${
                  report.uptimeMetrics.notificationUptime >= 98.0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {report.uptimeMetrics.notificationUptime.toFixed(2)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">Target: 98.0%</div>
              </div>
            </div>
          </div>

          {/* Compliance Status */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                {report.summary.complianceRate >= 99.5 ? (
                  <span className="text-green-600 text-2xl">✓</span>
                ) : (
                  <span className="text-yellow-600 text-2xl">⚠</span>
                )}
              </div>
              <div className="ml-3">
                <h5 className="text-sm font-semibold text-gray-900">Compliance Status</h5>
                <p className="text-sm text-gray-700 mt-1">
                  {report.summary.complianceRate >= 99.5
                    ? 'System is operating within compliance requirements. All metrics meet or exceed targets.'
                    : 'System compliance is below target. Review data integrity and uptime metrics for areas of improvement.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {!report && !loading && (
        <div className="text-center py-12 text-gray-500">
          <p>Select a date range and click "Generate Report" to create a compliance report</p>
        </div>
      )}
    </div>
  );
};

export default ComplianceReporting;
