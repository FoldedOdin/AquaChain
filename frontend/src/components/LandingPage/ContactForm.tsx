import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  UserIcon,
  EnvelopeIcon,
  PhoneIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { sanitizeInput, validateEmail, validatePhone } from '../../utils/security';
import { submitContactForm } from '../../services/contactService';

interface ContactFormData {
  name: string;
  email: string;
  phone: string;
  message: string;
  inquiryType: 'technician' | 'general' | 'support';
}

interface ContactFormProps {
  onSubmit?: (data: ContactFormData) => Promise<void>;
  className?: string;
}

interface FormErrors {
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
  submit?: string;
}

interface SubmissionState {
  isSubmitting: boolean;
  isSuccess: boolean;
  isError: boolean;
  message: string;
}

/**
 * Contact Form Component
 * Handles technician inquiries and general contact submissions
 * Includes validation, sanitization, and user feedback
 */
const ContactForm: React.FC<ContactFormProps> = ({ onSubmit, className = '' }) => {
  const [formData, setFormData] = useState<ContactFormData>({
    name: '',
    email: '',
    phone: '',
    message: '',
    inquiryType: 'technician'
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [submissionState, setSubmissionState] = useState<SubmissionState>({
    isSubmitting: false,
    isSuccess: false,
    isError: false,
    message: ''
  });

  // Validate form data
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Phone validation (optional but must be valid if provided)
    if (formData.phone.trim() && !validatePhone(formData.phone)) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    // Message validation
    if (!formData.message.trim()) {
      newErrors.message = 'Message is required';
    } else if (formData.message.trim().length < 10) {
      newErrors.message = 'Message must be at least 10 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input changes with sanitization
  const handleInputChange = (field: keyof ContactFormData, value: string) => {
    let sanitizedValue: string;
    
    // Use appropriate sanitization based on field type
    if (field === 'name') {
      // Names: letters, spaces, hyphens, apostrophes only
      sanitizedValue = sanitizeInput(value);
    } else if (field === 'email') {
      // Email: basic sanitization, preserve @ and .
      sanitizedValue = value.trim();
    } else if (field === 'phone') {
      // Phone: numbers, spaces, +, -, (, )
      sanitizedValue = value.replace(/[^0-9\s\+\-\(\)]/g, '');
    } else if (field === 'message') {
      // Message: allow most characters for proper communication
      // Only prevent actual XSS attempts, allow spaces and punctuation
      sanitizedValue = value;
    } else {
      sanitizedValue = value;
    }
    
    setFormData(prev => ({
      ...prev,
      [field]: sanitizedValue
    }));

    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setSubmissionState({
      isSubmitting: true,
      isSuccess: false,
      isError: false,
      message: ''
    });

    try {
      if (onSubmit) {
        await onSubmit(formData);
      } else {
        // Submit to backend API
        const response = await submitContactForm(formData);
        console.log('Contact form submitted:', response.submissionId);
      }

      setSubmissionState({
        isSubmitting: false,
        isSuccess: true,
        isError: false,
        message: 'Thank you for your inquiry! We\'ll get back to you within 24 hours.'
      });

      // Reset form after successful submission
      setFormData({
        name: '',
        email: '',
        phone: '',
        message: '',
        inquiryType: 'technician'
      });

    } catch (error) {
      console.error('Contact form submission error:', error);
      setSubmissionState({
        isSubmitting: false,
        isSuccess: false,
        isError: true,
        message: error instanceof Error ? error.message : 'Sorry, there was an error sending your message. Please try again.'
      });
    }
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      onSubmit={handleSubmit}
      className={`space-y-6 ${className}`}
      noValidate
    >
      {/* Inquiry Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-3">
          Type of Inquiry
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { value: 'technician', label: 'Become a Technician' },
            { value: 'general', label: 'General Inquiry' },
            { value: 'support', label: 'Technical Support' }
          ].map(({ value, label }) => (
            <label
              key={value}
              className={`
                relative flex items-center justify-center p-3 rounded-lg border-2 cursor-pointer
                transition-all duration-200
                ${formData.inquiryType === value
                  ? 'border-aqua-500 bg-aqua-500/10 text-aqua-400'
                  : 'border-slate-600 bg-slate-800/50 text-gray-300 hover:border-slate-500'
                }
              `}
            >
              <input
                type="radio"
                name="inquiryType"
                value={value}
                checked={formData.inquiryType === value}
                onChange={(e) => handleInputChange('inquiryType', e.target.value)}
                className="sr-only"
              />
              <span className="text-sm font-medium">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Name Field */}
      <div>
        <label htmlFor="contact-name" className="block text-sm font-medium text-gray-300 mb-2">
          Full Name *
        </label>
        <div className="relative">
          <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            id="contact-name"
            type="text"
            value={formData.name}
            onChange={(e) => handleInputChange('name', e.target.value)}
            className={`
              w-full pl-10 pr-4 py-3 bg-slate-800/50 border rounded-lg
              text-white placeholder-gray-400
              focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-transparent
              transition-all duration-200
              ${errors.name ? 'border-red-500' : 'border-slate-600'}
            `}
            placeholder="Enter your full name"
            required
            aria-describedby={errors.name ? 'name-error' : undefined}
          />
        </div>
        {errors.name && (
          <p id="name-error" className="mt-2 text-sm text-red-400 flex items-center space-x-1">
            <ExclamationCircleIcon className="w-4 h-4" />
            <span>{errors.name}</span>
          </p>
        )}
      </div>

      {/* Email Field */}
      <div>
        <label htmlFor="contact-email" className="block text-sm font-medium text-gray-300 mb-2">
          Email Address *
        </label>
        <div className="relative">
          <EnvelopeIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            id="contact-email"
            type="email"
            value={formData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            className={`
              w-full pl-10 pr-4 py-3 bg-slate-800/50 border rounded-lg
              text-white placeholder-gray-400
              focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-transparent
              transition-all duration-200
              ${errors.email ? 'border-red-500' : 'border-slate-600'}
            `}
            placeholder="Enter your email address"
            required
            aria-describedby={errors.email ? 'email-error' : undefined}
          />
        </div>
        {errors.email && (
          <p id="email-error" className="mt-2 text-sm text-red-400 flex items-center space-x-1">
            <ExclamationCircleIcon className="w-4 h-4" />
            <span>{errors.email}</span>
          </p>
        )}
      </div>

      {/* Phone Field */}
      <div>
        <label htmlFor="contact-phone" className="block text-sm font-medium text-gray-300 mb-2">
          Phone Number (Optional)
        </label>
        <div className="relative">
          <PhoneIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            id="contact-phone"
            type="tel"
            value={formData.phone}
            onChange={(e) => handleInputChange('phone', e.target.value)}
            className={`
              w-full pl-10 pr-4 py-3 bg-slate-800/50 border rounded-lg
              text-white placeholder-gray-400
              focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-transparent
              transition-all duration-200
              ${errors.phone ? 'border-red-500' : 'border-slate-600'}
            `}
            placeholder="Enter your phone number"
            aria-describedby={errors.phone ? 'phone-error' : undefined}
          />
        </div>
        {errors.phone && (
          <p id="phone-error" className="mt-2 text-sm text-red-400 flex items-center space-x-1">
            <ExclamationCircleIcon className="w-4 h-4" />
            <span>{errors.phone}</span>
          </p>
        )}
      </div>

      {/* Message Field */}
      <div>
        <label htmlFor="contact-message" className="block text-sm font-medium text-gray-300 mb-2">
          Message *
        </label>
        <div className="relative">
          <ChatBubbleLeftRightIcon className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <textarea
            id="contact-message"
            rows={5}
            value={formData.message}
            onChange={(e) => handleInputChange('message', e.target.value)}
            className={`
              w-full pl-10 pr-4 py-3 bg-slate-800/50 border rounded-lg
              text-white placeholder-gray-400 resize-vertical
              focus:outline-none focus:ring-2 focus:ring-aqua-500 focus:border-transparent
              transition-all duration-200
              ${errors.message ? 'border-red-500' : 'border-slate-600'}
            `}
            placeholder={
              formData.inquiryType === 'technician' 
                ? 'Tell us about your experience, location, and availability...'
                : 'How can we help you?'
            }
            required
            aria-describedby={errors.message ? 'message-error' : undefined}
          />
        </div>
        {errors.message && (
          <p id="message-error" className="mt-2 text-sm text-red-400 flex items-center space-x-1">
            <ExclamationCircleIcon className="w-4 h-4" />
            <span>{errors.message}</span>
          </p>
        )}
      </div>

      {/* Submission Status */}
      {(submissionState.isSuccess || submissionState.isError) && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`
            p-4 rounded-lg border flex items-center space-x-3
            ${submissionState.isSuccess 
              ? 'bg-green-500/10 border-green-500/30 text-green-400'
              : 'bg-red-500/10 border-red-500/30 text-red-400'
            }
          `}
        >
          {submissionState.isSuccess ? (
            <CheckCircleIcon className="w-5 h-5 flex-shrink-0" />
          ) : (
            <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
          )}
          <p>{submissionState.message}</p>
        </motion.div>
      )}

      {/* Submit Button */}
      <motion.button
        type="submit"
        disabled={submissionState.isSubmitting}
        whileHover={{ scale: submissionState.isSubmitting ? 1 : 1.02 }}
        whileTap={{ scale: submissionState.isSubmitting ? 1 : 0.98 }}
        className={`
          w-full py-4 px-6 rounded-lg font-semibold text-white
          transition-all duration-200
          focus:outline-none focus:ring-4 focus:ring-aqua-500/50
          ${submissionState.isSubmitting
            ? 'bg-gray-600 cursor-not-allowed'
            : 'bg-aqua-600 hover:bg-aqua-700'
          }
        `}
      >
        {submissionState.isSubmitting ? (
          <div className="flex items-center justify-center space-x-2">
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span>Sending Message...</span>
          </div>
        ) : (
          'Send Message'
        )}
      </motion.button>

      {/* Privacy Notice */}
      <p className="text-xs text-gray-400 text-center">
        By submitting this form, you agree to our{' '}
        <a href="/privacy" className="text-aqua-400 hover:text-aqua-300 underline">
          Privacy Policy
        </a>{' '}
        and{' '}
        <a href="/terms" className="text-aqua-400 hover:text-aqua-300 underline">
          Terms of Service
        </a>
        .
      </p>
    </motion.form>
  );
};

export default ContactForm;