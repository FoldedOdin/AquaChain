/**
 * WebSocket Service
 * Manages WebSocket connections with connection pooling, automatic reconnection,
 * and multi-region support
 */

interface WebSocketConnection {
  ws: WebSocket;
  topic: string;
  isConnected: boolean;
  reconnectAttempts: number;
  lastConnectedAt: Date | null;
  subscribers: Set<(data: unknown) => void>;
}

interface WebSocketServiceOptions {
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  enableMultiRegion?: boolean;
}

interface RegionEndpoint {
  region: string;
  endpoint: string;
  priority: number;
  isHealthy: boolean;
  lastHealthCheck: Date | null;
}

class WebSocketService {
  private connections: Map<string, WebSocketConnection> = new Map();
  private reconnectTimeouts: Map<string, NodeJS.Timeout> = new Map();
  private heartbeatIntervals: Map<string, NodeJS.Timeout> = new Map();
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private heartbeatInterval: number;
  private enableMultiRegion: boolean;
  private regionEndpoints: RegionEndpoint[] = [];
  private currentRegionIndex = 0;
  
  // Logging control to prevent spam in development
  private loggedTopics: Set<string> = new Set();
  private loggedDisconnections: Set<string> = new Set();
  private loggedErrors: Set<string> = new Set();
  private loggedMaxAttempts: Set<string> = new Set();

  constructor(options: WebSocketServiceOptions = {}) {
    this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
    this.reconnectDelay = options.reconnectDelay || 1000;
    this.heartbeatInterval = options.heartbeatInterval || 30000;
    this.enableMultiRegion = options.enableMultiRegion || false;

    // Initialize region endpoints if multi-region is enabled
    if (this.enableMultiRegion) {
      this.initializeRegionEndpoints();
    }
  }

  /**
   * Initialize multi-region endpoints
   */
  private initializeRegionEndpoints(): void {
    const primaryEndpoint = process.env.REACT_APP_WEBSOCKET_ENDPOINT || 'ws://localhost:3001/ws';
    const secondaryEndpoint = process.env.REACT_APP_WEBSOCKET_ENDPOINT_SECONDARY;
    const tertiaryEndpoint = process.env.REACT_APP_WEBSOCKET_ENDPOINT_TERTIARY;

    this.regionEndpoints = [
      {
        region: 'primary',
        endpoint: primaryEndpoint,
        priority: 1,
        isHealthy: true,
        lastHealthCheck: null
      }
    ];

    if (secondaryEndpoint) {
      this.regionEndpoints.push({
        region: 'secondary',
        endpoint: secondaryEndpoint,
        priority: 2,
        isHealthy: true,
        lastHealthCheck: null
      });
    }

    if (tertiaryEndpoint) {
      this.regionEndpoints.push({
        region: 'tertiary',
        endpoint: tertiaryEndpoint,
        priority: 3,
        isHealthy: true,
        lastHealthCheck: null
      });
    }

    // Sort by priority
    this.regionEndpoints.sort((a, b) => a.priority - b.priority);
  }

  /**
   * Get the current WebSocket endpoint (with multi-region support)
   */
  private getCurrentEndpoint(): string {
    if (!this.enableMultiRegion || this.regionEndpoints.length === 0) {
      // Check if we're in development mode
      const isDevelopment = process.env.NODE_ENV === 'development';
      
      if (isDevelopment) {
        // In development, check if WebSocket server is available
        const wsEndpoint = process.env.REACT_APP_WEBSOCKET_ENDPOINT;
        if (wsEndpoint) {
          return wsEndpoint;
        }
        
        // Fallback to API endpoint with WebSocket path
        const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
        const wsEndpoint2 = apiEndpoint.replace('http://', 'ws://').replace('https://', 'wss://');
        return `${wsEndpoint2}/ws`;
      }
      
      // Production endpoint
      const apiEndpoint = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';
      const wsEndpoint = apiEndpoint.replace('http://', 'ws://').replace('https://', 'wss://');
      return `${wsEndpoint}/ws`;
    }

    // Find the first healthy endpoint
    const healthyEndpoint = this.regionEndpoints.find(e => e.isHealthy);
    if (healthyEndpoint) {
      return healthyEndpoint.endpoint;
    }

    // If no healthy endpoints, try the primary
    return this.regionEndpoints[0].endpoint;
  }

  /**
   * Mark a region as unhealthy and try the next one
   */
  private markRegionUnhealthy(endpoint: string): void {
    const region = this.regionEndpoints.find(e => e.endpoint === endpoint);
    if (region) {
      region.isHealthy = false;
      region.lastHealthCheck = new Date();
      console.warn(`Region ${region.region} marked as unhealthy`);

      // Schedule health check to re-enable after 5 minutes
      setTimeout(() => {
        region.isHealthy = true;
        console.log(`Region ${region.region} re-enabled for health checks`);
      }, 300000); // 5 minutes
    }
  }

  /**
   * Connect to a WebSocket topic
   * Reuses existing connection if available
   */
  connect(topic: string, onMessage: (data: unknown) => void): void {
    // Check if WebSocket is disabled by user preference
    const wsEnabled = localStorage.getItem('aquachain_websocket_enabled') === 'true';
    
    if (!wsEnabled) {
      console.log(`🔌 WebSocket disabled by user preference for topic: ${topic}`);
      // Notify subscriber that WebSocket is disabled
      onMessage({
        type: 'websocket_disabled',
        message: 'WebSocket connections are disabled. Using polling instead.',
        topic
      });
      return;
    }
    
    const WEBSOCKET_DISABLED = false;
    
    if (WEBSOCKET_DISABLED) {
      console.log(`🔌 WebSocket temporarily disabled for topic: ${topic}`);
      // Notify subscriber that WebSocket is disabled
      onMessage({
        type: 'websocket_disabled',
        message: 'WebSocket connections are temporarily disabled. Using polling instead.',
        topic
      });
      return;
    }
    
    // Check if connection already exists
    const existingConnection = this.connections.get(topic);
    
    if (existingConnection) {
      // Reuse existing connection
      if (existingConnection.isConnected && existingConnection.ws.readyState === WebSocket.OPEN) {
        console.log(`Reusing existing connection for topic: ${topic}`);
        existingConnection.subscribers.add(onMessage);
        return;
      } else {
        // Connection exists but not open, clean it up and reconnect
        this.cleanupConnection(topic);
      }
    }

    // Create new connection
    this.createConnection(topic, onMessage);
  }

  /**
   * Create a new WebSocket connection
   */
  private createConnection(topic: string, onMessage: (data: unknown) => void): void {
    try {
      const endpoint = this.getCurrentEndpoint();
      const wsUrl = `${endpoint}?topic=${encodeURIComponent(topic)}`;
      
      // Always log connection attempts for debugging
      console.log(`🔌 WebSocket connecting to: ${wsUrl}`);
      console.log(`   Environment: ${process.env.NODE_ENV}`);
      console.log(`   Endpoint from env: ${process.env.REACT_APP_WEBSOCKET_ENDPOINT}`);
      
      const ws = new WebSocket(wsUrl);

      const connection: WebSocketConnection = {
        ws,
        topic,
        isConnected: false,
        reconnectAttempts: 0,
        lastConnectedAt: null,
        subscribers: new Set([onMessage])
      };

      this.connections.set(topic, connection);

      ws.onopen = () => {
        // Log successful connections
        console.log(`✅ WebSocket connected: ${topic}`);
        connection.isConnected = true;
        connection.reconnectAttempts = 0;
        connection.lastConnectedAt = new Date();

        // Send authentication if token is available
        const authToken = localStorage.getItem('authToken') || localStorage.getItem('aquachain_token');
        if (authToken) {
          ws.send(JSON.stringify({ type: 'auth', token: authToken }));
        }

        // Subscribe to topic
        ws.send(JSON.stringify({ type: 'subscribe', topic }));

        // Start heartbeat
        this.startHeartbeat(topic);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Ignore heartbeat responses
          if (data.type === 'pong') {
            return;
          }

          // Notify all subscribers
          connection.subscribers.forEach(callback => {
            try {
              callback(data);
            } catch (error) {
              console.error('Error in subscriber callback:', error);
            }
          });
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        connection.isConnected = false;
        // Always log errors for debugging
        console.error(`❌ WebSocket error on topic ${topic}:`, error);
        console.error(`   URL: ${wsUrl}`);
        console.error(`   ReadyState: ${ws.readyState}`);
      };

      ws.onclose = (event) => {
        connection.isConnected = false;
        this.stopHeartbeat(topic);
        
        // Always log disconnections for debugging
        console.log(`🔌 WebSocket disconnected: ${topic}`);
        console.log(`   Code: ${event.code}, Reason: ${event.reason || 'No reason'}`);
        console.log(`   Was clean: ${event.wasClean}`);

        // Handle reconnection with development mode considerations
        this.handleReconnect(topic, endpoint);
      };

    } catch (error) {
      const isDevelopment = process.env.NODE_ENV === 'development';
      if (isDevelopment) {
        // Only log once per topic to avoid spam
        if (!this.loggedErrors) this.loggedErrors = new Set();
        if (!this.loggedErrors.has(topic)) {
          console.warn(`⚠️ WebSocket unavailable in development: ${topic}`);
          this.loggedErrors.add(topic);
        }
        
        // In development, notify subscribers about connection unavailability
        const mockConnection: WebSocketConnection = {
          ws: null as any,
          topic,
          isConnected: false,
          reconnectAttempts: 0,
          lastConnectedAt: null,
          subscribers: new Set([onMessage])
        };
        this.connections.set(topic, mockConnection);
        
        // Notify subscriber that WebSocket is unavailable in development
        onMessage({
          type: 'development_mode',
          message: 'WebSocket server not available in development mode',
          topic
        });
      } else {
        console.error(`❌ Failed to create WebSocket connection for topic ${topic}:`, error);
      }
    }
  }

