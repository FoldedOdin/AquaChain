import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  XMarkIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { User, Mail, Phone, MapPin, Lock } from 'lucide-react';

interface AddressObject {
  country?: string;
  pincode?: string;
  flatHouse?: string;
  areaStreet?: string;
  landmark?: string;
  city?: string;
  state?: string;
  formatted?: string;
}

interface EditProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentProfile: {
    firstName?: string;
    lastName?: string;
    email: string;
    phone?: string;
    address?: string | AddressObject;
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
  
  // Detailed address fields
  const [country, setCountry] = useState('India');
  const [pincode, setPincode] = useState('');
  const [flatHouse, setFlatHouse] = useState('');
  const [areaStreet, setAreaStreet] = useState('');
  const [landmark, setLandmark] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [countryCode, setCountryCode] = useState('+91'); // Default to India

  // OTP state
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [otpError, setOtpError] = useState('');
  const [resendTimer, setResendTimer] = useState(0);
  const [otpSentTo, setOtpSentTo] = useState('');

  // Track if we've initialized the form for this modal session
  const initializedRef = useRef(false);

  // Memoize stable values from currentProfile to prevent unnecessary re-renders
  const stableProfile = useMemo(() => ({
    firstName: currentProfile.firstName || '',
    lastName: currentProfile.lastName || '',
    email: currentProfile.email || '',
    phone: currentProfile.phone || '',
    address: currentProfile.address
  }), [
    currentProfile.firstName,
    currentProfile.lastName,
    currentProfile.email,
    currentProfile.phone,
    currentProfile.address
  ]);

  // Update form when modal opens (only once per open)
  useEffect(() => {
    if (isOpen && !initializedRef.current) {
      // Initialize form with current profile data
      setFirstName(stableProfile.firstName);
      setLastName(stableProfile.lastName);
      setEmail(stableProfile.email);
      
      // Parse phone number to extract country code
      const currentPhone = stableProfile.phone || '';
      if (currentPhone.startsWith('+')) {
        // Extract country code (e.g., +91 from +919876543210)
        const commonCodes = ['+91', '+1', '+44', '+61', '+81', '+86', '+33', '+49', '+39', '+34', '+7', '+55', '+27', '+971', '+65', '+60', '+62', '+63', '+66', '+84', '+92', '+880', '+94', '+977'];
        const matchedCode = commonCodes.find(code => currentPhone.startsWith(code));
        if (matchedCode) {
          setCountryCode(matchedCode);
          setPhone(currentPhone.substring(matchedCode.length));
        } else {
          // Default to +91 if no match
          setCountryCode('+91');
          setPhone(currentPhone.substring(1)); // Remove the +
        }
      } else {
        // No country code, assume it's just the number
        setCountryCode('+91');
        setPhone(currentPhone);
      }
      
      // Parse existing address - handle both object and string formats
      const addr = stableProfile.address;
      if (addr) {
        if (typeof addr === 'object' && !Array.isArray(addr)) {
          // Address is already an object
          const addressObj = addr as AddressObject;
          setCountry(addressObj.country || 'India');
          setPincode(addressObj.pincode || '');
          setFlatHouse(addressObj.flatHouse || '');
          setAreaStreet(addressObj.areaStreet || '');
          setLandmark(addressObj.landmark || '');
          setCity(addressObj.city || '');
          setState(addressObj.state || '');
        } else if (typeof addr === 'string' && addr) {
          // Legacy string format - try to parse comma-separated address
          const parts = addr.split(',').map(p => p.trim());
          if (parts.length >= 3) {
            setFlatHouse(parts[0] || '');
            setAreaStreet(parts[1] || '');
            setCity(parts[parts.length - 2] || '');
            setState(parts[parts.length - 1] || '');
          }
        }
      } else {
        // Reset address fields if no address
        setCountry('India');
        setPincode('');
        setFlatHouse('');
        setAreaStreet('');
        setLandmark('');
        setCity('');
        setState('');
      }
      
      // Reset other states
      setStep('form');
      setErrorMessage('');
      
      initializedRef.current = true;
    } else if (!isOpen) {
      // Reset the flag when modal closes so it reinitializes on next open
      initializedRef.current = false;
    }
  }, [isOpen, stableProfile]);

  // Resend timer countdown
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  // Check if sensitive fields changed
  const hasSensitiveChanges = () => {
    return email !== stableProfile.email || 
           phone !== stableProfile.phone;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!firstName.trim() || !lastName.trim()) {
      setErrorMessage('First name and last name are required');
      return;
    }

