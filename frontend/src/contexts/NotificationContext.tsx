/**
 * Notification Context
 * Provides global notification system for the application
 */

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'info' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  duration?: number; // Auto-dismiss after duration (ms), 0 = no auto-dismiss
}

interface NotificationContextType {
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const id = `notification-${Date.now()}-${Math.random()}`;
    const newNotification: Notification = {
      ...notification,
      id,
      timestamp: new Date(),
      duration: notification.duration ?? 5000 // Default 5 seconds
    };

    setNotifications(prev => [newNotification, ...prev]);

    // Auto-dismiss if duration is set
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        addNotification,
        removeNotification,
        clearAll
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};
// Convenience hook for simple notifications
export const useNotification = () => {
  const { addNotification } = useNotifications();

  const showNotification = useCallback((message: string, type: 'success' | 'warning' | 'info' | 'error' = 'info', title?: string) => {
    addNotification({
      type,
      title: title || type.charAt(0).toUpperCase() + type.slice(1),
      message,
      duration: type === 'error' ? 8000 : 5000
    });
  }, [addNotification]);

  return { showNotification };
};