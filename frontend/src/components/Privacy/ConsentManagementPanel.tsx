import React, { useState, useEffect } from 'react';
import { Check, X, Clock, Info, AlertCircle } from 'lucide-react';

interface ConsentOption {
  type: string;
  title: string;
  description: string;
  required: boolean;
}

interface Consent {
  granted: boolean;
  timestamp: string | null;
  version: string;
}

interface ConsentHistory {
  consent_type: string;
  action: string;
  timestamp: string;
  ip_address: string;
  user_agent: string;
}

interface ConsentManagementPanelProps {
  userId: string;
}

const CONSENT_OPTIONS: ConsentOption[] = [
  {
    type: 'data_processing',
    title: 'Essential Data Processing',
    description: 'Required for core functionality including water quality monitoring, device management, and account services. This consent is necessary to use the platform.',
    required: true
  },
  {
    type: 'analytics',
    title: 'Analytics & Performance',
    description: 'Allow us to collect anonymous usage data to improve platform performance and user experience. This helps us understand how features are used.',
    required: false
  },
  {
    type: 'marketing',
    title: 'Marketing Communications',
    description: 'Receive updates about new features, product announcements, and promotional offers via email. You can unsubscribe at any time.',
    required: false
  },
  {
    type: 'third_party_sharing',
    title: 'Third-Party Data Sharing',
    description: 'Allow sharing of anonymized data with trusted partners for research and industry insights. Your personal information is never shared.',
    required: false
  }
];

