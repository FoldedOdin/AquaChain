import React, { useState, useEffect, useRef } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { LoginForm, SignupForm } from './AuthForms';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogin: (credentials: LoginCredentials) => Promise<void>;
  onSignup: (userData: SignupData) => Promise<void>;
  initialTab?: 'login' | 'signup';
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe: boolean;
}

export interface SignupData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  role: 'consumer' | 'technician';
  acceptTerms: boolean;
}

const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onLogin,
  onSignup,
  initialTab = 'login'
}) => {
  const [activeTab, setActiveTab] = useState<'login' | 'signup'>(initialTab);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const initialFocusRef = useRef<HTMLButtonElement>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
      setError(null);
      setSuccess(null);
      setIsLoading(false);
    }
  }, [isOpen, initialTab]);

  const handleTabChange = (tab: 'login' | 'signup') => {
    setActiveTab(tab);
    setError(null);
    setSuccess(null);
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  return (
    <Transition appear show={isOpen} as={React.Fragment}>
      <Dialog
        as="div"
        className="relative z-50"
        onClose={handleClose}
        initialFocus={initialFocusRef}
      >
        {/* Backdrop */}
        <Transition.Child
          as={React.Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={React.Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white shadow-xl transition-all">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  transition={{ duration: 0.3 }}
                  className="relative"
                >
                  {/* Close button */}
                  <button
                    ref={initialFocusRef}
                    type="button"
                    className="absolute right-4 top-4 z-10 rounded-full p-2 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:ring-offset-2"
                    onClick={handleClose}
                    disabled={isLoading}
                    aria-label="Close authentication modal"
                  >
                    <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                  </button>

                  {/* Header with underwater theme */}
                  <div className="relative bg-gradient-to-br from-aqua-500 to-aqua-600 px-6 py-8 text-white">
                    <div className="absolute inset-0 bg-gradient-to-br from-aqua-400/20 to-transparent" />
                    <div className="relative">
                      <Dialog.Title
                        as="h3"
                        className="text-2xl font-bold leading-6"
                      >
                        Welcome to AquaChain
                      </Dialog.Title>
                      <p className="mt-2 text-aqua-100">
                        {activeTab === 'login' 
                          ? 'Sign in to access your water quality dashboard'
                          : 'Join the AquaChain network for real-time water monitoring'
                        }
                      </p>
                    </div>
                  </div>

                  {/* Tab navigation */}
                  <div className="border-b border-gray-200 bg-gray-50">
                    <nav className="-mb-px flex" aria-label="Authentication tabs">
                      <button
                        type="button"
                        className={`w-1/2 py-4 px-1 text-center border-b-2 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-inset focus:ring-aqua-500 ${
                          activeTab === 'login'
                            ? 'border-aqua-500 text-aqua-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => handleTabChange('login')}
                        disabled={isLoading}
                        aria-selected={activeTab === 'login'}
                        role="tab"
                      >
                        Sign In
                      </button>
                      <button
                        type="button"
                        className={`w-1/2 py-4 px-1 text-center border-b-2 font-medium text-sm focus:outline-none focus:ring-2 focus:ring-inset focus:ring-aqua-500 ${
                          activeTab === 'signup'
                            ? 'border-aqua-500 text-aqua-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                        onClick={() => handleTabChange('signup')}
                        disabled={isLoading}
                        aria-selected={activeTab === 'signup'}
                        role="tab"
                      >
                        Sign Up
                      </button>
                    </nav>
                  </div>

                  {/* Form content */}
                  <div className="px-6 py-6">
                    <AnimatePresence mode="wait">
                      {activeTab === 'login' ? (
                        <LoginForm
                          key="login"
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
                          key="signup"
                          onSubmit={onSignup}
                          isLoading={isLoading}
                          setIsLoading={setIsLoading}
                          error={error}
                          setError={setError}
                          success={success}
                          setSuccess={setSuccess}
                        />
                      )}
                    </AnimatePresence>
                  </div>
                </motion.div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
};



export default AuthModal;