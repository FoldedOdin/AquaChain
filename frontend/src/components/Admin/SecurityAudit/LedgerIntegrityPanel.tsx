import React from 'react';
import { Database, CheckCircle, Shield, Clock } from 'lucide-react';
import { mockLedgerIntegrity } from '../../../data/mockSecurityAudit';

const LedgerIntegrityPanel: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <Database className="w-6 h-6 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Ledger Integrity</h3>
            <p className="text-xs text-gray-500">Data Integrity Verification</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-4">
        <div className="p-4 bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg border border-indigo-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Ledger Entries Verified</span>
            <Database className="w-5 h-5 text-indigo-600" />
          </div>
          <p className="text-3xl font-bold text-indigo-900">
            {mockLedgerIntegrity.entriesVerified.toLocaleString()}
          </p>
        </div>

        <div className="p-4 bg-gradient-to-r from-green-50 to-green-100 rounded-lg border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Hash Verification</span>
            <CheckCircle className="w-5 h-5 text-green-600" />
          </div>
          <p className="text-2xl font-bold text-green-900">{mockLedgerIntegrity.hashVerification}</p>
          <p className="text-xs text-green-700 mt-1">All hashes validated</p>
        </div>

        <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Last Integrity Check</span>
            <Clock className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-xl font-bold text-blue-900">{mockLedgerIntegrity.lastCheck}</p>
        </div>

        <div className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Tamper Detection</span>
            <Shield className="w-5 h-5 text-gray-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{mockLedgerIntegrity.tamperDetection}</p>
          <p className="text-xs text-gray-600 mt-1">No anomalies detected</p>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
        <p className="text-xs text-blue-800">
          <strong>Immutable Ledger:</strong> All audit entries are cryptographically signed and stored in an 
          append-only ledger with hash chain verification for tamper-proof audit trails.
        </p>
      </div>
    </div>
  );
};

export default LedgerIntegrityPanel;
