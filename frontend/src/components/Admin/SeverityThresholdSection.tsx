import React from 'react';
import { Info, XCircle } from 'lucide-react';

interface SeverityThresholdSectionProps {
  thresholds: any;
  onChange: (field: string, value: any) => void;
  editMode: boolean;
  errors: Record<string, string>;
  showTooltip: string | null;
  setShowTooltip: (field: string | null) => void;
}

const SeverityThresholdSection: React.FC<SeverityThresholdSectionProps> = ({
  thresholds,
  onChange,
  editMode,
  errors,
  showTooltip,
  setShowTooltip
}) => {
  // Tooltip component matching existing pattern
  const Tooltip = ({ field, content }: { field: string; content: string }) => (
    <div className="relative inline-block">
      <button
        type="button"
        onMouseEnter={() => setShowTooltip(field)}
        onMouseLeave={() => setShowTooltip(null)}
        className="ml-1 text-gray-400 hover:text-gray-600 focus:outline-none"
      >
        <Info size={16} />
      </button>
      {showTooltip === field && (
        <div className="absolute z-10 w-64 p-2 mt-1 text-sm text-white bg-gray-900 rounded-lg shadow-lg -left-24">
          {content}
          <div className="absolute w-2 h-2 bg-gray-900 transform rotate-45 -top-1 left-1/2"></div>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">
        Alert Thresholds
      </h3>
      
      {/* pH Thresholds */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          pH Range
          <Tooltip 
            field="pH-severity" 
            content="WHO recommends pH between 6.5-8.5 for drinking water. Warning triggers yellow alerts with email/push notifications. Critical triggers red alerts with SMS/email/push notifications."
          />
        </label>
        
        {/* Visual Band Diagram */}
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-xs font-medium text-blue-900 mb-2">💡 How Thresholds Work:</div>
          <div className="flex items-center justify-center space-x-1 text-xs">
            <div className="px-2 py-1 bg-yellow-200 rounded">Warning Min</div>
            <span>→</span>
            <div className="px-2 py-1 bg-red-200 rounded">Critical Min</div>
            <span>→</span>
            <div className="px-3 py-1 bg-green-200 rounded font-semibold">SAFE ZONE</div>
            <span>→</span>
            <div className="px-2 py-1 bg-red-200 rounded">Critical Max</div>
            <span>→</span>
            <div className="px-2 py-1 bg-yellow-200 rounded">Warning Max</div>
          </div>
          <div className="text-xs text-blue-700 mt-2 text-center">
            Critical thresholds are INSIDE warning thresholds (more restrictive)
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          {/* Warning Thresholds */}
          <div className="border-2 border-yellow-300 rounded-lg p-4 bg-yellow-50">
            <div className="flex items-center mb-3">
              <span className="text-yellow-700 font-medium text-sm">⚠️ Warning Level</span>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Minimum pH <span className="text-yellow-600">(Outer Lower Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 5.5"
                  value={thresholds?.pH?.warning?.min ?? ''}
                  onChange={(e) => onChange('pH.warning.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Must be smallest value</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Maximum pH <span className="text-yellow-600">(Outer Upper Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 8.5"
                  value={thresholds?.pH?.warning?.max ?? ''}
                  onChange={(e) => onChange('pH.warning.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Must be largest value</p>
              </div>
            </div>
          </div>
          
          {/* Critical Thresholds */}
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <div className="flex items-center mb-3">
              <span className="text-red-700 font-medium text-sm">🔴 Critical Level</span>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Minimum pH <span className="text-red-600">(Inner Lower Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 6.0"
                  value={thresholds?.pH?.critical?.min ?? ''}
                  onChange={(e) => onChange('pH.critical.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Between warning min and critical max</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Maximum pH <span className="text-red-600">(Inner Upper Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 8.0"
                  value={thresholds?.pH?.critical?.max ?? ''}
                  onChange={(e) => onChange('pH.critical.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Between critical min and warning max</p>
              </div>
            </div>
          </div>
        </div>
        
        {errors['pH'] && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <XCircle className="h-4 w-4 mr-1" />
            {errors['pH']}
          </p>
        )}
        
        <div className="mt-3 p-2 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs font-medium text-gray-700">
            ✅ Valid Example: Warning Min (5.5) &lt; Critical Min (6.0) &lt; Critical Max (8.0) &lt; Warning Max (8.5)
          </p>
        </div>
      </div>

      {/* Turbidity Thresholds */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Turbidity (NTU)
          <Tooltip 
            field="turbidity-severity" 
            content="WHO guideline: <5 NTU for drinking water. Higher values indicate suspended particles that may harbor pathogens. Warning level triggers yellow alerts, Critical level triggers red alerts with SMS."
          />
        </label>
        
        {/* Visual Band Diagram for Max-Only Parameters */}
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="text-xs font-medium text-blue-900 mb-2">💡 How Max Thresholds Work:</div>
          <div className="flex items-center justify-center space-x-1 text-xs">
            <div className="px-3 py-1 bg-green-200 rounded font-semibold">SAFE (Low Values)</div>
            <span>→</span>
            <div className="px-2 py-1 bg-red-200 rounded">Critical Max</div>
            <span>→</span>
            <div className="px-2 py-1 bg-yellow-200 rounded">Warning Max</div>
            <span>→</span>
            <div className="px-3 py-1 bg-gray-200 rounded">UNSAFE (High Values)</div>
          </div>
          <div className="text-xs text-blue-700 mt-2 text-center">
            Critical max must be SMALLER than warning max (triggers alert sooner)
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          {/* Warning Threshold */}
          <div className="border-2 border-yellow-300 rounded-lg p-4 bg-yellow-50">
            <div className="flex items-center mb-3">
              <span className="text-yellow-700 font-medium text-sm">⚠️ Warning Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Maximum Turbidity <span className="text-yellow-600">(Outer Limit)</span>
              </label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g., 5.0"
                value={thresholds?.turbidity?.warning?.max ?? ''}
                onChange={(e) => onChange('turbidity.warning.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Must be larger than critical max</p>
            </div>
          </div>
          
          {/* Critical Threshold */}
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <div className="flex items-center mb-3">
              <span className="text-red-700 font-medium text-sm">🔴 Critical Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Maximum Turbidity <span className="text-red-600">(Inner Limit)</span>
              </label>
              <input
                type="number"
                step="0.1"
                placeholder="e.g., 4.0"
                value={thresholds?.turbidity?.critical?.max ?? ''}
                onChange={(e) => onChange('turbidity.critical.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Must be smaller than warning max</p>
            </div>
          </div>
        </div>
        
        {errors['turbidity'] && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <XCircle className="h-4 w-4 mr-1" />
            {errors['turbidity']}
          </p>
        )}
        
        <div className="mt-3 p-2 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs font-medium text-gray-700">
            ✅ Valid Example: Critical Max (4.0) &lt; Warning Max (5.0)
          </p>
        </div>
      </div>

      {/* TDS Thresholds */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          TDS (ppm)
          <Tooltip 
            field="tds-severity" 
            content="WHO guideline: <500 ppm for acceptable taste. Higher values may indicate dissolved minerals or contaminants. Warning level triggers yellow alerts, Critical level triggers red alerts with SMS."
          />
        </label>
        
        <div className="grid grid-cols-2 gap-4">
          {/* Warning Threshold */}
          <div className="border-2 border-yellow-300 rounded-lg p-4 bg-yellow-50">
            <div className="flex items-center mb-3">
              <span className="text-yellow-700 font-medium text-sm">⚠️ Warning Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Maximum TDS <span className="text-yellow-600">(Outer Limit)</span>
              </label>
              <input
                type="number"
                step="1"
                placeholder="e.g., 500"
                value={thresholds?.tds?.warning?.max ?? ''}
                onChange={(e) => onChange('tds.warning.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Must be larger than critical max</p>
            </div>
          </div>
          
          {/* Critical Threshold */}
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <div className="flex items-center mb-3">
              <span className="text-red-700 font-medium text-sm">🔴 Critical Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Maximum TDS <span className="text-red-600">(Inner Limit)</span>
              </label>
              <input
                type="number"
                step="1"
                placeholder="e.g., 400"
                value={thresholds?.tds?.critical?.max ?? ''}
                onChange={(e) => onChange('tds.critical.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Must be smaller than warning max</p>
            </div>
          </div>
        </div>
        
        {errors['tds'] && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <XCircle className="h-4 w-4 mr-1" />
            {errors['tds']}
          </p>
        )}
        
        <div className="mt-3 p-2 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs font-medium text-gray-700">
            ✅ Valid Example: Critical Max (400) &lt; Warning Max (500)
          </p>
        </div>
      </div>

      {/* Temperature Thresholds */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Temperature (°C)
          <Tooltip 
            field="temperature-severity" 
            content="Typical range: 10-35°C. Extreme temperatures may affect water quality and indicate system issues. Warning level triggers yellow alerts, Critical level triggers red alerts with SMS."
          />
        </label>
        
        <div className="grid grid-cols-2 gap-4">
          {/* Warning Thresholds */}
          <div className="border-2 border-yellow-300 rounded-lg p-4 bg-yellow-50">
            <div className="flex items-center mb-3">
              <span className="text-yellow-700 font-medium text-sm">⚠️ Warning Level</span>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Minimum Temperature <span className="text-yellow-600">(Outer Lower Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 0"
                  value={thresholds?.temperature?.warning?.min ?? ''}
                  onChange={(e) => onChange('temperature.warning.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Must be smallest value</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Maximum Temperature <span className="text-yellow-600">(Outer Upper Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 40"
                  value={thresholds?.temperature?.warning?.max ?? ''}
                  onChange={(e) => onChange('temperature.warning.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Must be largest value</p>
              </div>
            </div>
          </div>
          
          {/* Critical Thresholds */}
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <div className="flex items-center mb-3">
              <span className="text-red-700 font-medium text-sm">🔴 Critical Level</span>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Minimum Temperature <span className="text-red-600">(Inner Lower Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 5"
                  value={thresholds?.temperature?.critical?.min ?? ''}
                  onChange={(e) => onChange('temperature.critical.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Between warning min and critical max</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Maximum Temperature <span className="text-red-600">(Inner Upper Bound)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g., 35"
                  value={thresholds?.temperature?.critical?.max ?? ''}
                  onChange={(e) => onChange('temperature.critical.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <p className="text-xs text-gray-500 mt-1">Between critical min and warning max</p>
              </div>
            </div>
          </div>
        </div>
        
        {errors['temperature'] && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <XCircle className="h-4 w-4 mr-1" />
            {errors['temperature']}
          </p>
        )}
        
        <div className="mt-3 p-2 bg-gray-50 rounded border border-gray-200">
          <p className="text-xs font-medium text-gray-700">
            ✅ Valid Example: Warning Min (0) &lt; Critical Min (5) &lt; Critical Max (35) &lt; Warning Max (40)
          </p>
        </div>
      </div>
    </div>
  );
};

export default SeverityThresholdSection;
