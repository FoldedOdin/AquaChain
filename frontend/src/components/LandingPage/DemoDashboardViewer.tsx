import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  MapPinIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  BellIcon,
  UserIcon,
  BuildingOfficeIcon,
  WrenchScrewdriverIcon
} from '@heroicons/react/24/outline';
import {
  CheckCircleIcon as CheckCircleSolid,
  ExclamationTriangleIcon as ExclamationTriangleSolid
} from '@heroicons/react/20/solid';
import {
  Droplet,
  TrendingUp,
  TrendingDown,
  Activity,
  AlertCircle,
  Minus
} from 'lucide-react';

interface DemoDashboardViewerProps {
  isOpen: boolean;
  onClose: () => void;
  onBackToLanding: () => void;
}

interface WaterQualityData {
  parameter: string;
  value: number;
  unit: string;
  status: 'good' | 'warning' | 'critical';
  threshold: number;
  lastUpdated: string;
}

interface DeviceStatus {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance';
  batteryLevel: number;
  lastSeen: string;
}

interface Alert {
  id: string;
  type: 'warning' | 'critical';
  message: string;
  timestamp: string;
  deviceId: string;
  resolved: boolean;
}

// Sample demo data
const sampleWaterQualityData: WaterQualityData[] = [
  {
    parameter: 'pH Level',
    value: 7.2,
    unit: 'pH',
    status: 'good',
    threshold: 7.5,
    lastUpdated: '2 minutes ago'
  },
  {
    parameter: 'Dissolved Oxygen',
    value: 8.5,
    unit: 'mg/L',
    status: 'good',
    threshold: 6.0,
    lastUpdated: '2 minutes ago'
  },
  {
    parameter: 'Turbidity',
    value: 12.3,
    unit: 'NTU',
    status: 'warning',
    threshold: 10.0,
    lastUpdated: '3 minutes ago'
  },
  {
    parameter: 'Temperature',
    value: 22.1,
    unit: '°C',
    status: 'good',
    threshold: 25.0,
    lastUpdated: '1 minute ago'
  },
  {
    parameter: 'Chlorine',
    value: 0.8,
    unit: 'mg/L',
    status: 'good',
    threshold: 1.0,
    lastUpdated: '2 minutes ago'
  },
  {
    parameter: 'Total Dissolved Solids',
    value: 245,
    unit: 'ppm',
    status: 'good',
    threshold: 500,
    lastUpdated: '4 minutes ago'
  }
];

const sampleDevices: DeviceStatus[] = [
  {
    id: 'AQ-001',
    name: 'Main Reservoir Sensor',
    location: 'North Reservoir',
    status: 'online',
    batteryLevel: 87,
    lastSeen: '1 minute ago'
  },
  {
    id: 'AQ-002', 
    name: 'Distribution Point A',
    location: 'Downtown District',
    status: 'online',
    batteryLevel: 92,
    lastSeen: '2 minutes ago'
  },
  {
    id: 'AQ-003',
    name: 'Treatment Plant Outlet',
    location: 'Water Treatment Facility',
    status: 'maintenance',
    batteryLevel: 45,
    lastSeen: '15 minutes ago'
  }
];

const sampleAlerts: Alert[] = [
  {
    id: 'alert-001',
    type: 'warning',
    message: 'Turbidity levels elevated at Distribution Point A',
    timestamp: '5 minutes ago',
    deviceId: 'AQ-002',
    resolved: false
  },
  {
    id: 'alert-002',
    type: 'critical',
    message: 'Device AQ-003 requires maintenance - low battery',
    timestamp: '15 minutes ago',
    deviceId: 'AQ-003',
    resolved: false
  }
];

