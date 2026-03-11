/**
 * Contact Form Service
 * Handles API communication for contact form submissions
 */

interface ContactFormData {
  name: string;
  email: string;
  phone: string;
  message: string;
  inquiryType: 'technician' | 'general' | 'support';
}

interface ContactFormResponse {
  message: string;
  submissionId: string;
}

interface ContactFormError {
  error: string;
}

// Contact form uses a separate API Gateway
const CONTACT_API_URL = process.env.REACT_APP_CONTACT_API_URL || 'https://946twwm7kf.execute-api.ap-south-1.amazonaws.com/prod';
const CONTACT_ENDPOINT = `${CONTACT_API_URL}/contact`;

/**
 * Submit contact form data to the backend API
 */
export const submitContactForm = async (
  formData: ContactFormData
): Promise<ContactFormResponse> => {
  try {
    const response = await fetch(CONTACT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Failed to submit contact form');
    }

    return data as ContactFormResponse;
  } catch (error) {
    console.error('Error submitting contact form:', error);
    throw error;
  }
};

/**
 * Validate contact form data before submission
 */
export const validateContactFormData = (
  formData: ContactFormData
): string | null => {
  // Name validation
  if (!formData.name.trim()) {
    return 'Name is required';
  }
  if (formData.name.trim().length < 2) {
    return 'Name must be at least 2 characters';
  }

  // Email validation
  if (!formData.email.trim()) {
    return 'Email is required';
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(formData.email)) {
    return 'Please enter a valid email address';
  }

  // Phone validation (optional but must be valid if provided)
  if (formData.phone.trim()) {
    const phoneRegex = /^[\d\s\-\+\(\)]+$/;
    if (!phoneRegex.test(formData.phone) || formData.phone.length < 10) {
      return 'Please enter a valid phone number';
    }
  }

  // Message validation
  if (!formData.message.trim()) {
    return 'Message is required';
  }
  if (formData.message.trim().length < 10) {
    return 'Message must be at least 10 characters';
  }

  // Inquiry type validation
  const validInquiryTypes = ['technician', 'general', 'support'];
  if (!validInquiryTypes.includes(formData.inquiryType)) {
    return 'Invalid inquiry type';
  }

  return null;
};

export default {
  submitContactForm,
  validateContactFormData,
};
