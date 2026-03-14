/**
 * Technician Details Modal Component
 * Displays detailed information about assigned technician
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  UserIcon,
  PhoneIcon,
  EnvelopeIcon,
  MapPinIcon,
  StarIcon,
  ClockIcon,
  TruckIcon
} from '@heroicons/react/24/outline';
import { Technician, TechnicianAssignment } from '../../types/ordering';

interface TechnicianModalProps {
  technician: Technician | null;
  technicianAssignment?: TechnicianAssignment;
  isOpen: boolean;
  onClose: () => void;
}

const TechnicianModal: React.FC<TechnicianModalProps> = ({
  technician,
  technicianAssignment,
  isOpen,
  onClose
}) => {
  if (!isOpen || !technician) return null;

  // Format estimated arrival time
  const formatEstimatedArrival = (arrival: string | Date | undefined) => {
    if (!arrival) return 'Not specified';
    
    try {
      const date = typeof arrival === 'string' ? new Date(arrival) : arrival;
      if (isNaN(date.getTime())) return 'Not specified';
      
      return new Intl.DateTimeFormat('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }).format(date);
    } catch (error) {
      return 'Not specified';
    }
  };

  // Format distance
  const formatDistance = (distance: number | undefined) => {
    if (!distance || distance === 0) return 'Not specified';
    return `${distance.toFixed(1)} km`;
  };

  // Format rating
  const formatRating = (rating: number | undefined) => {
    if (!rating || rating === 0) return null;
    return rating.toFixed(1);
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Technician Details
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <XMarkIcon className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Technician Profile */}
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                <UserIcon className="h-8 w-8 text-indigo-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">
                  {technician.name || 'Technician'}
                </h3>
                {technician.experience && (
                  <p className="text-sm text-gray-600">
                    {technician.experience} experience
                  </p>
                )}
                {formatRating(technician.rating) && (
                  <div className="flex items-center space-x-1 mt-1">
                    <StarIcon className="h-4 w-4 text-yellow-500 fill-current" />
                    <span className="text-sm font-medium text-gray-700">
                      {formatRating(technician.rating)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Contact Information */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-900 uppercase tracking-wide">
                Contact Information
              </h4>
              
              {technician.phone && (
                <div className="flex items-center space-x-3">
                  <PhoneIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Phone</p>
                    <a 
                      href={`tel:${technician.phone}`}
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      {technician.phone}
                    </a>
                  </div>
                </div>
              )}

              {technician.email && (
                <div className="flex items-center space-x-3">
                  <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Email</p>
                    <a 
                      href={`mailto:${technician.email}`}
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      {technician.email}
                    </a>
                  </div>
                </div>
              )}

              {technician.address && (
                <div className="flex items-center space-x-3">
                  <MapPinIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Service Center</p>
                    <p className="text-sm text-gray-600">{technician.address}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Assignment Details */}
            {technicianAssignment && (
              <div className="space-y-4">
                <h4 className="text-sm font-medium text-gray-900 uppercase tracking-wide">
                  Assignment Details
                </h4>
                
                <div className="grid grid-cols-1 gap-4">
                  {technicianAssignment.estimatedArrival && (
                    <div className="flex items-center space-x-3">
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Estimated Arrival</p>
                        <p className="text-sm text-gray-600">
                          {formatEstimatedArrival(technicianAssignment.estimatedArrival)}
                        </p>
                      </div>
                    </div>
                  )}

                  {technicianAssignment.distance > 0 && (
                    <div className="flex items-center space-x-3">
                      <TruckIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Distance</p>
                        <p className="text-sm text-gray-600">
                          {formatDistance(technicianAssignment.distance)}
                        </p>
                      </div>
                    </div>
                  )}

                  {technicianAssignment.estimatedTravelTime && (
                    <div className="flex items-center space-x-3">
                      <ClockIcon className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Travel Time</p>
                        <p className="text-sm text-gray-600">
                          {technicianAssignment.estimatedTravelTime} minutes
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Status */}
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium text-green-900">
                  {technician.status === 'assigned' ? 'Assigned to your order' : 'Active'}
                </span>
              </div>
              <p className="text-sm text-green-700 mt-1">
                Your technician has been notified and will contact you soon.
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
            <div className="flex justify-between items-center">
              <p className="text-xs text-gray-500">
                Need help? Contact support
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default TechnicianModal;