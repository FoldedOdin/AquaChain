import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { MapPin, Navigation, Clock, AlertTriangle, CheckCircle, Filter } from 'lucide-react';

interface Task {
  taskId: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  location: {
    address: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  dueDate?: string;
  consumer?: {
    name: string;
  };
}

interface MapModalProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: Task[];
}

const MapModal: React.FC<MapModalProps> = ({ isOpen, onClose, tasks }) => {
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [mapView, setMapView] = useState<'list' | 'map'>('list');

  // Get current location
  useEffect(() => {
    if (isOpen && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.log('Geolocation not available:', error);
          // Default to a central location if geolocation fails
          setCurrentLocation({ lat: 37.7749, lng: -122.4194 });
        }
      );
    }
  }, [isOpen]);

  // Filter tasks
  const filteredTasks = useMemo(() => {
    if (filterStatus === 'all') return tasks;
    return tasks.filter(task => task.status === filterStatus);
  }, [tasks, filterStatus]);

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'assigned': return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'accepted': return 'bg-green-100 text-green-800 border-green-300';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'completed': return 'bg-gray-100 text-gray-800 border-gray-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-orange-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'in_progress': return <Clock className="w-4 h-4" />;
      case 'assigned': return <AlertTriangle className="w-4 h-4" />;
      default: return <MapPin className="w-4 h-4" />;
    }
  };

  // Calculate distance (simple approximation)
  const calculateDistance = (task: Task): string => {
    if (!currentLocation || !task.location.coordinates) return 'N/A';
    
    const lat1 = currentLocation.lat;
    const lon1 = currentLocation.lng;
    const lat2 = task.location.coordinates.lat;
    const lon2 = task.location.coordinates.lng;
    
    const R = 6371; // Radius of the earth in km
    const dLat = deg2rad(lat2 - lat1);
    const dLon = deg2rad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const d = R * c; // Distance in km
    
    if (d < 1) return `${Math.round(d * 1000)}m`;
    return `${d.toFixed(1)}km`;
  };

  const deg2rad = (deg: number) => {
    return deg * (Math.PI / 180);
  };

  // Open in Google Maps
  const openInMaps = (task: Task) => {
    if (task.location.coordinates) {
      const { lat, lng } = task.location.coordinates;
      window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, '_blank');
    } else {
      // Fallback to address search
      const address = encodeURIComponent(task.location.address);
      window.open(`https://www.google.com/maps/search/?api=1&query=${address}`, '_blank');
    }
  };

  // Sort tasks by distance
  const sortedTasks = useMemo(() => {
    if (!currentLocation) return filteredTasks;
    
    return [...filteredTasks].sort((a, b) => {
      if (!a.location.coordinates || !b.location.coordinates) return 0;
      
      const distA = calculateDistance(a);
      const distB = calculateDistance(b);
      
      // Extract numeric value for comparison
      const numA = parseFloat(distA.replace(/[^\d.]/g, ''));
      const numB = parseFloat(distB.replace(/[^\d.]/g, ''));
      
      return numA - numB;
    });
  }, [filteredTasks, currentLocation]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40" 
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
          >
            <div className="bg-white rounded-xl shadow-xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Task Locations</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {filteredTasks.length} task{filteredTasks.length !== 1 ? 's' : ''} found
                  </p>
                </div>
                <button 
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>

              {/* Filters */}
              <div className="p-4 border-b bg-gray-50">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Filter className="w-5 h-5 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">Filter:</span>
                  </div>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Tasks ({tasks.length})</option>
                    <option value="assigned">Assigned ({tasks.filter(t => t.status === 'assigned').length})</option>
                    <option value="accepted">Accepted ({tasks.filter(t => t.status === 'accepted').length})</option>
                    <option value="in_progress">In Progress ({tasks.filter(t => t.status === 'in_progress').length})</option>
                    <option value="completed">Completed ({tasks.filter(t => t.status === 'completed').length})</option>
                  </select>
                  
                  {currentLocation && (
                    <div className="ml-auto flex items-center gap-2 text-sm text-gray-600">
                      <Navigation className="w-4 h-4 text-blue-600" />
                      <span>Your location detected</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {sortedTasks.length > 0 ? (
                  <div className="space-y-4">
                    {sortedTasks.map((task) => (
                      <div
                        key={task.taskId}
                        className={`border-2 rounded-lg p-4 transition-all cursor-pointer ${
                          selectedTask?.taskId === task.taskId
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                        }`}
                        onClick={() => setSelectedTask(task)}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h4 className="font-semibold text-gray-900">{task.title}</h4>
                              <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(task.status)}`}>
                                {task.status.replace('_', ' ')}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{task.description}</p>
                          </div>
                          {task.priority && (
                            <div className={`flex items-center gap-1 px-2 py-1 rounded ${getPriorityColor(task.priority)}`}>
                              <AlertTriangle className="w-4 h-4" />
                              <span className="text-xs font-medium capitalize">{task.priority}</span>
                            </div>
                          )}
                        </div>

                        <div className="grid grid-cols-2 gap-3 mb-3">
                          <div className="flex items-start gap-2">
                            <MapPin className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="text-xs text-gray-500">Location</p>
                              <p className="text-sm text-gray-900">{task.location.address}</p>
                            </div>
                          </div>
                          
                          {currentLocation && task.location.coordinates && (
                            <div className="flex items-start gap-2">
                              <Navigation className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                              <div>
                                <p className="text-xs text-gray-500">Distance</p>
                                <p className="text-sm font-medium text-blue-600">{calculateDistance(task)}</p>
                              </div>
                            </div>
                          )}
                          
                          {task.dueDate && (
                            <div className="flex items-start gap-2">
                              <Clock className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                              <div>
                                <p className="text-xs text-gray-500">Due Date</p>
                                <p className="text-sm text-gray-900">{task.dueDate}</p>
                              </div>
                            </div>
                          )}
                          
                          {task.consumer && (
                            <div className="flex items-start gap-2">
                              <div className="w-4 h-4 bg-gray-300 rounded-full mt-0.5 flex-shrink-0" />
                              <div>
                                <p className="text-xs text-gray-500">Consumer</p>
                                <p className="text-sm text-gray-900">
                                  {typeof task.consumer === 'object' ? task.consumer.name : task.consumer}
                                </p>
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2 pt-3 border-t border-gray-200">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              openInMaps(task);
                            }}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                          >
                            <Navigation className="w-4 h-4" />
                            Get Directions
                          </button>
                          {task.location.coordinates && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(
                                  `https://www.google.com/maps/@${task.location.coordinates!.lat},${task.location.coordinates!.lng},15z`,
                                  '_blank'
                                );
                              }}
                              className="px-4 py-2 border border-blue-600 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors text-sm font-medium"
                            >
                              View on Map
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No Tasks Found</h3>
                    <p className="text-gray-600">
                      {filterStatus === 'all' 
                        ? 'You have no tasks assigned yet.'
                        : `No tasks with status "${filterStatus.replace('_', ' ')}".`}
                    </p>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-4 border-t bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Tip:</span> Tasks are sorted by distance from your location
                  </div>
                  <button
                    onClick={onClose}
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default MapModal;
