import React, { useState, useEffect, useRef } from 'react';
import { TechnicianTask } from '../../types';
import { technicianService } from '../../services/technicianService';

interface TaskMapProps {
  tasks: TechnicianTask[];
  selectedTask: TechnicianTask | null;
  onTaskSelect: (task: TechnicianTask) => void;
}

// Mock Google Maps implementation for development
// In production, this would use the actual Google Maps API
const TaskMap: React.FC<TaskMapProps> = ({
  tasks,
  selectedTask,
  onTaskSelect
}) => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [currentLocation, setCurrentLocation] = useState<{lat: number, lng: number} | null>(null);
  const [routeInfo, setRouteInfo] = useState<{distance: string, duration: string} | null>(null);
  const [isLoadingRoute, setIsLoadingRoute] = useState(false);

  useEffect(() => {
    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
          // Update technician location in backend
          technicianService.updateLocation(
            position.coords.latitude,
            position.coords.longitude
          ).catch(console.error);
        },
        (error) => {
          console.error('Error getting location:', error);
          // Default to San Francisco for demo
          setCurrentLocation({ lat: 37.7749, lng: -122.4194 });
        }
      );
    }
  }, []);

  const getPriorityColor = (priority: TechnicianTask['priority']) => {
    switch (priority) {
      case 'critical':
        return '#dc2626'; // red-600
      case 'high':
        return '#ea580c'; // orange-600
      case 'medium':
        return '#ca8a04'; // yellow-600
      case 'low':
        return '#16a34a'; // green-600
      default:
        return '#6b7280'; // gray-500
    }
  };

  const getStatusIcon = (status: TechnicianTask['status']) => {
    switch (status) {
      case 'assigned':
        return '📋';
      case 'accepted':
        return '✅';
      case 'en_route':
        return '🚗';
      case 'in_progress':
        return '🔧';
      case 'completed':
        return '✅';
      default:
        return '📍';
    }
  };

  const handleGetDirections = async (task: TechnicianTask) => {
    if (!currentLocation) return;
    
    setIsLoadingRoute(true);
    try {
      // Mock route calculation - in production this would use Google Maps Directions API
      const distance = Math.sqrt(
        Math.pow(task.location.latitude - currentLocation.lat, 2) +
        Math.pow(task.location.longitude - currentLocation.lng, 2)
      ) * 111; // Rough km conversion
      
      setRouteInfo({
        distance: `${distance.toFixed(1)} km`,
        duration: `${Math.round(distance * 2)} min` // Mock duration
      });
      
      // In production, this would open Google Maps or similar
      const mapsUrl = `https://www.google.com/maps/dir/${currentLocation.lat},${currentLocation.lng}/${task.location.latitude},${task.location.longitude}`;
      window.open(mapsUrl, '_blank');
      
    } catch (error) {
      console.error('Error getting directions:', error);
    } finally {
      setIsLoadingRoute(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Task Locations Map
          </h3>
          {routeInfo && (
            <div className="text-sm text-gray-600">
              Route: {routeInfo.distance}, {routeInfo.duration}
            </div>
          )}
        </div>

        {/* Mock Map Container */}
        <div 
          ref={mapRef}
          className="relative h-96 bg-gray-100 rounded-lg border-2 border-dashed border-gray-300 overflow-hidden"
        >
          {/* Mock Map Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-green-50">
            <div className="absolute inset-0 opacity-20">
              <svg className="w-full h-full" viewBox="0 0 400 300">
                {/* Mock street grid */}
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#d1d5db" strokeWidth="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>
          </div>

          {/* Current Location Marker */}
          {currentLocation && (
            <div 
              className="absolute transform -translate-x-1/2 -translate-y-1/2 z-10"
              style={{
                left: '20%',
                top: '70%'
              }}
            >
              <div className="relative">
                <div className="w-4 h-4 bg-blue-600 rounded-full border-2 border-white shadow-lg"></div>
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
                  Your Location
                </div>
              </div>
            </div>
          )}

          {/* Task Markers */}
          {tasks.map((task, index) => {
            const isSelected = selectedTask?.taskId === task.taskId;
            const left = 30 + (index * 15) % 50;
            const top = 20 + (index * 10) % 60;
            
            return (
              <div
                key={task.taskId}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 cursor-pointer z-20 ${
                  isSelected ? 'scale-125' : 'hover:scale-110'
                } transition-transform`}
                style={{
                  left: `${left}%`,
                  top: `${top}%`
                }}
                onClick={() => onTaskSelect(task)}
              >
                <div className="relative">
                  <div 
                    className={`w-8 h-8 rounded-full border-3 border-white shadow-lg flex items-center justify-center text-white text-sm font-bold ${
                      isSelected ? 'ring-4 ring-primary-300' : ''
                    }`}
                    style={{ backgroundColor: getPriorityColor(task.priority) }}
                  >
                    {getStatusIcon(task.status)}
                  </div>
                  
                  {isSelected && (
                    <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs px-3 py-2 rounded-lg whitespace-nowrap max-w-48">
                      <div className="font-medium">{task.customerInfo.name}</div>
                      <div className="text-gray-300">{task.priority.toUpperCase()} - {task.status.replace('_', ' ').toUpperCase()}</div>
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Map Controls */}
          <div className="absolute top-4 right-4 flex flex-col space-y-2">
            <button className="bg-white p-2 rounded shadow hover:bg-gray-50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
            </button>
            <button className="bg-white p-2 rounded shadow hover:bg-gray-50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>

          {/* Legend */}
          <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-lg">
            <div className="text-xs font-medium text-gray-900 mb-2">Priority Levels</div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-600"></div>
                <span className="text-xs text-gray-600">Critical</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-orange-600"></div>
                <span className="text-xs text-gray-600">High</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-yellow-600"></div>
                <span className="text-xs text-gray-600">Medium</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-green-600"></div>
                <span className="text-xs text-gray-600">Low</span>
              </div>
            </div>
          </div>
        </div>

        {/* Selected Task Info */}
        {selectedTask && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900">
                  {selectedTask.customerInfo.name}
                </h4>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedTask.location.address}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {selectedTask.description}
                </p>
                
                <div className="flex items-center space-x-4 mt-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    selectedTask.priority === 'critical' ? 'bg-red-100 text-red-800' :
                    selectedTask.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                    selectedTask.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {selectedTask.priority.toUpperCase()}
                  </span>
                  
                  <span className="text-xs text-gray-500">
                    Status: {selectedTask.status.replace('_', ' ').toUpperCase()}
                  </span>
                  
                  {selectedTask.estimatedArrival && (
                    <span className="text-xs text-gray-500">
                      ETA: {new Date(selectedTask.estimatedArrival).toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="ml-4 flex space-x-2">
                <button
                  onClick={() => handleGetDirections(selectedTask)}
                  disabled={isLoadingRoute || !currentLocation}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  {isLoadingRoute ? (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m0 0L9 7" />
                    </svg>
                  )}
                  Directions
                </button>
                
                <button
                  onClick={() => window.open(`tel:${selectedTask.customerInfo.phone}`, '_self')}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  Call
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Real-time Location Tracking Notice */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                Your location is being tracked to provide accurate ETAs to customers. 
                Location updates are sent automatically when you move between tasks.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskMap;