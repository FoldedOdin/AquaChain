/**
 * Notification Service
 * Handles fetching and managing user notifications
 */

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'info' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  priority: 'low' | 'medium' | 'high';
  userId?: string;
  deviceId?: string;
  actionUrl?: string;
}

class NotificationService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
  }

  /**
   * Get authentication token
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
   * Fetch notifications for current user
   */
  async getNotifications(): Promise<Notification[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/notifications`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      // If endpoint doesn't exist (404) or service unavailable, return empty array
      if (response.status === 404 || response.status === 503 || response.status === 500) {
        console.warn('Notification service not available (status:', response.status, ')');
        return [];
      }

      const result = await response.json();

      if (!response.ok) {
        console.warn('Notification service error:', result.error || 'Unknown error');
        return [];
      }

      return result.notifications || [];
    } catch (error: any) {
      // Network errors or CORS issues - fail silently
      console.warn('Notification service unavailable:', error.message);
      return [];
    }
  }

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to mark notification as read');
      }
    } catch (error: any) {
      console.error('Mark as read error:', error);
      throw error;
    }
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/notifications/read-all`, {
        method: 'PUT',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to mark all as read');
      }
    } catch (error: any) {
      console.error('Mark all as read error:', error);
      throw error;
    }
  }

  /**
   * Delete notification
   */
  async deleteNotification(notificationId: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/api/notifications/${notificationId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to delete notification');
      }
    } catch (error: any) {
      console.error('Delete notification error:', error);
      throw error;
    }
  }

  /**
   * Create notification (admin/system use)
   */
  async createNotification(notification: Omit<Notification, 'id' | 'timestamp'>): Promise<Notification> {
    try {
      const response = await fetch(`${this.baseUrl}/api/notifications`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(notification)
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to create notification');
      }

      return result.notification;
    } catch (error: any) {
      console.error('Create notification error:', error);
      throw error;
    }
  }

  /**
   * Get unread count
   */
  async getUnreadCount(): Promise<number> {
    try {
      const response = await fetch(`${this.baseUrl}/api/notifications/unread-count`, {
        method: 'GET',
        headers: this.getAuthHeaders()
      });

      // If endpoint doesn't exist or has errors, return 0
      if (response.status === 404 || response.status === 503 || response.status === 500) {
        return 0;
      }

      const result = await response.json();

      if (!response.ok) {
        return 0;
      }

      return result.count || 0;
    } catch (error: any) {
      // Fail silently for any errors
      return 0;
    }
  }
}

// Export singleton instance
export const notificationService = new NotificationService();
export default notificationService;
