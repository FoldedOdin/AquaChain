import React, { useState, Fragment } from 'react';
import { logger } from '../../utils/logger';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import { validateEmail } from '../../utils/security';
import authService from '../../services/authService';

interface PasswordResetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ResetStep = 'request' | 'verify' | 'success';

/**
 * Password Reset Modal Component
 * Handles forgot password flow with email verification
 */
const PasswordResetModal: React.FC<PasswordResetModalProps> = ({
  isOpen,
  onClose
}) => {
  const [step, setStep] = useState<ResetStep>('request');
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [devOtp, setDevOtp] = useState<string | null>(null);

  // Reset state when modal closes
  React.useEffect(() => {
    if(!isOpen) {
      setTimeout(() => {
        setStep('request');
        setEmail('');
        setVerificationCode('');
        setNewPassword('');
        setConfirmPassword('');
        setError(null);
        setIsLoading(false);
        setDevOtp(null);
      }, 300);
    }
  }, [isOpen]);

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if(!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      // Call password reset API
      if(process.env.NODE_ENV === 'development') {
        // Development mode - generate a mock OTP and show it before advancing
        await new Promise(resolve => setTimeout(resolve, 800));
        const mockOtp = String(Math.floor(100000 + Math.random() * 900000));
        console.log(`%c🔑 [DEV] Password reset OTP for ${email}: ${mockOtp}`, 'background:#1a1a2e;color:#00d4ff;font-size:14px;padding:4px 8px;border-radius:4px;font-weight:bold;');
        setDevOtp(mockOtp);
        logger.info('Password reset requested for:', email);
      } else {
        // Production - use AWS Cognito
        const { resetPassword } = await import('aws-amplify/auth');
        await resetPassword({ username: email });
      }

      setStep('verify');
    } catch(err) {
      setError(err instanceof Error ? err.message : 'Failed to send reset code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyAndReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate inputs
    if(!verificationCode.trim()) {
      setError('Please enter the verification code');
      return;
    }

    if(newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if(newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      if(process.env.NODE_ENV === 'development') {
        // Development mode - simulate API call
        await new Promise(resolve => setTimeout(resolve, 1500));
        logger.info('Password reset confirmed for:', email);
      } else {
        // Production - use AWS Cognito
        const { confirmResetPassword } = await import('aws-amplify/auth');
        await confirmResetPassword({
          username: email,
          confirmationCode: verificationCode,
          newPassword: newPassword
        });
      }

      setStep('success');
    } catch(err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setError(null);
    setIsLoading(true);

    try {
      if(process.env.NODE_ENV === 'development') {
        await new Promise(resolve => setTimeout(resolve, 1000));
        logger.info('Verification code resent to:', email);
      } else {
        const { resetPassword } = await import('aws-amplify/auth');
        await resetPassword({ username: email });
      }

      setError(null);
      // Show success message briefly
      const successMsg = 'Verification code resent! Check your email.';
      setError(successMsg);
      setTimeout(() => setError(null), 3000);
    } catch(err) {
      setError(err instanceof Error ? err.message : 'Failed to resend code');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
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
                <button
                  type="button"
                  className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-aqua-500 rounded-full p-1"
                  onClick={onClose}
                  disabled={isLoading}
                  aria-label="Close modal"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>

                {/* Request Reset Step */}
                {step === 'request' && (
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                  >
                    <Dialog.Title
                      as="h3"
                      className="text-2xl font-bold text-gray-900 mb-2"
                    >
                      Reset Password
                    </Dialog.Title>
                    <p className="text-sm text-gray-600 mb-6">
                      Enter your email address and we'll send you a verification code to reset your password.
                    </p>

                    {error && (
                      <div className="rounded-md bg-red-50 p-4 mb-4">
                        <div className="flex">
                          <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                          <div className="ml-3">
                            <p className="text-sm text-red-800">{error}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <form onSubmit={handleRequestReset} className="space-y-4">
                      <div>
                        <label htmlFor="reset-email" className="block text-sm font-medium text-gray-700 mb-2">
                          Email Address
                        </label>
                        <input
                          id="reset-email"
                          type="email"
                          required
                          className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500"
                          placeholder="Enter your email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>

                      <button
                        type="submit"
                        disabled={isLoading || !email}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isLoading ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Sending Code...
                          </>
                        ) : (
                          'Send Reset Code'
                        )}
                      </button>
                    </form>
                  </motion.div>
                )}

                {/* Verify and Reset Step */}
                {step === 'verify' && (
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                  >
                    <Dialog.Title
                      as="h3"
                      className="text-2xl font-bold text-gray-900 mb-2"
                    >
                      Enter Verification Code
                    </Dialog.Title>
                    <p className="text-sm text-gray-600 mb-6">
                      We've sent a verification code to <strong>{email}</strong>. Enter the code and your new password below.
                    </p>

                    {/* DEV MODE: show OTP inline so you don't need to check email */}
                    {process.env.NODE_ENV === 'development' && devOtp && (
                      <div className="rounded-md bg-yellow-50 border border-yellow-300 p-3 mb-4 flex items-center gap-3">
                        <span className="text-yellow-600 text-lg">🔑</span>
                        <div>
                          <p className="text-xs font-semibold text-yellow-800 uppercase tracking-wide">Dev Mode — OTP</p>
                          <p className="text-2xl font-mono font-bold text-yellow-900 tracking-widest">{devOtp}</p>
                        </div>
                      </div>
                    )}

                    {error && (
                      <div className={`rounded-md p-4 mb-4 ${error.includes('resent') ? 'bg-green-50' : 'bg-red-50'}`}>
                        <div className="flex">
                          {error.includes('resent') ? (
                            <CheckCircleIcon className="h-5 w-5 text-green-400" />
                          ) : (
                            <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                          )}
                          <div className="ml-3">
                            <p className={`text-sm ${error.includes('resent') ? 'text-green-800' : 'text-red-800'}`}>{error}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <form onSubmit={handleVerifyAndReset} className="space-y-4">
                      <div>
                        <label htmlFor="verification-code" className="block text-sm font-medium text-gray-700 mb-2">
                          Verification Code
                        </label>
                        <input
                          id="verification-code"
                          type="text"
                          required
                          className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500"
                          placeholder="Enter 6-digit code"
                          value={verificationCode}
                          onChange={(e) => setVerificationCode(e.target.value)}
                          disabled={isLoading}
                          maxLength={6}
                        />
                      </div>

                      <div>
                        <label htmlFor="new-password" className="block text-sm font-medium text-gray-700 mb-2">
                          New Password
                        </label>
                        <input
                          id="new-password"
                          type={showPassword ? 'text' : 'password'}
                          required
                          className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500"
                          placeholder="Enter new password"
                          value={newPassword}
                          onChange={(e) => setNewPassword(e.target.value)}
                          disabled={isLoading}
                        />
                      </div>

                      <div>
                        <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700 mb-2">
                          Confirm Password
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

                      <div className="flex items-center">
                        <input
                          id="show-password"
                          type="checkbox"
                          className="h-4 w-4 text-aqua-600 focus:ring-aqua-500 border-gray-300 rounded"
                          checked={showPassword}
                          onChange={(e) => setShowPassword(e.target.checked)}
                        />
                        <label htmlFor="show-password" className="ml-2 block text-sm text-gray-900">
                          Show password
                        </label>
                      </div>

                      <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isLoading ? (
                          <>
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Resetting Password...
                          </>
                        ) : (
                          'Reset Password'
                        )}
                      </button>

                      <div className="text-center">
                        <button
                          type="button"
                          onClick={handleResendCode}
                          disabled={isLoading}
                          className="text-sm text-aqua-600 hover:text-aqua-500 focus:outline-none focus:underline"
                        >
                          Didn't receive the code? Resend
                        </button>
                      </div>
                    </form>
                  </motion.div>
                )}

                {/* Success Step */}
                {step === 'success' && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center"
                  >
                    <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                      <CheckCircleIcon className="h-6 w-6 text-green-600" />
                    </div>
                    <Dialog.Title
                      as="h3"
                      className="text-2xl font-bold text-gray-900 mb-2"
                    >
                      Password Reset Successful!
                    </Dialog.Title>
                    <p className="text-sm text-gray-600 mb-6">
                      Your password has been successfully reset. You can now sign in with your new password.
                    </p>
                    <button
                      type="button"
                      onClick={onClose}
                      className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500"
                    >
                      Close
                    </button>
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

export default PasswordResetModal;
