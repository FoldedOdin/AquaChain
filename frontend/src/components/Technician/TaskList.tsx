import React from 'react';
import { TechnicianTask } from '../../types';

interface TaskListProps {
  tasks: TechnicianTask[];
  selectedTask: TechnicianTask | null;
  onTaskSelect: (task: TechnicianTask) => void;
  onAcceptTask: (taskId: string) => void;
}

const TaskList: React.FC<TaskListProps> = ({
  tasks,
  selectedTask,
  onTaskSelect,
  onAcceptTask
}) => {
  const getPriorityColor = (priority: TechnicianTask['priority']) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: TechnicianTask['status']) => {
    switch (status) {
      case 'assigned':
        return 'bg-blue-100 text-blue-800';
      case 'accepted':
        return 'bg-green-100 text-green-800';
      case 'en_route':
        return 'bg-purple-100 text-purple-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      case 'completed':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const sortedTasks = [...tasks].sort((a, b) => {
    // Sort by priority first (critical > high > medium > low)
    const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority];
    if (priorityDiff !== 0) return priorityDiff;

    // Then by status (assigned > accepted > en_route > in_progress)
    const statusOrder = { assigned: 4, accepted: 3, en_route: 2, in_progress: 1, completed: 0 };
    const statusDiff = statusOrder[b.status] - statusOrder[a.status];
    if (statusDiff !== 0) return statusDiff;

    // Finally by due date
    if (a.dueDate && b.dueDate) {
      return new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime();
    }

    return 0;
  });

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
          Assigned Tasks ({tasks.length})
        </h3>
        
        {tasks.length === 0 ? (
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks assigned</h3>
            <p className="mt-1 text-sm text-gray-500">You have no tasks assigned at the moment.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sortedTasks.map((task) => (
              <div
                key={task.taskId}
                className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                  selectedTask?.taskId === task.taskId
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => onTaskSelect(task)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(task.priority)}`}>
                        {task.priority.toUpperCase()}
                      </span>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(task.status)}`}>
                        {task.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    
                    <h4 className="text-sm font-medium text-gray-900 truncate">
                      {task.customerInfo.name} - {task.deviceInfo.model}
                    </h4>
                    
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                      {task.description}
                    </p>
                    
                    <div className="flex items-center text-xs text-gray-500 mt-2 space-x-4">
                      <div className="flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
                        </svg>
                        {task.location.address.split(',')[0]}
                      </div>
                      
                      {task.estimatedArrival && (
                        <div className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                          </svg>
                          ETA: {formatTime(task.estimatedArrival)}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {task.status === 'assigned' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onAcceptTask(task.taskId);
                      }}
                      className="ml-3 inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      Accept
                    </button>
                  )}
                </div>
                
                {task.deviceInfo.lastReading && task.deviceInfo.lastReading.anomalyType !== 'normal' && (
                  <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-md">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      <span className="text-xs text-red-800">
                        {task.deviceInfo.lastReading.anomalyType === 'sensor_fault' ? 'Sensor Fault Detected' : 'Contamination Alert'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskList;