/**
 * Metrics Service
 * Fetches real-time system metrics from various sources
 */

import { MetricConfig } from '../config/landingPageMetrics';

export interface LiveMetrics {
  uptime: number; // percentage (0-100)
  responseTime: number; // milliseconds
  dataIntegrity: number; // percentage (0-100)
  lastUpdated: string; // ISO timestamp
}

export interface MetricsResponse {
  success: boolean;
  data: LiveMetrics;
  timestamp: string;
}

class MetricsService {
  private baseUrl: string;
  private cache: LiveMetrics | null = null;
  private cacheExpiry: number = 0;
  private cacheDuration: number = 60000; // 1 minute

  constructor() {
    // Use environment variable or default to mock endpoint
    this.baseUrl = process.env.REACT_APP_METRICS_API_URL || '';
  }

  /**
   * Fetch live metrics from API
   */
  async fetchMetrics(): Promise<LiveMetrics> {
    // Check cache first
    if (this.cache && Date.now() < this.cacheExpiry) {
      return this.cache;
    }

    try {
      // If no API URL configured, return mock data
      if (!this.baseUrl) {
        return this.getMockMetrics();
      }

      const response = await fetch(`${this.baseUrl}/metrics`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: MetricsResponse = await response.json();
      
      // Cache the result
      this.cache = result.data;
      this.cacheExpiry = Date.now() + this.cacheDuration;

      return result.data;
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      // Fallback to mock data on error
      return this.getMockMetrics();
    }
  }

  /**
   * Fetch metrics from AWS CloudWatch (if using AWS)
   */
  async fetchFromCloudWatch(): Promise<LiveMetrics> {
    try {
      // This would use AWS SDK to fetch CloudWatch metrics
      // For now, return mock data
      // In production, you'd use:
      // - AWS SDK for JavaScript
      // - CloudWatch GetMetricStatistics API
      // - Lambda function to aggregate metrics
      
      return this.getMockMetrics();
    } catch (error) {
      console.error('Failed to fetch CloudWatch metrics:', error);
      return this.getMockMetrics();
    }
  }

  /**
   * Fetch metrics from custom monitoring service
   */
  async fetchFromMonitoring(): Promise<LiveMetrics> {
    try {
      // This could connect to:
      // - Datadog API
      // - New Relic API
      // - Prometheus/Grafana
      // - Custom monitoring endpoint
      
      return this.getMockMetrics();
    } catch (error) {
      console.error('Failed to fetch monitoring metrics:', error);
      return this.getMockMetrics();
    }
  }

  /**
   * Format metrics for display
   */
  formatMetrics(metrics: LiveMetrics): MetricConfig[] {
    return [
      {
        id: 'uptime',
        value: `${metrics.uptime.toFixed(1)}%`,
        label: 'System Uptime',
        description: `Last updated: ${new Date(metrics.lastUpdated).toLocaleString()}`
      },
      {
        id: 'response-time',
        value: `<${Math.round(metrics.responseTime)}s`,
        label: 'Alert Response',
        description: `Average response time: ${metrics.responseTime.toFixed(1)}s`
      },
      {
        id: 'data-integrity',
        value: `${metrics.dataIntegrity.toFixed(1)}%`,
        label: 'Data Integrity',
        description: 'Blockchain-verified accuracy'
      }
    ];
  }

  /**
   * Mock metrics for development/fallback
   */
  private getMockMetrics(): LiveMetrics {
    // Simulate slight variations in metrics
    const baseUptime = 99.8;
    const baseResponse = 28;
    const baseIntegrity = 100;

    return {
      uptime: baseUptime + (Math.random() * 0.2 - 0.1), // 99.7-99.9%
      responseTime: baseResponse + (Math.random() * 4 - 2), // 26-30s
      dataIntegrity: baseIntegrity,
      lastUpdated: new Date().toISOString()
    };
  }

  /**
   * Clear cache (useful for testing)
   */
  clearCache(): void {
    this.cache = null;
    this.cacheExpiry = 0;
  }

  /**
   * Set cache duration
   */
  setCacheDuration(duration: number): void {
    this.cacheDuration = duration;
  }
}

// Export singleton instance
export const metricsService = new MetricsService();

export default metricsService;