    // Validate pincode if provided
    if (pincode && !/^\d{6}$/.test(pincode)) {
      setErrorMessage('Pincode must be exactly 6 digits');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      // Build structured address object
      const addressObj = {
        country,
        pincode: pincode.trim(),
        flatHouse: flatHouse.trim(),
        areaStreet: areaStreet.trim(),
        landmark: landmark.trim(),
        city: city.trim(),
        state: state.trim(),
        // Also create formatted string for backward compatibility
        formatted: [flatHouse, areaStreet, landmark, city, state, pincode, country]
          .map(p => p ? p.trim() : '')
          .filter(p => p && p !== 'undefined')
          .join(', ')
      };

      // Format phone with country code (E.164 format)
      const formattedPhone = phone.trim() ? `${countryCode}${phone.trim()}` : '';

      const updates = {
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        phone: formattedPhone,
        address: addressObj
      };

      // Check if sensitive information changed
      const needsVerification = hasSensitiveChanges();
      setRequiresOTP(needsVerification);

      if (needsVerification) {
        // Request OTP
        console.log('🔐 Requesting OTP for profile update...');
        console.log('📧 Email:', currentProfile.email);
        console.log('📝 Changes:', updates);
        
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
        console.log('📬 OTP Request Response:', result);

        if (!response.ok) {
          console.error('❌ OTP Request Failed:', {
            status: response.status,
            statusText: response.statusText,
            error: result.error,
            message: result.message,
            details: result.details
          });
          
          // Show detailed error message
          let errorMsg = 'Failed to send OTP';
          if (result.error?.includes('SES') || result.error?.includes('email')) {
            errorMsg = 'Email service error. Please contact support or try again later.';
          } else if (result.message) {
            errorMsg = result.message;
          } else if (result.error) {
            errorMsg = result.error;
          }
          
          throw new Error(errorMsg);
        }

        // Log success details
        console.log('✅ OTP sent successfully');
        console.log('📮 Delivery method:', result.deliveryMethod);
        console.log('📧 Sent to:', result.deliveryTarget);
        
        // In dev mode, show OTP in console and alert
        if (result.devOtp) {
          console.log('🔑 DEV MODE - OTP:', result.devOtp);
          console.log('⚠️ This OTP is only visible in development mode');
          
          // Show alert with OTP for easy testing
          alert(`🔑 DEV MODE\n\nYour OTP is: ${result.devOtp}\n\nThis is only shown in development mode.`);
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
          throw new Error(result.message || result.error || 'Failed to update profile');
        }

        // Update localStorage with new profile data
        const storedUser = localStorage.getItem('aquachain_user');
        if (storedUser) {
          const userData = JSON.parse(storedUser);
          userData.profile = {
            ...userData.profile,
            firstName: updates.firstName,
            lastName: updates.lastName,
            phone: updates.phone,
            address: updates.address
          };
          localStorage.setItem('aquachain_user', JSON.stringify(userData));
          console.log('✅ Updated profile in localStorage');
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
      console.log('🔐 Verifying OTP...');
      
      // Build structured address object
      const addressObj = {
        country,
        pincode: pincode.trim(),
        flatHouse: flatHouse.trim(),
        areaStreet: areaStreet.trim(),
        landmark: landmark.trim(),
        city: city.trim(),
        state: state.trim(),
        formatted: [flatHouse, areaStreet, landmark, city, state, pincode, country]
          .map(p => p ? p.trim() : '')
          .filter(p => p && p !== 'undefined')
          .join(', ')
      };

      // Format phone with country code (E.164 format)
      const formattedPhone = phone.trim() ? `${countryCode}${phone.trim()}` : '';

      const updates = {
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        phone: formattedPhone,
        address: addressObj
      };

      console.log('📝 Submitting OTP verification with updates:', updates);

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
      console.log('📬 OTP Verification Response:', result);

      if (!response.ok) {
        console.error('❌ OTP Verification Failed:', {
          status: response.status,
          statusText: response.statusText,
          error: result.error,
          message: result.message
        });
        
        let errorMsg = 'Invalid OTP';
        if (result.message) {
          errorMsg = result.message;
        } else if (result.error) {
          errorMsg = result.error;
        }
        
        throw new Error(errorMsg);
      }

      console.log('✅ Profile updated successfully');

      // Update localStorage with new profile data
      const storedUser = localStorage.getItem('aquachain_user');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        userData.profile = {
          ...userData.profile,
          firstName: updates.firstName,
          lastName: updates.lastName,
          phone: updates.phone,
          address: updates.address
        };
        localStorage.setItem('aquachain_user', JSON.stringify(userData));
        console.log('✅ Updated profile in localStorage after OTP verification');
      }

      setStep('success');
      setTimeout(() => {
        onProfileUpdated();
        handleClose();
      }, 2000);

    } catch (error: any) {
      console.error('❌ OTP verification error:', error);
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
      // Build structured address object
      const addressObj = {
        country,
        pincode: pincode.trim(),
        flatHouse: flatHouse.trim(),
        areaStreet: areaStreet.trim(),
        landmark: landmark.trim(),
        city: city.trim(),
        state: state.trim(),
        formatted: [flatHouse, areaStreet, landmark, city, state, pincode, country]
          .map(p => p ? p.trim() : '')
          .filter(p => p && p !== 'undefined')
          .join(', ')
      };

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
            phone: phone.trim() ? `${countryCode}${phone.trim()}` : '',
            address: addressObj
          }
        })
      });

      const result = await response.json();
      console.log('📬 Resend OTP Response:', result);

      if (!response.ok) {
        console.error('❌ Resend OTP Failed:', {
          status: response.status,
          statusText: response.statusText,
          error: result.error,
          message: result.message
        });
        
        let errorMsg = 'Failed to resend OTP';
        if (result.error?.includes('SES') || result.error?.includes('email')) {
          errorMsg = 'Email service error. Please contact support or try again later.';
        } else if (result.message) {
          errorMsg = result.message;
        } else if (result.error) {
          errorMsg = result.error;
        }
        
        throw new Error(errorMsg);
      }

      console.log('✅ OTP resent successfully');
      
      // In dev mode, show OTP
      if (result.devOtp) {
        console.log('🔑 DEV MODE - New OTP:', result.devOtp);
        alert(`🔑 DEV MODE\n\nYour new OTP is: ${result.devOtp}\n\nThis is only shown in development mode.`);
      }

      setResendTimer(60);
      setOtp(['', '', '', '', '', '']);
      
    } catch (error: any) {
      console.error('❌ Resend OTP error:', error);
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
    setIsSubmitting(false);
    setRequiresOTP(false);
    onClose();
  };

  // Indian states list
  const indianStates = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
  ];
  
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

                {/* Address Section */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Address Details</h3>
                  
                  {/* Country/Region */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Country/Region
                    </label>
                    <select
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                    >
                      <option value="India">India</option>
                    </select>
                  </div>

                  {/* Full Name */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Full name (First and Last name)
                    </label>
                    <input
                      type="text"
                      value={`${firstName} ${lastName}`.trim()}
                      readOnly
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-50 text-gray-600"
                    />
                  </div>

                  {/* Mobile Number with Country Code */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Mobile number
                    </label>
                    <div className="flex gap-2">
                      <select
                        value={countryCode}
                        onChange={(e) => setCountryCode(e.target.value)}
                        className="w-32 px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                      >
                        <option value="+91">🇮🇳 +91</option>
                        <option value="+1">🇺🇸 +1</option>
                        <option value="+44">🇬🇧 +44</option>
                        <option value="+61">🇦🇺 +61</option>
                        <option value="+81">🇯🇵 +81</option>
                        <option value="+86">🇨🇳 +86</option>
                        <option value="+33">🇫🇷 +33</option>
                        <option value="+49">🇩🇪 +49</option>
                        <option value="+39">🇮🇹 +39</option>
                        <option value="+34">🇪🇸 +34</option>
                        <option value="+7">🇷🇺 +7</option>
                        <option value="+55">🇧🇷 +55</option>
                        <option value="+27">🇿🇦 +27</option>
                        <option value="+971">🇦🇪 +971</option>
                        <option value="+65">🇸🇬 +65</option>
                        <option value="+60">🇲🇾 +60</option>
                        <option value="+62">🇮🇩 +62</option>
                        <option value="+63">🇵🇭 +63</option>
                        <option value="+66">🇹🇭 +66</option>
                        <option value="+84">🇻🇳 +84</option>
                        <option value="+92">🇵🇰 +92</option>
                        <option value="+880">🇧🇩 +880</option>
                        <option value="+94">🇱🇰 +94</option>
                        <option value="+977">🇳🇵 +977</option>
                      </select>
                      <input
                        type="tel"
                        value={phone}
                        onChange={(e) => {
                          // Remove non-numeric characters
                          const cleaned = e.target.value.replace(/\D/g, '');
                          setPhone(cleaned);
                        }}
                        placeholder="9876543210"
                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      Enter number without country code. Used for OTP verification and delivery updates.
                    </p>
                  </div>

                  {/* Pincode */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Pincode
                    </label>
                    <input
                      type="text"
                      value={pincode}
                      onChange={(e) => setPincode(e.target.value)}
                      placeholder="6 digits [0-9] PIN code"
                      maxLength={6}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Flat, House no., Building, Company, Apartment */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Flat, House no., Building, Company, Apartment
                    </label>
                    <input
                      type="text"
                      value={flatHouse}
                      onChange={(e) => setFlatHouse(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Area, Street, Sector, Village */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Area, Street, Sector, Village
                    </label>
                    <input
                      type="text"
                      value={areaStreet}
                      onChange={(e) => setAreaStreet(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Landmark */}
                  <div className="mb-4">
                    <label className="block text-sm font-semibold text-gray-900 mb-2">
                      Landmark
                    </label>
                    <input
                      type="text"
                      value={landmark}
                      onChange={(e) => setLandmark(e.target.value)}
                      placeholder="E.g. near apollo hospital"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Town/City and State */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        Town/City
                      </label>
                      <input
                        type="text"
                        value={city}
                        onChange={(e) => setCity(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-900 mb-2">
                        State
                      </label>
                      <select
                        value={state}
                        onChange={(e) => setState(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                      >
                        <option value="">Choose a state</option>
                        {indianStates.map((stateName) => (
                          <option key={stateName} value={stateName}>
                            {stateName}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

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
