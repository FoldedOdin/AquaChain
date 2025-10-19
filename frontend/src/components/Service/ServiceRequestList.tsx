import React from 'react';
import { ServiceRequest } from '../../types';

interface ServiceRequestListProps {
  serviceRequests: ServiceRequest[];
  onSelectRequest: (request: ServiceRequest) => void;
  selectedRequestId?: string;
}

const ServiceRequestList: React.FC<ServiceRequestListProps> = ({
  serviceRequests,
  onSelectRequest,
  selectedRequestId
}) => {
  const getStatusColor = (status: ServiceRequest['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'assigned':
        return 'bg-blue-100 text-blue-800';
      case 'accepted':
        return 'bg-indigo-100 text-indigo-800';
      case 'en_route':
        return 'bg-purple-100 text-purple-800';
      case 'in_progress':
        return 'bg-orange-100 text-orange-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: ServiceRequest['status']) => {
    switch (status) {
      case 'pending':
        return 'Pending';
      case 'assigned':
        return 'Assigned';
      case 'accepted':
        return 'Accepted';
      case 'en_route':
        return 'En Route';
      case 'in_progress':
        return 'In Progress';
      case 'completed':
        return 'Completed';
      case 'cancelled':
        return 'Cancelled';
      default:
        return status;
    }
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  if (serviceRequests.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No service requests</h3>
          <p className="mt-1 text-sm text-gray-500">
            You haven't submitted any service requests yet.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Service Requests</h3>
        <p className="mt-1 text-sm text-gray-500">
          Click on a request to view details and track progress
        </p>
      </div>

      <div className="divide-y divide-gray-200">
        {serviceRequests.map((request) => {
          const isSelected = selectedRequestId === request.requestId;
          const latestNote = request.notes[request.notes.length - 1];
          
          return (
            <div
              key={request.requestId}
              onClick={() => onSelectRequest(request)}
              className={`
                p-6 cursor-pointer transition-colors duration-200
                ${isSelected ? 'bg-primary-50 border-l-4 border-primary-500' : 'hover:bg-gray-50'}
              `}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <h4 className="text-sm font-medium text-gray-900">
                    Request #{request.requestId.slice(-8)}
                  </h4>
                  <span className={`
                    inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${getStatusColor(request.status)}
                  `}>
                    {getStatusLabel(request.status)}
                  </span>
                </div>
                <div className="text-sm text-gray-500">
                  {getTimeAgo(request.createdAt)}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-3">
                <div>
                  <div className="text-xs text-gray-500">Device</div>
                  <div className="text-sm font-medium text-gray-900">{request.deviceId}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Created</div>
                  <div className="text-sm text-gray-700">{formatDate(request.createdAt)}</div>
                </div>
                {request.technicianId && (
                  <div>
                    <div className="text-xs text-gray-500">Technician</div>
                    <div className="text-sm text-gray-700">{request.technicianId}</div>
                  </div>
                )}
                {request.estimatedArrival && (
                  <div>
                    <div className="text-xs text-gray-500">Estimated Arrival</div>
                    <div className="text-sm text-gray-700">{formatDate(request.estimatedArrival)}</div>
                  </div>
                )}
              </div>

              {latestNote && (
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-700">Latest Update</span>
                    <span className="text-xs text-gray-500">{getTimeAgo(latestNote.timestamp)}</span>
                  </div>
                  <p className="text-sm text-gray-600 line-clamp-2">{latestNote.content}</p>
                </div>
              )}

              {/* Rating Display */}
              {request.customerRating && (
                <div className="mt-3 flex items-center space-x-2">
                  <span className="text-xs text-gray-500">Your Rating:</span>
                  <div className="flex">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <svg
                        key={star}
                        className={`w-4 h-4 ${
                          star <= request.customerRating! ? 'text-yellow-400' : 'text-gray-300'
                        }`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              )}

              {/* Visual indicator for selected item */}
              {isSelected && (
                <div className="mt-3 flex items-center text-primary-600">
                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm font-medium">Selected</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ServiceRequestList;