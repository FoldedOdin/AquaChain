import { useState, useEffect } from 'react';
import ServiceRequestForm, { ServiceRequestData } from '../components/Service/ServiceRequestForm';
import ServiceRequestList from '../components/Service/ServiceRequestList';
import ServiceRequestTracker from '../components/Service/ServiceRequestTracker';
import { ServiceRequest } from '../types';
import { 
  createServiceRequest, 
  getServiceRequests, 
  rateServiceRequest,
  simulateServiceUpdates 
} from '../services/serviceRequests';

const Service = () => {
  const [serviceRequests, setServiceRequests] = useState<ServiceRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<ServiceRequest | null>(null);
  const [showRequestForm, setShowRequestForm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load service requests on component mount
  useEffect(() => {
    loadServiceRequests();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Set up real-time updates for active requests
  useEffect(() => {
    const activeRequests = serviceRequests.filter(req => 
      !['completed', 'cancelled'].includes(req.status)
    );

    const cleanupFunctions: (() => void)[] = [];

    activeRequests.forEach(request => {
      const cleanup = simulateServiceUpdates(request.requestId, (updatedRequest) => {
        setServiceRequests(prev => 
          prev.map(req => 
            req.requestId === updatedRequest.requestId ? updatedRequest : req
          )
        );
        
        // Update selected request if it's the one being updated
        if (selectedRequest?.requestId === updatedRequest.requestId) {
          setSelectedRequest(updatedRequest);
        }
      });
      
      if (cleanup) {
        cleanupFunctions.push(cleanup);
      }
    });

    return () => {
      cleanupFunctions.forEach(cleanup => cleanup());
    };
  }, [serviceRequests, selectedRequest]);

  const loadServiceRequests = async () => {
    try {
      setIsLoading(true);
      const requests = await getServiceRequests();
      setServiceRequests(requests);
      
      // Auto-select the most recent request if none is selected
      if (!selectedRequest && requests.length > 0) {
        setSelectedRequest(requests[0]);
      }
    } catch (error) {
      console.error('Failed to load service requests:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRequest = async (requestData: ServiceRequestData) => {
    try {
      setIsSubmitting(true);
      const newRequest = await createServiceRequest(requestData);
      setServiceRequests(prev => [newRequest, ...prev]);
      setSelectedRequest(newRequest);
      setShowRequestForm(false);
    } catch (error) {
      console.error('Failed to create service request:', error);
      // In a real app, show error notification
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRateService = async (rating: number, feedback: string) => {
    if (!selectedRequest) return;
    
    try {
      await rateServiceRequest(selectedRequest.requestId, rating, feedback);
      
      // Update local state
      const updatedRequest = {
        ...selectedRequest,
        customerRating: rating,
        notes: [
          ...selectedRequest.notes,
          {
            timestamp: new Date().toISOString(),
            author: 'user-123',
            type: 'customer_feedback' as const,
            content: feedback || `Customer rated this service ${rating}/5 stars.`
          }
        ]
      };
      
      setSelectedRequest(updatedRequest);
      setServiceRequests(prev => 
        prev.map(req => 
          req.requestId === updatedRequest.requestId ? updatedRequest : req
        )
      );
    } catch (error) {
      console.error('Failed to rate service:', error);
    }
  };

  const handleSelectRequest = (request: ServiceRequest) => {
    setSelectedRequest(request);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="md:flex md:items-center md:justify-between">
          <div className="flex-1 min-w-0">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Service Requests
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Request technician service and track service status
            </p>
          </div>
        </div>

        {/* Loading skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-20 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-32 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Service Requests
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Request technician service and track service status
          </p>
        </div>
        
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setShowRequestForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Request Service
          </button>
        </div>
      </div>

      {/* Service Request Form Modal */}
      {showRequestForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <ServiceRequestForm
              onSubmit={handleCreateRequest}
              onCancel={() => setShowRequestForm(false)}
              isSubmitting={isSubmitting}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Request List */}
        <div>
          <ServiceRequestList
            serviceRequests={serviceRequests}
            onSelectRequest={handleSelectRequest}
            selectedRequestId={selectedRequest?.requestId}
          />
        </div>

        {/* Service Request Details */}
        <div>
          {selectedRequest ? (
            <ServiceRequestTracker
              serviceRequest={selectedRequest}
              onRate={handleRateService}
            />
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 8l2 2 4-4" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">Select a service request</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose a service request from the list to view details and track progress.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      {serviceRequests.length === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Need help with your water quality device?
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  Our certified technicians can help with sensor calibration, maintenance, repairs, and troubleshooting. 
                  Click "Request Service" to get started.
                </p>
              </div>
              <div className="mt-4">
                <div className="-mx-2 -my-1.5 flex">
                  <button
                    onClick={() => setShowRequestForm(true)}
                    className="bg-blue-50 px-2 py-1.5 rounded-md text-sm font-medium text-blue-800 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-blue-50 focus:ring-blue-600"
                  >
                    Request Service Now
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Service;