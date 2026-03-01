import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { PencilIcon, CheckIcon, XMarkIcon, PhoneIcon, UserIcon, EnvelopeIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../contexts/AuthContext';
import adminService from '../../services/adminService';

interface AdminProfileProps {
  onUpdate?: () => void;
}

const AdminProfile: React.FC<AdminProfileProps> = ({ onUpdate }) => {
  const { user, refreshUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    firstName: user?.profile?.firstName || '',
    lastName: user?.profile?.lastName || '',
    phone: user?.profile?.phone || ''
  });

  const handleEdit = () => {
    setIsEditing(true);
    setError(null);
    setSuccess(null);
    setFormData({
      firstName: user?.profile?.firstName || '',
      lastName: user?.profile?.lastName || '',
      phone: user?.profile?.phone || ''
    });
  };

  const handleCancel = () => {
    setIsEditing(false);
    setError(null);
    setSuccess(null);
    setFormData({
      firstName: user?.profile?.firstName || '',
      lastName: user?.profile?.lastName || '',
      phone: user?.profile?.phone || ''
    });
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      setError(null);
      setSuccess(null);

      // Validate inputs
      if (!formData.firstName.trim()) {
        setError('First name is required');
        return;
      }

      if (!formData.lastName.trim()) {
        setError('Last name is required');
        return;
      }

      // Validate phone number format (optional but if provided, must be valid)
      if (formData.phone && !isValidPhone(formData.phone)) {
        setError('Please enter a valid phone number (e.g., +1234567890 or 1234567890)');
        return;
      }

      // Update profile via API
      await adminService.updateProfile({
        profile: {
          firstName: formData.firstName.trim(),
          lastName: formData.lastName.trim(),
          phone: formData.phone.trim()
        }
      });

      // Refresh user data
      await refreshUser();

      setSuccess('Profile updated successfully');
      setIsEditing(false);

      // Call onUpdate callback if provided
      if (onUpdate) {
        onUpdate();
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      console.error('Profile update error:', err);
      setError(err.message || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const isValidPhone = (phone: string): boolean => {
    // Allow formats: +1234567890, 1234567890, (123) 456-7890, 123-456-7890
    const phoneRegex = /^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
  };

  const formatPhone = (phone: string): string => {
    if (!phone) return 'Not provided';
    
    // Remove all non-digit characters
    const cleaned = phone.replace(/\D/g, '');
    
    // Indian phone number format: +91 XXXXX XXXXX or XXXXX XXXXX
    if (cleaned.startsWith('91') && cleaned.length === 12) {
      // Format: +91 XXXXX XXXXX
      return `+91 ${cleaned.slice(2, 7)} ${cleaned.slice(7)}`;
    } else if (cleaned.length === 10) {
      // Format: XXXXX XXXXX (without country code)
      return `${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('0')) {
      // Format with leading 0: 0XXXXX XXXXX
      return `${cleaned.slice(0, 6)} ${cleaned.slice(6)}`;
    }
    
    // Fallback: return as-is if format doesn't match
    return phone;
  };

  if (!user) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Administrator Profile</h2>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-purple-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition-colors duration-200"
          >
            <PencilIcon className="w-4 h-4" />
            Edit Profile
          </button>
        )}
      </div>

      {/* Success Message */}
      {success && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center gap-2 text-green-800"
        >
          <CheckIcon className="w-5 h-5" />
          <span className="text-sm font-medium">{success}</span>
        </motion.div>
      )}

      {/* Error Message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800"
        >
          <XMarkIcon className="w-5 h-5" />
          <span className="text-sm font-medium">{error}</span>
        </motion.div>
      )}

      {/* Profile Content */}
      <div className="space-y-4">
        {/* Name Fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* First Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <div className="flex items-center gap-2">
                <UserIcon className="w-4 h-4" />
                First Name
              </div>
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter first name"
              />
            ) : (
              <p className="text-gray-900 py-2">{user.profile?.firstName || 'Not provided'}</p>
            )}
          </div>

          {/* Last Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <div className="flex items-center gap-2">
                <UserIcon className="w-4 h-4" />
                Last Name
              </div>
            </label>
            {isEditing ? (
              <input
                type="text"
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Enter last name"
              />
            ) : (
              <p className="text-gray-900 py-2">{user.profile?.lastName || 'Not provided'}</p>
            )}
          </div>
        </div>

        {/* Email (Read-only) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <div className="flex items-center gap-2">
              <EnvelopeIcon className="w-4 h-4" />
              Email
            </div>
          </label>
          <p className="text-gray-900 py-2">{user.email}</p>
          <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
        </div>

        {/* Phone Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <div className="flex items-center gap-2">
              <PhoneIcon className="w-4 h-4" />
              Mobile Number
            </div>
          </label>
          {isEditing ? (
            <div>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="+91 XXXXX XXXXX or 10-digit number"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter Indian mobile number (e.g., +919876543210 or 9876543210)
              </p>
            </div>
          ) : (
            <p className="text-gray-900 py-2">{formatPhone(user.profile?.phone || '')}</p>
          )}
        </div>

        {/* Role (Read-only) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
          <div className="inline-flex items-center gap-2 bg-purple-100 text-purple-700 px-3 py-1.5 rounded-full text-sm font-medium">
            <span className="capitalize">{user.role}</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      {isEditing && (
        <div className="flex items-center gap-3 mt-6 pt-6 border-t border-gray-200">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200"
          >
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <CheckIcon className="w-4 h-4" />
                Save Changes
              </>
            )}
          </button>
          <button
            onClick={handleCancel}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          >
            <XMarkIcon className="w-4 h-4" />
            Cancel
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default AdminProfile;
