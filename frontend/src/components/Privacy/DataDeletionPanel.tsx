import React, { useState, useEffect } from 'react';
import { Trash2, Clock, CheckCircle, XCircle, AlertTriangle, Ban } from 'lucide-react';
import { gdprService } from '../../services/gdprService';

interface DeletionRequest {
  request_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  scheduled_deletion_date?: string;
  days_remaining?: number;
  completed_at?: string;
  cancelled_at?: string;
  deletion_summary?: any;
  error_message?: string;
}

interface DataDeletionPanelProps {
  userId: string;
  userEmail: string;
}

const DataDeletionPanel: React.FC<DataDeletionPanelProps> = ({ userId, userEmail }) => {
  const [deletions, setDeletions] = useState<DeletionRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [cancellingRequestId, setCancellingRequestId] = useState<string | null>(null);

  useEffect(() => {
    loadDeletions();
  }, [userId]);

  const loadDeletions = async () => {
    try {
      setLoading(true);
      const data = await gdprService.listUserDeletions();
      setDeletions(data.deletions || []);
    } catch (err) {
      console.error('Error loading deletions:', err);
      setError('Failed to load deletion history');
    } finally {
      setLoading(false);
    }
  };

  const requestDeletion = async () => {
    if (confirmText !== 'DELETE MY ACCOUNT') {
      setError('Please type "DELETE MY ACCOUNT" to confirm');
      return;
    }

    try {
      setRequesting(true);
      setError(null);
      setSuccessMessage(null);

      const data = await gdprService.requestDataDeletion(userId, userEmail, false);
      
      setSuccessMessage(
        `Your account deletion request has been received. Your account will be permanently deleted in 30 days. ` +
        `You can cancel this request at any time before the deletion date.`
      );

      setShowConfirmDialog(false);
      setConfirmText('');

      // Reload deletions list
      await loadDeletions();
    } catch (err) {
      console.error('Error requesting deletion:', err);
      setError(err instanceof Error ? err.message : 'Failed to request data deletion');
    } finally {
      setRequesting(false);
    }
  };

  const cancelDeletion = async (requestId: string) => {
    try {
      setCancellingRequestId(requestId);
      setError(null);
      setSuccessMessage(null);

      await gdprService.cancelDeletionRequest(requestId);
      
      setSuccessMessage('Your deletion request has been cancelled successfully.');

      // Reload deletions list
      await loadDeletions();
    } catch (err) {
      console.error('Error cancelling deletion:', err);
      setError(err instanceof Error ? err.message : 'Failed to cancel deletion request');
    } finally {
      setCancellingRequestId(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'cancelled':
        return <Ban className="w-5 h-5 text-gray-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'pending':
        return 'Pending';
      case 'processing':
        return 'Processing';
      case 'cancelled':
        return 'Cancelled';
      case 'failed':
        return 'Failed';
      default:
        return status;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const hasPendingDeletion = deletions.some(d => d.status === 'pending' || d.status === 'processing');

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Data Deletion</h2>
        <p className="text-gray-600">
          Request permanent deletion of your account and all associated data. 
          This action cannot be undone after the 30-day waiting period.
        </p>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center">
            <XCircle className="w-5 h-5 text-red-500 mr-2" />
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center">
            <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
            <p className="text-green-700">{successMessage}</p>
          </div>
        </div>
      )}

      {/* Warning Box */}
      <div className="mb-6 p-4 bg-red-50 border-2 border-red-300 rounded-md">
        <div className="flex items-start">
          <AlertTriangle className="w-6 h-6 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-red-800 mb-2">Warning: Permanent Action</h3>
            <p className="text-red-700 mb-2">
              Deleting your account will permanently remove:
            </p>
            <ul className="list-disc list-inside space-y-1 text-red-700 text-sm">
              <li>Your profile and account information</li>
              <li>All registered devices and their configurations</li>
              <li>All sensor readings and historical data</li>
              <li>All alerts and notifications</li>
              <li>All service requests and support tickets</li>
              <li>Your consent preferences</li>
            </ul>
            <p className="text-red-700 mt-2 font-medium">
              This action cannot be undone after the 30-day waiting period expires.
            </p>
          </div>
        </div>
      </div>

      {/* Delete Button */}
      {!hasPendingDeletion && (
        <div className="mb-6">
          <button
            onClick={() => setShowConfirmDialog(true)}
            className="flex items-center px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            data-testid="delete-my-account"
          >
            <Trash2 className="w-5 h-5 mr-2" />
            Delete My Account
          </button>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-center mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600 mr-3" />
              <h3 className="text-xl font-bold text-gray-900">Confirm Account Deletion</h3>
            </div>
            
            <div className="mb-4">
              <p className="text-gray-700 mb-4">
                Are you absolutely sure you want to delete your account? This will:
              </p>
              <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm mb-4">
                <li>Schedule your account for deletion in 30 days</li>
                <li>Permanently remove all your data after the waiting period</li>
                <li>Prevent you from logging in after deletion</li>
              </ul>
              <p className="text-gray-700 mb-4">
                You can cancel this request within 30 days if you change your mind.
              </p>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Type <span className="font-bold text-red-600">DELETE MY ACCOUNT</span> to confirm:
                </label>
                <input
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  placeholder="DELETE MY ACCOUNT"
                  data-testid="confirm-deletion-input"
                />
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={() => {
                  setShowConfirmDialog(false);
                  setConfirmText('');
                  setError(null);
                }}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
                disabled={requesting}
              >
                Cancel
              </button>
              <button
                onClick={requestDeletion}
                disabled={requesting || confirmText !== 'DELETE MY ACCOUNT'}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                data-testid="confirm-deletion-button"
              >
                {requesting ? 'Processing...' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deletion History */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Deletion Requests</h3>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Clock className="w-6 h-6 text-gray-400 animate-spin mr-2" />
            <span className="text-gray-600">Loading deletion history...</span>
          </div>
        ) : deletions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No deletion requests</p>
          </div>
        ) : (
          <div className="space-y-4">
            {deletions.map((deletion) => (
              <div
                key={deletion.request_id}
                className={`border rounded-md p-4 ${
                  deletion.status === 'pending' ? 'border-yellow-300 bg-yellow-50' :
                  deletion.status === 'completed' ? 'border-green-300 bg-green-50' :
                  deletion.status === 'cancelled' ? 'border-gray-300 bg-gray-50' :
                  deletion.status === 'failed' ? 'border-red-300 bg-red-50' :
                  'border-gray-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getStatusIcon(deletion.status)}
                    <div>
                      <p className="font-medium text-gray-800">
                        Deletion Request - {getStatusText(deletion.status)}
                      </p>
                      <p className="text-sm text-gray-600">
                        Requested: {formatDate(deletion.created_at)}
                      </p>
                      {deletion.scheduled_deletion_date && deletion.status === 'pending' && (
                        <p className="text-sm text-gray-600">
                          Scheduled: {formatDate(deletion.scheduled_deletion_date)}
                          {deletion.days_remaining !== undefined && (
                            <span className="ml-2 font-medium text-yellow-700">
                              ({deletion.days_remaining} days remaining)
                            </span>
                          )}
                        </p>
                      )}
                      {deletion.completed_at && (
                        <p className="text-sm text-gray-600">
                          Completed: {formatDate(deletion.completed_at)}
                        </p>
                      )}
                      {deletion.cancelled_at && (
                        <p className="text-sm text-gray-600">
                          Cancelled: {formatDate(deletion.cancelled_at)}
                        </p>
                      )}
                      {deletion.error_message && (
                        <p className="text-sm text-red-600 mt-1">
                          Error: {deletion.error_message}
                        </p>
                      )}
                      {deletion.deletion_summary && (
                        <div className="mt-2 text-sm text-gray-600">
                          <p className="font-medium">Deleted Items:</p>
                          <ul className="list-disc list-inside ml-2">
                            {Object.entries(deletion.deletion_summary.deleted_items || {}).map(([key, value]) => (
                              <li key={key}>{key}: {value as number} item(s)</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {deletion.status === 'pending' && (
                    <button
                      onClick={() => cancelDeletion(deletion.request_id)}
                      disabled={cancellingRequestId === deletion.request_id}
                      className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors text-sm"
                      data-testid="cancel-deletion"
                    >
                      <Ban className="w-4 h-4 mr-2" />
                      {cancellingRequestId === deletion.request_id ? 'Cancelling...' : 'Cancel Request'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Information Box */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <div className="flex items-start">
          <AlertTriangle className="w-5 h-5 text-blue-500 mr-2 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">Important Information:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Deletion requests have a 30-day waiting period</li>
              <li>You can cancel your request at any time during the waiting period</li>
              <li>After 30 days, the deletion is permanent and cannot be undone</li>
              <li>Audit logs will be anonymized but retained for compliance</li>
              <li>You will receive a confirmation email when deletion is complete</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataDeletionPanel;