  /**
   * Handle automatic reconnection with exponential backoff
   */
  private handleReconnect(topic: string, failedEndpoint: string): void {
    const connection = this.connections.get(topic);
    if (!connection) return;

    const isDevelopment = process.env.NODE_ENV === 'development';

    // In development mode, limit reconnection attempts to prevent loops
    if (isDevelopment && connection.reconnectAttempts >= 2) {
      console.log(`🔌 WebSocket: Stopping reconnection attempts for ${topic} (development mode, max 2 attempts)`);
      
      // Notify subscribers about connection failure
      connection.subscribers.forEach(callback => {
        callback({
          type: 'connection_error',
          message: `Failed to connect after ${connection.reconnectAttempts} attempts`,
          topic
        });
      });
      
      // Clean up the connection
      this.cleanupConnection(topic);
      return;
    }

    // Production reconnection logic
    const maxAttempts = this.maxReconnectAttempts;

    // Check if we've exceeded max reconnect attempts
    if (connection.reconnectAttempts >= maxAttempts) {
      console.error(`❌ Max reconnect attempts (${maxAttempts}) reached for topic: ${topic}`);
      
      // Mark region as unhealthy if multi-region is enabled
      if (this.enableMultiRegion) {
        this.markRegionUnhealthy(failedEndpoint);
      }

      // Notify subscribers about connection failure
      connection.subscribers.forEach(callback => {
        callback({
          type: 'connection_error',
          message: `Failed to reconnect after ${maxAttempts} attempts`,
          topic
        });
      });

      // Clean up the connection
      this.cleanupConnection(topic);
      return;
    }

    // Calculate delay with exponential backoff
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, connection.reconnectAttempts),
      30000 // Max 30s
    );

    connection.reconnectAttempts++;

    console.log(
      `🔄 Reconnecting to topic ${topic} (attempt ${connection.reconnectAttempts}/${maxAttempts}) in ${delay}ms`
    );

    // Schedule reconnection
    const timeoutId = setTimeout(() => {
      this.reconnectTimeouts.delete(topic);
      
      // Get all current subscribers
      const subscribers = Array.from(connection.subscribers);
      
      // Clean up old connection
      this.cleanupConnection(topic);
      
      // Create new connection with all subscribers
      if (subscribers.length > 0) {
        this.createConnection(topic, subscribers[0]);
        // Re-add other subscribers
        const newConnection = this.connections.get(topic);
        if (newConnection) {
          subscribers.slice(1).forEach(sub => newConnection.subscribers.add(sub));
        }
      }
    }, delay);

    this.reconnectTimeouts.set(topic, timeoutId);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(topic: string): void {
    const connection = this.connections.get(topic);
    if (!connection) return;

    const intervalId = setInterval(() => {
      if (connection.ws.readyState === WebSocket.OPEN) {
        connection.ws.send(JSON.stringify({ type: 'ping' }));
      } else {
        this.stopHeartbeat(topic);
      }
    }, this.heartbeatInterval);

    this.heartbeatIntervals.set(topic, intervalId);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(topic: string): void {
    const intervalId = this.heartbeatIntervals.get(topic);
    if (intervalId) {
      clearInterval(intervalId);
      this.heartbeatIntervals.delete(topic);
    }
  }

  /**
   * Disconnect from a topic for a specific subscriber
   */
  disconnect(topic: string, onMessage?: (data: unknown) => void): void {
    const connection = this.connections.get(topic);
    if (!connection) return;

    if (onMessage) {
      // Remove specific subscriber
      connection.subscribers.delete(onMessage);
      
      // If no more subscribers, close the connection
      if (connection.subscribers.size === 0) {
        this.cleanupConnection(topic);
      }
    } else {
      // Disconnect all subscribers
      this.cleanupConnection(topic);
    }
  }

  /**
   * Clean up a connection
   */
  private cleanupConnection(topic: string): void {
    const connection = this.connections.get(topic);
    if (!connection) return;

    // Clear reconnect timeout
    const timeoutId = this.reconnectTimeouts.get(topic);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.reconnectTimeouts.delete(topic);
    }

    // Stop heartbeat
    this.stopHeartbeat(topic);

    // Close WebSocket
    if (connection.ws.readyState === WebSocket.OPEN || 
        connection.ws.readyState === WebSocket.CONNECTING) {
      connection.ws.close();
    }

    // Remove connection
    this.connections.delete(topic);
    
    // Only log cleanup in production to avoid spam
    if (process.env.NODE_ENV !== 'development') {
      console.log(`Cleaned up connection for topic: ${topic}`);
    }
  }

  /**
   * Disconnect all connections
   */
  disconnectAll(): void {
    console.log('Disconnecting all WebSocket connections');
    const topics = Array.from(this.connections.keys());
    topics.forEach(topic => this.cleanupConnection(topic));
  }

  /**
   * Get connection status for a topic
   */
  getConnectionStatus(topic: string): {
    isConnected: boolean;
    reconnectAttempts: number;
    subscriberCount: number;
    lastConnectedAt: Date | null;
  } | null {
    const connection = this.connections.get(topic);
    if (!connection) return null;

    return {
      isConnected: connection.isConnected,
      reconnectAttempts: connection.reconnectAttempts,
      subscriberCount: connection.subscribers.size,
      lastConnectedAt: connection.lastConnectedAt
    };
  }

  /**
   * Get all active connections
   */
  getActiveConnections(): string[] {
    return Array.from(this.connections.keys()).filter(topic => {
      const connection = this.connections.get(topic);
      return connection?.isConnected;
    });
  }

  /**
   * Check health of all region endpoints
   */
  async checkRegionHealth(): Promise<void> {
    if (!this.enableMultiRegion) return;

    const healthChecks = this.regionEndpoints.map(async (region) => {
      try {
        // Simple health check: try to create a connection
        const ws = new WebSocket(region.endpoint);
        
        return new Promise<void>((resolve) => {
          const timeout = setTimeout(() => {
            ws.close();
            region.isHealthy = false;
            region.lastHealthCheck = new Date();
            resolve();
          }, 5000);

          ws.onopen = () => {
            clearTimeout(timeout);
            ws.close();
            region.isHealthy = true;
            region.lastHealthCheck = new Date();
            resolve();
          };

          ws.onerror = () => {
            clearTimeout(timeout);
            ws.close();
            region.isHealthy = false;
            region.lastHealthCheck = new Date();
            resolve();
          };
        });
      } catch (error) {
        region.isHealthy = false;
        region.lastHealthCheck = new Date();
      }
    });

    await Promise.all(healthChecks);
    console.log('Region health check completed:', this.regionEndpoints);
  }

  /**
   * Get region health status
   */
  getRegionHealth(): RegionEndpoint[] {
    return this.regionEndpoints.map(r => ({ ...r }));
  }
}

// Export singleton instance
export const websocketService = new WebSocketService({
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  heartbeatInterval: 30000,
  enableMultiRegion: process.env.REACT_APP_ENABLE_MULTI_REGION === 'true'
});

export default websocketService;
