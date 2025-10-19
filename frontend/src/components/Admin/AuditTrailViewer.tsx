import { useState } from 'react';
import { AuditTrailEntry } from '../../types/admin';
import { getAuditTrail, verifyHashChain } from '../../services/adminService';

const AuditTrailViewer = () => {
  const [entries, setEntries] = useState<AuditTrailEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<boolean | null>(null);
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setHours(date.getHours() - 24);
    return date.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [deviceFilter, setDeviceFilter] = useState('');
  const [expandedEntry, setExpandedEntry] = useState<string | null>(null);

  const handleLoadAuditTrail = async () => {
    setLoading(true);
    setVerificationResult(null);
    try {
      const data = await getAuditTrail(startDate, endDate, deviceFilter || undefined);
      setEntries(data);
    } catch (error) {
      console.error('Error loading audit trail:', error);
      alert('Failed to load audit trail');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyHashChain = async () => {
    if (entries.length === 0) {
      alert('Please load audit trail entries first');
      return;
    }

    setVerifying(true);
    try {
      const startSeq = entries[0].sequenceNumber;
      const endSeq = entries[entries.length - 1].sequenceNumber;
      const result = await verifyHashChain(startSeq, endSeq);
      setVerificationResult(result);
    } catch (error) {
      console.error('Error verifying hash chain:', error);
      alert('Failed to verify hash chain');
    } finally {
      setVerifying(false);
    }
  };

  const handleExportData = () => {
    if (entries.length === 0) return;

    const csvContent = [
      ['Sequence', 'Timestamp', 'Device ID', 'WQI', 'Anomaly Type', 'Data Hash', 'Chain Hash', 'Verified'].join(','),
      ...entries.map(entry => [
        entry.sequenceNumber,
        entry.timestamp,
        entry.deviceId,
        entry.wqi,
        entry.anomalyType,
        entry.dataHash,
        entry.chainHash,
        entry.verified ? 'Yes' : 'No'
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-trail-${startDate}-to-${endDate}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const toggleEntryExpansion = (logId: string) => {
    setExpandedEntry(expandedEntry === logId ? null : logId);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold mb-6">Audit Trail Viewer</h2>

      {/* Controls */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Load Audit Trail</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">Device ID (Optional)</label>
            <input
              type="text"
              value={deviceFilter}
              onChange={(e) => setDeviceFilter(e.target.value)}
              placeholder="e.g., DEV-3421"
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleLoadAuditTrail}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400"
            >
              {loading ? 'Loading...' : 'Load Entries'}
            </button>
          </div>
        </div>
      </div>

      {/* Actions */}
      {entries.length > 0 && (
        <div className="flex gap-3 mb-6">
          <button
            onClick={handleVerifyHashChain}
            disabled={verifying}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
          >
            {verifying ? 'Verifying...' : 'Verify Hash Chain'}
          </button>
          <button
            onClick={handleExportData}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            Export Data
          </button>
        </div>
      )}

      {/* Verification Result */}
      {verificationResult !== null && (
        <div className={`mb-6 p-4 rounded-lg border-2 ${
          verificationResult
            ? 'bg-green-50 border-green-500'
            : 'bg-red-50 border-red-500'
        }`}>
          <div className="flex items-center">
            <span className={`text-2xl mr-3 ${verificationResult ? 'text-green-600' : 'text-red-600'}`}>
              {verificationResult ? '✓' : '✗'}
            </span>
            <div>
              <h4 className={`font-semibold ${verificationResult ? 'text-green-900' : 'text-red-900'}`}>
                Hash Chain Verification {verificationResult ? 'Successful' : 'Failed'}
              </h4>
              <p className={`text-sm ${verificationResult ? 'text-green-700' : 'text-red-700'}`}>
                {verificationResult
                  ? 'All ledger entries are cryptographically verified and the hash chain is intact.'
                  : 'Hash chain verification failed. Data integrity may be compromised.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Entries Summary */}
      {entries.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="border rounded-lg p-3">
            <div className="text-sm text-gray-600">Total Entries</div>
            <div className="text-2xl font-bold text-blue-600">{entries.length}</div>
          </div>
          <div className="border rounded-lg p-3">
            <div className="text-sm text-gray-600">Sequence Range</div>
            <div className="text-lg font-semibold text-gray-900">
              {entries[0].sequenceNumber} - {entries[entries.length - 1].sequenceNumber}
            </div>
          </div>
          <div className="border rounded-lg p-3">
            <div className="text-sm text-gray-600">Verified Entries</div>
            <div className="text-2xl font-bold text-green-600">
              {entries.filter(e => e.verified).length}
            </div>
          </div>
          <div className="border rounded-lg p-3">
            <div className="text-sm text-gray-600">Unique Devices</div>
            <div className="text-2xl font-bold text-purple-600">
              {new Set(entries.map(e => e.deviceId)).size}
            </div>
          </div>
        </div>
      )}

      {/* Entries Table */}
      {entries.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Sequence</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">WQI</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Anomaly</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Verified</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {entries.map((entry) => (
                <>
                  <tr key={entry.logId} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-mono text-sm text-gray-900">{entry.sequenceNumber}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm text-gray-900">
                        {new Date(entry.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-gray-900">{entry.deviceId}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className={`text-sm font-semibold ${
                        entry.wqi >= 60 ? 'text-green-600' :
                        entry.wqi >= 40 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {entry.wqi.toFixed(1)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        entry.anomalyType === 'normal' ? 'bg-green-100 text-green-800' :
                        entry.anomalyType === 'sensor_fault' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {entry.anomalyType}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {entry.verified ? (
                        <span className="text-green-600 text-lg">✓</span>
                      ) : (
                        <span className="text-red-600 text-lg">✗</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleEntryExpansion(entry.logId)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        {expandedEntry === entry.logId ? 'Hide' : 'Details'}
                      </button>
                    </td>
                  </tr>
                  {expandedEntry === entry.logId && (
                    <tr>
                      <td colSpan={7} className="px-4 py-4 bg-gray-50">
                        <div className="space-y-2">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <div className="text-xs font-semibold text-gray-600 mb-1">Log ID</div>
                              <div className="font-mono text-xs text-gray-900 break-all">{entry.logId}</div>
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-gray-600 mb-1">Data Hash</div>
                              <div className="font-mono text-xs text-gray-900 break-all">{entry.dataHash}</div>
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-gray-600 mb-1">Previous Hash</div>
                              <div className="font-mono text-xs text-gray-900 break-all">{entry.previousHash}</div>
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-gray-600 mb-1">Chain Hash</div>
                              <div className="font-mono text-xs text-gray-900 break-all">{entry.chainHash}</div>
                            </div>
                            <div className="md:col-span-2">
                              <div className="text-xs font-semibold text-gray-600 mb-1">KMS Signature</div>
                              <div className="font-mono text-xs text-gray-900 break-all">{entry.kmsSignature}</div>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {entries.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          <p>Select a date range and click "Load Entries" to view audit trail</p>
        </div>
      )}

      {/* Information Box */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-blue-900 mb-2">About Audit Trail</h4>
        <p className="text-sm text-blue-800">
          The audit trail provides a tamper-evident record of all water quality readings. Each entry is cryptographically
          linked to the previous entry using hash chaining, and signed with AWS KMS for verification. The hash chain
          verification ensures that no data has been modified or deleted after being recorded.
        </p>
      </div>
    </div>
  );
};

export default AuditTrailViewer;