const ConsentManagementPanel: React.FC<ConsentManagementPanelProps> = ({ userId }) => {
  const [consents, setConsents] = useState<Record<string, Consent>>({});
  const [history, setHistory] = useState<ConsentHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [pendingChanges, setPendingChanges] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadConsents();
  }, [userId]);

  const loadConsents = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/gdpr/consents', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load consent preferences');
      }

      const data = await response.json();
      setConsents(data.consents || {});
      
      // Initialize pending changes with current values
      const initial: Record<string, boolean> = {};
      CONSENT_OPTIONS.forEach(option => {
        initial[option.type] = data.consents?.[option.type]?.granted || false;
      });
      setPendingChanges(initial);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load consents');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await fetch('/api/gdpr/consents/history', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load consent history');
      }

      const data = await response.json();
      setHistory(data.history || []);
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  const handleConsentChange = (consentType: string, granted: boolean) => {
    setPendingChanges(prev => ({
      ...prev,
      [consentType]: granted
    }));
    setHasChanges(true);
    setSuccess(null);
    setError(null);
  };

  const saveConsents = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      // Only send changed consents
      const updates: Record<string, boolean> = {};
      Object.keys(pendingChanges).forEach(type => {
        const currentValue = consents[type]?.granted || false;
        if (pendingChanges[type] !== currentValue) {
          updates[type] = pendingChanges[type];
        }
      });

      if (Object.keys(updates).length === 0) {
        setSuccess('No changes to save');
        setHasChanges(false);
        return;
      }

      const response = await fetch('/api/gdpr/consents/bulk', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ consents: updates })
      });

      if (!response.ok) {
        throw new Error('Failed to update consent preferences');
      }

      const data = await response.json();
      setConsents(data.consents || {});
      setHasChanges(false);
      setSuccess('Consent preferences updated successfully');

      // Reload to get updated data
      await loadConsents();
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update consents');
    } finally {
      setSaving(false);
    }
  };

  const cancelChanges = () => {
    // Reset pending changes to current values
    const reset: Record<string, boolean> = {};
    CONSENT_OPTIONS.forEach(option => {
      reset[option.type] = consents[option.type]?.granted || false;
    });
    setPendingChanges(reset);
    setHasChanges(false);
    setSuccess(null);
    setError(null);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Consent Management</h2>
        <p className="text-gray-600">
          Control how your data is used. You can change these preferences at any time.
        </p>
      </div>

      {/* Alert Messages */}
      {error && (
        <div className="mx-6 mt-6 bg-red-50 border border-red-200 rounded-md p-4 flex items-start">
          <AlertCircle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="mx-6 mt-6 bg-green-50 border border-green-200 rounded-md p-4 flex items-start">
          <Check className="w-5 h-5 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-green-800">Success</h3>
            <p className="text-sm text-green-700 mt-1">{success}</p>
          </div>
        </div>
      )}

      {/* Consent Options */}
      <div className="p-6 space-y-6">
        {CONSENT_OPTIONS.map((option) => {
          const consent = consents[option.type];
          const isGranted = pendingChanges[option.type] || false;
          const lastUpdated = consent?.timestamp;

          return (
            <div
              key={option.type}
              className="border border-gray-200 rounded-lg p-5 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <h3 className="text-lg font-semibold text-gray-800">
                      {option.title}
                    </h3>
                    {option.required && (
                      <span className="ml-2 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        Required
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{option.description}</p>
                  {lastUpdated && (
                    <div className="flex items-center text-xs text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      Last updated: {formatDate(lastUpdated)}
                    </div>
                  )}
                </div>

                <div className="ml-4 flex-shrink-0">
                  <button
                    onClick={() => handleConsentChange(option.type, !isGranted)}
                    disabled={option.required || saving}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                      isGranted
                        ? 'bg-blue-600'
                        : 'bg-gray-200'
                    } ${
                      option.required || saving
                        ? 'opacity-50 cursor-not-allowed'
                        : 'cursor-pointer'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        isGranted ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>

              {option.required && (
                <div className="mt-3 flex items-start text-xs text-gray-500">
                  <Info className="w-4 h-4 mr-1 flex-shrink-0 mt-0.5" />
                  <span>This consent is required to use the platform and cannot be disabled.</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action Buttons */}
      {hasChanges && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
          <p className="text-sm text-gray-600">You have unsaved changes</p>
          <div className="flex space-x-3">
            <button
              onClick={cancelChanges}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={saveConsents}
              disabled={saving}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 flex items-center"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Consent History */}
      <div className="p-6 border-t border-gray-200">
        <button
          onClick={() => {
            setShowHistory(!showHistory);
            if (!showHistory && history.length === 0) {
              loadHistory();
            }
          }}
          className="text-sm font-medium text-blue-600 hover:text-blue-700 flex items-center"
        >
          <Clock className="w-4 h-4 mr-2" />
          {showHistory ? 'Hide' : 'View'} Consent History
        </button>

        {showHistory && (
          <div className="mt-4">
            {history.length === 0 ? (
              <p className="text-sm text-gray-500">No consent history available</p>
            ) : (
              <div className="space-y-3">
                {history.map((entry, index) => (
                  <div
                    key={index}
                    className="flex items-start text-sm border-l-2 border-gray-300 pl-4 py-2"
                  >
                    <div className="flex-1">
                      <div className="flex items-center">
                        {entry.action === 'granted' ? (
                          <Check className="w-4 h-4 text-green-600 mr-2" />
                        ) : (
                          <X className="w-4 h-4 text-red-600 mr-2" />
                        )}
                        <span className="font-medium text-gray-800">
                          {CONSENT_OPTIONS.find(o => o.type === entry.consent_type)?.title || entry.consent_type}
                        </span>
                        <span className={`ml-2 ${entry.action === 'granted' ? 'text-green-600' : 'text-red-600'}`}>
                          {entry.action}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatDate(entry.timestamp)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Information Footer */}
      <div className="px-6 py-4 bg-blue-50 border-t border-blue-100">
        <div className="flex items-start">
          <Info className="w-5 h-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">About Your Consent</p>
            <p>
              Your consent choices are tracked with metadata (IP address, timestamp) for compliance purposes.
              You can change these preferences at any time, and your choices will take effect immediately.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConsentManagementPanel;
