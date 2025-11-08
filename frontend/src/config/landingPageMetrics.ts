/**
 * Landing Page Metrics Configuration
 * 
 * Update these values to change the metrics displayed on the landing page
 * without modifying component code.
 * 
 * These represent your service level targets or actual performance metrics.
 */

export interface MetricConfig {
  id: string;
  value: string;
  label: string;
  description?: string;
}

export const trustMetrics: MetricConfig[] = [
  {
    id: 'uptime',
    value: '99.8%',
    label: 'System Uptime',
    description: 'Average uptime over the last 12 months'
  },
  {
    id: 'response-time',
    value: '<30s',
    label: 'Alert Response',
    description: 'Average time to deliver critical alerts'
  },
  {
    id: 'data-integrity',
    value: '100%',
    label: 'Data Integrity',
    description: 'Blockchain-verified data accuracy'
  }
];

/**
 * Update frequency for metrics (if pulling from API)
 * Set to 0 to disable automatic updates and use static values
 * Recommended: 60000 (1 minute) for live metrics
 */
export const METRICS_UPDATE_INTERVAL = 0; // milliseconds (0 = disabled, use static)
// To enable live metrics, set to: 60000 (1 minute) or 300000 (5 minutes)

/**
 * API endpoint for fetching live metrics (optional)
 * This is set via environment variable REACT_APP_METRICS_API_URL
 * Leave empty to use static values from this config
 */
export const METRICS_API_ENDPOINT = process.env.REACT_APP_METRICS_API_URL || '';

/**
 * Footer metrics configuration
 */
export const footerMetrics = {
  uptime: '99.8%',
  status: 'Operational'
};

export default {
  trustMetrics,
  footerMetrics,
  METRICS_UPDATE_INTERVAL,
  METRICS_API_ENDPOINT
};
