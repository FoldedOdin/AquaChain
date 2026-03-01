import { apiClient } from './apiClient';
import { fetchWithAuth } from '../utils/apiInterceptor';

export interface IncidentReport {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolved' | 'closed';
  createdAt: string;
  updatedAt: string;
  assignedTo: string;
  description: string;
  category: 'security' | 'performance' | 'system' | 'data' | 'network';
  priority: number;
  resolution?: string;
  resolvedAt?: string;
  metadata?: Record<string, any>;
}

export interface IncidentStats {
  totalIncidents: number;
  openIncidents: number;
  criticalIncidents: number;
  avgResolutionTime: number; // in hours
  incidentsByCategory: Array<{
    category: string;
    count: number;
  }>;
  incidentsBySeverity: Array<{
    severity: string;
    count: number;
  }>;
}

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';

export const getIncidentReports = async (
  status?: string,
  severity?: string,
  limit: number = 50
): Promise<IncidentReport[]> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    params.append('limit', limit.toString());

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/incidents?${params}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      // If the endpoint doesn't exist yet, return empty array silently
      if (response.status === 404) {
        // Only log once per session to reduce console noise
        if (!sessionStorage.getItem('incident_reports_endpoint_warned')) {
          console.info('Incident reports endpoint not yet implemented - using empty data');
          sessionStorage.setItem('incident_reports_endpoint_warned', 'true');
        }
        return [];
      }
      throw new Error('Failed to fetch incident reports');
    }

    const data = await response.json();
    return data.incidents || [];
  } catch (error) {
    // Only log errors that aren't 404s to reduce noise
    if (error instanceof Error && !error.message.includes('404')) {
      console.error('Error fetching incident reports:', error);
    }
    
    // Return empty array instead of mock data for production
    return [];
  }
};

export const getIncidentStats = async (days: number = 30): Promise<IncidentStats> => {
  try {
    const token = localStorage.getItem('aquachain_token') || localStorage.getItem('authToken');
    
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/incidents/stats?days=${days}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      // If the endpoint doesn't exist yet, return empty stats silently
      if (response.status === 404) {
        // Only log once per session to reduce console noise
        if (!sessionStorage.getItem('incident_stats_endpoint_warned')) {
          console.info('Incident statistics endpoint not yet implemented - using empty data');
          sessionStorage.setItem('incident_stats_endpoint_warned', 'true');
        }
        return {
          totalIncidents: 0,
          openIncidents: 0,
          criticalIncidents: 0,
          avgResolutionTime: 0,
          incidentsByCategory: [],
          incidentsBySeverity: []
        };
      }
      throw new Error('Failed to fetch incident stats');
    }

    const data = await response.json();
    return data.stats;
  } catch (error) {
    // Only log errors that aren't 404s to reduce noise
    if (error instanceof Error && !error.message.includes('404')) {
      console.error('Error fetching incident stats:', error);
    }
    
    // Return empty stats instead of mock data for production
    return {
      totalIncidents: 0,
      openIncidents: 0,
      criticalIncidents: 0,
      avgResolutionTime: 0,
      incidentsByCategory: [],
      incidentsBySeverity: []
    };
  }
};

export const createIncident = async (incident: Omit<IncidentReport, 'id' | 'createdAt' | 'updatedAt'>): Promise<IncidentReport> => {
  try {
    interface CreateIncidentResponse {
      incident: IncidentReport;
    }
    
    const response = await apiClient.post<CreateIncidentResponse>('/api/admin/incidents', incident);
    return response.data.incident;
  } catch (error) {
    console.error('Error creating incident:', error);
    throw error;
  }
};

export const updateIncident = async (id: string, updates: Partial<IncidentReport>): Promise<IncidentReport> => {
  try {
    interface UpdateIncidentResponse {
      incident: IncidentReport;
    }
    
    const response = await apiClient.put<UpdateIncidentResponse>(`/api/admin/incidents/${id}`, updates);
    return response.data.incident;
  } catch (error) {
    console.error('Error updating incident:', error);
    throw error;
  }
};

export const resolveIncident = async (id: string, resolution: string): Promise<IncidentReport> => {
  try {
    interface ResolveIncidentResponse {
      incident: IncidentReport;
    }
    
    const response = await apiClient.post<ResolveIncidentResponse>(`/api/admin/incidents/${id}/resolve`, { resolution });
    return response.data.incident;
  } catch (error) {
    console.error('Error resolving incident:', error);
    throw error;
  }
};

// Mock data functions removed - using empty data when endpoints are not available