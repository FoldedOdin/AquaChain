/**
 * Auth Stats Service
 * Fetches real authentication activity data from the backend.
 * Kept separate from adminService to avoid circular HMR issues.
 */
import { fetchWithAuth } from '../utils/apiInterceptor';

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:3002';

export interface AuthEventSummary {
  successfulLogins: number;
  failedLogins: number;
  blockedAccounts: number;
  mfaEnabledPercentage: number | null;
  periodHours: number;
  totalEvents: number;
}

export interface AuthLoginEvent {
  id: string;
  user: string;
  action: string;
  status: string;
  ip: string;
  timestamp: string;
  userAgent: string;
}

export interface AuthTimelinePoint {
  hour: string;
  success: number;
  failed: number;
}

export interface AuthStatsResponse {
  summary: AuthEventSummary;
  recentEvents: AuthLoginEvent[];
  timeline: AuthTimelinePoint[];
}

export const getAuthStats = async (hours = 24, limit = 20): Promise<AuthStatsResponse> => {
  let response: Response;
  try {
    response = await fetchWithAuth(
      `${API_BASE_URL}/api/admin/audit/auth-stats?hours=${hours}&limit=${limit}`,
      { method: 'GET' }
    );
  } catch {
    // Network error or CORS preflight blocked — endpoint not reachable yet
    throw new Error('ENDPOINT_NOT_DEPLOYED');
  }

  if (response.status === 403 || response.status === 404) {
    throw new Error('ENDPOINT_NOT_DEPLOYED');
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as any).error || `Request failed with status ${response.status}`);
  }

  return response.json();
};
