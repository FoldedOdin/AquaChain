import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ArrowLeftIcon,
  ExclamationTriangleIcon,
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
  Minus,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface DemoDashboardViewerProps {
  isOpen: boolean;
  onClose: () => void;
  onBackToLanding: () => void;
}

interface WaterQualityData {
  id: string;
  parameter: string;
  value: number;
  unit: string;
  status: 'excellent' | 'good' | 'fair' | 'poor';
  threshold: number;
  trend: number;
  color: string;
  lastUpdated: string;
  sparklineData: number[];
}

interface DeviceStatus {
  id: string;
  name: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance';
  batteryLevel: number;
  lastSeen: string;
  coordinates: { lat: number; lng: number };
}

interface Alert {
  id: string;
  type: 'warning' | 'critical' | 'info';
  message: string;
  timestamp: string;
  deviceId: string;
  resolved: boolean;
  priority: 'low' | 'medium' | 'high';
}



// Function to generate time-based data - creates different datasets for each time range
const generateTimeBasedData = (timeRange: string): WaterQualityData[] => {
  const baseData = [
    {
      id: 'wqi',
      parameter: 'Water Quality Index',
      value: 85.3,
      unit: '',
      status: 'good' as const,
      threshold: 90,
      trend: 2.5,
      color: '#06b6d4',
      lastUpdated: '2 minutes ago',
      sparklineData: [82, 83, 84, 85, 86, 85, 84, 85, 86, 85]
    },
    {
      id: 'ph',
      parameter: 'pH Level',
      value: 7.2,
      unit: 'pH',
      status: 'excellent' as const,
      threshold: 7.5,
      trend: -0.3,
      color: '#10b981',
      lastUpdated: '2 minutes ago',
      sparklineData: [7.3, 7.2, 7.1, 7.2, 7.3, 7.2, 7.1, 7.2, 7.2, 7.2]
    },
    {
      id: 'turbidity',
      parameter: 'Turbidity',
      value: 3.8,
      unit: 'NTU',
      status: 'good' as const,
      threshold: 5.0,
      trend: 0,
      color: '#8b5cf6',
      lastUpdated: '3 minutes ago',
      sparklineData: [3.9, 3.8, 3.7, 3.8, 3.9, 3.8, 3.7, 3.8, 3.8, 3.8]
    },
    {
      id: 'do',
      parameter: 'Dissolved Oxygen',
      value: 8.5,
      unit: 'mg/L',
      status: 'excellent' as const,
      threshold: 6.0,
      trend: 1.2,
      color: '#10b981',
      lastUpdated: '1 minute ago',
      sparklineData: [8.2, 8.3, 8.4, 8.5, 8.6, 8.5, 8.4, 8.5, 8.6, 8.5]
    },
    {
      id: 'chlorine',
      parameter: 'Chlorine',
      value: 0.8,
      unit: 'mg/L',
      status: 'good' as const,
      threshold: 1.0,
      trend: -0.5,
      color: '#06b6d4',
      lastUpdated: '2 minutes ago',
      sparklineData: [0.9, 0.8, 0.7, 0.8, 0.9, 0.8, 0.7, 0.8, 0.8, 0.8]
    },
    {
      id: 'tds',
      parameter: 'Total Dissolved Solids',
      value: 245,
      unit: 'ppm',
      status: 'excellent' as const,
      threshold: 500,
      trend: 0.8,
      color: '#10b981',
      lastUpdated: '4 minutes ago',
      sparklineData: [240, 242, 244, 245, 246, 245, 244, 245, 246, 245]
    }
  ];

  // Modify data based on time range
  return baseData.map(param => {
    const baseParam = { ...param };
    
    switch (timeRange) {
      case '1day':
        // Current data (no changes)
        return {
          ...baseParam,
          lastUpdated: 'Just now'
        };
        
      case '7days':
        // Slightly different values for 7-day view
        return {
          ...baseParam,
          value: Number((param.value * (0.95 + Math.random() * 0.1)).toFixed(1)),
          trend: Number((param.trend + (Math.random() - 0.5) * 2).toFixed(1)),
          lastUpdated: '1 week average',
          sparklineData: Array.from({ length: 7 }, () => 
            param.value * (0.9 + Math.random() * 0.2)
          )
        };
        
      case '30days':
        // Monthly averages with more variation
        return {
          ...baseParam,
          value: Number((param.value * (0.9 + Math.random() * 0.2)).toFixed(1)),
          trend: Number((param.trend + (Math.random() - 0.5) * 4).toFixed(1)),
          lastUpdated: '30 day average',
          sparklineData: Array.from({ length: 10 }, () => 
            param.value * (0.85 + Math.random() * 0.3)
          )
        };
        
      default:
        return baseParam;
    }
  });
};


const sampleDevices: DeviceStatus[] = [
  {
    id: 'AQ-001',
    name: 'Main Reservoir Sensor',
    location: 'North Reservoir',
    status: 'online',
    batteryLevel: 87,
    lastSeen: '1 minute ago',
    coordinates: { lat: 40.7128, lng: -74.0060 }
  },
  {
    id: 'AQ-002', 
    name: 'Distribution Point A',
    location: 'Downtown District',
    status: 'online',
    batteryLevel: 92,
    lastSeen: '2 minutes ago',
    coordinates: { lat: 40.7589, lng: -73.9851 }
  },
  {
    id: 'AQ-003',
    name: 'Treatment Plant Outlet',
    location: 'Water Treatment Facility',
    status: 'maintenance',
    batteryLevel: 45,
    lastSeen: '15 minutes ago',
    coordinates: { lat: 40.6892, lng: -74.0445 }
  },
  {
    id: 'AQ-004',
    name: 'Backup Monitoring Station',
    location: 'East Side District',
    status: 'online',
    batteryLevel: 78,
    lastSeen: '3 minutes ago',
    coordinates: { lat: 40.7282, lng: -73.7949 }
  }
];

