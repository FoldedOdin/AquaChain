import React, { useState, useEffect } from 'react';
import { Shield, Download, Trash2, FileText } from 'lucide-react';
import DataExportPanel from '../components/Privacy/DataExportPanel';
import DataDeletionPanel from '../components/Privacy/DataDeletionPanel';
import ConsentManagementPanel from '../components/Privacy/ConsentManagementPanel';

interface User {
  userId: string;
  email: string;
  name: string;
}

const PrivacySettings: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<'export' | 'delete' | 'consent'>('export');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const response = await fetch('/api/user/profile', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data);
      }
    } catch (err) {
      console.error('Error loading user profile:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading privacy settings...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600">Failed to load user profile</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-2">
            <Shield className="w-8 h-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Privacy & Data Settings</h1>
          </div>
          <p className="text-gray-600">
            Manage your personal data and privacy preferences in accordance with GDPR
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('export')}
                className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'export'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Download className="w-5 h-5 mr-2" />
                Data Export
              </button>
              <button
                onClick={() => setActiveTab('delete')}
                className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'delete'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Trash2 className="w-5 h-5 mr-2" />
                Data Deletion
              </button>
              <button
                onClick={() => setActiveTab('consent')}
                className={`flex items-center px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'consent'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <FileText className="w-5 h-5 mr-2" />
                Consent Management
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'export' && (
            <DataExportPanel userId={user.userId} userEmail={user.email} />
          )}

          {activeTab === 'delete' && (
            <DataDeletionPanel userId={user.userId} userEmail={user.email} />
          )}

          {activeTab === 'consent' && (
            <ConsentManagementPanel userId={user.userId} />
          )}
        </div>

        {/* GDPR Information */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Your Rights Under GDPR</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Right to Access</h4>
              <p>You can request a copy of all your personal data we hold.</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Right to Rectification</h4>
              <p>You can update or correct your personal information at any time.</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Right to Erasure</h4>
              <p>You can request deletion of your personal data (right to be forgotten).</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-800 mb-2">Right to Data Portability</h4>
              <p>You can receive your data in a structured, machine-readable format.</p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              For questions about your privacy rights or data processing, please contact our 
              Data Protection Officer at{' '}
              <a href="mailto:privacy@aquachain.com" className="text-blue-600 hover:underline">
                privacy@aquachain.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrivacySettings;
