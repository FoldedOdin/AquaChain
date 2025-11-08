/**
 * useRealTimeUpdates Hook Tests
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import { useRealTimeUpdates } from '../useRealTimeUpdates';
import { websocketService } from '../../services/websocketService';
import React from 'react';

// Mock the websocket service
jest.mock('../../services/websocketService');

// Mock the NotificationContext
const mockAddNotification = jest.fn();
jest.mock('../../contexts/NotificationContext', () => ({
  useNotifications: () => ({
    addNotification: mockAddNotification
  })
}));

describe('useRealTimeUpdates Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('Connection Management', () => {
    it('connects automatically when autoConnect is true', () => {
      renderHook(() => useRealTimeUpdates('test-topic'));

      expect(websocketService.connect).toHaveBeenCalledWith(
        'test-topic',
        expect.any(Function)
      );
    });

    it('does not connect automatically when autoConnect is false', () => {
      renderHook(() => useRealTimeUpdates('test-topic', { autoConnect: false }));

      expect(websocketService.connect).not.toHaveBeenCalled();
    });

    it('provides connect function', () => {
      const { result } = renderHook(() => useRealTimeUpdates('test-topic', { autoConnect: false }));

      expect(result.current.connect).toBeDefined();
      expect(typeof result.current.connect).toBe('function');
    });

    it('connects when connect function is called', () => {
      const { result } = renderHook(() => useRealTimeUpdates('test-topic', { autoConnect: false }));

      act(() => {
        result.current.connect();
      });

      expect(websocketService.connect).toHaveBeenCalledWith(
        'test-topic',
        expect.any(Function)
      );
    });

    it('disconnects on unmount', () => {
      const { unmount } = renderHook(() => useRealTimeUpdates('test-topic'));

      unmount();

      expect(websocketService.disconnect).toHaveBeenCalled();
    });

    it('provides disconnect function', () => {
      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      expect(result.current.disconnect).toBeDefined();
      expect(typeof result.current.disconnect).toBe('function');
    });
  });

  describe('Update Handling', () => {
    it('initializes with empty updates array', () => {
      const { result } = renderHook(() => useRealTimeUpdates('test-topic', { autoConnect: false }));

      expect(result.current.updates).toEqual([]);
      expect(result.current.latestUpdate).toBeNull();
    });

    it('stores received updates', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      const mockUpdate = {
        type: 'sensor_reading',
        data: { temperature: 25 },
        timestamp: '2024-01-01T12:00:00Z'
      };

      act(() => {
        messageHandler?.(mockUpdate);
      });

      await waitFor(() => {
        expect(result.current.updates).toHaveLength(1);
      });

      expect(result.current.latestUpdate).toEqual(mockUpdate);
    });

    it('maintains last 100 updates', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      // Send 105 updates
      act(() => {
        for (let i = 0; i < 105; i++) {
          messageHandler?.({
            type: 'test',
            data: { value: i },
            timestamp: new Date().toISOString()
          });
        }
      });

      await waitFor(() => {
        expect(result.current.updates).toHaveLength(100);
      });
    });

    it('adds timestamp if not provided', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      act(() => {
        messageHandler?.({
          type: 'test',
          data: { value: 1 }
        });
      });

      await waitFor(() => {
        expect(result.current.latestUpdate?.timestamp).toBeDefined();
      });
    });

    it('provides clearUpdates function', () => {
      const { result } = renderHook(() => useRealTimeUpdates('test-topic', { autoConnect: false }));

      expect(result.current.clearUpdates).toBeDefined();
      expect(typeof result.current.clearUpdates).toBe('function');
    });

    it('clears updates when clearUpdates is called', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      act(() => {
        messageHandler?.({
          type: 'test',
          data: { value: 1 },
          timestamp: new Date().toISOString()
        });
      });

      await waitFor(() => {
        expect(result.current.updates).toHaveLength(1);
      });

      act(() => {
        result.current.clearUpdates();
      });

      expect(result.current.updates).toEqual([]);
      expect(result.current.latestUpdate).toBeNull();
    });
  });

  describe('Connection Status', () => {
    it('tracks connection status', async () => {
      (websocketService.getConnectionStatus as jest.Mock).mockReturnValue({
        isConnected: true,
        reconnectAttempts: 0,
        subscriberCount: 1,
        lastConnectedAt: new Date()
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(result.current.isConnected).toBe(true);
      });
    });

    it('tracks reconnection attempts', async () => {
      (websocketService.getConnectionStatus as jest.Mock).mockReturnValue({
        isConnected: false,
        reconnectAttempts: 3,
        subscriberCount: 1,
        lastConnectedAt: null
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      await waitFor(() => {
        expect(result.current.reconnectAttempts).toBe(3);
      });
    });

    it('polls connection status every second', () => {
      renderHook(() => useRealTimeUpdates('test-topic'));

      expect(websocketService.getConnectionStatus).toHaveBeenCalledTimes(0);

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(websocketService.getConnectionStatus).toHaveBeenCalledTimes(1);

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(websocketService.getConnectionStatus).toHaveBeenCalledTimes(2);
    });
  });

  describe('Error Handling', () => {
    it('handles connection errors', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      const errorUpdate = {
        type: 'connection_error',
        message: 'Connection failed',
        topic: 'test-topic'
      };

      act(() => {
        messageHandler?.(errorUpdate);
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      expect(result.current.error?.message).toBe('Connection failed');
      expect(result.current.isConnected).toBe(false);
    });

    it('shows notification on connection error', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      renderHook(() => useRealTimeUpdates('test-topic'));

      const errorUpdate = {
        type: 'connection_error',
        message: 'Connection failed',
        topic: 'test-topic'
      };

      act(() => {
        messageHandler?.(errorUpdate);
      });

      await waitFor(() => {
        expect(mockAddNotification).toHaveBeenCalled();
      });

      expect(mockAddNotification).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'error',
          title: 'Connection Lost',
          duration: 0
        })
      );
    });

    it('clears error on successful message', async () => {
      let messageHandler: ((data: any) => void) | null = null;
      
      (websocketService.connect as jest.Mock).mockImplementation((topic, handler) => {
        messageHandler = handler;
      });

      const { result } = renderHook(() => useRealTimeUpdates('test-topic'));

      // Send error
      act(() => {
        messageHandler?.({
          type: 'connection_error',
          message: 'Connection failed',
          topic: 'test-topic'
        });
      });

      await waitFor(() => {
        expect(result.current.error).toBeTruthy();
      });

      // Send successful message
      act(() => {
        messageHandler?.({
          type: 'sensor_reading',
          data: { value: 1 },
          timestamp: new Date().toISOString()
        });
      });

      await waitFor(() => {
        expect(result.current.error).toBeNull();
      });
    });
  });

  describe('Cleanup', () => {
    it('cleans up status polling on unmount', () => {
      const { unmount } = renderHook(() => useRealTimeUpdates('test-topic'));

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      unmount();

      const callCountBeforeUnmount = (websocketService.getConnectionStatus as jest.Mock).mock.calls.length;

      act(() => {
        jest.advanceTimersByTime(5000);
      });

      expect(websocketService.getConnectionStatus).toHaveBeenCalledTimes(callCountBeforeUnmount);
    });

    it('disconnects with correct handler on unmount', () => {
      const { unmount } = renderHook(() => useRealTimeUpdates('test-topic'));

      unmount();

      expect(websocketService.disconnect).toHaveBeenCalledWith(
        'test-topic',
        expect.any(Function)
      );
    });
  });
});
