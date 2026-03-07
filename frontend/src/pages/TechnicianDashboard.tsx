import { useState, useMemo, useCallback, useEffect, lazy, Suspense } from 'react';
import { TechnicianTask } from '../types';
import { technicianService } from '../services/technicianService';
import TaskList from '../components/Technician/TaskList';
import TaskDetails from '../components/Technician/TaskDetails';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import DataCard from '../components/Dashboard/DataCard';
import { useDashboardData } from '../hooks/useDashboardData';
import { useDataExport } from '../hooks/useDataExport';

// Lazy load heavy components
const TaskMap = lazy(() => import('../components/Technician/TaskMap'));
const MaintenanceHistory = lazy(() => import('../components/Technician/MaintenanceHistory'));

// Loading component for view content
const ViewLoadingFallback = () => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

const TechnicianDashboard = () => {
  const [selectedTask, setSelectedTask] = useState<TechnicianTask | null>(null);
  const [view, setView] = useState<'list' | 'map' | 'history'>('list');

  // Use shared hooks
  const dashboardData = useDashboardData();
  const { exportData, exporting } = useDataExport();

  // Extract data from the hook
  const tasks = useMemo(() => [], []); // TODO: Implement technician tasks fetching
  const isLoading = dashboardData.loading;
  const error = dashboardData.error;
  
  // Refetch function
  const refetch = useCallback(() => {
    // Trigger refresh via context
    window.location.reload();
  }, []);

  // Set initial selected task
  useEffect(() => {
    if (tasks.length > 0 && !selectedTask) {
      setSelectedTask(tasks[0]);
    }
  }, [tasks, selectedTask]);

  // Memoize computed task counts
  const taskCounts = useMemo(() => ({
    assigned: tasks.filter((t: TechnicianTask) => t.status === 'assigned').length,
    accepted: tasks.filter((t: TechnicianTask) => t.status === 'accepted').length,
    inProgress: tasks.filter((t: TechnicianTask) => ['en_route', 'in_progress'].includes(t.status)).length,
    highPriority: tasks.filter((t: TechnicianTask) => ['high', 'critical'].includes(t.priority)).length
  }), [tasks]);

  // Memoize event handlers
  const handleTaskSelect = useCallback((task: TechnicianTask) => {
    setSelectedTask(task);
  }, []);

  const handleTaskUpdate = useCallback(async (taskId: string, status: TechnicianTask['status'], note?: string) => {
    try {
      await technicianService.updateTaskStatus(taskId, status, note);
      await refetch(); // Reload tasks to get updated data
    } catch (err) {
      console.error('Error updating task:', err);
    }
  }, [refetch]);

  const handleAcceptTask = useCallback(async (taskId: string) => {
    try {
      await technicianService.acceptTask(taskId);
      await refetch();
    } catch (err) {
      console.error('Error accepting task:', err);
    }
  }, [refetch]);

  const handleExportTasks = useCallback(async () => {
    try {
      await exportData(tasks, {
        format: 'json',
        filename: `technician-tasks-${new Date().toISOString().split('T')[0]}.json`,
        includeMetadata: true
      });
    } catch (err) {
      console.error('Error exporting tasks:', err);
    }
  }, [exportData, tasks]);

  const handleViewChange = useCallback((newView: 'list' | 'map' | 'history') => {
    setView(newView);
  }, []);

  if (isLoading) {
    return (
      <DashboardLayout
        role="technician"
        header={
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <DataCard key={i} title="" value="" loading={true} />
          ))}
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout
        role="technician"
        header={
          <>
            <h1 className="text-2xl font-bold text-gray-900">Field Service Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">Manage your assigned tasks and service requests</p>
          </>
        }
      >
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Tasks</h3>
          <p className="text-red-700">{error.message}</p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      role="technician"
      header={
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Field Service Dashboard</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage your assigned tasks and service requests
            </p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => handleViewChange('list')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${view === 'list'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              List View
            </button>
            <button
              onClick={() => handleViewChange('map')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${view === 'map'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Map View
            </button>
            <button
              onClick={() => handleViewChange('history')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${view === 'history'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              History
            </button>
            <button
              onClick={handleExportTasks}
              disabled={exporting}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : 'Export'}
            </button>
          </div>
        </div>
      }
    >

      {/* Task Summary using DataCard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <DataCard
          title="Assigned"
          value={taskCounts.assigned}
          icon={
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
          }
        />
        <DataCard
          title="Accepted"
          value={taskCounts.accepted}
          icon={
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          }
        />
        <DataCard
          title="In Progress"
          value={taskCounts.inProgress}
          icon={
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
            </svg>
          }
        />
        <DataCard
          title="High Priority"
          value={taskCounts.highPriority}
          icon={
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          }
        />
      </div>

      {/* Main Content */}
      {view === 'list' ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <TaskList
              tasks={tasks}
              selectedTask={selectedTask}
              onTaskSelect={handleTaskSelect}
              onAcceptTask={handleAcceptTask}
            />
          </div>
          <div className="lg:col-span-2">
            {selectedTask ? (
              <TaskDetails
                task={selectedTask}
                onTaskUpdate={handleTaskUpdate}
                onRefresh={refetch}
              />
            ) : (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="text-center text-gray-500">
                  <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No task selected</h3>
                  <p className="mt-1 text-sm text-gray-500">Select a task from the list to view details</p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : view === 'map' ? (
        <Suspense fallback={<ViewLoadingFallback />}>
          <TaskMap
            tasks={tasks}
            selectedTask={selectedTask}
            onTaskSelect={handleTaskSelect}
          />
        </Suspense>
      ) : (
        <Suspense fallback={<ViewLoadingFallback />}>
          <MaintenanceHistory />
        </Suspense>
      )}
    </DashboardLayout>
  );
};

export default TechnicianDashboard;