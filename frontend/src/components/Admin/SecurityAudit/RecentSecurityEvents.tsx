import React from 'react';
import { FileText, Clock } from 'lucide-react';
import { mockSecurityEvents, getStatusColor } from '../../../data/mockSecurityAudit';

const RecentSecurityEvents: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <FileText className="w-6 h-6 text-purple-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Recent Security Events</h3>
            <p className="text-xs text-gray-500">Audit Log Table</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Time</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Event</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">User</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-gray-600 uppercase">Status</th>
            </tr>
          </thead>
          <tbody>
            {mockSecurityEvents.map((event) => (
              <tr
                key={event.id}
                className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-900">{event.time}</span>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="text-sm text-gray-700">{event.event}</span>
                </td>
                <td className="py-3 px-4">
                  <span className="text-sm font-mono text-gray-600">{event.user}</span>
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 text-xs font-semibold rounded ${getStatusColor(event.status)}`}>
                    {event.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* View All Button */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <button className="w-full text-sm text-purple-600 hover:text-purple-700 font-medium">
          View Complete Audit Trail →
        </button>
      </div>
    </div>
  );
};

export default RecentSecurityEvents;
