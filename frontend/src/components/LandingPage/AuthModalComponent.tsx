import React, { useState, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { LoginForm, SignupForm } from './AuthForms';
import { LoginCredentials, SignupData } from './AuthModal';

interface AuthModalComponentProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: 'login' | 'signup';
  onLogin: (credentials: LoginCredentials) => Promise<void>;
  onSignup: (userData: SignupData) => Promise<void>;
}

/**
 * Authentication Modal Component
 * Provides tabbed interface for login and signup
 */
const AuthModalComponent: React.FC<AuthModalComponentProps> = ({
  isOpen,
  onClose,
  initialTab = 'login',
  onLogin,
  onSignup
}) => {
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>(initialTab);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setError(null);
      setSuccess(null);
      setIsLoading(false);
    }
  }, [isOpen, initialTab]);

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={handleClose}>
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
                  onClick={handleClose}
                  disabled={isLoading}
                  aria-label="Close modal"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>

                {/* Modal Title */}
                <Dialog.Title
                  as="h3"
                  className="text-2xl font-bold text-gray-900 mb-6 text-center"
                >
                  {activeTab === 'login' ? 'Welcome Back' : 'Create Account'}
                </Dialog.Title>

                {/* Tab Navigation */}
                <div className="flex border-b border-gray-200 mb-6">
                  <button
                    type="button"
                    className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                      activeTab === 'login'
                        ? 'text-aqua-600 border-b-2 border-aqua-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => {
                      setActiveTab('login');
                      setError(null);
                      setSuccess(null);
                    }}
                    disabled={isLoading}
                  >
                    Sign In
                  </button>
                  <button
                    type="button"
                    className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                      activeTab === 'signup'
                        ? 'text-aqua-600 border-b-2 border-aqua-600'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                    onClick={() => {
                      setActiveTab('signup');
                      setError(null);
                      setSuccess(null);
                    }}
                    disabled={isLoading}
                  >
                    Sign Up
                  </button>
                </div>

                {/* Form Content */}
                <div className="mt-4">
                  {activeTab === 'login' ? (
                    <LoginForm
                      onSubmit={onLogin}
                      isLoading={isLoading}
                      setIsLoading={setIsLoading}
                      error={error}
                      setError={setError}
                      success={success}
                      setSuccess={setSuccess}
                    />
                  ) : (
                    <SignupForm
                      onSubmit={onSignup}
                      isLoading={isLoading}
                      setIsLoading={setIsLoading}
                      error={error}
                      setError={setError}
                      success={success}
                      setSuccess={setSuccess}
                    />
                  )}
                </div>

                {/* Switch Tab Link */}
                <div className="mt-6 text-center text-sm text-gray-600">
                  {activeTab === 'login' ? (
                    <>
                      Don't have an account?{' '}
                      <button
                        type="button"
                        className="text-aqua-600 hover:text-aqua-500 font-medium focus:outline-none focus:underline"
                        onClick={() => setActiveTab('signup')}
                        disabled={isLoading}
                      >
                        Sign up
                      </button>
                    </>
                  ) : (
                    <>
                      Already have an account?{' '}
                      <button
                        type="button"
                        className="text-aqua-600 hover:text-aqua-500 font-medium focus:outline-none focus:underline"
                        onClick={() => setActiveTab('login')}
                        disabled={isLoading}
                      >
                        Sign in
                      </button>
                    </>
                  )}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};

export default AuthModalComponent;
