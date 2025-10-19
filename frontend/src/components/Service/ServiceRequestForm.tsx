import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface ServiceRequestFormProps {
  onSubmit: (request: ServiceRequestData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

export interface ServiceRequestData {
  deviceId: string;
  issueType: string;
  priority: 'low' | 'medium' | 'high';
  description: string;
  preferredTime?: string;
  contactPhone?: string;
}

const ServiceRequestForm: React.FC<ServiceRequestFormProps> = ({
  onSubmit,
  onCancel,
  isSubmitting = false
}) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState<ServiceRequestData>({
    deviceId: user?.deviceIds[0] || '',
    issueType: '',
    priority: 'medium',
    description: '',
    preferredTime: '',
    contactPhone: user?.profile.phone || ''
  });

  const [errors, setErrors] = useState<Partial<ServiceRequestData>>({});

  const issueTypes = [
    { value: 'sensor_malfunction', label: 'Sensor Malfunction' },
    { value: 'connectivity_issues', label: 'Connectivity Issues' },
    { value: 'calibration_needed', label: 'Calibration Needed' },
    { value: 'physical_damage', label: 'Physical Damage' },
    { value: 'installation_support', label: 'Installation Support' },
    { value: 'maintenance_checkup', label: 'Routine Maintenance' },
    { value: 'other', label: 'Other Issue' }
  ];

  const validateForm = (): boolean => {
    const newErrors: Partial<ServiceRequestData> = {};

    if (!formData.deviceId) {
      newErrors.deviceId = 'Please select a device';
    }
    if (!formData.issueType) {
      newErrors.issueType = 'Please select an issue type';
    }
    if (!formData.description.trim()) {
      newErrors.description = 'Please provide a description';
    }
    if (formData.description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleInputChange = (field: keyof ServiceRequestData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Request Technician Service</h3>
        <p className="mt-1 text-sm text-gray-500">
          Fill out the form below to request a technician visit for your water quality device.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="px-6 py-4 space-y-6">
        {/* Device Selection */}
        <div>
          <label htmlFor="deviceId" className="block text-sm font-medium text-gray-700 mb-2">
            Device <span className="text-red-500">*</span>
          </label>
          <select
            id="deviceId"
            value={formData.deviceId}
            onChange={(e) => handleInputChange('deviceId', e.target.value)}
            className={`
              block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500
              ${errors.deviceId ? 'border-red-300' : 'border-gray-300'}
            `}
          >
            <option value="">Select a device</option>
            {user?.deviceIds.map(deviceId => (
              <option key={deviceId} value={deviceId}>
                {deviceId} - {deviceId === 'DEV-3421' ? 'Kitchen Sink' : 'Main Water Line'}
              </option>
            ))}
          </select>
          {errors.deviceId && (
            <p className="mt-1 text-sm text-red-600">{errors.deviceId}</p>
          )}
        </div>

        {/* Issue Type */}
        <div>
          <label htmlFor="issueType" className="block text-sm font-medium text-gray-700 mb-2">
            Issue Type <span className="text-red-500">*</span>
          </label>
          <select
            id="issueType"
            value={formData.issueType}
            onChange={(e) => handleInputChange('issueType', e.target.value)}
            className={`
              block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500
              ${errors.issueType ? 'border-red-300' : 'border-gray-300'}
            `}
          >
            <option value="">Select issue type</option>
            {issueTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
          {errors.issueType && (
            <p className="mt-1 text-sm text-red-600">{errors.issueType}</p>
          )}
        </div>

        {/* Priority */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Priority Level
          </label>
          <div className="flex space-x-4">
            {[
              { value: 'low', label: 'Low', color: 'text-green-600 border-green-300' },
              { value: 'medium', label: 'Medium', color: 'text-yellow-600 border-yellow-300' },
              { value: 'high', label: 'High', color: 'text-red-600 border-red-300' }
            ].map(priority => (
              <label key={priority.value} className="flex items-center">
                <input
                  type="radio"
                  name="priority"
                  value={priority.value}
                  checked={formData.priority === priority.value}
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                  className="mr-2 text-primary-600 focus:ring-primary-500"
                />
                <span className={`text-sm font-medium ${priority.color}`}>
                  {priority.label}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
            Description <span className="text-red-500">*</span>
          </label>
          <textarea
            id="description"
            rows={4}
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Please describe the issue in detail. Include any error messages, symptoms, or observations..."
            className={`
              block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500
              ${errors.description ? 'border-red-300' : 'border-gray-300'}
            `}
          />
          <div className="mt-1 flex justify-between">
            {errors.description ? (
              <p className="text-sm text-red-600">{errors.description}</p>
            ) : (
              <p className="text-sm text-gray-500">
                Minimum 10 characters ({formData.description.length}/10)
              </p>
            )}
          </div>
        </div>

        {/* Preferred Time */}
        <div>
          <label htmlFor="preferredTime" className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Time (Optional)
          </label>
          <input
            type="datetime-local"
            id="preferredTime"
            value={formData.preferredTime}
            onChange={(e) => handleInputChange('preferredTime', e.target.value)}
            min={new Date().toISOString().slice(0, 16)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
          <p className="mt-1 text-sm text-gray-500">
            Leave blank for earliest available appointment
          </p>
        </div>

        {/* Contact Phone */}
        <div>
          <label htmlFor="contactPhone" className="block text-sm font-medium text-gray-700 mb-2">
            Contact Phone
          </label>
          <input
            type="tel"
            id="contactPhone"
            value={formData.contactPhone}
            onChange={(e) => handleInputChange('contactPhone', e.target.value)}
            placeholder="+1 (555) 123-4567"
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
          <p className="mt-1 text-sm text-gray-500">
            We'll use this number to coordinate the service visit
          </p>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </>
            ) : (
              'Submit Request'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ServiceRequestForm;