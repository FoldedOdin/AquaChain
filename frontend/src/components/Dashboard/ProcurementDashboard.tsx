/**
 * Procurement & Finance Dashboard
 * Dedicated high-authority dashboard for Procurement & Finance Controllers
 * Implements comprehensive financial controls with MFA requirement
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../contexts/NotificationContext';
import DashboardLayout from './DashboardLayout';
import LoadingSpinner from '../Loading/LoadingSpinner';
import ErrorBoundary from '../ErrorBoundary';
import ApprovalQueue from './Procurement/ApprovalQueue';
import BudgetTracking from './Procurement/BudgetTracking';
import FinancialAuditLog from './Procurement/FinancialAuditLog';
import { UserProfile } from '../../types';

interface TabConfig {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
  requiresMFA: boolean;
}

const ProcurementDashboard: React.FC = () => {
  const { user, isLoading, requireMFA, isMFAVerified } = useAuth();
  const { showNotification } = useNotification();
  const [activeTab, setActiveTab] = useState<string>('approvals');
  const [isInitializing, setIsInitializing] = useState(true);
  const [mfaRequired, setMfaRequired] = useState(false);

  // Define tab configuration for procurement dashboard
  const tabConfigs: TabConfig[] = [
    {
      id: 'approvals',
      label: 'Purchase Order Approvals',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      component: ApprovalQueue,
      requiresMFA: true
    },
    {
      id: 'budget',
      label: 'Budget Tracking',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
        </svg>
      ),
      component: BudgetTracking,
      requiresMFA: false
    },
    {
      id: 'audit',
      label: 'Financial Audit Log',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      component: FinancialAuditLog,
      requiresMFA: true
    }
  ];

  // Validate user role and initialize dashboard
  useEffect(() => {
    if (!isLoading && user) {
      // Only procurement controllers can access this dashboard
      if (user.role !== 'procurement_controller') {
        showNotification('Access denied. This dashboard is restricted to Procurement & Finance Controllers.', 'error');
        return;
      }

      setIsInitializing(false);
    }
  }, [user, isLoading, showNotification]);

  // Handle MFA requirement for sensitive operations
  useEffect(() => {
    const currentTab = tabConfigs.find(tab => tab.id === activeTab);
    if (currentTab?.requiresMFA && !isMFAVerified) {
      setMfaRequired(true);
    } else {
      setMfaRequired(false);
    }
  }, [activeTab, isMFAVerified, tabConfigs]);

  // Handle tab change with MFA validation
  const handleTabChange = (tabId: string) => {
    if (!user) return;

    const requestedTab = tabConfigs.find(tab => tab.id === tabId);
    if (!requestedTab) return;

    // Check if MFA is required for this tab
    if (requestedTab.requiresMFA && !isMFAVerified) {
      requireMFA?.();
      return;
    }

    setActiveTab(tabId);
  };

  // Handle MFA verification
  const handleMFAVerification = () => {
    setMfaRequired(false);
    showNotification('Multi-factor authentication verified. Access granted.', 'success');
  };

  // Render loading state
  if (isLoading || isInitializing) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="text-gray-600 mt-4">Loading Procurement Dashboard...</p>
        </div>
      </div>
    );
  }

  // Render unauthorized state
  if (!user || user.role !== 'procurement_controller') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 0h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Access Restricted</h1>
          <p className="text-gray-600 mb-6">
            This dashboard is restricted to Procurement & Finance Controllers only.
          </p>
          <button 
            onClick={() => window.location.href = '/dashboard'}
            className="bg-red-600 hover:bg-red-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
          >
            Return to Main Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Render MFA requirement state
  if (mfaRequired) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6 bg-white rounded-lg shadow-lg">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 0h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Multi-Factor Authentication Required</h1>
          <p className="text-gray-600 mb-6">
            This section requires additional security verification. Please complete multi-factor authentication to continue.
          </p>
          <div className="space-y-3">
            <button 
              onClick={() => requireMFA?.()}
              className="w-full bg-amber-600 hover:bg-amber-700 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
            >
              Verify Identity
            </button>
            <button 
              onClick={() => setActiveTab('budget')}
              className="w-full bg-gray-300 hover:bg-gray-400 text-gray-700 font-semibold px-6 py-3 rounded-lg transition-colors duration-200"
            >
              View Budget Tracking (No MFA Required)
            </button>
          </div>
        </div>
      </div>
    );
  }

  const activeTabConfig = tabConfigs.find(tab => tab.id === activeTab);
  const ActiveComponent = activeTabConfig?.component;

  // Dashboard header content
  const headerContent = (
    <div className="flex justify-between items-center">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Procurement & Finance Dashboard</h1>
        <p className="text-sm text-gray-600 mt-1">
          Welcome back, {user.profile.firstName} {user.profile.lastName}
        </p>
        <div className="flex items-center space-x-4 mt-2">
          <div className="text-sm text-gray-500">
            Role: <span className="font-medium text-gray-900">Procurement & Finance Controller</span>
          </div>
          {isMFAVerified && (
            <div className="flex items-center text-sm text-green-600">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              MFA Verified
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center space-x-4">
        <div className="text-right text-sm text-gray-500">
          <div>High Security Dashboard</div>
          <div className="text-xs">All actions are audited</div>
        </div>
      </div>
    </div>
  );

  return (
    <ErrorBoundary>
      <DashboardLayout
        header={headerContent}
        role="admin" // Using admin theme for high-authority dashboard
      >
        <div className="space-y-6">
          {/* Tab Navigation */}
          <div className="bg-white shadow-sm rounded-lg">
            <nav className="flex space-x-8 px-6" aria-label="Tabs">
              {tabConfigs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`
                    flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors duration-200
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                    ${tab.requiresMFA && !isMFAVerified ? 'opacity-50' : ''}
                  `}
                  aria-current={activeTab === tab.id ? 'page' : undefined}
                  disabled={tab.requiresMFA && !isMFAVerified}
                >
                  {tab.icon}
                  <span>{tab.label}</span>
                  {tab.requiresMFA && (
                    <svg className="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 0h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  )}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="bg-white shadow-sm rounded-lg p-6">
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

export default ProcurementDashboard;