const sampleAlerts: Alert[] = [
  {
    id: 'alert-001',
    type: 'warning',
    message: 'Turbidity levels slightly elevated at Distribution Point A',
    timestamp: '5 minutes ago',
    deviceId: 'AQ-002',
    resolved: false,
    priority: 'medium'
  },
  {
    id: 'alert-002',
    type: 'critical',
    message: 'Device AQ-003 requires maintenance - low battery detected',
    timestamp: '15 minutes ago',
    deviceId: 'AQ-003',
    resolved: false,
    priority: 'high'
  },
  {
    id: 'alert-003',
    type: 'info',
    message: 'Scheduled maintenance completed at North Reservoir',
    timestamp: '1 hour ago',
    deviceId: 'AQ-001',
    resolved: true,
    priority: 'low'
  }
];

// Status Badge Component following style guide
const StatusBadge: React.FC<{ status: string; children: React.ReactNode }> = ({ status, children }) => {
  const styles = {
    excellent: 'bg-green-100 text-green-800 border-green-200',
    good: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    fair: 'bg-amber-100 text-amber-800 border-amber-200',
    poor: 'bg-red-100 text-red-800 border-red-200',
  };
  
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${styles[status as keyof typeof styles] || styles.good}`}>
      {children}
    </span>
  );
};

// Trend Indicator Component
const TrendIndicator: React.FC<{ value: number; compact?: boolean }> = ({ value, compact = false }) => {
  const isPositive = value > 0;
  const isNegative = value < 0;
  const isStable = value === 0;

  if (compact) {
    return (
      <div className={`inline-flex items-center gap-1 text-xs font-semibold ${
        isPositive ? 'text-green-600' :
        isNegative ? 'text-red-600' :
        'text-gray-600'
      }`}>
        {isPositive && <TrendingUp className="w-3 h-3" />}
        {isNegative && <TrendingDown className="w-3 h-3" />}
        {isStable && <Minus className="w-3 h-3" />}
        <span>{Math.abs(value)}%</span>
      </div>
    );
  }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold ${
      isPositive ? 'bg-green-100 text-green-700' :
      isNegative ? 'bg-red-100 text-red-700' :
      'bg-gray-100 text-gray-700'
    }`}>
      {isPositive && <TrendingUp className="w-4 h-4" />}
      {isNegative && <TrendingDown className="w-4 h-4" />}
      {isStable && <Minus className="w-4 h-4" />}
      <span>{isPositive ? '+' : ''}{value}%</span>
      <span className="text-xs font-normal opacity-75">vs last period</span>
    </div>
  );
};

// Water Quality Card following style guide
const WaterQualityCard: React.FC<{ data: WaterQualityData; index: number }> = ({ data, index }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'excellent': return <CheckCircleSolid className="w-5 h-5 text-green-500" />;
      case 'good': return <CheckCircleSolid className="w-5 h-5 text-cyan-500" />;
      case 'fair': return <ExclamationTriangleSolid className="w-5 h-5 text-amber-500" />;
      case 'poor': return <ExclamationTriangleSolid className="w-5 h-5 text-red-500" />;
      default: return <CheckCircleSolid className="w-5 h-5 text-cyan-500" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="text-sm font-medium text-gray-600 mb-1">
            {data.parameter}
          </div>
          <div className="text-3xl font-bold text-gray-900 tabular-nums">
            {data.value}
            <span className="text-base text-gray-500 ml-2 font-normal">
              {data.unit}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={data.status}>
            {getStatusIcon(data.status)}
            <span className="ml-1 capitalize">{data.status}</span>
          </StatusBadge>
          <TrendIndicator value={data.trend} compact />
        </div>
      </div>

      {/* Sparkline SVG */}
      <svg className="w-full h-16 mb-3" viewBox="0 0 200 60" preserveAspectRatio="none">
        <defs>
          <linearGradient id={`gradient-${data.id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={data.color} stopOpacity="0.3"/>
            <stop offset="100%" stopColor={data.color} stopOpacity="0"/>
          </linearGradient>
        </defs>
        
        <path
          d="M0,40 L20,35 L40,38 L60,32 L80,30 L100,28 L120,25 L140,27 L160,24 L180,20 L200,18 L200,60 L0,60 Z"
          fill={`url(#gradient-${data.id})`}
        />
        
        <path
          d="M0,40 L20,35 L40,38 L60,32 L80,30 L100,28 L120,25 L140,27 L160,24 L180,20 L200,18"
          stroke={data.color}
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        <circle cx="200" cy="18" r="4" fill={data.color} />
      </svg>

      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>Threshold: {data.threshold} {data.unit}</span>
        <span className="flex items-center gap-1">
          <ClockIcon className="w-4 h-4" />
          <span>{data.lastUpdated}</span>
        </span>
      </div>
    </motion.div>
  );
};

const DeviceCard: React.FC<{ device: DeviceStatus; index: number }> = ({ device, index }) => {
  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'online': return {
        badge: 'bg-green-100 text-green-800 border-green-200',
        indicator: 'bg-green-500',
        animation: 'animate-pulse-subtle'
      };
      case 'offline': return {
        badge: 'bg-red-100 text-red-800 border-red-200',
        indicator: 'bg-red-500',
        animation: ''
      };
      case 'maintenance': return {
        badge: 'bg-amber-100 text-amber-800 border-amber-200',
        indicator: 'bg-amber-500',
        animation: 'animate-pulse'
      };
      default: return {
        badge: 'bg-gray-100 text-gray-800 border-gray-200',
        indicator: 'bg-gray-500',
        animation: ''
      };
    }
  };

  const getBatteryStyles = (level: number) => {
    if (level > 60) return 'text-green-600 bg-green-50';
    if (level > 30) return 'text-amber-600 bg-amber-50';
    return 'text-red-600 bg-red-50';
  };

  const statusStyles = getStatusStyles(device.status);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-aqua-100 rounded-lg">
              <Activity className="w-5 h-5 text-aqua-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{device.name}</h3>
              <p className="text-sm text-gray-600 flex items-center gap-1">
                <MapPinIcon className="w-4 h-4" />
                <span>{device.location}</span>
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex flex-col items-end gap-2">
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border ${statusStyles.badge}`}>
            <div className={`w-2 h-2 rounded-full ${statusStyles.indicator} ${statusStyles.animation}`} />
            <span className="capitalize">{device.status}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="bg-gray-50 rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-1">Device ID</div>
          <div className="font-mono text-sm font-semibold text-gray-900">{device.id}</div>
        </div>
        <div className={`rounded-lg p-3 ${getBatteryStyles(device.batteryLevel)}`}>
          <div className="text-xs mb-1">Battery Level</div>
          <div className="font-bold text-lg tabular-nums">{device.batteryLevel}%</div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">Last seen:</span>
        <span className="font-medium text-gray-900">{device.lastSeen}</span>
      </div>

      {/* Connection strength indicator */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-600">Signal Strength</span>
          <span className="text-xs font-medium text-gray-900">Strong</span>
        </div>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((bar) => (
            <div
              key={bar}
              className={`h-2 flex-1 rounded-sm ${
                bar <= 4 ? 'bg-green-500' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};

