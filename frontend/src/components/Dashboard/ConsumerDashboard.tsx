import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  UserIcon,
  Cog6ToothIcon,
  BellIcon,
  PowerIcon
} from '@heroicons/react/24/outline';
import { Droplet, Activity } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

// Import the existing dashboard components from DemoDashboardViewer
import DemoDashboardViewer from '../LandingPage/DemoDashboardViewer';
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface ConsumerDashboardProps {
  // Optional props for customization
}

const ConsumerDashboard: React.FC<ConsumerDashboardProps> = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showDemoViewer, setShowDemoViewer] = useState(true);
  const [showExportModal, setShowExportModal] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      navigate('/');
    }
  }, [user, navigate]);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleBackToLanding = () => {
    navigate('/');
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-aqua-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // If showing demo viewer, render it with consumer role
  if (showDemoViewer) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Custom Header for Consumer Dashboard */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-aqua-100 rounded-lg">
                  <Droplet className="w-6 h-6 text-aqua-600" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    AquaChain Consumer Dashboard
                  </h1>
                  <p className="text-sm text-gray-600">
                    Welcome back, {user.profile?.firstName || user.email}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1.5 rounded-full text-sm font-medium">
                <UserIcon className="w-4 h-4" />
                <span>Consumer</span>
              </div>
              
              <NotificationCenter userRole="consumer" />
              
              <button
                onClick={() => setShowDemoViewer(false)}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                title="Dashboard Settings"
              >
                <Cog6ToothIcon className="w-5 h-5" />
              </button>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                title="Logout"
              >
                <PowerIcon className="w-5 h-5" />
                <span className="text-sm">Logout</span>
              </button>
            </div>
          </div>
        </header>

        {/* Render the demo dashboard with consumer role pre-selected */}
        <div className="relative">
          <DemoDashboardViewer
            isOpen={true}
            onClose={() => setShowDemoViewer(false)}
            onBackToLanding={handleBackToLanding}
            initialRole="citizen"
          />
        </div>
      </div>
    );
  }

  // Dashboard settings/profile view
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowDemoViewer(true)}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors duration-200 font-medium"
            >
              <ArrowLeftIcon className="w-5 h-5" />
              <span>Back to Dashboard</span>
            </button>
            <div className="h-6 w-px bg-gray-300" />
            <h1 className="text-xl font-bold text-gray-900">Dashboard Settings</h1>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
          >
            <PowerIcon className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto p-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* User Profile Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <p className="text-gray-900">{user.profile?.firstName} {user.profile?.lastName}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <p className="text-gray-900">{user.email}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <p className="text-gray-900 capitalize">{user.role}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Member Since</label>
                <p className="text-gray-900">
                  {new Date().toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </p>
              </div>
            </div>
          </div>

          {/* Dashboard Preferences */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Preferences</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Real-time Updates</h3>
                  <p className="text-sm text-gray-600">Receive live water quality updates</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-aqua-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Email Notifications</h3>
                  <p className="text-sm text-gray-600">Get notified about water quality alerts</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-aqua-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>
            </div>
          </div>

          {/* Water Quality Summary */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Water Quality</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-green-700">pH Level</span>
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">Good</span>
                </div>
                <div className="text-2xl font-bold text-green-900">7.2</div>
                <div className="text-xs text-green-700">Optimal range: 6.5-8.5</div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-700">Chlorine</span>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Good</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">0.8 ppm</div>
                <div className="text-xs text-blue-700">Safe level: 0.2-4.0 ppm</div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-amber-700">Turbidity</span>
                  <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">Monitor</span>
                </div>
                <div className="text-2xl font-bold text-amber-900">0.9 NTU</div>
                <div className="text-xs text-amber-700">Target: &lt;1.0 NTU</div>
              </div>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Notifications</h2>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">Water Quality Normal</p>
                  <p className="text-xs text-green-700">All parameters within safe ranges - 2 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">Maintenance Scheduled</p>
                  <p className="text-xs text-blue-700">Routine sensor calibration planned for tomorrow - 1 day ago</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="w-2 h-2 bg-gray-500 rounded-full mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">System Update</p>
                  <p className="text-xs text-gray-700">Dashboard updated with new features - 3 days ago</p>
                </div>
              </div>
            </div>
          </div>

          {/* Usage Statistics */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Water Usage</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">This Month</span>
                  <span className="text-sm text-gray-600">2,340 gallons</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-aqua-600 h-2 rounded-full" style={{width: '78%'}}></div>
                </div>
                <p className="text-xs text-gray-600 mt-1">78% of average usage</p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700">Daily Average</span>
                  <span className="text-sm text-gray-600">78 gallons</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '65%'}}></div>
                </div>
                <p className="text-xs text-gray-600 mt-1">Below recommended limit</p>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setShowDemoViewer(true)}
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                <Activity className="w-5 h-5 text-aqua-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">View Water Quality</h3>
                  <p className="text-sm text-gray-600">Check current water quality metrics</p>
                </div>
              </button>
              
              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <BellIcon className="w-5 h-5 text-aqua-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">View Alerts</h3>
                  <p className="text-sm text-gray-600">Check safety alerts and notifications</p>
                </div>
              </button>

              <button
                onClick={() => setShowExportModal(true)}
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                <svg className="w-5 h-5 text-aqua-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Export Data</h3>
                  <p className="text-sm text-gray-600">Download your water quality data</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <svg className="w-5 h-5 text-aqua-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Get Support</h3>
                  <p className="text-sm text-gray-600">Contact customer support</p>
                </div>
              </button>
            </div>
          </div>
        </motion.div>
      </main>

      {/* Data Export Modal */}
      <DataExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        userRole="consumer"
      />
    </div>
  );
};

export default ConsumerDashboard;