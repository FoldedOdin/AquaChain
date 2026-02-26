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
        
        <div className="grid grid-cols-2 gap-4">
          {/* Warning Thresholds */}
          <div className="border-2 border-yellow-300 rounded-lg p-4 bg-yellow-50">
            <div className="flex items-center mb-3">
              <span className="text-yellow-700 font-medium text-sm">⚠️ Warning Level</span>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Minimum pH</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.pH?.warning?.min ?? ''}
                  onChange={(e) => onChange('pH.warning.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Maximum pH</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.pH?.warning?.max ?? ''}
                  onChange={(e) => onChange('pH.warning.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
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
                <label className="block text-xs font-medium text-gray-700 mb-1">Minimum pH</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.pH?.critical?.min ?? ''}
                  onChange={(e) => onChange('pH.critical.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Maximum pH</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.pH?.critical?.max ?? ''}
                  onChange={(e) => onChange('pH.critical.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
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
        
        <p className="mt-2 text-xs text-gray-500">
          Relationship: Warning Min &lt; Critical Min &lt; Critical Max &lt; Warning Max
        </p>
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
        
        <div className="grid grid-cols-2 gap-4">
          {/* Warning Threshold */}
          <div className="border-2 border-yellow-300 rounded-lg p-4 bg-yellow-50">
            <div className="flex items-center mb-3">
              <span className="text-yellow-700 font-medium text-sm">⚠️ Warning Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Maximum Turbidity</label>
              <input
                type="number"
                step="0.1"
                value={thresholds?.turbidity?.warning?.max ?? ''}
                onChange={(e) => onChange('turbidity.warning.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>
          
          {/* Critical Threshold */}
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <div className="flex items-center mb-3">
              <span className="text-red-700 font-medium text-sm">🔴 Critical Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Maximum Turbidity</label>
              <input
                type="number"
                step="0.1"
                value={thresholds?.turbidity?.critical?.max ?? ''}
                onChange={(e) => onChange('turbidity.critical.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>
        
        {errors['turbidity'] && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <XCircle className="h-4 w-4 mr-1" />
            {errors['turbidity']}
          </p>
        )}
        
        <p className="mt-2 text-xs text-gray-500">
          Relationship: Critical Max &lt; Warning Max
        </p>
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
              <label className="block text-xs font-medium text-gray-700 mb-1">Maximum TDS</label>
              <input
                type="number"
                step="1"
                value={thresholds?.tds?.warning?.max ?? ''}
                onChange={(e) => onChange('tds.warning.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>
          
          {/* Critical Threshold */}
          <div className="border-2 border-red-300 rounded-lg p-4 bg-red-50">
            <div className="flex items-center mb-3">
              <span className="text-red-700 font-medium text-sm">🔴 Critical Level</span>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Maximum TDS</label>
              <input
                type="number"
                step="1"
                value={thresholds?.tds?.critical?.max ?? ''}
                onChange={(e) => onChange('tds.critical.max', parseFloat(e.target.value))}
                disabled={!editMode}
                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>
        
        {errors['tds'] && (
          <p className="mt-2 text-sm text-red-600 flex items-center">
            <XCircle className="h-4 w-4 mr-1" />
            {errors['tds']}
          </p>
        )}
        
        <p className="mt-2 text-xs text-gray-500">
          Relationship: Critical Max &lt; Warning Max
        </p>
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
                <label className="block text-xs font-medium text-gray-700 mb-1">Minimum Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.temperature?.warning?.min ?? ''}
                  onChange={(e) => onChange('temperature.warning.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Maximum Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.temperature?.warning?.max ?? ''}
                  onChange={(e) => onChange('temperature.warning.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
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
                <label className="block text-xs font-medium text-gray-700 mb-1">Minimum Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.temperature?.critical?.min ?? ''}
                  onChange={(e) => onChange('temperature.critical.min', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Maximum Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds?.temperature?.critical?.max ?? ''}
                  onChange={(e) => onChange('temperature.critical.max', parseFloat(e.target.value))}
                  disabled={!editMode}
                  className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
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
        
        <p className="mt-2 text-xs text-gray-500">
          Relationship: Warning Min &lt; Critical Min &lt; Critical Max &lt; Warning Max
        </p>
      </div>
    </div>
  );
};

export default SeverityThresholdSection;
