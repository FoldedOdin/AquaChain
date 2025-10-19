import { useState } from 'react';
import { TechnicianTask, TaskNote } from '../../types';
import { technicianService } from '../../services/technicianService';
import MaintenanceReport from './MaintenanceReport';

interface TaskDetailsProps {
  task: TechnicianTask;
  onTaskUpdate: (taskId: string, status: TechnicianTask['status'], note?: string) => void;
  onRefresh: () => void;
}

const TaskDetails = ({
  task,
  onTaskUpdate,
  onRefresh
}: TaskDetailsProps) => {
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [noteContent, setNoteContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showMaintenanceReport, setShowMaintenanceReport] = useState(false);

  const getStatusActions = (status: TechnicianTask['status']) => {
    switch (status) {
      case 'assigned':
        return [
          { label: 'Accept Task', status: 'accepted' as const, color: 'bg-green-600 hover:bg-green-700', action: 'status' }
        ];
      case 'accepted':
        return [
          { label: 'Start Travel', status: 'en_route' as const, color: 'bg-blue-600 hover:bg-blue-700', action: 'status' }
        ];
      case 'en_route':
        return [
          { label: 'Arrive at Site', status: 'in_progress' as const, color: 'bg-yellow-600 hover:bg-yellow-700', action: 'status' }
        ];
      case 'in_progress':
        return [
          { label: 'Complete Task', status: 'completed' as const, color: 'bg-green-600 hover:bg-green-700', action: 'maintenance' }
        ];
      default:
        return [];
    }
  };

  const handleStatusUpdate = async (newStatus: TechnicianTask['status']) => {
    try {
      setIsSubmitting(true);
      await onTaskUpdate(task.taskId, newStatus);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleActionClick = (action: { action: string; status: TechnicianTask['status'] }) => {
    if (action.action === 'maintenance') {
      setShowMaintenanceReport(true);
    } else {
      handleStatusUpdate(action.status);
    }
  };

  const handleMaintenanceComplete = () => {
    setShowMaintenanceReport(false);
    onRefresh();
  };

  const handleAddNote = async () => {
    if (!noteContent.trim()) return;

    try {
      setIsSubmitting(true);
      await technicianService.addTaskNote(task.taskId, {
        author: 'Current Technician', // This would come from auth context
        type: 'technician_note',
        content: noteContent.trim(),
        attachments: []
      });
      setNoteContent('');
      setShowNoteForm(false);
      onRefresh();
    } catch (error) {
      console.error('Error adding note:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPriorityColor = (priority: TechnicianTask['priority']) => {
    switch (priority) {
      case 'critical':
        return 'text-red-800 bg-red-100';
      case 'high':
        return 'text-orange-800 bg-orange-100';
      case 'medium':
        return 'text-yellow-800 bg-yellow-100';
      case 'low':
        return 'text-green-800 bg-green-100';
      default:
        return 'text-gray-800 bg-gray-100';
    }
  };

  const statusActions = getStatusActions(task.status);

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Task Details
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Task ID: {task.taskId}
            </p>
          </div>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getPriorityColor(task.priority)}`}>
            {task.priority.toUpperCase()} PRIORITY
          </span>
        </div>

        {/* Customer Information */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Customer Information</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Name</label>
                <p className="mt-1 text-sm text-gray-900">{task.customerInfo.name}</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Phone</label>
                <p className="mt-1 text-sm text-gray-900">
                  <a href={`tel:${task.customerInfo.phone}`} className="text-primary-600 hover:text-primary-500">
                    {task.customerInfo.phone}
                  </a>
                </p>
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Address</label>
                <p className="mt-1 text-sm text-gray-900">{task.location.address}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Device Information */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Device Information</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Model</label>
                <p className="mt-1 text-sm text-gray-900">{task.deviceInfo.model}</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Serial Number</label>
                <p className="mt-1 text-sm text-gray-900">{task.deviceInfo.serialNumber}</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Device ID</label>
                <p className="mt-1 text-sm text-gray-900">{task.deviceId}</p>
              </div>
            </div>

            {task.deviceInfo.lastReading && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Last Reading</label>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{task.deviceInfo.lastReading.readings.pH}</div>
                    <div className="text-xs text-gray-500">pH</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{task.deviceInfo.lastReading.readings.turbidity}</div>
                    <div className="text-xs text-gray-500">Turbidity</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{task.deviceInfo.lastReading.readings.tds}</div>
                    <div className="text-xs text-gray-500">TDS</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{task.deviceInfo.lastReading.readings.temperature}°C</div>
                    <div className="text-xs text-gray-500">Temp</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-gray-900">{task.deviceInfo.lastReading.wqi}</div>
                    <div className="text-xs text-gray-500">WQI</div>
                  </div>
                </div>
                
                {task.deviceInfo.lastReading.anomalyType !== 'normal' && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex items-center">
                      <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <span className="text-sm text-red-800">
                        {task.deviceInfo.lastReading.anomalyType === 'sensor_fault' ? 'Sensor Fault Detected' : 'Contamination Alert'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Task Description */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Task Description</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-900">{task.description}</p>
          </div>
        </div>

        {/* Timeline */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Timeline</h4>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Assigned</label>
                <p className="mt-1 text-gray-900">{formatDateTime(task.assignedAt)}</p>
              </div>
              {task.estimatedArrival && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">ETA</label>
                  <p className="mt-1 text-gray-900">{formatDateTime(task.estimatedArrival)}</p>
                </div>
              )}
              {task.dueDate && (
                <div>
                  <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">Due Date</label>
                  <p className="mt-1 text-gray-900">{formatDateTime(task.dueDate)}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        {statusActions.length > 0 && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Actions</h4>
            <div className="flex flex-wrap gap-3">
              {statusActions.map((action) => (
                <button
                  key={action.status}
                  onClick={() => handleActionClick(action)}
                  disabled={isSubmitting}
                  className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white ${action.color} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50`}
                >
                  {isSubmitting ? (
                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  ) : null}
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Notes Section */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900">Notes & Updates</h4>
            <button
              onClick={() => setShowNoteForm(!showNoteForm)}
              className="inline-flex items-center px-3 py-1 border border-gray-300 text-xs font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Add Note
            </button>
          </div>

          {showNoteForm && (
            <div className="mb-4 p-4 border border-gray-200 rounded-lg">
              <textarea
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                placeholder="Add a note about this task..."
                rows={3}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              <div className="mt-3 flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowNoteForm(false);
                    setNoteContent('');
                  }}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddNote}
                  disabled={!noteContent.trim() || isSubmitting}
                  className="px-4 py-1 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                >
                  Add Note
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {task.notes.length === 0 ? (
              <p className="text-sm text-gray-500 italic">No notes yet</p>
            ) : (
              task.notes.map((note) => (
                <div key={note.id} className="bg-gray-50 rounded-lg p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="text-sm font-medium text-gray-900">{note.author}</span>
                        <span className="text-xs text-gray-500">{formatDateTime(note.timestamp)}</span>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          note.type === 'status_update' ? 'bg-blue-100 text-blue-800' :
                          note.type === 'technician_note' ? 'bg-green-100 text-green-800' :
                          note.type === 'customer_feedback' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {note.type.replace('_', ' ')}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{note.content}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Maintenance Report Modal */}
      {showMaintenanceReport && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white">
            <MaintenanceReport
              task={task}
              onComplete={handleMaintenanceComplete}
              onCancel={() => setShowMaintenanceReport(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default TaskDetails;