const AlertCard: React.FC<{ alert: Alert; index: number }> = ({ alert, index }) => {
  const getAlertStyles = (type: string, resolved: boolean) => {
    if (resolved) {
      return {
        container: 'bg-gray-50 border-gray-200',
        icon: 'text-gray-500',
        iconBg: 'bg-gray-100',
        title: 'text-gray-700',
        badge: 'bg-gray-100 text-gray-700'
      };
    }

    switch (type) {
      case 'critical': return {
        container: 'bg-red-50 border-red-200 animate-alert-pulse',
        icon: 'text-red-600',
        iconBg: 'bg-red-100',
        title: 'text-red-900',
        badge: 'bg-red-100 text-red-800'
      };
      case 'warning': return {
        container: 'bg-amber-50 border-amber-200',
        icon: 'text-amber-600',
        iconBg: 'bg-amber-100',
        title: 'text-amber-900',
        badge: 'bg-amber-100 text-amber-800'
      };
      case 'info': return {
        container: 'bg-blue-50 border-blue-200',
        icon: 'text-blue-600',
        iconBg: 'bg-blue-100',
        title: 'text-blue-900',
        badge: 'bg-blue-100 text-blue-800'
      };
      default: return {
        container: 'bg-gray-50 border-gray-200',
        icon: 'text-gray-600',
        iconBg: 'bg-gray-100',
        title: 'text-gray-900',
        badge: 'bg-gray-100 text-gray-800'
      };
    }
  };

  const getAlertIcon = (type: string, resolved: boolean) => {
    if (resolved) return <CheckCircleSolid className="w-5 h-5" />;
    
    switch (type) {
      case 'critical': return <ExclamationTriangleSolid className="w-5 h-5" />;
      case 'warning': return <ExclamationTriangleSolid className="w-5 h-5" />;
      case 'info': return <CheckCircleSolid className="w-5 h-5" />;
      default: return <AlertCircle className="w-5 h-5" />;
    }
  };

  const getPriorityBadge = (priority: string) => {
    const styles = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-amber-100 text-amber-800',
      low: 'bg-green-100 text-green-800'
    };
    return styles[priority as keyof typeof styles] || styles.medium;
  };

  const alertStyles = getAlertStyles(alert.type, alert.resolved);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className={`border rounded-xl p-4 ${alertStyles.container} transition-all duration-300`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-2 rounded-lg ${alertStyles.iconBg}`}>
          <div className={alertStyles.icon}>
            {getAlertIcon(alert.type, alert.resolved)}
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3 mb-2">
            <p className={`font-medium ${alertStyles.title}`}>
              {alert.message}
            </p>
            <div className="flex gap-2 flex-shrink-0">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${getPriorityBadge(alert.priority)}`}>
                {alert.priority.toUpperCase()}
              </span>
              {alert.resolved && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                  RESOLVED
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="flex items-center gap-1">
              <Activity className="w-4 h-4" />
              Device: {alert.deviceId}
            </span>
            <span className="flex items-center gap-1">
              <ClockIcon className="w-4 h-4" />
              {alert.timestamp}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// Time Range Selector Component
const TimeRangeSelector: React.FC<{ value: string; onChange: (value: string) => void }> = ({ value, onChange }) => {
  const ranges = [
    { value: '1day', label: '24 Hours', description: 'Real-time data' },
    { value: '7days', label: '7 Days', description: 'Weekly trends' },
    { value: '30days', label: '30 Days', description: 'Monthly averages' },
  ];

  return (
    <div className="inline-flex bg-gray-100 p-1 rounded-lg gap-1">
      {ranges.map(range => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
            value === range.value
              ? 'bg-white text-aqua-600 shadow-sm font-semibold'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          }`}
          title={range.description}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
};

// Animated Status Card for WQI
const AnimatedStatusCard: React.FC<{ wqi: number; location: string; lastUpdate: string }> = ({ wqi, location, lastUpdate }) => {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = wqi;
    const duration = 1000;
    const increment = end / (duration / 16);

    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setDisplayValue(end);
        clearInterval(timer);
      } else {
        setDisplayValue(Math.floor(start));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [wqi]);

  const getStatus = (value: number) => {
    if (value >= 90) return {
      text: 'Excellent',
      color: 'green',
      gradient: 'from-green-500 to-green-600',
      icon: CheckCircleSolid
    };
    if (value >= 70) return {
      text: 'Good',
      color: 'cyan',
      gradient: 'from-cyan-500 to-cyan-600',
      icon: CheckCircleSolid
    };
    if (value >= 50) return {
      text: 'Fair',
      color: 'amber',
      gradient: 'from-amber-500 to-amber-600',
      icon: ExclamationTriangleSolid
    };
    return {
      text: 'Poor',
      color: 'red',
      gradient: 'from-red-500 to-red-600',
      icon: ExclamationTriangleSolid
    };
  };

  const status = getStatus(wqi);
  const StatusIcon = status.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
    >
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-aqua-100 rounded-lg">
              <Droplet className="w-6 h-6 text-aqua-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900">Water Quality</h3>
          </div>
          <div className="inline-flex items-center gap-2 bg-aqua-50 px-3 py-1.5 rounded-full text-sm font-medium text-aqua-900 animate-pulse-subtle">
            <MapPinIcon className="w-4 h-4" />
            <span>{location}</span>
          </div>
        </div>

        <div className="text-center py-8">
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{
              type: "spring",
              stiffness: 200,
              damping: 20,
              delay: 0.2
            }}
            className={`text-7xl font-display font-extrabold bg-gradient-to-br ${status.gradient} bg-clip-text text-transparent mb-4`}
          >
            {displayValue}
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className={`inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-br ${status.gradient} text-white shadow-lg`}
          >
            <StatusIcon className="w-5 h-5" />
            <span className="font-semibold text-lg">{status.text}</span>
          </motion.div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-100 flex items-center justify-center gap-2 text-sm text-gray-600">
          <span>Last updated:</span>
          <span className="font-medium text-gray-900">{lastUpdate}</span>
        </div>
      </div>
    </motion.div>
  );
};

/**
 * Demo Dashboard Viewer Component
 * Redesigned following the comprehensive style guide
 * Features role-based dashboards, time-series data, and modern animations
 */
const DemoDashboardViewer: React.FC<DemoDashboardViewerProps> = ({
  isOpen,
  onClose,
  onBackToLanding
}) => {
  const [activeRole, setActiveRole] = useState<'citizen' | 'field-technician' | 'lab-analyst' | 'auditor'>('citizen');
  const [activeTab, setActiveTab] = useState<'overview' | 'devices' | 'alerts'>('overview');
  const [timeRange, setTimeRange] = useState('1day');
  const [currentData, setCurrentData] = useState<WaterQualityData[]>([]);
  const [updatedCells, setUpdatedCells] = useState(new Set<string>());
  const [showScrollIndicator, setShowScrollIndicator] = useState(true);
  const [scrollY, setScrollY] = useState(0);
  const [isDataLoading, setIsDataLoading] = useState(false);

  // Reset to default state when opening
  useEffect(() => {
    if (isOpen) {
      setActiveRole('citizen');
      setActiveTab('overview');
      setTimeRange('1day');
    }
  }, [isOpen]);

  // Update data when time range changes
  useEffect(() => {
    if (isOpen) {
      setIsDataLoading(true);
      
      // Simulate API call delay
      const timer = setTimeout(() => {
        const newData = generateTimeBasedData(timeRange);
        setCurrentData(newData);
        setIsDataLoading(false);
      }, 300);

      return () => clearTimeout(timer);
    }
  }, [timeRange, isOpen]);

  // Simulate real-time data updates
  useEffect(() => {
    if (!isOpen || timeRange !== '1day') return; // Only update for real-time data

    const interval = setInterval(() => {
      // Simulate random parameter updates
      const randomIndex = Math.floor(Math.random() * currentData.length);
      const cellId = `${randomIndex}-value`;
      
      setUpdatedCells(prev => new Set(prev).add(cellId));
      
      // Update the actual data slightly for real-time effect
      if (timeRange === '1day') {
        setCurrentData(prev => prev.map((item, index) => {
          if (index === randomIndex) {
            const variation = (Math.random() - 0.5) * 0.1;
            return {
              ...item,
              value: Number((item.value * (1 + variation)).toFixed(1)),
              lastUpdated: 'Just now'
            };
          }
          return item;
        }));
      }
      
      setTimeout(() => {
        setUpdatedCells(prev => {
          const newSet = new Set(prev);
          newSet.delete(cellId);
          return newSet;
        });
      }, 800);
    }, 5000);

    return () => clearInterval(interval);
  }, [isOpen, timeRange, currentData.length]);

  // Handle scroll events for scroll indicator
  useEffect(() => {
    if (!isOpen) return;

    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target && target.classList.contains('dashboard-main-content')) {
        const scrollTop = target.scrollTop;
        const scrollHeight = target.scrollHeight;
        const clientHeight = target.clientHeight;
        
        setScrollY(scrollTop);
        
        // Hide scroll indicator after scrolling down 200px or reaching near bottom
        const shouldHideIndicator = scrollTop > 200 || (scrollTop + clientHeight >= scrollHeight - 100);
        setShowScrollIndicator(!shouldHideIndicator);
      }
    };

    // Add a small delay to ensure the DOM is ready
    const timer = setTimeout(() => {
      const mainElement = document.querySelector('.dashboard-main-content');
      if (mainElement) {
        mainElement.addEventListener('scroll', handleScroll);
      }
    }, 100);

    return () => {
      clearTimeout(timer);
      const mainElement = document.querySelector('.dashboard-main-content');
      if (mainElement) {
        mainElement.removeEventListener('scroll', handleScroll);
      }
    };
  }, [isOpen]);

  // Scroll down function
  const scrollToContent = () => {
    const mainElement = document.querySelector('.dashboard-main-content');
    if (mainElement) {
      mainElement.scrollTo({
        top: 400,
        behavior: 'smooth'
      });
    }
  };

  // Scroll to top function
  const scrollToTop = () => {
    const mainElement = document.querySelector('.dashboard-main-content');
    if (mainElement) {
      mainElement.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  // Auto-scroll to top when changing tabs or roles
  useEffect(() => {
    const mainElement = document.querySelector('.dashboard-main-content');
    if (mainElement && isOpen) {
      mainElement.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  }, [activeTab, activeRole, isOpen]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-gray-50 flex flex-col"
      >
        {/* Demo Watermark */}
        <motion.div 
          className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10"
          style={{ y: scrollY * 0.1 }}
        >
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-amber-100 border border-amber-300 text-amber-800 px-6 py-3 rounded-xl text-sm font-semibold shadow-lg backdrop-blur-sm"
          >
            🚧 DEMONSTRATION DATA - NOT REAL SENSOR READINGS
          </motion.div>
        </motion.div>

        {/* Role Selector */}
        <motion.div 
          className="absolute top-20 left-1/2 transform -translate-x-1/2 z-10"
          style={{ y: scrollY * 0.05 }}
        >
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-xl p-2 shadow-lg"
          >
            <div className="flex gap-2">
              {[
                { id: 'citizen', label: '👤 Citizen', desc: 'Public water quality info', icon: UserIcon, color: 'aqua' },
                { id: 'field-technician', label: '🔧 Field Tech', desc: 'Real-time monitoring', icon: WrenchScrewdriverIcon, color: 'cyan' },
                { id: 'lab-analyst', label: '🧪 Lab Analyst', desc: 'Detailed analysis', icon: ChartBarIcon, color: 'green' },
                { id: 'auditor', label: '🏛️ Auditor', desc: 'Compliance tracking', icon: BuildingOfficeIcon, color: 'purple' }
              ].map(({ id, label, desc, icon: Icon, color }) => (
                <button
                  key={id}
                  onClick={() => setActiveRole(id as 'citizen' | 'field-technician' | 'lab-analyst' | 'auditor')}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 group
                    ${activeRole === id 
                      ? `bg-${color}-500 text-white shadow-md` 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }
                  `}
                  title={desc}
                >
                  <Icon className="w-4 h-4" />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </motion.div>
        </motion.div>

        {/* Header */}
        <header className="bg-white/95 backdrop-blur-sm border-b border-gray-200 px-6 py-4 shadow-sm flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBackToLanding}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors duration-200 font-medium"
                aria-label="Back to landing page"
              >
                <ArrowLeftIcon className="w-5 h-5" />
                <span>Back to AquaChain</span>
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <div className="flex items-center gap-3">
                <div className="p-2 bg-aqua-100 rounded-lg">
                  <Droplet className="w-6 h-6 text-aqua-600" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    AquaChain Dashboard
                  </h1>
                  <p className="text-sm text-gray-600">
                    {activeRole === 'citizen' && '👤 Citizen View - Public water quality information'}
                    {activeRole === 'field-technician' && '🔧 Field Technician - Real-time monitoring dashboard'}
                    {activeRole === 'lab-analyst' && '🧪 Laboratory Analyst - Detailed analysis and reports'}
                    {activeRole === 'auditor' && '🏛️ Regulatory Auditor - Compliance tracking and oversight'}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="inline-flex items-center gap-2 bg-green-100 text-green-700 px-3 py-1.5 rounded-full text-sm font-medium">
                <div className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </div>
                Live Data
              </div>
              <button
                onClick={onClose}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                aria-label="Close demo"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex gap-2 mt-4">
            {(() => {
              const tabs = {
                citizen: [
                  { id: 'overview', label: 'Water Quality', icon: Droplet },
                  { id: 'alerts', label: 'Safety Alerts', icon: BellIcon }
                ],
                'field-technician': [
                  { id: 'overview', label: 'Real-Time Data', icon: Activity },
                  { id: 'devices', label: 'Equipment Status', icon: Cog6ToothIcon },
                  { id: 'alerts', label: 'Field Alerts', icon: ExclamationTriangleIcon }
                ],
                'lab-analyst': [
                  { id: 'overview', label: 'Analysis Dashboard', icon: ChartBarIcon },
                  { id: 'devices', label: 'Lab Equipment', icon: Cog6ToothIcon },
                  { id: 'alerts', label: 'Quality Alerts', icon: ExclamationTriangleIcon }
                ],
                auditor: [
                  { id: 'overview', label: 'Compliance Overview', icon: ChartBarIcon },
                  { id: 'devices', label: 'Infrastructure Audit', icon: Cog6ToothIcon },
                  { id: 'alerts', label: 'Compliance Alerts', icon: ExclamationTriangleIcon }
                ]
              };
              return tabs[activeRole];
            })().map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as 'overview' | 'devices' | 'alerts')}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 font-medium
                  ${activeTab === id 
                    ? 'bg-aqua-500 text-white shadow-md' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </header>

        {/* Scroll Down Indicator */}
        <AnimatePresence>
          {showScrollIndicator && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: 1.5 }}
              className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-20"
            >
              <motion.button
                onClick={scrollToContent}
                className="group flex flex-col items-center gap-2 bg-white/95 backdrop-blur-sm border border-gray-200 rounded-2xl px-6 py-4 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 hover:bg-white"
                aria-label="Scroll down to see more content"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span className="text-sm font-semibold text-gray-700 group-hover:text-aqua-600 transition-colors">
                  Explore Dashboard
                </span>
                <motion.div
                  animate={{ y: [0, 6, 0] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                  className="text-aqua-500 group-hover:text-aqua-600 transition-colors"
                >
                  <ChevronDown className="w-6 h-6" />
                </motion.div>
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Scroll Progress Indicator */}
        <div className="fixed top-0 left-0 w-full h-1 bg-gray-200/50 z-30">
          <motion.div
            className="h-full bg-gradient-to-r from-aqua-500 to-aqua-600 shadow-sm"
            initial={{ scaleX: 0 }}
            animate={{ 
              scaleX: Math.min(1, scrollY / Math.max(1, 2000)) // Approximate scroll height
            }}
            transition={{ duration: 0.1, ease: "easeOut" }}
            style={{ transformOrigin: "left" }}
          />
        </div>

        {/* Debug Scroll Position (remove in production) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="fixed top-4 right-4 z-40 bg-black/80 text-white px-3 py-1 rounded text-xs font-mono">
            Scroll: {Math.round(scrollY)}px
          </div>
        )}

        {/* Main Content */}
        <main className="dashboard-main-content flex-1 overflow-y-auto p-6 pt-8 scroll-smooth">
          <div className="max-w-7xl mx-auto">
            {/* Role Description */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 p-4 bg-white border border-gray-200 rounded-xl shadow-sm"
            >
              <p className="text-gray-700">
                {activeRole === 'citizen' && "👤 Citizen View: Access public water quality information for your area, view safety alerts, and understand water quality metrics that affect your daily life."}
                {activeRole === 'field-technician' && "🔧 Field Technician View: Real-time monitoring dashboard with live sensor data, equipment status, and field maintenance alerts for water system operations."}
                {activeRole === 'lab-analyst' && "🧪 Laboratory Analyst View: Detailed analysis dashboard with precision measurements, historical comparisons, and comprehensive reporting tools for water quality assessment."}
                {activeRole === 'auditor' && "🏛️ Regulatory Auditor View: Compliance tracking dashboard with audit trails, violation alerts, and regulatory oversight tools for water quality standards."}
              </p>
            </motion.div>

            {activeTab === 'overview' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <h2 className="text-2xl font-display font-bold text-gray-900 mb-1">
                      {activeRole === 'citizen' && 'Your Local Water Quality'}
                      {activeRole === 'field-technician' && 'Real-Time Water Quality Monitoring'}
                      {activeRole === 'lab-analyst' && 'Laboratory Analysis Dashboard'}
                      {activeRole === 'auditor' && 'Compliance Monitoring Overview'}
                    </h2>
                    <p className="text-sm text-gray-600">
                      {timeRange === '1day' && 'Real-time parameter tracking'}
                      {timeRange === '7days' && 'Weekly trend analysis'}
                      {timeRange === '30days' && 'Monthly performance overview'}
                      {' '}for {activeRole.replace('-', ' ')}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <TimeRangeSelector value={timeRange} onChange={setTimeRange} />
                    {isDataLoading ? (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <div className="w-4 h-4 border-2 border-aqua-200 border-t-aqua-500 rounded-full animate-spin" />
                        <span>Updating data...</span>
                      </div>
                    ) : (
                      <div className="text-sm text-gray-500">
                        {timeRange === '1day' && 'Updated just now'}
                        {timeRange === '7days' && 'Data from last 7 days'}
                        {timeRange === '30days' && 'Data from last 30 days'}
                      </div>
                    )}
                  </div>
                </div>

                {/* Hero WQI Card for Citizens */}
                {activeRole === 'citizen' && (
                  <div className="mb-8">
                    <AnimatedStatusCard 
                      wqi={currentData.find(d => d.id === 'wqi')?.value || 85.3} 
                      location="Downtown District" 
                      lastUpdate={
                        timeRange === '1day' ? '2 minutes ago' :
                        timeRange === '7days' ? '7-day average' :
                        '30-day average'
                      } 
                    />
                  </div>
                )}

                {/* Parameter Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {(() => {
                    // Filter data based on role following style guide
                    if (activeRole === 'citizen') {
                      // Citizens see basic quality parameters
                      return currentData.filter(d => 
                        ['pH Level', 'Chlorine', 'Turbidity', 'Dissolved Oxygen'].includes(d.parameter)
                      );
                    } else if (activeRole === 'field-technician') {
                      // Field technicians see real-time operational data
                      return currentData.filter(d => 
                        ['Water Quality Index', 'pH Level', 'Turbidity', 'Dissolved Oxygen', 'Chlorine'].includes(d.parameter)
                      );
                    } else if (activeRole === 'lab-analyst') {
                      // Lab analysts see all technical data
                      return currentData;
                    } else {
                      // Auditors see compliance-focused data
                      return currentData.filter(d => 
                        ['Water Quality Index', 'pH Level', 'Dissolved Oxygen', 'Total Dissolved Solids'].includes(d.parameter)
                      );
                    }
                  })().map((data, index) => (
                    <motion.div
                      key={`${data.parameter}-${timeRange}`}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05, duration: 0.3 }}
                    >
                      <WaterQualityCard data={data} index={0} />
                    </motion.div>
                  ))}
                </div>

                {/* Real-time Data Table for Lab Analysts */}
                {activeRole === 'lab-analyst' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden"
                  >
                    <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                        Precision Measurements
                        <span className="inline-flex items-center gap-1.5 text-xs font-normal bg-green-100 text-green-700 px-2 py-1 rounded-full">
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                          </span>
                          Live
                        </span>
                      </h3>
                    </div>
                    
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-gradient-to-b from-gray-50 to-gray-100 border-b border-gray-200">
                          <tr>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Parameter</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Current Value</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Unit</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Status</th>
                            <th className="px-6 py-4 text-left text-sm font-semibold text-gray-700">Trend</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {currentData.map((param, index) => (
                            <motion.tr
                              key={param.id}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.05 }}
                              className="hover:bg-gray-50 transition-colors"
                            >
                              <td className="px-6 py-4 text-sm font-medium text-gray-900">
                                {param.parameter}
                              </td>
                              <td className={`px-6 py-4 text-sm text-gray-700 font-mono tabular-nums ${
                                updatedCells.has(`${index}-value`) ? 'animate-data-update' : ''
                              }`}>
                                {param.value}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-600">
                                {param.unit}
                              </td>
                              <td className="px-6 py-4">
                                <StatusBadge status={param.status}>
                                  <span className="capitalize">{param.status}</span>
                                </StatusBadge>
                              </td>
                              <td className="px-6 py-4">
                                <TrendIndicator value={param.trend} compact />
                              </td>
                            </motion.tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {activeTab === 'devices' && (activeRole === 'field-technician' || activeRole === 'lab-analyst' || activeRole === 'auditor') && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-2xl font-display font-bold text-gray-900 mb-1">
                      {activeRole === 'field-technician' && 'Equipment Status & Maintenance'}
                      {activeRole === 'lab-analyst' && 'Laboratory Equipment Management'}
                      {activeRole === 'auditor' && 'Infrastructure Audit & Compliance'}
                    </h2>
                    <p className="text-sm text-gray-600">
                      Monitor device health, battery levels, and connectivity status
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-gray-600">
                      <span className="font-medium text-green-600">{sampleDevices.filter(d => d.status === 'online').length}</span> Online
                      <span className="mx-2">•</span>
                      <span className="font-medium text-amber-600">{sampleDevices.filter(d => d.status === 'maintenance').length}</span> Maintenance
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {sampleDevices.map((device, index) => (
                    <DeviceCard key={device.id} device={device} index={index} />
                  ))}
                </div>

                {/* Device Summary for Auditors */}
                {activeRole === 'auditor' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Infrastructure Compliance Summary</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <CheckCircleSolid className="w-5 h-5 text-green-600" />
                          <span className="font-semibold text-green-900">Compliant Devices</span>
                        </div>
                        <div className="text-2xl font-bold text-green-900">
                          {sampleDevices.filter(d => d.status === 'online').length}
                        </div>
                        <div className="text-sm text-green-700">Operating within standards</div>
                      </div>
                      
                      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <ExclamationTriangleSolid className="w-5 h-5 text-amber-600" />
                          <span className="font-semibold text-amber-900">Requires Attention</span>
                        </div>
                        <div className="text-2xl font-bold text-amber-900">
                          {sampleDevices.filter(d => d.status === 'maintenance').length}
                        </div>
                        <div className="text-sm text-amber-700">Maintenance scheduled</div>
                      </div>
                      
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <ChartBarIcon className="w-5 h-5 text-blue-600" />
                          <span className="font-semibold text-blue-900">Audit Score</span>
                        </div>
                        <div className="text-2xl font-bold text-blue-900">94%</div>
                        <div className="text-sm text-blue-700">Overall compliance rating</div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {activeTab === 'alerts' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="space-y-6"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-2xl font-display font-bold text-gray-900 mb-1">
                      {activeRole === 'citizen' && 'Public Safety Alerts'}
                      {activeRole === 'field-technician' && 'Field Operations Alerts'}
                      {activeRole === 'lab-analyst' && 'Quality Control Alerts'}
                      {activeRole === 'auditor' && 'Compliance & Regulatory Alerts'}
                    </h2>
                    <p className="text-sm text-gray-600">
                      Monitor system alerts and notifications relevant to your role
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-gray-600">
                      <span className="font-medium text-red-600">
                        {sampleAlerts.filter(a => a.type === 'critical' && !a.resolved).length}
                      </span> Critical
                      <span className="mx-2">•</span>
                      <span className="font-medium text-amber-600">
                        {sampleAlerts.filter(a => a.type === 'warning' && !a.resolved).length}
                      </span> Warning
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {(() => {
                    // Filter alerts based on role
                    if (activeRole === 'citizen') {
                      // Citizens see only public safety alerts
                      return sampleAlerts.filter(alert => 
                        alert.message.includes('Turbidity') || alert.message.includes('quality') || alert.priority === 'high'
                      );
                    } else if (activeRole === 'field-technician') {
                      // Field technicians see operational and maintenance alerts
                      return sampleAlerts.filter(alert =>
                        alert.message.includes('maintenance') || alert.message.includes('battery') || alert.type === 'critical'
                      );
                    } else if (activeRole === 'lab-analyst') {
                      // Lab analysts see quality-related alerts
                      return sampleAlerts.filter(alert =>
                        alert.message.includes('Turbidity') || alert.message.includes('quality') || alert.message.includes('maintenance')
                      );
                    } else {
                      // Auditors see all alerts for compliance tracking
                      return sampleAlerts;
                    }
                  })().map((alert, index) => (
                    <AlertCard key={alert.id} alert={alert} index={index} />
                  ))}
                </div>

                {/* Alert Summary for Auditors */}
                {activeRole === 'auditor' && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Alert Audit Trail</h3>
                    <div className="space-y-3">
                      {[
                        { action: 'Alert Generated', time: '15 minutes ago', user: 'System', details: 'Low battery alert for AQ-003' },
                        { action: 'Alert Acknowledged', time: '12 minutes ago', user: 'Field Tech #1', details: 'Maintenance scheduled' },
                        { action: 'Quality Check', time: '5 minutes ago', user: 'Lab Analyst', details: 'Turbidity levels verified' },
                        { action: 'Compliance Review', time: '2 minutes ago', user: 'Auditor', details: 'Standards compliance confirmed' }
                      ].map((entry, index) => (
                        <div key={index} className="bg-purple-50 border-l-4 border-purple-500 p-4 hover:bg-purple-100 hover:border-l-[6px] hover:pl-[22px] transition-all duration-200 rounded-r-lg">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-900">{entry.action}</span>
                            <span className="text-xs text-gray-500">{entry.time}</span>
                          </div>
                          <div className="text-sm text-gray-600 mt-1">
                            <span className="font-medium">{entry.user}:</span> {entry.details}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}

            {/* Additional Content Section for Scrolling */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="mt-12 space-y-6"
            >
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Total Sensors</div>
                    <div className="text-2xl font-bold text-gray-900">24</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Data Points Today</div>
                    <div className="text-2xl font-bold text-gray-900">1,247</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Uptime</div>
                    <div className="text-2xl font-bold text-gray-900">99.8%</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  {[
                    { time: '2 minutes ago', action: 'Water quality data updated', status: 'success' },
                    { time: '5 minutes ago', action: 'Sensor AQ-002 maintenance completed', status: 'info' },
                    { time: '12 minutes ago', action: 'Alert resolved: Turbidity levels normalized', status: 'success' },
                    { time: '1 hour ago', action: 'Daily compliance report generated', status: 'info' },
                    { time: '2 hours ago', action: 'System backup completed successfully', status: 'success' }
                  ].map((activity, index) => (
                    <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          activity.status === 'success' ? 'bg-green-500' : 'bg-blue-500'
                        }`} />
                        <span className="text-sm text-gray-700">{activity.action}</span>
                      </div>
                      <span className="text-xs text-gray-500">{activity.time}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Spacer to ensure scroll functionality */}
              <div className="h-32"></div>
            </motion.div>
          </div>
        </main>

        {/* Back to Top Button */}
        <AnimatePresence>
          {scrollY > 300 && (
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={scrollToTop}
              className="fixed bottom-8 right-8 z-20 bg-aqua-500 hover:bg-aqua-600 text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 group"
              aria-label="Scroll back to top"
            >
              <motion.div
                animate={{ y: [0, -2, 0] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
              >
                <ChevronUp className="w-5 h-5" />
              </motion.div>
            </motion.button>
          )}
        </AnimatePresence>

        {/* Footer with Demo Notice */}
        <footer className="bg-white/95 backdrop-blur-sm border-t border-gray-200 px-6 py-4 shadow-sm flex-shrink-0">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
            <div className="flex flex-wrap items-center gap-4 text-gray-600">
              <span className="flex items-center gap-1">
                🔒 <span className="font-medium">Tamper-evident ledger active</span>
              </span>
              <span className="flex items-center gap-1">
                📡 <span className="font-medium">Real-time monitoring enabled</span>
              </span>
              <span className="flex items-center gap-1">
                🤖 <span className="font-medium">AI insights processing</span>
              </span>
            </div>
            <button
              onClick={onBackToLanding}
              className="bg-gradient-to-r from-aqua-500 to-aqua-600 hover:from-aqua-600 hover:to-aqua-700 text-white font-semibold px-6 py-3 rounded-lg shadow-lg shadow-aqua-500/30 hover:shadow-xl hover:shadow-aqua-500/40 transition-all duration-300"
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