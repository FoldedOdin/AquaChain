import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { User, Mail, Phone, MapPin, Lock, Map } from 'lucide-react';
import AddressMapPicker from './AddressMapPicker';

interface EditProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentProfile: {
    firstName?: string;
    lastName?: string;
    email: string;
    phone?: string;
    address?: string;
  };
  onProfileUpdated: () => void;
}

type EditStep = 'form' | 'otp' | 'success' | 'error';

const EditProfileModal: React.FC<EditProfileModalProps> = ({ 
  isOpen, 
  onClose, 
  currentProfile,
  onProfileUpdated 
}) => {
  const [step, setStep] = useState<EditStep>('form');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [requiresOTP, setRequiresOTP] = useState(false);

  // Form state
  const [firstName, setFirstName] = useState(currentProfile.firstName || '');
  const [lastName, setLastName] = useState(currentProfile.lastName || '');
  const [email, setEmail] = useState(currentProfile.email || '');
  const [phone, setPhone] = useState(currentProfile.phone || '');
  const [address, setAddress] = useState(currentProfile.address || '');
  const [password, setPassword] = useState('');

  // OTP state
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [otpError, setOtpError] = useState('');
  const [resendTimer, setResendTimer] = useState(0);
  const [otpSentTo, setOtpSentTo] = useState('');
  const [showMapPicker, setShowMapPicker] = useState(false);

  // Track if modal was just opened to initialize form only once
  const prevIsOpenRef = useRef(false);

  // Update form only when modal is first opened, not on every render
  useEffect(() => {
    // Only initialize when modal transitions from closed to open
    if (isOpen && !prevIsOpenRef.current) {
      setFirstName(currentProfile.firstName || '');
      setLastName(currentProfile.lastName || '');
      setEmail(currentProfile.email || '');
      setPhone(currentProfile.phone || '');
      setAddress(currentProfile.address || '');
    }
    prevIsOpenRef.current = isOpen;
  }, [isOpen, currentProfile.firstName, currentProfile.lastName, currentProfile.email, currentProfile.phone, currentProfile.address]);

  // Resend timer countdown
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  // Check if sensitive fields changed
  const hasSensitiveChanges = () => {
    return email !== currentProfile.email || 
           phone !== currentProfile.phone;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!firstName.trim() || !lastName.trim()) {
      setErrorMessage('First name and last name are required');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const updates = {
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        address: address.trim()
      };

      // Check if sensitive information changed
      const needsVerification = hasSensitiveChanges();
      setRequiresOTP(needsVerification);

      if (needsVerification) {
        // Request OTP
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/profile/request-otp`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
          },
          body: JSON.stringify({
            email: currentProfile.email, // Send to current email
            changes: updates
          })
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || 'Failed to send OTP');
        }

        setOtpSentTo(currentProfile.email);
        setResendTimer(60); // 60 seconds cooldown
        setStep('otp');
      } else {
        // No sensitive changes, update directly
        const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/profile/update`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
          },
          body: JSON.stringify(updates)
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.error || 'Failed to update profile');
        }

        setStep('success');
        setTimeout(() => {
          onProfileUpdated();
          handleClose();
        }, 2000);
      }

    } catch (error: any) {
      console.error('Profile update error:', error);
      setErrorMessage(error.message || 'Failed to update profile. Please try again.');
      setStep('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) return; // Only allow single digit
    
    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);
    setOtpError('');

    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handleVerifyOtp = async () => {
    const otpCode = otp.join('');
    
    if (otpCode.length !== 6) {
      setOtpError('Please enter complete OTP');
      return;
    }

    setIsSubmitting(true);
    setOtpError('');

    try {
      const updates = {
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        address: address.trim()
      };

      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/profile/verify-and-update`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        },
        body: JSON.stringify({
          otp: otpCode,
          updates
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Invalid OTP');
      }

      setStep('success');
      setTimeout(() => {
        onProfileUpdated();
        handleClose();
      }, 2000);

    } catch (error: any) {
      console.error('OTP verification error:', error);
      setOtpError(error.message || 'Invalid OTP. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendTimer > 0) return;

    setIsSubmitting(true);
    setOtpError('');

    try {
      const response = await fetch(`${process.env.REACT_APP_API_ENDPOINT}/api/profile/request-otp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('aquachain_token')}`
        },
        body: JSON.stringify({
          email: currentProfile.email,
          changes: {
            firstName: firstName.trim(),
            lastName: lastName.trim(),
            email: email.trim(),
            phone: phone.trim(),
            address: address.trim()
          }
        })
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to resend OTP');
      }

      setResendTimer(60);
      setOtp(['', '', '', '', '', '']);
      
    } catch (error: any) {
      setOtpError(error.message || 'Failed to resend OTP');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setStep('form');
    setOtp(['', '', '', '', '', '']);
    setOtpError('');
    setErrorMessage('');
    setPassword('');
    setIsSubmitting(false);
    setRequiresOTP(false);
    onClose();
  };

  console.log('EditProfileModal render - isOpen:', isOpen);
  
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-indigo-600 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                <User className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white">
                {step === 'otp' ? 'Verify Your Identity' : 'Edit Profile'}
              </h2>
            </div>
            <button
              onClick={handleClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(90vh-140px)] p-6">
            {step === 'success' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <CheckCircleIcon className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Profile Updated Successfully!</h3>
                <p className="text-gray-600">Your profile information has been updated.</p>
              </motion.div>
            )}

            {step === 'error' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-12"
              >
                <ExclamationTriangleIcon className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Update Failed</h3>
                <p className="text-gray-600 mb-4">{errorMessage}</p>
                <button
                  onClick={() => setStep('form')}
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
                >
                  Try Again
                </button>
              </motion.div>
            )}

            {step === 'otp' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="text-center mb-6">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <ShieldCheckIcon className="w-8 h-8 text-blue-600" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Enter Verification Code</h3>
                  <p className="text-gray-600">
                    We've sent a 6-digit code to <strong>{otpSentTo}</strong>
                  </p>
                </div>

                {/* OTP Input */}
                <div className="flex justify-center space-x-3 mb-6">
                  {otp.map((digit, index) => (
                    <input
                      key={index}
                      id={`otp-${index}`}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpChange(index, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(index, e)}
                      className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  ))}
                </div>

                {otpError && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 text-center">
                    {otpError}
                  </div>
                )}

                {/* Resend OTP */}
                <div className="text-center mb-6">
                  {resendTimer > 0 ? (
                    <p className="text-sm text-gray-600">
                      Resend code in <strong>{resendTimer}s</strong>
                    </p>
                  ) : (
                    <button
                      onClick={handleResendOtp}
                      disabled={isSubmitting}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
                    >
                      Resend Code
                    </button>
                  )}
                </div>

                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <ShieldCheckIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-900">
                      <p className="font-semibold mb-1">Why do I need to verify?</p>
                      <p>You're changing sensitive information (email or phone). We need to verify it's really you for security.</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {step === 'form' && (
              <form onSubmit={handleSubmit}>
                <p className="text-gray-600 mb-6">
                  Update your profile information. Changes to email or phone will require verification.
                </p>

                {/* Name Fields */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      First Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <User className="w-5 h-5 text-gray-400" />
                      </div>
                      <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Last Name <span className="text-red-500">*</span>
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <User className="w-5 h-5 text-gray-400" />
                      </div>
                      <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>
                  </div>
                </div>

                {/* Email */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Email Address <span className="text-red-500">*</span>
                    {email !== currentProfile.email && (
                      <span className="ml-2 text-xs text-orange-600 font-normal">
                        (Requires verification)
                      </span>
                    )}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Mail className="w-5 h-5 text-gray-400" />
                    </div>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                </div>

                {/* Phone */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Phone Number
                    {phone !== currentProfile.phone && phone && (
                      <span className="ml-2 text-xs text-orange-600 font-normal">
                        (Requires verification)
                      </span>
                    )}
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <Phone className="w-5 h-5 text-gray-400" />
                    </div>
                    <input
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91 xxxxxxxxxx"
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Address */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold text-gray-900 mb-2">
                    Address
                  </label>
                  
                  {!showMapPicker ? (
                    <div className="space-y-3">
                      <div className="relative">
                        <div className="absolute top-3 left-0 pl-3 flex items-start pointer-events-none">
                          <MapPin className="w-5 h-5 text-gray-400" />
                        </div>
                        <textarea
                          value={address}
                          onChange={(e) => setAddress(e.target.value)}
                          placeholder="Road, City, State, ZIP"
                          rows={3}
                          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                        />
                      </div>
                      <button
                        type="button"
                        onClick={() => setShowMapPicker(true)}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 border-2 border-blue-500 text-blue-600 rounded-lg hover:bg-blue-50 transition"
                      >
                        <Map className="w-4 h-4" />
                        Pick Address on Map
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <AddressMapPicker
                        onAddressSelect={(selectedAddress) => {
                          setAddress(selectedAddress.formatted);
                          setShowMapPicker(false);
                        }}
                        initialAddress={address}
                      />
                      <button
                        type="button"
                        onClick={() => setShowMapPicker(false)}
                        className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
                      >
                        Cancel Map Selection
                      </button>
                    </div>
                  )}
                </div>

                {/* Security Notice */}
                {hasSensitiveChanges() && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
                    <div className="flex items-start space-x-3">
                      <Lock className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                      <div className="text-sm text-orange-900">
                        <p className="font-semibold mb-1">Verification Required</p>
                        <p>You're changing sensitive information. We'll send a verification code to your current email address.</p>
                      </div>
                    </div>
                  </div>
                )}

                {errorMessage && (
                  <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                    {errorMessage}
                  </div>
                )}
              </form>
            )}
          </div>

          {/* Footer */}
          {step === 'form' && (
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
              <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="w-4 h-4" />
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </div>
          )}

          {step === 'otp' && (
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t">
              <button
                onClick={() => setStep('form')}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
              >
                Back
              </button>
              <button
                onClick={handleVerifyOtp}
                disabled={isSubmitting || otp.join('').length !== 6}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Verifying...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheckIcon className="w-4 h-4" />
                    <span>Verify & Update</span>
                  </>
                )}
              </button>
            </div>
          )}
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default EditProfileModal;
