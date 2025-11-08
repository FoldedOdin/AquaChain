import React, { useState, useEffect } from 'react';
import { Download, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { gdprService } from '../../services/gdprService';

interface ExportRequest {
  request_id: string;
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  download_url?: string;
  error_message?: string;
}

interface DataExportPanelProps {
  userId: string;
  userEmail: string;
}

const DataExportPanel: React.FC<DataExportPanelProps> = ({ userId, userEmail }) => {
  const [exports, setExports] = useState<ExportRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadExports();
  }, [userId]);

  const loadExports = async () => {
    try {
      setLoading(true);
      const data = await gdprService.listUserExports();
      setExports(data.exports || []);
    } catch (err) {
      console.error('Error loading exports:', err);
      setError('Failed to load export history');
    } finally {
      setLoading(false);
    }
  };

  const requestExport = async () => {
    try {
      setRequesting(true);
      setError(null);
      setSuccessMessage(null);

      const data = await gdprService.requestDataExport(userId, userEmail);
      
      setSuccessMessage(
        'Your data export has been completed! You can download it using the link below. ' +
        'The download link will expire in 7 days.'
      );

      // Reload exports list
      await loadExports();
    } catch (err) {
      console.error('Error requesting export:', err);
      setError(err instanceof Error ? err.message : 'Failed to request data export');
    } finally {
      setRequesting(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Data Export</h2>
        <p className="text-gray-600">
          Request a copy of all your personal data stored in AquaChain. 
          The export will include your profile, devices, sensor readings, alerts, and activity history.
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

      <div className="mb-6">
        <button
          onClick={requestExport}
          disabled={requesting}
          className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          data-testid="request-data-export"
        >
          <Download className="w-5 h-5 mr-2" />
          {requesting ? 'Processing...' : 'Request Data Export'}
        </button>
        <p className="mt-2 text-sm text-gray-500">
          Your data will be exported in JSON format and available for download within 48 hours.
        </p>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Export History</h3>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Clock className="w-6 h-6 text-gray-400 animate-spin mr-2" />
            <span className="text-gray-600">Loading export history...</span>
          </div>
        ) : exports.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No export requests yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {exports.map((exportRequest) => (
              <div
                key={exportRequest.request_id}
                className="border border-gray-200 rounded-md p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    {getStatusIcon(exportRequest.status)}
                    <div>
                      <p className="font-medium text-gray-800">
                        Export Request
                      </p>
                      <p className="text-sm text-gray-600">
                        Requested: {formatDate(exportRequest.created_at)}
                      </p>
                      {exportRequest.completed_at && (
                        <p className="text-sm text-gray-600">
                          Completed: {formatDate(exportRequest.completed_at)}
                        </p>
                      )}
                      {exportRequest.error_message && (
                        <p className="text-sm text-red-600 mt-1">
                          Error: {exportRequest.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  {exportRequest.status === 'completed' && exportRequest.download_url && (
                    <a
                      href={exportRequest.download_url}
                      download
                      className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                      data-testid="download-export"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-blue-500 mr-2 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium mb-1">Important Information:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Download links expire after 7 days</li>
              <li>Exports are automatically deleted after 30 days</li>
              <li>You can request a new export at any time</li>
              <li>The export includes all data as of the request time</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExportPanel;
