import React from 'react';
import { Info, RefreshCw } from 'lucide-react';
import { SystemHealthResponse, ServiceHealth } from '../../types/admin';

interface SystemHealthPanelProps {
  health: SystemHealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

const SystemHealthPanel: React.FC<SystemHealthPanelProps> = ({ 
  health, 
  loading, 
  onRefresh 
}) => {
  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'healthy':
        return '🟢';
      case 'degraded':
        return '🟡';
      case 'down':
        return '🔴';
      default:
        return '⚪';
    }
  };
  
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'text-green-600';
      case 'degraded':
        return 'text-yellow-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return 'Unknown';
    }
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">System Health</h3>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Refresh system health"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Checking...' : 'Refresh'}</span>
        </button>
      </div>
      
      {loading && !health ? (
        <div className="space-y-3" role="status" aria-label="Loading system health">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="animate-pulse flex items-center space-x-4">
              <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
              <div className="flex-1 h-4 bg-gray-200 rounded"></div>
              <div className="h-4 w-20 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : health ? (
        <div className="space-y-3">
          {health.services.map((service: ServiceHealth) => (
            <div 
              key={service.name} 
              className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0"
            >
              <div className="flex items-center space-x-3">
                <span className="text-2xl" role="img" aria-label={`${service.status} status`}>
                  {getStatusIcon(service.status)}
                </span>
                <span className="text-sm font-medium text-gray-900">
                  {service.name}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className={`text-sm font-medium capitalize ${getStatusColor(service.status)}`}>
                  {service.status}
                </span>
                {service.message && (
                  <div className="relative group">
                    <Info className="h-4 w-4 text-gray-400 cursor-help" />
                    <div className="absolute right-0 bottom-full mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-10">
                      {service.message}
                      <div className="absolute top-full right-4 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500">
                Last checked: {formatTimestamp(health.checkedAt)}
              </span>
              {health.cacheHit && (
                <span className="text-xs text-gray-400 italic">(cached)</span>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <p className="text-sm">Unable to load system health</p>
          <button
            onClick={onRefresh}
            className="mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            Try again
          </button>
        </div>
      )}
    </div>
  );
};

export default SystemHealthPanel;
