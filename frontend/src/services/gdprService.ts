/**
 * GDPR Service
 * Handles data export, deletion, and consent management API calls
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

interface ExportRequest {
  request_id: string;
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  download_url?: string;
  error_message?: string;
}

interface ExportResponse {
  request_id: string;
  status: string;
  message: string;
  download_url?: string;
  expires_in_days?: number;
}

interface ExportListResponse {
  exports: ExportRequest[];
  count: number;
}

interface DeletionRequest {
  request_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  scheduled_deletion_date?: string;
  days_remaining?: number;
  completed_at?: string;
  cancelled_at?: string;
  deletion_summary?: any;
  error_message?: string;
}

interface DeletionResponse {
  request_id: string;
  status: string;
  message: string;
  scheduled_deletion_date?: string;
  days_until_deletion?: number;
  cancellation_info?: string;
  deletion_summary?: any;
}

interface DeletionListResponse {
  deletions: DeletionRequest[];
  count: number;
}

class GDPRService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : ''
    };
  }

  /**
   * Request a data export for the current user
   */
  async requestDataExport(userId: string, email: string): Promise<ExportResponse> {
    const response = await fetch(`${API_BASE_URL}/gdpr/export`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        user_id: userId,
        email: email
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to request data export');
    }

    return response.json();
  }

  /**
   * Get the status of a specific export request
   */
  async getExportStatus(requestId: string): Promise<ExportRequest> {
    const response = await fetch(`${API_BASE_URL}/gdpr/export/${requestId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to get export status');
    }

    return response.json();
  }

  /**
   * List all export requests for the current user
   */
  async listUserExports(): Promise<ExportListResponse> {
    const response = await fetch(`${API_BASE_URL}/gdpr/exports`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to list exports');
    }

    return response.json();
  }

  /**
   * Request account deletion
   */
  async requestDataDeletion(userId: string, email: string, immediate: boolean = false): Promise<DeletionResponse> {
    const response = await fetch(`${API_BASE_URL}/gdpr/delete`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        user_id: userId,
        email: email,
        immediate: immediate
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to request data deletion');
    }

    return response.json();
  }

  /**
   * Get the status of a specific deletion request
   */
  async getDeletionStatus(requestId: string): Promise<DeletionRequest> {
    const response = await fetch(`${API_BASE_URL}/gdpr/delete/${requestId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to get deletion status');
    }

    return response.json();
  }

  /**
   * List all deletion requests for the current user
   */
  async listUserDeletions(): Promise<DeletionListResponse> {
    const response = await fetch(`${API_BASE_URL}/gdpr/deletions`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to list deletions');
    }

    return response.json();
  }

  /**
   * Cancel a pending deletion request
   */
  async cancelDeletionRequest(requestId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/delete/${requestId}/cancel`, {
      method: 'POST',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to cancel deletion request');
    }

    return response.json();
  }

  /**
   * Get all user consents
   */
  async getUserConsents(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/consents`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to get user consents');
    }

    return response.json();
  }

  /**
   * Update a single user consent
   */
  async updateConsent(
    consentType: string,
    granted: boolean
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/consents`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        consent_type: consentType,
        granted: granted
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update consent');
    }

    return response.json();
  }

  /**
   * Bulk update multiple consents
   */
  async bulkUpdateConsents(consents: Record<string, boolean>): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/consents/bulk`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        consents: consents
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to update consents');
    }

    return response.json();
  }

  /**
   * Check a specific consent
   */
  async checkConsent(consentType: string): Promise<boolean> {
    const response = await fetch(
      `${API_BASE_URL}/gdpr/consents/check?consent_type=${consentType}`,
      {
        headers: this.getAuthHeaders()
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to check consent');
    }

    const data = await response.json();
    return data.granted;
  }

  /**
   * Get consent history
   */
  async getConsentHistory(consentType?: string): Promise<any> {
    const url = consentType
      ? `${API_BASE_URL}/gdpr/consents/history?consent_type=${consentType}`
      : `${API_BASE_URL}/gdpr/consents/history`;

    const response = await fetch(url, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to get consent history');
    }

    return response.json();
  }
}

export const gdprService = new GDPRService();
export default gdprService;
