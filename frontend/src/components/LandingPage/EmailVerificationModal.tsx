import React, { useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import authService from '../../services/authService';

interface EmailVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  onVerified: () => void;
}

const EmailVerificationModal: React.FC<EmailVerificationModalProps> = ({
  isOpen,
  onClose,
  email,
  onVerified
}) => {
  const [code, setCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isResending, setIsResending] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!code || code.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await authService.confirmSignUp(email, code);
      setSuccess('Email verified successfully!');
      
      // Wait a moment to show success message
      setTimeout(() => {
        onVerified();
        onClose();
      }, 1500);
    } catch (err: any) {
      if (err.code === 'CodeMismatchException') {
        setError('Invalid verification code. Please try again.');
      } else if (err.code === 'ExpiredCodeException') {
        setError('Verification code has expired. Please request a new one.');
      } else {
        setError(err.message || 'Verification failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendCode = async () => {
    setIsResending(true);
    setError(null);
    setSuccess(null);

    try {
      await authService.resendConfirmationCode(email);
      setSuccess('Verification code sent! Please check your email.');
    } catch (err: any) {
      setError(err.message || 'Failed to resend code. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  const handleCodeChange = (value: string) => {
    // Only allow digits and limit to 6 characters
    const sanitized = value.replace(/\D/g, '').slice(0, 6);
    setCode(sanitized);
    setError(null);
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

                {/* Modal Title */}
                <Dialog.Title
                  as="h3"
                  className="text-2xl font-bold text-gray-900 mb-2 text-center"
                >
                  Verify Your Email
                </Dialog.Title>

                <p className="text-sm text-gray-600 text-center mb-6">
                  We've sent a 6-digit verification code to<br />
                  <span className="font-medium text-gray-900">{email}</span>
                </p>

                {/* Error/Success Messages */}
                {error && (
                  <div className="mb-4 rounded-md bg-red-50 p-4" role="alert">
                    <div className="flex">
                      <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
                      <div className="ml-3">
                        <p className="text-sm text-red-800">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {success && (
                  <div className="mb-4 rounded-md bg-green-50 p-4" role="alert">
                    <div className="flex">
                      <CheckCircleIcon className="h-5 w-5 text-green-400" aria-hidden="true" />
                      <div className="ml-3">
                        <p className="text-sm text-green-800">{success}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Verification Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="verification-code" className="block text-sm font-medium text-gray-700 mb-2">
                      Verification Code
                    </label>
                    <input
                      id="verification-code"
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={6}
                      className="block w-full text-center text-2xl tracking-widest rounded-md border border-gray-300 px-3 py-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-aqua-500"
                      placeholder="000000"
                      value={code}
                      onChange={(e) => handleCodeChange(e.target.value)}
                      disabled={isLoading}
                      autoFocus
                      aria-describedby="code-description"
                    />
                    <p id="code-description" className="mt-2 text-xs text-gray-500 text-center">
                      Enter the 6-digit code from your email
                    </p>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading || code.length !== 6}
                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-aqua-600 hover:bg-aqua-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-aqua-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Verifying...
                      </>
                    ) : (
                      'Verify Email'
                    )}
                  </button>
                </form>

                {/* Resend Code */}
                <div className="mt-6 text-center">
                  <p className="text-sm text-gray-600">
                    Didn't receive the code?{' '}
                    <button
                      type="button"
                      className="text-aqua-600 hover:text-aqua-500 font-medium focus:outline-none focus:underline disabled:opacity-50"
                      onClick={handleResendCode}
                      disabled={isResending || isLoading}
                    >
                      {isResending ? 'Sending...' : 'Resend code'}
                    </button>
                  </p>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default EmailVerificationModal;
