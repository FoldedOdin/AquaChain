/**
 * Compliance Service
 * 
 * Handles API calls for compliance reporting and monitoring
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

export interface ComplianceReport {
  report_date: string;
  period: string;
  report_type: string;
  compliance_status: string;
  violations: ComplianceViolation[];
  sections: {
    data_access: DataAccessReport;
    data_retention: DataRetentionReport;
    security_controls: SecurityControlsReport;
    gdpr_requests: GDPRRequestsReport;
    audit_summary: AuditSummaryReport;
  };
}

export interface ComplianceViolation {
  rule_id: string;
  rule_name: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
  details: any;
  detected_at: string;
}

export interface DataAccessReport {
  total_accesses: number;
  unique_users: number;
  access_by_user: Record<string, number>;
  access_by_resource: Record<string, number>;
  access_by_day: Record<string, number>;
  period_start: string;
  period_end: string;
}

export interface DataRetentionReport {
  audit_logs: {
    retention_period_years: number;
    logs_exceeding_retention: number;
    retention_compliant: boolean;
  };
  inactive_devices: {
    threshold_days: number;
    count: number;
    recommendation: string;
  };
  data_lifecycle_policies: Record<string, string>;
}

export interface SecurityControlsReport {
  authentication: {
    total_auth_events: number;
    failed_login_attempts: number;
    mfa_enabled: boolean;
    password_policy_enforced: boolean;
  };
  encryption: {
    data_at_rest: string;
    data_in_transit: string;
    kms_keys: Record<string, string>;
  };
  access_controls: Record<string, string>;
  monitoring: Record<string, string>;
}

export interface GDPRRequestsReport {
  total_requests: number;
  requests_by_type: Record<string, number>;
  requests_by_status: Record<string, number>;
  avg_completion_time_hours: Record<string, number>;
  sla_compliance: Record<string, {
    sla_hours: number;
    avg_completion_hours: number;
    compliant: boolean;
  }>;
  period_start: string;
  period_end: string;
}

export interface AuditSummaryReport {
  total_audit_logs: number;
  logs_by_action_type: Record<string, number>;
  audit_log_retention: string;
  audit_log_immutability: string;
  period_start: string;
  period_end: string;
}

class ComplianceService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  /**
   * Get recent compliance reports
   */
  async getRecentReports(limit: number = 12): Promise<ComplianceReport[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/compliance/reports?limit=${limit}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to fetch compliance reports');
      }

      const data = await response.json();
      return data.reports || [];
    } catch (error) {
      console.error('Error fetching compliance reports:', error);
      throw error;
    }
  }

  /**
   * Get a specific compliance report by period
   */
  async getReportByPeriod(year: number, month: number): Promise<ComplianceReport> {
    try {
      const response = await fetch(`${API_BASE_URL}/compliance/reports/${year}/${month}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to fetch compliance report');
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching compliance report:', error);
      throw error;
    }
  }

  /**
   * Trigger manual compliance report generation
   */
  async generateReport(year?: number, month?: number): Promise<{ message: string; report_location: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/compliance/reports/generate`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ year, month })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to generate compliance report');
      }

      return response.json();
    } catch (error) {
      console.error('Error generating compliance report:', error);
      throw error;
    }
  }

  /**
   * Get compliance violations for a specific period
   */
  async getViolations(year: number, month: number): Promise<ComplianceViolation[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/compliance/violations/${year}/${month}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to fetch compliance violations');
      }

      const data = await response.json();
      return data.violations || [];
    } catch (error) {
      console.error('Error fetching compliance violations:', error);
      throw error;
    }
  }

  /**
   * Get compliance metrics summary
   */
  async getMetricsSummary(): Promise<{
    total_reports: number;
    compliant_reports: number;
    total_violations: number;
    violations_by_severity: Record<string, number>;
  }> {
    try {
      const response = await fetch(`${API_BASE_URL}/compliance/metrics/summary`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to fetch compliance metrics');
      }

      return response.json();
    } catch (error) {
      console.error('Error fetching compliance metrics:', error);
      throw error;
    }
  }

  /**
   * Download compliance report as JSON
   */
  async downloadReport(year: number, month: number): Promise<Blob> {
    try {
      const response = await fetch(`${API_BASE_URL}/compliance/reports/${year}/${month}/download`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to download compliance report');
      }

      return response.blob();
    } catch (error) {
      console.error('Error downloading compliance report:', error);
      throw error;
    }
  }
}

export const complianceService = new ComplianceService();
