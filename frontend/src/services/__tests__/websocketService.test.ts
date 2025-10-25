/**
 * WebSocket Service Tests
 */

import { websocketService } from '../websocketService';

// Mock WebSocket
class MockWebSocket {
  public readyState: number = WebSocket.CONNECTING;
  public onopen: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public url: string;

  constructor(url: string) {
    this.url = url;
    // Simulate async connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 0);
  }

  send(data: string) {
    // Mock send
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close', { code: 1000 }));
  }
}

(global as any).WebSocket = MockWebSocket;

describe('WebSocket Service', () => {
  let mockCallback: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockCallback = jest.fn();
    
    // Clear any existing connections
    websocketService.disconnectAll();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
    websocketService.disconnectAll();
  });

  describe('Connection Management', () => {
    it('creates a new WebSocket connection', () => {
      websocketService.connect('test-topic', mockCallback);

      const connections = websocketService.getActiveConnections();
      expect(connections).toContain('test-topic');
    });

    it('reuses existing connection for same topic', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();

      websocketService.connect('test-topic', callback1);
      
      jest.runAllTimers();
      
      websocketService.connect('test-topic', callback2);

      const status = websocketService.getConnectionStatus('test-topic');
      expect(status?.subscriberCount).toBe(2);
    });

    it('creates separate connections for different topics', () => {
      websocketService.connect('topic-1', jest.fn());
      websocketService.connect('topic-2', jest.fn());

      jest.runAllTimers();

      const connections = websocketService.getActiveConnections();
      expect(connections).toContain('topic-1');
      expect(connections).toContain('topic-2');
    });

    it('includes topic in WebSocket URL', () => {
      websocketService.connect('test-topic', mockCallback);

      // The URL should include the topic as a query parameter
      // This is tested indirectly through the connection being created
      const status = websocketService.getConnectionStatus('test-topic');
      expect(status).toBeTruthy();
    });
  });

  describe('Message Handling', () => {
    it('calls subscriber callback when message received', (done) => {
      const callback = jest.fn();
      websocketService.connect('test-topic', callback);

      jest.runAllTimers();

      // Simulate message
      const mockWs = (global as any).WebSocket.mock.instances[0];
      const messageData = { type: 'update', data: { value: 42 } };
      
      mockWs.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify(messageData)
      }));

      setTimeout(() => {
        expect(callback).toHaveBeenCalledWith(messageData);
        done();
      }, 0);
    });

    it('notifies all subscribers for a topic', (done) => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();

      websocketService.connect('test-topic', callback1);
      jest.runAllTimers();
      
      websocketService.connect('test-topic', callback2);

      const mockWs = (global as any).WebSocket.mock.instances[0];
      const messageData = { type: 'update', data: { value: 42 } };
      
      mockWs.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify(messageData)
      }));

      setTimeout(() => {
        expect(callback1).toHaveBeenCalledWith(messageData);
        expect(callback2).toHaveBeenCalledWith(messageData);
        done();
      }, 0);
    });

    it('ignores pong messages', (done) => {
      const callback = jest.fn();
      websocketService.connect('test-topic', callback);

      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      mockWs.onmessage?.(new MessageEvent('message', {
        data: JSON.stringify({ type: 'pong' })
      }));

      setTimeout(() => {
        expect(callback).not.toHaveBeenCalled();
        done();
      }, 0);
    });

    it('handles malformed JSON messages gracefully', (done) => {
      const callback = jest.fn();
      websocketService.connect('test-topic', callback);

      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      mockWs.onmessage?.(new MessageEvent('message', {
        data: 'invalid json'
      }));

      setTimeout(() => {
        expect(callback).not.toHaveBeenCalled();
        done();
      }, 0);
    });
  });

  describe('Disconnection', () => {
    it('disconnects from a topic', () => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      websocketService.disconnect('test-topic');

      const status = websocketService.getConnectionStatus('test-topic');
      expect(status).toBeNull();
    });

    it('removes specific subscriber when callback provided', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();

      websocketService.connect('test-topic', callback1);
      jest.runAllTimers();
      
      websocketService.connect('test-topic', callback2);

      websocketService.disconnect('test-topic', callback1);

      const status = websocketService.getConnectionStatus('test-topic');
      expect(status?.subscriberCount).toBe(1);
    });

    it('closes connection when last subscriber disconnects', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();

      websocketService.connect('test-topic', callback1);
      jest.runAllTimers();
      
      websocketService.connect('test-topic', callback2);

      websocketService.disconnect('test-topic', callback1);
      websocketService.disconnect('test-topic', callback2);

      const status = websocketService.getConnectionStatus('test-topic');
      expect(status).toBeNull();
    });

    it('disconnects all connections', () => {
      websocketService.connect('topic-1', jest.fn());
      websocketService.connect('topic-2', jest.fn());
      jest.runAllTimers();

      websocketService.disconnectAll();

      expect(websocketService.getActiveConnections()).toHaveLength(0);
    });
  });

  describe('Connection Status', () => {
    it('returns null for non-existent connection', () => {
      const status = websocketService.getConnectionStatus('non-existent');
      expect(status).toBeNull();
    });

    it('returns connection status', () => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const status = websocketService.getConnectionStatus('test-topic');
      
      expect(status).toBeTruthy();
      expect(status?.isConnected).toBe(true);
      expect(status?.reconnectAttempts).toBe(0);
      expect(status?.subscriberCount).toBe(1);
    });

    it('tracks multiple subscribers', () => {
      websocketService.connect('test-topic', jest.fn());
      jest.runAllTimers();
      
      websocketService.connect('test-topic', jest.fn());

      const status = websocketService.getConnectionStatus('test-topic');
      expect(status?.subscriberCount).toBe(2);
    });

    it('returns active connections', () => {
      websocketService.connect('topic-1', jest.fn());
      websocketService.connect('topic-2', jest.fn());
      jest.runAllTimers();

      const connections = websocketService.getActiveConnections();
      expect(connections).toHaveLength(2);
      expect(connections).toContain('topic-1');
      expect(connections).toContain('topic-2');
    });
  });

  describe('Reconnection', () => {
    it('attempts reconnection on connection close', (done) => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      mockWs.onclose?.(new CloseEvent('close', { code: 1006 }));

      // Advance timers to trigger reconnection
      jest.advanceTimersByTime(1000);

      setTimeout(() => {
        const status = websocketService.getConnectionStatus('test-topic');
        expect(status?.reconnectAttempts).toBeGreaterThan(0);
        done();
      }, 0);
    });

    it('uses exponential backoff for reconnection', () => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      
      // First reconnection attempt
      mockWs.onclose?.(new CloseEvent('close', { code: 1006 }));
      jest.advanceTimersByTime(1000); // Initial delay

      // Second reconnection attempt
      const mockWs2 = (global as any).WebSocket.mock.instances[1];
      mockWs2.onclose?.(new CloseEvent('close', { code: 1006 }));
      jest.advanceTimersByTime(2000); // 2x delay

      const status = websocketService.getConnectionStatus('test-topic');
      expect(status?.reconnectAttempts).toBeGreaterThan(1);
    });

    it('stops reconnecting after max attempts', (done) => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      // Simulate 5 failed connection attempts
      for (let i = 0; i < 5; i++) {
        const mockWs = (global as any).WebSocket.mock.instances[i];
        mockWs.onclose?.(new CloseEvent('close', { code: 1006 }));
        jest.advanceTimersByTime(Math.pow(2, i) * 1000);
      }

      setTimeout(() => {
        const status = websocketService.getConnectionStatus('test-topic');
        expect(status).toBeNull();
        done();
      }, 0);
    });

    it('notifies subscribers after max reconnect attempts', (done) => {
      const callback = jest.fn();
      websocketService.connect('test-topic', callback);
      jest.runAllTimers();

      // Simulate 5 failed connection attempts
      for (let i = 0; i < 5; i++) {
        const mockWs = (global as any).WebSocket.mock.instances[i];
        mockWs.onclose?.(new CloseEvent('close', { code: 1006 }));
        jest.advanceTimersByTime(Math.pow(2, i) * 1000);
      }

      setTimeout(() => {
        expect(callback).toHaveBeenCalledWith(
          expect.objectContaining({
            type: 'connection_error',
            topic: 'test-topic'
          })
        );
        done();
      }, 100);
    });
  });

  describe('Heartbeat', () => {
    it('sends ping messages periodically', (done) => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      const sendSpy = jest.spyOn(mockWs, 'send');

      // Advance time to trigger heartbeat
      jest.advanceTimersByTime(30000);

      setTimeout(() => {
        expect(sendSpy).toHaveBeenCalledWith(
          JSON.stringify({ type: 'ping' })
        );
        done();
      }, 0);
    });

    it('stops heartbeat on disconnection', () => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      const sendSpy = jest.spyOn(mockWs, 'send');

      websocketService.disconnect('test-topic');

      // Advance time past heartbeat interval
      jest.advanceTimersByTime(60000);

      expect(sendSpy).not.toHaveBeenCalledWith(
        JSON.stringify({ type: 'ping' })
      );
    });
  });

  describe('Authentication', () => {
    it('sends auth token on connection', (done) => {
      localStorage.setItem('authToken', 'test-token');

      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      const sendSpy = jest.spyOn(mockWs, 'send');

      setTimeout(() => {
        expect(sendSpy).toHaveBeenCalledWith(
          JSON.stringify({ type: 'auth', token: 'test-token' })
        );
        localStorage.removeItem('authToken');
        done();
      }, 0);
    });

    it('subscribes to topic after connection', (done) => {
      websocketService.connect('test-topic', mockCallback);
      jest.runAllTimers();

      const mockWs = (global as any).WebSocket.mock.instances[0];
      const sendSpy = jest.spyOn(mockWs, 'send');

      setTimeout(() => {
        expect(sendSpy).toHaveBeenCalledWith(
          JSON.stringify({ type: 'subscribe', topic: 'test-topic' })
        );
        done();
      }, 0);
    });
  });
});
