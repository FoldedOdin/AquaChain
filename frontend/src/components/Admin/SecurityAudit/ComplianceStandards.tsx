import React from 'react';
import { Award, CheckCircle } from 'lucide-react';
import { mockComplianceStandards } from '../../../data/mockSecurityAudit';

const ComplianceStandards: React.FC = () => {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-green-100 rounded-lg">
            <Award className="w-6 h-6 text-green-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Compliance Standards</h3>
            <p className="text-xs text-gray-500">Certifications & Regulations</p>
          </div>
        </div>
        <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded font-medium">
          SIMULATED
        </span>
      </div>

      {/* Compliance Badges */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {mockComplianceStandards.map((standard, index) => (
          <div
            key={index}
            className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border-2 border-green-200 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start gap-3">
              <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="text-base font-bold text-green-900 mb-1">{standard.name}</h4>
                <p className="text-sm text-gray-700">{standard.description}</p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                    ✓ VERIFIED
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Additional Info */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-900">
            <strong>Enterprise-Grade Compliance:</strong> AquaChain adheres to international standards for 
            information security, data protection, environmental monitoring, and water safety regulations.
          </p>
        </div>
      </div>

      {/* Audit Schedule */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Next Compliance Audit:</span>
          <span className="font-semibold text-gray-900">Q2 2026</span>
        </div>
        <div className="flex items-center justify-between text-sm mt-2">
          <span className="text-gray-600">Last Audit Date:</span>
          <span className="font-semibold text-gray-900">January 15, 2026</span>
        </div>
      </div>
    </div>
  );
};

export default ComplianceStandards;
