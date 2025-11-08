import React, { useState, useEffect } from 'react';
import { CheckCircleIcon, ClockIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface EmailVerificationStatusProps {
  email: string;
  onVerified?: () => void;
}

const EmailVerificationStatus: React.FC<EmailVerificationStatusProps> = ({ 
  email, 
  onVerified 
}) => {
  const [isVerified, setIsVerified] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkVerificationStatus = async () => {
    try {
      setIsChecking(true);
      setError(null);
      
      const response = await fetch(
        `${process.env.REACT_APP_API_ENDPOINT}/api/auth/verification-status/${encodeURIComponent(email)}`
      );
      
      const result = await response.json();
      
      if (response.ok) {
        setIsVerified(result.emailVerified);
        if (result.emailVerified && onVerified) {
          onVerified();
        }
      } else {
        setError(result.error || 'Failed to check verification status');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkVerificationStatus();
    
    // Check every 2 seconds until verified
    const interval = setInterval(() => {
      if (!isVerified) {
        checkVerificationStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [email, isVerified]);

  if (error) {
    return (
      <div className="flex items-center space-x-2 text-red-600">
        <ExclamationTriangleIcon className="h-5 w-5" />
        <span className="text-sm">{error}</span>
        <button
          onClick={checkVerificationStatus}
          className="text-sm text-aqua-600 hover:text-aqua-700 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (isVerified) {
    return (
      <div className="flex items-center space-x-2 text-green-600">
        <CheckCircleIcon className="h-5 w-5" />
        <span className="text-sm font-medium">Email verified! You can now sign in.</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-amber-600">
      <ClockIcon className={`h-5 w-5 ${isChecking ? 'animate-spin' : ''}`} />
      <span className="text-sm">
        {isChecking ? 'Checking verification status...' : 'Waiting for email verification...'}
      </span>
    </div>
  );
};

export default EmailVerificationStatus;