const WaterQualityCard: React.FC<{ data: WaterQualityData; index: number }> = ({ data, index }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'good': return 'text-green-400 bg-green-400/10 border-green-400/20';
      case 'warning': return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
      case 'critical': return 'text-red-400 bg-red-400/10 border-red-400/20';
      default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircleIcon className="w-5 h-5" />;
      case 'warning': return <ExclamationTriangleIcon className="w-5 h-5" />;
      case 'critical': return <ExclamationTriangleIcon className="w-5 h-5" />;
      default: return <ClockIcon className="w-5 h-5" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">{data.parameter}</h3>
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border ${getStatusColor(data.status)}`}>
          {getStatusIcon(data.status)}
          <span className="text-sm font-medium capitalize">{data.status}</span>
        </div>
      </div>
      
      <div className="flex items-baseline space-x-2 mb-2">
        <span className="text-3xl font-bold text-white">{data.value}</span>
        <span className="text-gray-400">{data.unit}</span>
      </div>
      
      <div className="flex items-center justify-between text-sm text-gray-400">
        <span>Threshold: {data.threshold} {data.unit}</span>
        <span className="flex items-center space-x-1">
          <ClockIcon className="w-4 h-4" />
          <span>{data.lastUpdated}</span>
        </span>
      </div>
    </motion.div>
  );
};

const DeviceCard: React.FC<{ device: DeviceStatus; index: number }> = ({ device, index }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-400 bg-green-400/10';
      case 'offline': return 'text-red-400 bg-red-400/10';
      case 'maintenance': return 'text-yellow-400 bg-yellow-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  const getBatteryColor = (level: number) => {
    if (level > 60) return 'text-green-400';
    if (level > 30) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{device.name}</h3>
          <p className="text-gray-400 flex items-center space-x-1">
            <MapPinIcon className="w-4 h-4" />
            <span>{device.location}</span>
          </p>
        </div>
        <div className={`px-3 py-1 rounded-full ${getStatusColor(device.status)}`}>
          <span className="text-sm font-medium capitalize">{device.status}</span>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-gray-400">Battery:</span>
          <span className={`font-semibold ${getBatteryColor(device.batteryLevel)}`}>
            {device.batteryLevel}%
          </span>
        </div>
        <span className="text-sm text-gray-400">{device.lastSeen}</span>
      </div>
    </motion.div>
  );
};

const AlertCard: React.FC<{ alert: Alert; index: number }> = ({ alert, index }) => {
  const getAlertColor = (type: string) => {
    switch (type) {
      case 'warning': return 'border-yellow-400/30 bg-yellow-400/5';
      case 'critical': return 'border-red-400/30 bg-red-400/5';
      default: return 'border-gray-400/30 bg-gray-400/5';
    }
  };

  const getAlertIcon = (type: string) => {
    return <ExclamationTriangleIcon className={`w-5 h-5 ${type === 'critical' ? 'text-red-400' : 'text-yellow-400'}`} />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className={`border rounded-xl p-4 ${getAlertColor(alert.type)}`}
    >
      <div className="flex items-start space-x-3">
        {getAlertIcon(alert.type)}
        <div className="flex-1">
          <p className="text-white font-medium">{alert.message}</p>
          <div className="flex items-center space-x-4 mt-2 text-sm text-gray-400">
            <span>Device: {alert.deviceId}</span>
            <span>{alert.timestamp}</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * Demo Dashboard Viewer Component
 * Displays sample water quality data, device status, and alerts
 * Includes watermarks and navigation back to landing page
 */
const DemoDashboardViewer: React.FC<DemoDashboardViewerProps> = ({
  isOpen,
  onClose,
  onBackToLanding
}) => {
  const [activeRole, setActiveRole] = useState<'citizen' | 'authority' | 'operator'>('citizen');
  const [activeTab, setActiveTab] = useState<'overview' | 'devices' | 'alerts'>('overview');

  // Reset to default state when opening
  useEffect(() => {
    if (isOpen) {
      setActiveRole('citizen');
      setActiveTab('overview');
    }
  }, [isOpen]);

  // Simulate real-time data updates
  useEffect(() => {
    if (!isOpen) return;

    const interval = setInterval(() => {
      // This would normally update the data from an API
      // For demo purposes, we'll just trigger a re-render
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-slate-900"
      >
        {/* Demo Watermark */}
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className="bg-yellow-500/20 border border-yellow-500/30 text-yellow-400 px-4 py-2 rounded-full text-sm font-medium">
            🚧 DEMONSTRATION DATA - NOT REAL SENSOR READINGS
          </div>
        </div>

        {/* Role Selector */}
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 z-10">
          <div className="bg-slate-800/90 backdrop-blur-sm border border-slate-700/50 rounded-xl p-2">
            <div className="flex space-x-2">
              {[
                { id: 'citizen', label: '👤 Citizen View', desc: 'Public water quality info' },
                { id: 'authority', label: '🏛️ Authority View', desc: 'Regulatory oversight' },
                { id: 'operator', label: '⚙️ Operator View', desc: 'Technical management' }
              ].map(({ id, label, desc }) => (
                <button
                  key={id}
                  onClick={() => setActiveRole(id as any)}
                  className={`
                    px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 group
                    ${activeRole === id 
                      ? 'bg-aqua-600 text-white' 
                      : 'text-gray-400 hover:text-white hover:bg-slate-700/50'
                    }
                  `}
                  title={desc}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Header */}
        <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700/50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={onBackToLanding}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200"
                aria-label="Back to landing page"
              >
                <ArrowLeftIcon className="w-5 h-5" />
                <span>Back to AquaChain</span>
              </button>
              <div className="h-6 w-px bg-slate-600" />
              <h1 className="text-xl font-bold text-white">
                AquaChain Dashboard Demo - {
                  activeRole === 'citizen' ? '👤 Citizen View' :
                  activeRole === 'authority' ? '🏛️ Authority View' :
                  '⚙️ Operator View'
                }
              </h1>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white transition-colors duration-200"
              aria-label="Close demo"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-8 mt-4">
            {(() => {
              const tabs = {
                citizen: [
                  { id: 'overview', label: 'Water Quality', icon: ChartBarIcon },
                  { id: 'alerts', label: 'Public Alerts', icon: ExclamationTriangleIcon }
                ],
                authority: [
                  { id: 'overview', label: 'Regional Overview', icon: ChartBarIcon },
                  { id: 'devices', label: 'Infrastructure', icon: Cog6ToothIcon },
                  { id: 'alerts', label: 'Compliance Alerts', icon: ExclamationTriangleIcon }
                ],
                operator: [
                  { id: 'overview', label: 'System Overview', icon: ChartBarIcon },
                  { id: 'devices', label: 'Device Management', icon: Cog6ToothIcon },
                  { id: 'alerts', label: 'Technical Alerts', icon: ExclamationTriangleIcon }
                ]
              };
              return tabs[activeRole];
            })().map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`
                  flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200
                  ${activeTab === id 
                    ? 'bg-aqua-600 text-white' 
                    : 'text-gray-400 hover:text-white hover:bg-slate-700/50'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </header>

        {/* Main Content */}
        <main className="flex-1 overflow-auto p-6 pt-32">
          <div className="max-w-7xl mx-auto">
            {/* Role Description */}
            <div className="mb-6 p-4 bg-slate-800/30 border border-slate-700/50 rounded-xl">
              <p className="text-gray-300">
                {activeRole === 'citizen' && "👤 Citizen View: Access public water quality information for your area, view safety alerts, and understand water quality metrics that affect your daily life."}
                {activeRole === 'authority' && "🏛️ Authority View: Monitor regional water quality compliance, oversee infrastructure status, and manage regulatory alerts across multiple districts."}
                {activeRole === 'operator' && "⚙️ Operator View: Technical dashboard for water system operators with detailed device management, maintenance alerts, and system diagnostics."}
              </p>
            </div>

            {activeTab === 'overview' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <h2 className="text-2xl font-bold text-white mb-6">
                  {activeRole === 'citizen' && 'Your Local Water Quality'}
                  {activeRole === 'authority' && 'Regional Water Quality Overview'}
                  {activeRole === 'operator' && 'System Performance Overview'}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {(() => {
                    // Filter data based on role
                    if (activeRole === 'citizen') {
                      // Citizens see basic quality parameters
                      return sampleWaterQualityData.filter(d => 
                        ['pH Level', 'Chlorine', 'Temperature', 'Turbidity'].includes(d.parameter)
                      );
                    } else if (activeRole === 'authority') {
                      // Authorities see compliance-focused data
                      return sampleWaterQualityData.filter(d => 
                        ['pH Level', 'Dissolved Oxygen', 'Chlorine', 'Total Dissolved Solids'].includes(d.parameter)
                      );
                    } else {
                      // Operators see all technical data
                      return sampleWaterQualityData;
                    }
                  })().map((data, index) => (
                    <WaterQualityCard key={data.parameter} data={data} index={index} />
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'devices' && (activeRole === 'authority' || activeRole === 'operator') && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <h2 className="text-2xl font-bold text-white mb-6">
                  {activeRole === 'authority' ? 'Infrastructure Status' : 'Device Management'}
                </h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {sampleDevices.map((device, index) => (
                    <DeviceCard key={device.id} device={device} index={index} />
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'alerts' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <h2 className="text-2xl font-bold text-white mb-6">
                  {activeRole === 'citizen' && 'Public Safety Alerts'}
                  {activeRole === 'authority' && 'Compliance & Safety Alerts'}
                  {activeRole === 'operator' && 'Technical & Maintenance Alerts'}
                </h2>
                <div className="space-y-4">
                  {(() => {
                    // Filter alerts based on role
                    if (activeRole === 'citizen') {
                      // Citizens see only public safety alerts
                      return sampleAlerts.filter(alert => 
                        alert.message.includes('Turbidity') || alert.message.includes('quality')
                      );
                    } else {
                      // Authorities and operators see all alerts
                      return sampleAlerts;
                    }
                  })().map((alert, index) => (
                    <AlertCard key={alert.id} alert={alert} index={index} />
                  ))}
                </div>
              </motion.div>
            )}
          </div>
        </main>

        {/* Footer with Demo Notice */}
        <footer className="bg-slate-800/50 backdrop-blur-sm border-t border-slate-700/50 px-6 py-4">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4 text-gray-400">
              <span>🔒 Tamper-evident ledger active</span>
              <span>📡 Real-time monitoring enabled</span>
              <span>🤖 AI insights processing</span>
            </div>
            <button
              onClick={onBackToLanding}
              className="bg-aqua-600 hover:bg-aqua-700 text-white px-6 py-2 rounded-lg transition-colors duration-200"
            >
              Get Started with AquaChain
            </button>
          </div>
        </footer>
      </motion.div>
    </AnimatePresence>
  );
};

export default DemoDashboardViewer;