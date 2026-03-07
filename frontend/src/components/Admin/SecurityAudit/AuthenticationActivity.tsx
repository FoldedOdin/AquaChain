import React from 'react';
import { Shield, UserCheck, UserX, Lock, TrendingUp } from 'lucide-react';
import { mockAuthActivity, mockLoginEvents, getLoginStatusColor } from '../../../data/mockSecurityAudit';

const AuthenticationActivity: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <UserCheck className="w-4 h-4 text-green-600" />
            <span className="text-xs font-medium text-gray-600">Successful Logins</span>
          </div>
          <p className="text-3xl font-bold text-green-900">{mockAuthActivity.successfulLogins24h}</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
          <div className="flex items-center gap-2 mb-2">
            <UserX className="w-4 h-4 text-red-600" />
            <span className="text-xs font-medium text-gray-600">Failed Logins</span>
          </div>
          <p className="text-3xl font-bold text-red-900">{mockAuthActivity.failedLogins}</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg border border-amber-200">
          <div className="flex items-center gap-2 mb-2">
            <Lock className="w-4 h-4 text-amber-600" />
            <span className="text-xs font-medium text-gray-600">Blocked Accounts</span>
          </div>
          <p className="text-3xl font-bold text-amber-900">{mockAuthActivity.blockedAccounts}</p>
        </div>

        <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-medium text-gray-600">MFA Enabled</span>
          </div>
          <p className="text-3xl font-bold text-purple-900">{mockAuthActivity.mfaEnabledPercentage}%</p>
        </div>
      </div>

      {/* Recent Login Events */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Recent Login Events</h4>
        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {mockLoginEvents.map((event) => (
            <div
              key={event.id}
              className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-gray-900">{event.user}</span>
                    <span className={`text-xs font-semibold ${getLoginStatusColor(event.status)}`}>
                      {event.action}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-600">
                    <span className="font-mono">{event.ip}</span>
                    <span>•</span>
                    <span>{event.location}</span>
                  </div>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap ml-2">{event.time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Login Timeline Chart Placeholder */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Login Activity Timeline</h4>
        <div className="h-24 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border-2 border-dashed border-blue-200 flex items-center justify-center">
          <p className="text-sm text-gray-600">
            📊 Chart visualization (integrate recharts for production)
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthenticationActivity;
