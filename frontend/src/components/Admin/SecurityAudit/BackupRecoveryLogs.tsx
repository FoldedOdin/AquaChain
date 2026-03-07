import React from 'react';
import { Database, CheckCircle, Clock, HardDrive, Calendar } from 'lucide-react';
import { mockBackupInfo } from '../../../data/mockSecurityAudit';

const BackupRecoveryLogs: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Database className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Backup & Disaster Recovery</h3>
            <p className="text-xs text-gray-500">System Resilience</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Backup Status */}
      <div className="space-y-4 mb-6">
        <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Backup Verification</span>
            </div>
            <span className={`px-3 py-1 text-sm font-bold rounded ${
              mockBackupInfo.verification === 'Passed' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {mockBackupInfo.verification}
            </span>
          </div>
          <p className="text-xs text-gray-600">All backup integrity checks completed successfully</p>
        </div>

        <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">Last Restore Test</span>
          </div>
          <p className="text-2xl font-bold text-blue-900">{mockBackupInfo.lastRestoreTest}</p>
          <p className="text-xs text-gray-600 mt-1">Restore time: 2.3 hours (within RTO)</p>
        </div>

        <div className="p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-lg border border-purple-200">
          <div className="flex items-center gap-2 mb-2">
            <HardDrive className="w-5 h-5 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">Backup Size</span>
          </div>
          <p className="text-2xl font-bold text-purple-900">{mockBackupInfo.backupSize}</p>
          <p className="text-xs text-gray-600 mt-1">Compressed and encrypted</p>
        </div>

        <div className="p-4 bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-lg border border-indigo-200">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-5 h-5 text-indigo-600" />
            <span className="text-sm font-medium text-gray-700">Next Scheduled Backup</span>
          </div>
          <p className="text-2xl font-bold text-indigo-900">{mockBackupInfo.nextScheduledBackup}</p>
          <p className="text-xs text-gray-600 mt-1">Automated daily backups</p>
        </div>
      </div>

      {/* Recovery Metrics */}
      <div className="pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Recovery Objectives</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 mb-1">RTO (Recovery Time Objective)</p>
            <p className="text-xl font-bold text-gray-900">&lt; 4 hours</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-xs text-gray-600 mb-1">RPO (Recovery Point Objective)</p>
            <p className="text-xl font-bold text-gray-900">&lt; 1 hour</p>
          </div>
        </div>
      </div>

      {/* Backup Schedule */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Backup Schedule</h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span className="text-gray-700">Full Backup</span>
            <span className="font-semibold text-gray-900">Daily at 02:00 AM</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span className="text-gray-700">Incremental Backup</span>
            <span className="font-semibold text-gray-900">Every 6 hours</span>
          </div>
          <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
            <span className="text-gray-700">Retention Period</span>
            <span className="font-semibold text-gray-900">90 days</span>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
        <p className="text-xs text-blue-800">
          <strong>Disaster Recovery:</strong> Multi-region backup replication with automated failover 
          ensures business continuity and data protection.
        </p>
      </div>
    </div>
  );
};

export default BackupRecoveryLogs;
