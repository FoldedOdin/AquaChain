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
   * Request account deletion (to be implemented)
   */
  async requestDataDeletion(userId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/delete`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        user_id: userId
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to request data deletion');
    }

    return response.json();
  }

  /**
   * Get user consents (to be implemented)
   */
  async getUserConsents(userId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/consents/${userId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to get user consents');
    }

    return response.json();
  }

  /**
   * Update user consent (to be implemented)
   */
  async updateConsent(
    userId: string,
    consentType: string,
    granted: boolean
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/gdpr/consents`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        user_id: userId,
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
}

export const gdprService = new GDPRService();
export default gdprService;
