import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeftIcon,
  WrenchScrewdriverIcon,
  Cog6ToothIcon,
  BellIcon,
  PowerIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';
import { Activity, Settings } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

// Import the existing dashboard components from DemoDashboardViewer
import DemoDashboardViewer from '../LandingPage/DemoDashboardViewer';
import NotificationCenter from './NotificationCenter';
import DataExportModal from './DataExportModal';

interface TechnicianDashboardProps {
  // Optional props for customization
}

const TechnicianDashboard: React.FC<TechnicianDashboardProps> = () => {
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading technician dashboard...</p>
        </div>
      </div>
    );
  }

  // If showing demo viewer, render it with field-technician role
  if (showDemoViewer) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Custom Header for Technician Dashboard */}
        <header className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-cyan-100 rounded-lg">
                  <WrenchScrewdriverIcon className="w-6 h-6 text-cyan-600" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    AquaChain Field Technician Dashboard
                  </h1>
                  <p className="text-sm text-gray-600">
                    Welcome back, {user.profile?.firstName || user.email}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 bg-cyan-100 text-cyan-700 px-3 py-1.5 rounded-full text-sm font-medium">
                <WrenchScrewdriverIcon className="w-4 h-4" />
                <span>Field Technician</span>
              </div>
              
              <NotificationCenter userRole="technician" />
              
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

        {/* Render the demo dashboard with field-technician role pre-selected */}
        <div className="relative">
          <DemoDashboardViewer
            isOpen={true}
            onClose={() => setShowDemoViewer(false)}
            onBackToLanding={handleBackToLanding}
            initialRole="field-technician"
          />
        </div>
      </div>
    );
  }

  // Dashboard settings/profile view for technicians
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
            <h1 className="text-xl font-bold text-gray-900">Technician Settings</h1>
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
          {/* Technician Profile Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Technician Profile</h2>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Technician ID</label>
                <p className="text-gray-900 font-mono">TECH-{user.userId?.slice(-6) || '001234'}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Certification Level</label>
                <p className="text-gray-900">Level 2 - Water Quality Specialist</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Service Area</label>
                <p className="text-gray-900">Downtown District, North Reservoir</p>
              </div>
            </div>
          </div>

          {/* Work Statistics */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Work Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <ClipboardDocumentListIcon className="w-5 h-5 text-cyan-600" />
                  <span className="font-semibold text-cyan-900">Tasks Completed</span>
                </div>
                <div className="text-2xl font-bold text-cyan-900">47</div>
                <div className="text-sm text-cyan-700">This month</div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-5 h-5 text-green-600" />
                  <span className="font-semibold text-green-900">Devices Serviced</span>
                </div>
                <div className="text-2xl font-bold text-green-900">23</div>
                <div className="text-sm text-green-700">This month</div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Settings className="w-5 h-5 text-blue-600" />
                  <span className="font-semibold text-blue-900">Avg Response Time</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">18m</div>
                <div className="text-sm text-blue-700">Below target</div>
              </div>
            </div>
          </div>

          {/* Dashboard Preferences */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Preferences</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Real-time Alerts</h3>
                  <p className="text-sm text-gray-600">Receive immediate notifications for critical issues</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-cyan-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Mobile Notifications</h3>
                  <p className="text-sm text-gray-600">Get push notifications on your mobile device</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-cyan-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2">
                  <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Auto-assign Tasks</h3>
                  <p className="text-sm text-gray-600">Automatically receive tasks in your service area</p>
                </div>
                <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2">
                  <span className="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                </button>
              </div>
            </div>
          </div>

          {/* Active Tasks */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Active Tasks</h2>
            <div className="space-y-3">
              <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-red-900">Sensor Calibration - Station #47</h3>
                    <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">High Priority</span>
                  </div>
                  <p className="text-sm text-red-700">pH sensor showing drift, requires immediate calibration</p>
                  <p className="text-xs text-red-600 mt-1">Due: Today, 3:00 PM</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-amber-900">Routine Maintenance - North Reservoir</h3>
                    <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">Medium</span>
                  </div>
                  <p className="text-sm text-amber-700">Monthly sensor cleaning and inspection</p>
                  <p className="text-xs text-amber-600 mt-1">Due: Tomorrow, 9:00 AM</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-blue-900">Equipment Installation - Station #52</h3>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">Scheduled</span>
                  </div>
                  <p className="text-sm text-blue-700">Install new turbidity sensor</p>
                  <p className="text-xs text-blue-600 mt-1">Due: Friday, 10:00 AM</p>
                </div>
              </div>
            </div>
          </div>

          {/* Equipment Status */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Equipment Status Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">pH Sensors</span>
                  </div>
                  <span className="text-sm text-green-700">23/24 Online</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Chlorine Sensors</span>
                  </div>
                  <span className="text-sm text-green-700">18/18 Online</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
                    <span className="text-sm font-medium text-amber-900">Turbidity Sensors</span>
                  </div>
                  <span className="text-sm text-amber-700">15/16 Online</span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Flow Meters</span>
                  </div>
                  <span className="text-sm text-green-700">12/12 Online</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-green-900">Pressure Sensors</span>
                  </div>
                  <span className="text-sm text-green-700">8/8 Online</span>
                </div>

                <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-sm font-medium text-red-900">Temperature Sensors</span>
                  </div>
                  <span className="text-sm text-red-700">9/10 Online</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Field Activity</h2>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 border-l-4 border-green-500 bg-green-50">
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">Completed: Sensor Calibration</p>
                  <p className="text-xs text-green-700">Station #43 - pH sensor calibrated successfully</p>
                  <p className="text-xs text-green-600 mt-1">2 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border-l-4 border-blue-500 bg-blue-50">
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">Started: Equipment Inspection</p>
                  <p className="text-xs text-blue-700">Downtown District - Routine monthly inspection</p>
                  <p className="text-xs text-blue-600 mt-1">4 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 border-l-4 border-purple-500 bg-purple-50">
                <div className="flex-1">
                  <p className="text-sm font-medium text-purple-900">Completed: Software Update</p>
                  <p className="text-xs text-purple-700">Updated firmware on 6 devices</p>
                  <p className="text-xs text-purple-600 mt-1">Yesterday, 2:30 PM</p>
                </div>
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
                <Activity className="w-5 h-5 text-cyan-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Monitor Equipment</h3>
                  <p className="text-sm text-gray-600">Check real-time device status and data</p>
                </div>
              </button>
              
              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <BellIcon className="w-5 h-5 text-cyan-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Field Alerts</h3>
                  <p className="text-sm text-gray-600">View maintenance and service alerts</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <ClipboardDocumentListIcon className="w-5 h-5 text-cyan-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Task Management</h3>
                  <p className="text-sm text-gray-600">View and manage assigned tasks</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <Settings className="w-5 h-5 text-cyan-600" />
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Equipment Setup</h3>
                  <p className="text-sm text-gray-600">Configure and calibrate devices</p>
                </div>
              </button>

              <button
                onClick={() => setShowExportModal(true)}
                className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                <svg className="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Export Reports</h3>
                  <p className="text-sm text-gray-600">Download maintenance and field reports</p>
                </div>
              </button>

              <button className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                <svg className="w-5 h-5 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <div className="text-left">
                  <h3 className="font-medium text-gray-900">Work Orders</h3>
                  <p className="text-sm text-gray-600">View and manage work orders</p>
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
        userRole="technician"
      />
    </div>
  );
};

export default TechnicianDashboard;