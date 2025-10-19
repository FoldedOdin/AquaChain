import { ServiceRequest } from '../types';

// Mock service request data
export const mockServiceRequests: ServiceRequest[] = [
  {
    requestId: 'SR-2025-001',
    consumerId: 'user-123',
    technicianId: 'TECH-456',
    deviceId: 'DEV-3421',
    status: 'in_progress',
    location: {
      latitude: 37.7749,
      longitude: -122.4194,
      address: '123 Main St, San Francisco, CA 94102'
    },
    estimatedArrival: new Date(Date.now() + 30 * 60 * 1000).toISOString(), // 30 minutes from now
    notes: [
      {
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
        author: 'System',
        type: 'status_update',
        content: 'Service request created and submitted for technician assignment.'
      },
      {
        timestamp: new Date(Date.now() - 90 * 60 * 1000).toISOString(), // 90 minutes ago
        author: 'System',
        type: 'status_update',
        content: 'Technician TECH-456 has been assigned to your request.'
      },
      {
        timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1 hour ago
        author: 'TECH-456',
        type: 'technician_note',
        content: 'I have accepted your service request. Currently gathering necessary tools and will be en route shortly.'
      },
      {
        timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
        author: 'TECH-456',
        type: 'status_update',
        content: 'I am now en route to your location. ETA is approximately 30 minutes.'
      },
      {
        timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), // 5 minutes ago
        author: 'TECH-456',
        type: 'status_update',
        content: 'I have arrived and am beginning the diagnostic process on your water quality sensor.'
      }
    ],
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    requestId: 'SR-2025-002',
    consumerId: 'user-123',
    technicianId: 'TECH-789',
    deviceId: 'DEV-3422',
    status: 'completed',
    location: {
      latitude: 37.7749,
      longitude: -122.4194,
      address: '123 Main St, San Francisco, CA 94102'
    },
    notes: [
      {
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
        author: 'System',
        type: 'status_update',
        content: 'Service request created for routine maintenance checkup.'
      },
      {
        timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000 + 30 * 60 * 1000).toISOString(),
        author: 'System',
        type: 'status_update',
        content: 'Technician TECH-789 has been assigned to your request.'
      },
      {
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
        author: 'TECH-789',
        type: 'technician_note',
        content: 'Completed routine maintenance. Calibrated all sensors and replaced pH sensor probe. System is functioning optimally.'
      },
      {
        timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000 + 5 * 60 * 1000).toISOString(),
        author: 'user-123',
        type: 'customer_feedback',
        content: 'Thank you for the excellent service! The technician was professional and thorough.'
      }
    ],
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    completedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    customerRating: 5
  },
  {
    requestId: 'SR-2025-003',
    consumerId: 'user-123',
    deviceId: 'DEV-3421',
    status: 'pending',
    location: {
      latitude: 37.7749,
      longitude: -122.4194,
      address: '123 Main St, San Francisco, CA 94102'
    },
    notes: [
      {
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(), // 30 minutes ago
        author: 'System',
        type: 'status_update',
        content: 'Service request submitted. Searching for available technicians in your area.'
      }
    ],
    createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  }
];

// Simulate API calls
export const createServiceRequest = async (requestData: any): Promise<ServiceRequest> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  const newRequest: ServiceRequest = {
    requestId: `SR-2025-${String(Math.floor(Math.random() * 1000)).padStart(3, '0')}`,
    consumerId: 'user-123',
    deviceId: requestData.deviceId,
    status: 'pending',
    location: {
      latitude: 37.7749,
      longitude: -122.4194,
      address: '123 Main St, San Francisco, CA 94102'
    },
    notes: [
      {
        timestamp: new Date().toISOString(),
        author: 'System',
        type: 'status_update',
        content: `Service request created for ${requestData.issueType.replace('_', ' ')}. Priority: ${requestData.priority}. ${requestData.description}`
      }
    ],
    createdAt: new Date().toISOString(),
  };
  
  // Add to mock data
  mockServiceRequests.unshift(newRequest);
  
  return newRequest;
};

export const getServiceRequests = async (): Promise<ServiceRequest[]> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Sort by creation date (newest first)
  return [...mockServiceRequests].sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );
};

export const rateServiceRequest = async (requestId: string, rating: number, feedback: string): Promise<void> => {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const requestIndex = mockServiceRequests.findIndex(req => req.requestId === requestId);
  if (requestIndex !== -1) {
    mockServiceRequests[requestIndex].customerRating = rating;
    
    // Add feedback note
    mockServiceRequests[requestIndex].notes.push({
      timestamp: new Date().toISOString(),
      author: 'user-123',
      type: 'customer_feedback',
      content: feedback || `Customer rated this service ${rating}/5 stars.`
    });
  }
};

// Simulate real-time updates for active service requests
export const simulateServiceUpdates = (requestId: string, onUpdate: (request: ServiceRequest) => void) => {
  const request = mockServiceRequests.find(req => req.requestId === requestId);
  if (!request || request.status === 'completed' || request.status === 'cancelled') {
    return;
  }

  const updateInterval = setInterval(() => {
    const updatedRequest = mockServiceRequests.find(req => req.requestId === requestId);
    if (updatedRequest) {
      // Simulate status progression
      if (updatedRequest.status === 'pending' && Math.random() < 0.3) {
        updatedRequest.status = 'assigned';
        updatedRequest.technicianId = `TECH-${Math.floor(Math.random() * 1000)}`;
        updatedRequest.notes.push({
          timestamp: new Date().toISOString(),
          author: 'System',
          type: 'status_update',
          content: `Technician ${updatedRequest.technicianId} has been assigned to your request.`
        });
        onUpdate(updatedRequest);
      } else if (updatedRequest.status === 'assigned' && Math.random() < 0.4) {
        updatedRequest.status = 'accepted';
        updatedRequest.estimatedArrival = new Date(Date.now() + 45 * 60 * 1000).toISOString();
        updatedRequest.notes.push({
          timestamp: new Date().toISOString(),
          author: updatedRequest.technicianId!,
          type: 'technician_note',
          content: 'I have accepted your service request and will arrive within 45 minutes.'
        });
        onUpdate(updatedRequest);
      }
    }
  }, 10000); // Check every 10 seconds

  // Clean up interval after 5 minutes
  setTimeout(() => {
    clearInterval(updateInterval);
  }, 5 * 60 * 1000);

  return () => clearInterval(updateInterval);
};