import React, { useState, useEffect } from 'react';
import { complianceService } from '../services/complianceService';

interface ComplianceReport {
  report_date: string;
  period: string;
  compliance_status: string;
  violations: Array<{
    rule_name: string;
    severity: string;
    description: string;
    details: any;
  }>;
  sections: {
    gdpr_requests: {
      total_requests: number;
      requests_by_type: Record<string, number>;
      sla_compliance: Record<string, any>;
    };
    audit_summary: {
      total_audit_logs: number;
      logs_by_action_type: Record<string, number>;
    };
    data_access: {
      total_accesses: number;
      unique_users: number;
    };
  };
}

const ComplianceDashboard: React.FC = () => {
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [selectedReport, setSelectedReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await complianceService.getRecentReports();
      setReports(data);
      if (data.length > 0) {
        setSelectedReport(data[0]);
      }
    } catch (err) {
      setError('Failed to load compliance reports');
      console.error('Error loading reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'CRITICAL':
        return 'text-red-700 bg-red-100';
      case 'HIGH':
        return 'text-orange-700 bg-orange-100';
      case 'MEDIUM':
        return 'text-yellow-700 bg-yellow-100';
      case 'LOW':
        return 'text-blue-700 bg-blue-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const getComplianceStatusColor = (status: string): string => {
    return status === 'COMPLIANT' 
      ? 'text-green-700 bg-green-100' 
      : 'text-red-700 bg-red-100';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading compliance reports...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-red-800 font-semibold mb-2">Error</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadReports}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Compliance Dashboard
          </h1>
          <p className="text-gray-600">
            Monitor compliance status, GDPR requests, and audit logs
          </p>
        </div>

        {/* Report Selector */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Report Period
          </label>
          <select
            value={selectedReport?.period || ''}
            onChange={(e) => {
              const report = reports.find(r => r.period === e.target.value);
              setSelectedReport(report || null);
            }}
            className="w-full md:w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {reports.map((report) => (
              <option key={report.period} value={report.period}>
                {report.period}
              </option>
            ))}
          </select>
        </div>

        {selectedReport && (
          <>
            {/* Compliance Status Card */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-2">
                    Compliance Status
                  </h2>
                  <p className="text-gray-600">
                    Report Period: {selectedReport.period}
                  </p>
                  <p className="text-sm text-gray-500">
                    Generated: {new Date(selectedReport.report_date).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span
                    className={`px-4 py-2 rounded-full font-semibold ${getComplianceStatusColor(
                      selectedReport.compliance_status
                    )}`}
                  >
                    {selectedReport.compliance_status}
                  </span>
                </div>
              </div>
            </div>

            {/* Violations */}
            {selectedReport.violations && selectedReport.violations.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Compliance Violations ({selectedReport.violations.length})
                </h2>
                <div className="space-y-4">
                  {selectedReport.violations.map((violation, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {violation.rule_name}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(
                            violation.severity
                          )}`}
                        >
                          {violation.severity}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-2">{violation.description}</p>
                      <details className="text-sm">
                        <summary className="cursor-pointer text-blue-600 hover:text-blue-700">
                          View Details
                        </summary>
                        <pre className="mt-2 p-3 bg-gray-50 rounded overflow-x-auto">
                          {JSON.stringify(violation.details, null, 2)}
                        </pre>
                      </details>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* GDPR Requests Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  GDPR Requests
                </h2>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Requests</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {selectedReport.sections.gdpr_requests.total_requests}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">By Type</p>
                    {Object.entries(
                      selectedReport.sections.gdpr_requests.requests_by_type
                    ).map(([type, count]) => (
                      <div key={type} className="flex justify-between py-1">
                        <span className="text-gray-700 capitalize">{type}</span>
                        <span className="font-semibold text-gray-900">{count}</span>
                      </div>
                    ))}
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">SLA Compliance</p>
                    {Object.entries(
                      selectedReport.sections.gdpr_requests.sla_compliance
                    ).map(([type, data]: [string, any]) => (
                      <div key={type} className="py-1">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-700 capitalize">{type}</span>
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              data.compliant
                                ? 'bg-green-100 text-green-700'
                                : 'bg-red-100 text-red-700'
                            }`}
                          >
                            {data.compliant ? 'Compliant' : 'Non-Compliant'}
                          </span>
                        </div>
                        {data.avg_completion_hours > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            Avg: {data.avg_completion_hours.toFixed(1)}h / SLA:{' '}
                            {data.sla_hours}h
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Audit Log Statistics */}
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Audit Log Statistics
                </h2>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Audit Logs</p>
                    <p className="text-3xl font-bold text-gray-900">
                      {selectedReport.sections.audit_summary.total_audit_logs.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-2">By Action Type</p>
                    {Object.entries(
                      selectedReport.sections.audit_summary.logs_by_action_type
                    ).map(([action, count]) => (
                      <div key={action} className="flex justify-between py-1">
                        <span className="text-gray-700">{action}</span>
                        <span className="font-semibold text-gray-900">
                          {count.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Data Access Metrics */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Data Access Metrics
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-gray-600">Total Data Accesses</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {selectedReport.sections.data_access.total_accesses.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Unique Users</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {selectedReport.sections.data_access.unique_users}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}

        {reports.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <p className="text-gray-600 mb-4">No compliance reports available</p>
            <p className="text-sm text-gray-500">
              Reports are generated automatically on the 1st of each month
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplianceDashboard;
