import { TechnicianTask, MaintenanceReport, TaskNote, TaskAttachment } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'https://api.aquachain.example.com';

class TechnicianService {
  private async getAuthToken(): Promise<string> {
    // Get token from localStorage (set by AuthContext)
    const token = localStorage.getItem('authToken');
    if (!token) {
      throw new Error('No authentication token found');
    }
    return token;
  }

  private async apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = await this.getAuthToken();
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }

    return response.json();
  }

  async getAssignedTasks(): Promise<TechnicianTask[]> {
    try {
      const response = await this.apiCall<{ tasks: TechnicianTask[], recentActivities: any[] }>('/api/v1/technician/tasks');
      return response.tasks || [];
    } catch (error) {
      console.error('Error fetching assigned tasks:', error);
      // Return empty array on error instead of throwing
      return [];
    }
  }

  async acceptTask(taskId: string): Promise<void> {
    await this.apiCall(`/api/v1/technician/tasks/${taskId}/accept`, {
      method: 'POST'
    });
  }

  async updateTaskStatus(taskId: string, status: TechnicianTask['status'], note?: string): Promise<void> {
    await this.apiCall(`/api/v1/technician/tasks/${taskId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, note })
    });
  }

  async addTaskNote(taskId: string, note: Omit<TaskNote, 'id' | 'timestamp'>): Promise<void> {
    await this.apiCall(`/api/v1/technician/tasks/${taskId}/notes`, {
      method: 'POST',
      body: JSON.stringify(note)
    });
  }

  async uploadTaskAttachment(taskId: string, file: File, type: TaskAttachment['type']): Promise<TaskAttachment> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('type', type);

    const token = await this.getAuthToken();
    const response = await fetch(`${API_BASE_URL}/api/v1/technician/tasks/${taskId}/attachments`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error('Failed to upload attachment');
    }

    return response.json();
  }

  async completeTask(taskId: string, report: Omit<MaintenanceReport, 'reportId' | 'completedAt'>): Promise<void> {
    await this.apiCall(`/api/v1/technician/tasks/${taskId}/complete`, {
      method: 'POST',
      body: JSON.stringify(report)
    });
  }

  async getTaskHistory(limit: number = 50): Promise<TechnicianTask[]> {
    return this.apiCall(`/api/v1/technician/tasks/history?limit=${limit}`);
  }

  async updateLocation(latitude: number, longitude: number): Promise<void> {
    await this.apiCall('/api/v1/technician/location', {
      method: 'PUT',
      body: JSON.stringify({ latitude, longitude })
    });
  }

  async getRouteToTask(taskId: string): Promise<any> {
    return this.apiCall(`/api/v1/technician/tasks/${taskId}/route`);
  }
}

export const technicianService = new TechnicianService();