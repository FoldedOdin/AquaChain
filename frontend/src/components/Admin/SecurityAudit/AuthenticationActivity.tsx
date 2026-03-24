import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Shield, UserCheck, UserX, Lock, TrendingUp, RefreshCw, AlertCircle } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  getAuthStats,
  AuthStatsResponse,
  AuthLoginEvent,
} from '../../../services/authStatsService';

const SESSION_KEY = 'aquachain_auth_stats_unavailable';

const isKnownUnavailable = () => sessionStorage.getItem(SESSION_KEY) === '1';
const markUnavailable = () => sessionStorage.setItem(SESSION_KEY, '1');
const clearUnavailable = () => sessionStorage.removeItem(SESSION_KEY);

const shouldSkipRequest = (): boolean => isKnownUnavailable();

const STATUS_COLOR: Record<string, string> = {
  SUCCESS: 'text-green-600',
  FAILURE: 'text-red-600',
  LOCKED: 'text-amber-600',
  RATE_LIMITED: 'text-orange-600',
};

const formatHour = (hourKey: string): string => {
  try {
    const hourPart = hourKey.split('T')[1] ?? '';
    const h = parseInt(hourPart, 10);
    const suffix = h >= 12 ? 'PM' : 'AM';
    const display = h % 12 === 0 ? 12 : h % 12;
    return `${display}${suffix}`;
  } catch {
    return hourKey;
  }
};

const formatTimestamp = (iso: string): string => {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
};

const AuthenticationActivity: React.FC = () => {
  const [data, setData] = useState<AuthStatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Clear any stale "unavailable" flag from the old hardcoded block so the
  // endpoint is retried now that it has been deployed.
  const [notDeployed, setNotDeployed] = useState(() => {
    clearUnavailable();
    return false;
  });
  const fetchedRef = useRef(false);

  const load = useCallback(async (isManual = false) => {
    if (shouldSkipRequest() && !isManual) return;

    setLoading(true);
    setError(null);
    setNotDeployed(false);
    fetchedRef.current = true;

    try {
      const result = await getAuthStats(24, 20);
      clearUnavailable();
      setData(result);
    } catch (err: any) {
      if (err.message === 'ENDPOINT_NOT_DEPLOYED') {
        markUnavailable();
        setNotDeployed(true);
      } else {
        setError(err.message || 'Failed to load authentication data');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (shouldSkipRequest()) return;
    if (fetchedRef.current) return;
    load();
  }, [load]);

  const summary = data?.summary;
  const recentEvents: AuthLoginEvent[] = data?.recentEvents ?? [];
  const timeline = (data?.timeline ?? []).map(p => ({
    ...p,
    label: formatHour(p.hour),
  }));

  // Endpoint not yet deployed — clean placeholder, no retries, no console noise
  if (!loading && notDeployed) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Shield className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Authentication Activity</h3>
            <p className="text-xs text-gray-500">Last 24 Hours</p>
          </div>
        </div>
        <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
          <div className="p-3 bg-gray-100 rounded-full">
            <Shield className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-sm font-medium text-gray-600">Live data not yet available</p>
          <p className="text-xs text-gray-400 max-w-xs">
            Deploy the CDK stack to enable real authentication statistics from AWS.
          </p>
          <button
            onClick={() => load(true)}
            className="mt-2 flex items-center gap-1.5 px-3 py-1.5 text-xs text-blue-600 border border-blue-200 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Shield className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Authentication Activity</h3>
            <p className="text-xs text-gray-500">Last 24 Hours</p>
          </div>
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="flex items-center gap-1 px-3 py-1.5 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Unexpected error */}
      {error && (
        <div className="mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <UserCheck className="w-4 h-4 text-green-600" />
            <span className="text-xs font-medium text-gray-600">Successful Logins</span>
          </div>
          <p className="text-3xl font-bold text-green-900">
            {loading ? '—' : (summary?.successfulLogins ?? 0)}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
          <div className="flex items-center gap-2 mb-2">
            <UserX className="w-4 h-4 text-red-600" />
            <span className="text-xs font-medium text-gray-600">Failed Logins</span>
          </div>
          <p className="text-3xl font-bold text-red-900">
            {loading ? '—' : (summary?.failedLogins ?? 0)}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg border border-amber-200">
          <div className="flex items-center gap-2 mb-2">
            <Lock className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-medium text-gray-600">Blocked Accounts</span>
          </div>
          <p className="text-3xl font-bold text-amber-900">
            {loading ? '—' : (summary?.blockedAccounts ?? 0)}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-medium text-gray-600">MFA Enabled</span>
          </div>
          <p className="text-3xl font-bold text-purple-900">
            {loading
              ? '—'
              : summary?.mfaEnabledPercentage != null
                ? `${summary.mfaEnabledPercentage}%`
                : 'N/A'}
          </p>
        </div>
      </div>

      {/* Recent Login Events */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Login Events</h4>
        {loading ? (
          <div className="space-y-2">
            {[1, 2, 3].map(n => (
              <div key={n} className="h-14 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : recentEvents.length === 0 ? (
          <p className="text-sm text-gray-400 italic py-4 text-center">No login events in the last 24 hours.</p>
        ) : (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {recentEvents.map(event => (
              <div
                key={event.id}
                className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">{event.user}</span>
                      <span className={`text-xs font-semibold ${STATUS_COLOR[event.status] ?? 'text-gray-600'}`}>
                        {event.action}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 font-mono">{event.ip}</span>
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Login Activity Timeline */}
      <div className="pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Login Activity Timeline</h4>
        {loading ? (
          <div className="h-40 bg-gray-100 rounded-lg animate-pulse" />
        ) : timeline.length === 0 ? (
          <div className="h-24 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-dashed border-blue-200 flex items-center justify-center">
            <p className="text-sm text-gray-500">No timeline data available</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={timeline} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                formatter={(value: number, name: string) => [value, name === 'success' ? 'Success' : 'Failed']}
              />
              <Legend formatter={(v) => v === 'success' ? 'Success' : 'Failed'} wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="success" fill="#22c55e" radius={[2, 2, 0, 0]} />
              <Bar dataKey="failed" fill="#ef4444" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default AuthenticationActivity;
