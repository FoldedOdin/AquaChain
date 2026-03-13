import React from 'react';
import { CloudIcon, ServerIcon } from '@heroicons/react/24/outline';
import unifiedDataService from '../../services/dataServiceSelector';

/**
 * DataSourceIndicator Component
 * 
 * Shows whether the app is using real API or mock data
 */
const DataSourceIndicator: React.FC = () => {
  const isUsingMockData = unifiedDataService.isUsingMockData();
  
  if (!isUsingMockData) {
    return null; // Don't show indicator when using real API
  }
  
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-blue-100 border border-blue-300 rounded-lg px-3 py-2 shadow-lg">
        <div className="flex items-center space-x-2">
          <ServerIcon className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-blue-800">Using Mock Data</span>
        </div>
        <div className="text-xs text-blue-600 mt-1">
          Authentication issue detected
        </div>
      </div>
    </div>
  );
};

export default DataSourceIndicator;