/**
 * Security Audit Service
 * API client for security audit log operations
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.aquachain.example.com';

export interface AuditLog {
  logId: string;
  timestamp: string;
  deviceId: string;
  wqi: number;
  anomalyType: 'normal' | 'contamination' | 'sensor_fault' | 'calibration_needed';
  verified: boolean;
  dataHash: string;
}

export interface AuditLogFilters {
  deviceId?: string;
  anomalyType?: string;
  verificationStatus?: string;
  search?: string;
  startDate?: string;
  endDate?: string;
  limit?: number;
  nextToken?: string;
}

export interface AuditLogsResponse {
  logs: AuditLog[];
  count: number;
  total: number;
  nextToken?: string;
}

export interface ExportRequest {
  format: 'csv' | 'json';
  filters?: {
    deviceId?: string;
    anomalyType?: string;
    startDate?: string;
    endDate?: string;
  };
}

export interface ExportResponse {
  exportId: string;
  downloadUrl: string;
  recordCount: number;
  expiresIn: number;
}

export interface IntegrityStatus {
  recentChecks: Array<{
    date: string;
    verified: boolean;
    recordCount: number;
  }>;
  lastVerified: string | null;
  status: 'healthy' | 'warning' | 'error';
}

export interface VerifyIntegrityRequest {
  startDate: string;
  endDate: string;
}

export interface VerifyIntegrityResponse {
  verified: boolean;
  recordCount: number;
  message: string;
}

class SecurityAuditService {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Get audit logs with optional filtering
   */
  async getAuditLogs(filters?: AuditLogFilters): Promise<AuditLogsResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters?.deviceId) params.append('deviceId', filters.deviceId);
      if (filters?.anomalyType) params.append('anomalyType', filters.anomalyType);
      if (filters?.verificationStatus) params.append('verificationStatus', filters.verificationStatus);
      if (filters?.search) params.append('search', filters.search);
      if (filters?.startDate) params.append('startDate', filters.startDate);
      if (filters?.endDate) params.append('endDate', filters.endDate);
      if (filters?.limit) params.append('limit', filters.limit.toString());
      if (filters?.nextToken) params.append('nextToken', filters.nextToken);

      const response = await axios.get(
        `${API_BASE_URL}/admin/security/audit?${params.toString()}`,
        { headers: this.getAuthHeaders() }
      );

      return response.data;
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      throw error;
    }
  }

  /**
   * Export audit logs to CSV or JSON
   */
  async exportAuditLogs(request: ExportRequest): Promise<ExportResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/admin/security/audit/export`,
        request,
        { headers: this.getAuthHeaders() }
      );

      return response.data;
    } catch (error) {
      console.error('Error exporting audit logs:', error);
      throw error;
    }
  }

  /**
   * Get integrity verification status
   */
  async getIntegrityStatus(): Promise<IntegrityStatus> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/admin/security/integrity`,
        { headers: this.getAuthHeaders() }
      );

      return response.data;
    } catch (error) {
      console.error('Error fetching integrity status:', error);
      throw error;
    }
  }

  /**
   * Verify hash chain integrity for a date range
   */
  async verifyIntegrity(request: VerifyIntegrityRequest): Promise<VerifyIntegrityResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/admin/security/integrity/verify`,
        request,
        { headers: this.getAuthHeaders() }
      );

      return response.data;
    } catch (error) {
      console.error('Error verifying integrity:', error);
      throw error;
    }
  }

  /**
   * Download exported file
   */
  downloadExport(downloadUrl: string, filename: string = 'audit-export.csv'): void {
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

export default new SecurityAuditService();
