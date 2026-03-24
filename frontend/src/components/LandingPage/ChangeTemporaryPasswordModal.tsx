import React, { useState, Fragment } from 'react';
import { logger } from '../../utils/logger';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, CheckCircleIcon, ExclamationCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';

interface ChangeTemporaryPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  temporaryPassword: string;
  onSuccess: () => void;
}

/**
 * Change Temporary Password Modal
 * Handles the NEW_PASSWORD_REQUIRED flow when admin creates users
 */
const ChangeTemporaryPasswordModal: React.FC<ChangeTemporaryPasswordModalProps> = ({
  isOpen,
  onClose,
  email,
  temporaryPassword,
  onSuccess
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [success, setSuccess] = useState(false);

  // Password validation
  const validatePassword = (password: string): string | null => {
    if(password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if(!/[A-Z]/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if(!/[a-z]/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if(!/[0-9]/.test(password)) {
      return 'Password must contain at least one number';
    }
    if(!/[^A-Za-z0-9]/.test(password)) {
      return 'Password must contain at least one special character';
    }
    return null;
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate new password
    const passwordError = validatePassword(newPassword);
    if(passwordError) {
      setError(passwordError);
      return;
    }

    if(newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if(newPassword === temporaryPassword) {
      setError('New password must be different from temporary password');
      return;
    }

    setIsLoading(true);

    try {
      if(process.env.NODE_ENV === 'development' && process.env.REACT_APP_API_ENDPOINT?.includes('localhost')) {
        // Development mode - simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        logger.info('✅ Password changed successfully for:', email);
      } else {
        // Production - use AWS Cognito
        const { signIn, confirmSignIn } = await import('aws-amplify/auth');
        
        // First, sign in with temporary password
        const signInResult = await signIn({ 
          username: email, 
          password: temporaryPassword 
        });

        logger.info('🔐 SignIn result:', signInResult);

        // Check if new password is required
        if(signInResult.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') {
          // Complete the new password challenge
          await confirmSignIn({
            challengeResponse: newPassword
          });
          
          logger.info('✅ Password changed successfully');
        } else {
          throw new Error('Unexpected authentication state');
        }
      }

      setSuccess(true);
      
      // Auto-close and trigger success callback after 2 seconds
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 2000);
    } catch(err: unknown) {
      logger.error('❌ Password change error:', err);
      
      // Type guard for error objects
      const error = err as any;
      
      if(error?.name === 'NotAuthorizedException') {
        setError('Invalid temporary password. Please check your email for the correct password.');
      } else if(error?.name === 'InvalidPasswordException') {
        setError('Password does not meet requirements. Please try a stronger password.');
      } else {
        setError(error?.message || 'Failed to change password. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Reset state when modal closes
  React.useEffect(() => {
    if(!isOpen) {
      setTimeout(() => {
        setNewPassword('');
        setConfirmPassword('');
        setError(null);
        setSuccess(false);
        setIsLoading(false);
        setShowPassword(false);
      }, 300);
    }
  }, [isOpen]);

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={() => !isLoading && onClose()}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                {/* Close Button */}
                {!isLoading && !success && (
                  <button
                    type="button"
                    className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-aqua-500 rounded-full p-1"
                    onClick={onClose}
                    aria-label="Close modal"
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                )}

                {!success ? (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <Dialog.Title
                      as="h3"
                      className="text-2xl font-bold text-gray-900 mb-2"
                    >
                      Change Temporary Password
                    </Dialog.Title>
                    <p className="text-sm text-gray-600 mb-6">
                      You must change your temporary password before you can access your account.
                    </p>

                    {error && (
                      <div className="rounded-md bg-red-50 p-4 mb-4">
                        <div className="flex">
                          <ExclamationCircleIcon className="h-5 w-5 text-red-400 flex-shrink-0" />
                          <div className="ml-3">
                            <p className="text-sm text-red-800">{error}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <form onSubmit={handleChangePassword} className="space-y-4">
                      <div>
                        <label htmlFor="email-display" className="block text-sm font-medium text-gray-700 mb-2">
                          Email
                        </label>
                        <input
                          id="email-display"
                          type="email"
                          disabled
                          className="block w-full rounded-md border border-gray-300 px-3 py-2 bg-gray-50 text-gray-600 cursor-not-allowed"
                          value={email}
                        />
                      </div>

                      <div>
                        <label htmlFor="new-password" className="block text-sm font-medium text-gray-700 mb-2">
                          New Password
                        </label>
                        <div className="relative">
                          <input
                            id="new-password"
                            type={showPassword ? 'text' : 'password'}
                            required
                            className="block w-full rounded-md border border-gray-300 px-3 py-2 pr-10 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500"
                            placeholder="Enter new password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            className="absolute inset-y-0 right-0 pr-3 flex items-center"
                            onClick={() => setShowPassword(!showPassword)}
                          >
                            {showPassword ? (
                              <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                            ) : (
                              <EyeIcon className="h-5 w-5 text-gray-400" />
                            )}
                          </button>
                        </div>
                        <p className="mt-1 text-xs text-gray-500">
                          Must be 8+ characters with uppercase, lowercase, number, and special character
                        </p>
                      </div>

                      <div>
                        <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 mb-2">
                          Confirm New Password
                        </label>
                        <input
                          id="confirm-password"
                          type={showPassword ? 'text' : 'password'}
                          required
                          className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500"
                          placeholder="Confirm new password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={isLoading || !newPassword || !confirmPassword}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isLoading ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Changing Password...
                          </>
                        ) : (
                          'Change Password'
                        )}
                      </button>
                    </form>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center py-4"
                  >
                    <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
                      <CheckCircleIcon className="h-10 w-10 text-green-600" />
                    </div>
                    <Dialog.Title
                      as="h3"
                      className="text-2xl font-bold text-gray-900 mb-2"
                    >
                      Password Changed!
                    </Dialog.Title>
                    <p className="text-sm text-gray-600">
                      Your password has been successfully changed. Logging you in...
                    </p>
                  </motion.div>
                )}
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default ChangeTemporaryPasswordModal;
