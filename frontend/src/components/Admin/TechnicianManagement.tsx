import { useState, useEffect } from 'react';
import { TechnicianManagementData } from '../../types/admin';
import { getAllTechnicians, updateTechnician } from '../../services/adminService';

const TechnicianManagement = () => {
  const [technicians, setTechnicians] = useState<TechnicianManagementData[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'inactive' | 'on_leave'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [editingTechnician, setEditingTechnician] = useState<TechnicianManagementData | null>(null);

  useEffect(() => {
    loadTechnicians();
  }, []);

  const loadTechnicians = async () => {
    try {
      const data = await getAllTechnicians();
      setTechnicians(data);
    } catch (error) {
      console.error('Error loading technicians:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTechnicians = technicians.filter(tech => {
    const matchesFilter = filter === 'all' || tech.status === filter;
    const matchesSearch = searchTerm === '' || 
      tech.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tech.profile.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tech.profile.lastName.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const handleUpdateTechnician = async (technicianId: string, updates: Partial<TechnicianManagementData>) => {
    try {
      const updatedTech = await updateTechnician(technicianId, updates);
      setTechnicians(technicians.map(t => t.technicianId === technicianId ? updatedTech : t));
      setEditingTechnician(null);
    } catch (error) {
      console.error('Error updating technician:', error);
      alert('Failed to update technician');
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'inactive': return 'bg-gray-100 text-gray-800';
      case 'on_leave': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPerformanceColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return <div className="text-center py-8">Loading technicians...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold">Technician Management</h2>
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex gap-2">
          {(['all', 'active', 'inactive', 'on_leave'] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status === 'on_leave' ? 'On Leave' : status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Search technicians..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Technician Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Total Technicians</div>
          <div className="text-2xl font-bold">{technicians.length}</div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Active</div>
          <div className="text-2xl font-bold text-green-600">
            {technicians.filter(t => t.status === 'active').length}
          </div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Avg Performance</div>
          <div className="text-2xl font-bold text-blue-600">
            {(technicians.reduce((sum, t) => sum + t.performanceScore, 0) / technicians.length).toFixed(1)}
          </div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Active Jobs</div>
          <div className="text-2xl font-bold text-purple-600">
            {technicians.reduce((sum, t) => sum + t.stats.activeJobs, 0)}
          </div>
        </div>
        <div className="border rounded-lg p-3">
          <div className="text-sm text-gray-600">Completed Jobs</div>
          <div className="text-2xl font-bold text-gray-700">
            {technicians.reduce((sum, t) => sum + t.stats.completedJobs, 0)}
          </div>
        </div>
      </div>

      {/* Technician Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Technician</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Performance</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Jobs</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Rating</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Certifications</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {filteredTechnicians.map((tech) => (
              <tr key={tech.technicianId} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">
                    {tech.profile.firstName} {tech.profile.lastName}
                  </div>
                  <div className="text-xs text-gray-500">{tech.email}</div>
                  <div className="text-xs text-gray-500">{tech.profile.phone}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(tech.status)}`}>
                    {tech.status === 'on_leave' ? 'On Leave' : tech.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className={`text-lg font-bold ${getPerformanceColor(tech.performanceScore)}`}>
                    {tech.performanceScore.toFixed(1)}
                  </div>
                  <div className="text-xs text-gray-500">Score</div>
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900">
                    {tech.stats.completedJobs} / {tech.stats.totalJobs}
                  </div>
                  <div className="text-xs text-gray-500">
                    {tech.stats.activeJobs} active
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center">
                    <span className="text-yellow-500 mr-1">★</span>
                    <span className="text-sm font-medium">{tech.stats.avgCustomerRating.toFixed(1)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {tech.profile.certifications.map((cert, idx) => (
                      <span key={idx} className="inline-flex px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded">
                        {cert}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => setEditingTechnician(tech)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    Edit Schedule
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredTechnicians.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No technicians found matching your criteria
        </div>
      )}

      {/* Edit Technician Modal */}
      {editingTechnician && (
        <TechnicianScheduleModal
          technician={editingTechnician}
          onSave={(updates) => handleUpdateTechnician(editingTechnician.technicianId, updates)}
          onCancel={() => setEditingTechnician(null)}
        />
      )}
    </div>
  );
};

interface TechnicianScheduleModalProps {
  technician: TechnicianManagementData;
  onSave: (updates: Partial<TechnicianManagementData>) => void;
  onCancel: () => void;
}

const TechnicianScheduleModal = ({ technician, onSave, onCancel }: TechnicianScheduleModalProps) => {
  const [schedule, setSchedule] = useState(technician.workSchedule);
  const [status, setStatus] = useState(technician.status);

  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      workSchedule: schedule,
      status: status
    });
  };

  const updateDaySchedule = (day: typeof days[number], field: 'start' | 'end', value: string) => {
    setSchedule({
      ...schedule,
      [day]: {
        ...schedule[day],
        [field]: value
      }
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 my-8">
        <h3 className="text-lg font-semibold mb-4">
          Edit Schedule - {technician.profile.firstName} {technician.profile.lastName}
        </h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as any)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="on_leave">On Leave</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Override Status</label>
            <select
              value={schedule.overrideStatus}
              onChange={(e) => setSchedule({ ...schedule, overrideStatus: e.target.value as any })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="available">Available</option>
              <option value="unavailable">Unavailable</option>
              <option value="available_overtime">Available for Overtime</option>
            </select>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-3">Work Schedule</h4>
            <div className="space-y-3">
              {days.map((day) => (
                <div key={day} className="grid grid-cols-3 gap-4 items-center">
                  <div className="font-medium text-gray-700 capitalize">{day}</div>
                  <div>
                    <input
                      type="time"
                      value={schedule[day].start}
                      onChange={(e) => updateDaySchedule(day, 'start', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <input
                      type="time"
                      value={schedule[day].end}
                      onChange={(e) => updateDaySchedule(day, 'end', e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-3">Performance Stats</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="border rounded-lg p-3">
                <div className="text-sm text-gray-600">Performance Score</div>
                <div className="text-xl font-bold text-blue-600">{technician.performanceScore.toFixed(1)}</div>
              </div>
              <div className="border rounded-lg p-3">
                <div className="text-sm text-gray-600">Avg Customer Rating</div>
                <div className="text-xl font-bold text-yellow-600">
                  ★ {technician.stats.avgCustomerRating.toFixed(1)}
                </div>
              </div>
              <div className="border rounded-lg p-3">
                <div className="text-sm text-gray-600">Completed Jobs</div>
                <div className="text-xl font-bold text-green-600">{technician.stats.completedJobs}</div>
              </div>
              <div className="border rounded-lg p-3">
                <div className="text-sm text-gray-600">Avg Completion Time</div>
                <div className="text-xl font-bold text-purple-600">{technician.stats.avgCompletionTime}m</div>
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Update
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TechnicianManagement;
