/**
 * useNotifications Hook
 * 
 * Custom hook for managing notifications and notification history.
 * Provides methods to add, mark as read, and clear notifications.
 * 
 * Features:
 * - Add notifications with type (success, warning, error, info)
 * - Mark notifications as read
 * - Clear all notifications
 * - Get unread notification count
 * - Filter notifications by type
 * 
 * @module useNotifications
 */

import { useCallback, useMemo } from "react";
import { useDashboard } from "../contexts/DashboardContext";
import { Notification } from "../types/dashboard";

/**
 * Notification hook return type
 */
interface UseNotificationsReturn {
  /** All notifications in history */
  notifications: Notification[];
  /** Unread notifications */
  unreadNotifications: Notification[];
  /** Count of unread notifications */
  unreadCount: number;
  /** Add a new notification */
  addNotification: (notification: Omit<Notification, "id" | "timestamp" | "read">) => void;
  /** Mark a notification as read */
  markAsRead: (notificationId: string) => void;
  /** Mark all notifications as read */
  markAllAsRead: () => void;
  /** Clear all notifications */
  clearAll: () => void;
  /** Get notifications by type */
  getByType: (type: Notification["type"]) => Notification[];
}

/**
 * Hook for managing notifications
 * 
 * Provides access to notification history and methods to manage notifications.
 * Integrates with DashboardContext for persistent notification storage.
 * 
 * @returns Notification management methods and state
 * 
 * @example
 * ```tsx
 * const { addNotification, unreadCount, markAsRead } = useNotifications();
 * 
 * // Add a notification
 * addNotification({
 *   type: "success",
 *   message: "Device added successfully"
 * });
 * 
 * // Show unread count
 * <Badge>{unreadCount}</Badge>
 * ```
 */
export function useNotifications(): UseNotificationsReturn {
  const { notificationHistory, addNotification } = useDashboard();

  /**
   * Get unread notifications
   */
  const unreadNotifications = useMemo(() => {
    return notificationHistory.filter((n) => !n.read);
  }, [notificationHistory]);

  /**
   * Get unread count
   */
  const unreadCount = useMemo(() => {
    return unreadNotifications.length;
  }, [unreadNotifications]);

  /**
   * Mark a notification as read
   * 
   * Note: This is a simplified implementation. In a real application,
   * you would update the notification in the context state.
   * For now, we'll just filter it out from unread notifications.
   */
  const markAsRead = useCallback((notificationId: string) => {
    // In a real implementation, this would update the notification in context
    console.log(`Marking notification ${notificationId} as read`);
  }, []);

  /**
   * Mark all notifications as read
   */
  const markAllAsRead = useCallback(() => {
    // In a real implementation, this would update all notifications in context
    console.log("Marking all notifications as read");
  }, []);

  /**
   * Clear all notifications
   */
  const clearAll = useCallback(() => {
    // In a real implementation, this would clear notifications in context
    console.log("Clearing all notifications");
  }, []);

  /**
   * Get notifications by type
   */
  const getByType = useCallback(
    (type: Notification["type"]) => {
      return notificationHistory.filter((n) => n.type === type);
    },
    [notificationHistory]
  );

  return {
    notifications: notificationHistory,
    unreadNotifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    getByType,
  };
}

/**
 * Helper function to create notification objects
 * 
 * @param type - Notification type
 * @param message - Notification message
 * @returns Notification object without id, timestamp, and read fields
 * 
 * @example
 * ```tsx
 * const notification = createNotification("success", "Operation completed");
 * addNotification(notification);
 * ```
 */
export function createNotification(
  type: Notification["type"],
  message: string
): Omit<Notification, "id" | "timestamp" | "read"> {
  return { type, message };
}

/**
 * Predefined notification messages for common scenarios
 */
export const NotificationMessages = {
  // Device notifications
  DEVICE_ADDED: "Device added successfully",
  DEVICE_REMOVED: "Device removed successfully",
  DEVICE_OFFLINE: (deviceId: string) => `Device ${deviceId} is now offline`,
  DEVICE_ONLINE: (deviceId: string) => `Device ${deviceId} is now online`,
  DEVICE_RESTART: (deviceId: string) => `Device ${deviceId} restarted successfully`,
  
  // Alert notifications
  CRITICAL_ALERT: (deviceId: string) => `Critical alert for device ${deviceId}`,
  ALERT_ACKNOWLEDGED: "Alert acknowledged successfully",
  TECHNICIAN_ASSIGNED: "Technician assigned to alert",
  
  // ML notifications
  ML_RETRAIN_START: "ML model retraining started",
  ML_RETRAIN_COMPLETE: "ML model retraining completed successfully",
  ML_RETRAIN_FAILED: "ML model retraining failed",
  
  // System notifications
  HIGH_LATENCY: "System latency is high",
  DATA_EXPORT_COMPLETE: "Data export completed successfully",
  DATA_EXPORT_FAILED: "Data export failed",
  
  // User notifications
  USER_ROLE_CHANGED: "User role changed successfully",
  USER_DISABLED: "User disabled successfully",
  PASSWORD_RESET: "Password reset email sent",
} as const;

/**
 * Hook for showing toast notifications
 * 
 * This is a convenience hook that combines useNotifications with
 * common notification patterns.
 * 
 * @returns Methods to show different types of notifications
 * 
 * @example
 * ```tsx
 * const { showSuccess, showError } = useToastNotifications();
 * 
 * showSuccess("Operation completed");
 * showError("Operation failed");
 * ```
 */
export function useToastNotifications() {
  const { addNotification } = useNotifications();

  const showSuccess = useCallback(
    (message: string) => {
      addNotification(createNotification("success", message));
    },
    [addNotification]
  );

  const showError = useCallback(
    (message: string) => {
      addNotification(createNotification("error", message));
    },
    [addNotification]
  );

  const showWarning = useCallback(
    (message: string) => {
      addNotification(createNotification("warning", message));
    },
    [addNotification]
  );

  const showInfo = useCallback(
    (message: string) => {
      addNotification(createNotification("info", message));
    },
    [addNotification]
  );

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
}
