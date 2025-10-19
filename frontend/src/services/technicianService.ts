import { TechnicianTask, MaintenanceReport, TaskNote, TaskAttachment } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'https://api.aquachain.example.com';

class TechnicianService {
  private async getAuthToken(): Promise<string> {
    // This would get the token from the auth context
    return 'mock-token';
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
    // Mock data for development
    return [
      {
        taskId: 'TASK-001',
        serviceRequestId: 'SR-001',
        deviceId: 'DEV-3421',
        consumerId: 'user-456',
        priority: 'high',
        status: 'assigned',
        location: {
          latitude: 37.7749,
          longitude: -122.4194,
          address: '123 Main St, San Francisco, CA 94102'
        },
        estimatedArrival: '2025-10-19T16:30:00Z',
        description: 'pH sensor showing erratic readings, possible calibration issue',
        deviceInfo: {
          model: 'AquaChain Pro v2.1',
          serialNumber: 'AC-2024-3421',
          lastReading: {
            deviceId: 'DEV-3421',
            timestamp: '2025-10-19T14:23:45.123Z',
            location: { latitude: 37.7749, longitude: -122.4194 },
            readings: { pH: 4.2, turbidity: 1.5, tds: 145, temperature: 24.5, humidity: 68.2 },
            wqi: 35,
            anomalyType: 'sensor_fault',
            diagnostics: { batteryLevel: 85, signalStrength: -65, sensorStatus: 'error' }
          }
        },
        customerInfo: {
          name: 'Jane Smith',
          phone: '+1-555-0123',
          email: 'jane.smith@email.com'
        },
        assignedAt: '2025-10-19T14:30:00Z',
        dueDate: '2025-10-19T18:00:00Z',
        notes: [
          {
            id: 'note-1',
            timestamp: '2025-10-19T14:30:00Z',
            author: 'System',
            type: 'status_update',
            content: 'Task assigned to technician',
            attachments: []
          }
        ]
      },
      {
        taskId: 'TASK-002',
        serviceRequestId: 'SR-002',
        deviceId: 'DEV-3422',
        consumerId: 'user-789',
        priority: 'medium',
        status: 'accepted',
        location: {
          latitude: 37.7849,
          longitude: -122.4094,
          address: '456 Oak Ave, San Francisco, CA 94103'
        },
        estimatedArrival: '2025-10-19T17:15:00Z',
        description: 'Routine maintenance and calibration check',
        deviceInfo: {
          model: 'AquaChain Standard v1.8',
          serialNumber: 'AC-2023-3422'
        },
        customerInfo: {
          name: 'Bob Johnson',
          phone: '+1-555-0456',
          email: 'bob.johnson@email.com'
        },
        assignedAt: '2025-10-19T13:00:00Z',
        dueDate: '2025-10-19T19:00:00Z',
        notes: [
          {
            id: 'note-2',
            timestamp: '2025-10-19T13:00:00Z',
            author: 'System',
            type: 'status_update',
            content: 'Task assigned to technician',
            attachments: []
          },
          {
            id: 'note-3',
            timestamp: '2025-10-19T15:30:00Z',
            author: 'Tech-001',
            type: 'technician_note',
            content: 'Accepted task, heading to location',
            attachments: []
          }
        ]
      }
    ];
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