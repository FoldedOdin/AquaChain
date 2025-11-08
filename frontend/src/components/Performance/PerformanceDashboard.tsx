/**
 * Performance Dashboard Component
 * Displays real-time performance metrics and recommendations
 */

import React, { useState } from 'react';
import { usePerformanceMonitoring } from '../../hooks/usePerformanceMonitoring';
import { Activity, Zap, AlertCircle, CheckCircle, Clock, Wifi } from 'lucide-react';

interface PerformanceDashboardProps {
  isVisible?: boolean;
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  enableRecommendations?: boolean;
}

const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({
  isVisible = false,
  position = 'bottom-right',
  enableRecommendations = true
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const { 
    metrics, 
    isLoading, 
    overallScore, 
    recommendations, 
    connectionInfo,
    getMetrics 
  } = usePerformanceMonitoring({
    enableRealTimeMonitoring: true,
    enableRecommendations,
    enableConnectionMonitoring: true,
    reportingInterval: 3000
  });

  // Create mock insights for UI display
  const insights = {
    grade: overallScore >= 90 ? 'A' : overallScore >= 80 ? 'B' : overallScore >= 70 ? 'C' : 'D',
    coreWebVitals: {
      lcp: { status: metrics.lcp ? (metrics.lcp < 2500 ? 'good' : metrics.lcp < 4000 ? 'needs-improvement' : 'poor') : 'unknown' },
      fid: { status: metrics.fid ? (metrics.fid < 100 ? 'good' : metrics.fid < 300 ? 'needs-improvement' : 'poor') : 'unknown' },
      cls: { status: metrics.cls ? (metrics.cls < 0.1 ? 'good' : metrics.cls < 0.25 ? 'needs-improvement' : 'poor') : 'unknown' }
    }
  };

  if (!isVisible && process.env.NODE_ENV !== 'development') {
    return null;
  }

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-600 bg-green-100';
      case 'needs-improvement': return 'text-yellow-600 bg-yellow-100';
      case 'poor': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={`fixed ${positionClasses[position]} z-tooltip`}>
      {/* Collapsed View */}
      {!isExpanded && (
        <button
          onClick={() => setIsExpanded(true)}
          className="bg-white shadow-lg rounded-full p-3 hover:shadow-xl transition-shadow border border-gray-200"
          title="Performance Monitor"
        >
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-aqua-500" />
            <span className={`text-sm font-semibold ${getScoreColor(overallScore)}`}>
              {isLoading ? '...' : overallScore}
            </span>
          </div>
        </button>
      )}

      {/* Expanded View */}
      {isExpanded && (
        <div className="bg-white shadow-xl rounded-lg border border-gray-200 w-80 max-h-96 overflow-y-auto">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Activity className="w-5 h-5 text-aqua-500" />
                <h3 className="font-semibold text-gray-900">Performance</h3>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            
            {/* Overall Score */}
            <div className="mt-2 flex items-center space-x-2">
              <span className="text-sm text-gray-600">Score:</span>
              <span className={`text-lg font-bold ${getScoreColor(overallScore)}`}>
                {isLoading ? '...' : `${overallScore} (${insights.grade})`}
              </span>
            </div>
          </div>

          {/* Core Web Vitals */}
          <div className="p-4 border-b border-gray-200">
            <h4 className="font-medium text-gray-900 mb-3">Core Web Vitals</h4>
            <div className="space-y-2">
              {/* LCP */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">LCP</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-mono">
                    {metrics.lcp ? `${Math.round(metrics.lcp)}ms` : '...'}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(insights.coreWebVitals.lcp.status)}`}>
                    {insights.coreWebVitals.lcp.status}
                  </span>
                </div>
              </div>

              {/* FID */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Zap className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">FID</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-mono">
                    {metrics.fid ? `${Math.round(metrics.fid)}ms` : '...'}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(insights.coreWebVitals.fid.status)}`}>
                    {insights.coreWebVitals.fid.status}
                  </span>
                </div>
              </div>

              {/* CLS */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-600">CLS</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-mono">
                    {metrics.cls ? metrics.cls.toFixed(3) : '...'}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(insights.coreWebVitals.cls.status)}`}>
                    {insights.coreWebVitals.cls.status}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Connection Info */}
          {connectionInfo.effectiveType && (
            <div className="p-4 border-b border-gray-200">
              <h4 className="font-medium text-gray-900 mb-2">Connection</h4>
              <div className="flex items-center space-x-2">
                <Wifi className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-600">
                  {connectionInfo.effectiveType}
                  {connectionInfo.downlink && ` (${connectionInfo.downlink} Mbps)`}
                </span>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {enableRecommendations && recommendations.length > 0 && (
            <div className="p-4">
              <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
              <div className="space-y-2">
                {recommendations.slice(0, 3).map((recommendation, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    <span className="text-xs text-gray-600">{recommendation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Additional Metrics */}
          <div className="p-4 bg-gray-50 rounded-b-lg">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-gray-500">FCP:</span>
                <span className="ml-1 font-mono">
                  {metrics.fcp ? `${Math.round(metrics.fcp)}ms` : '...'}
                </span>
              </div>
              <div>
                <span className="text-gray-500">TTFB:</span>
                <span className="ml-1 font-mono">
                  {metrics.ttfb ? `${Math.round(metrics.ttfb)}ms` : '...'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceDashboard;