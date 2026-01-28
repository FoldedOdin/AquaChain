/**
 * API Client
 * Centralized HTTP client for making API requests with authentication
 */

export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
  }

  /**
   * Get authentication token from localStorage
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('aquachain_token');
  }

  /**
   * Get authorization headers
   */
  private getAuthHeaders(): HeadersInit {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response, expectBlob: boolean = false): Promise<ApiResponse<T>> {
    if (!response.ok) {
      // For error responses, try to get JSON error message first
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData?.error || errorData?.message || errorMessage;
      } catch {
        // If JSON parsing fails, use statusText
      }

      const error: ApiError = {
        message: errorMessage,
        status: response.status,
        code: response.status.toString()
      };
      throw error;
    }

    let data: T;

    if (expectBlob) {
      data = (await response.blob()) as unknown as T;
    } else {
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else if (contentType && contentType.includes('text/')) {
        data = (await response.text()) as unknown as T;
      } else {
        data = (await response.blob()) as unknown as T;
      }
    }

    return {
      data,
      status: response.status,
      statusText: response.statusText
    };
  }

  /**
   * Make GET request
   */
  async get<T = any>(url: string, options?: RequestInit & { expectBlob?: boolean }): Promise<ApiResponse<T>> {
    const { expectBlob, ...fetchOptions } = options || {};
    
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'GET',
      headers: this.getAuthHeaders(),
      ...fetchOptions
    });

    return this.handleResponse<T>(response, expectBlob);
  }

  /**
   * Make POST request
   */
  async post<T = any>(url: string, data?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make PUT request
   */
  async put<T = any>(url: string, data?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make PATCH request
   */
  async patch<T = any>(url: string, data?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'PATCH',
      headers: this.getAuthHeaders(),
      body: data ? JSON.stringify(data) : undefined,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make DELETE request
   */
  async delete<T = any>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(),
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Upload file
   */
  async upload<T = any>(url: string, file: File, options?: RequestInit): Promise<ApiResponse<T>> {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getAuthToken();
    const headers: HeadersInit = {
      ...(token && { 'Authorization': `Bearer ${token}` })
    };

    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'POST',
      headers,
      body: formData,
      ...options
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Download file
   */
  async download(url: string, filename?: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}${url}`, {
      method: 'GET',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(downloadUrl);
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;