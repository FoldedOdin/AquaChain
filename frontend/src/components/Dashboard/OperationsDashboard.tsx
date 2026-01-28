import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../contexts/NotificationContext';
import DashboardLayout from './DashboardLayout';
import LoadingSpinner from '../Loading/LoadingSpinner';
import ErrorBoundary from '../ErrorBoundary';
import InventoryManagerView from './Operations/InventoryManagerView';
import WarehouseManagerView from './Operations/WarehouseManagerView';
import SupplierCoordinatorView from './Operations/SupplierCoordinatorView';
import { UserProfile } from '../../types';

interface TabConfig {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
  roles: string[];
}

const OperationsDashboard: React.FC = () => {
  const { user, isLoading } = useAuth();
  const { showNotification } = useNotification();
  const [activeTab, setActiveTab] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState(true);

  // Define tab configuration based on roles
  const tabConfigs: TabConfig[] = [
    {
      id: 'inventory',
      label: 'Inventory Management',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      ),
      component: InventoryManagerView,
      roles: ['inventory_manager']
    },
    {
      id: 'warehouse',
      label: 'Warehouse Operations',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
      component: WarehouseManagerView,
      roles: ['warehouse_manager']
    },
    {
      id: 'suppliers',
      label: 'Supplier Management',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      component: SupplierCoordinatorView,
      roles: ['supplier_coordinator']
    }
  ];

  // Get available tabs based on user role
  const getAvailableTabs = (userRole: string): TabConfig[] => {
    return tabConfigs.filter(tab => tab.roles.includes(userRole));
  };

  // Initialize dashboard based on user role
  useEffect(() => {
    if (!isLoading && user) {
      const availableTabs = getAvailableTabs(user.role);
      
      if (availableTabs.length === 0) {
        showNotification('Access denied. You do not have permission to access the Operations Dashboard.', 'error');
        return;
      }

      // Set the first available tab as active
      if (!activeTab && availableTabs.length > 0) {
        setActiveTab(availableTabs[0].id);
      }

      setIsInitializing(false);
    }
  }, [user, isLoading, activeTab, showNotification]);

  // Handle tab change with role validation
  const handleTabChange = (tabId: string) => {
    if (!user) return;

    const availableTabs = getAvailableTabs(user.role);
    const requestedTab = availableTabs.find(tab => tab.id === tabId);

    if (!requestedTab) {
      showNotification('Access denied. You do not have permission to access this section.', 'error');
      return;
    }

    setActiveTab(tabId);
  };

  // Render loading state
  if (isLoading || isInitializing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="text-gray-600 mt-4">Loading Operations Dashboard...</p>
        </div>
      </div>
    );
  }

  // Render unauthorized state
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Authentication Required</h1>
          <p className="text-gray-600 mb-6">Please log in to access the Operations Dashboard.</p>
          <button 
            onClick={() => window.location.href = '/'}
            className="bg-aqua-600 hover:bg-aqua-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  const availableTabs = getAvailableTabs(user.role);
  
  // Render no access state
  if (availableTabs.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 0h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Restricted</h1>
          <p className="text-gray-600 mb-6">
            Your role ({user.role}) does not have access to the Operations Dashboard.
          </p>
          <button 
            onClick={() => window.location.href = '/dashboard'}
            className="bg-aqua-600 hover:bg-aqua-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
          >
            Go to Main Dashboard
          </button>
        </div>
      </div>
    );
  }

  const activeTabConfig = availableTabs.find(tab => tab.id === activeTab);
  const ActiveComponent = activeTabConfig?.component;

  return (
    <ErrorBoundary>
      <DashboardLayout 
        header={
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Operations Dashboard</h1>
              <p className="text-gray-600">Monitor and manage system operations</p>
            </div>
          </div>
        }
        role="admin"
      >
        <div className="min-h-screen bg-gray-50">
          {/* Navigation Tabs */}
          <div className="bg-white shadow-sm border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500">
                  Role: <span className="font-medium text-gray-900 capitalize">
                    {user.role.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="bg-white shadow-sm">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <nav className="flex space-x-8" aria-label="Tabs">
                {availableTabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`
                      flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200
                      ${activeTab === tab.id
                        ? 'border-aqua-500 text-aqua-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                    aria-current={activeTab === tab.id ? 'page' : undefined}
                  >
                    {tab.icon}
                    <span>{tab.label}</span>
                  </button>
                ))}
              </nav>
            </div>
          </div>

          {/* Tab Content */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {ActiveComponent && (
              <ErrorBoundary>
                <ActiveComponent />
              </ErrorBoundary>
            )}
          </div>
        </div>
      </DashboardLayout>
    </ErrorBoundary>
  );
};

export default OperationsDashboard;