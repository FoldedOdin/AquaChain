/**
 * Privacy Utilities
 * Functions for masking sensitive data
 */

/**
 * Mask phone number showing only last 4 digits
 * Examples:
 *   +91 98765 43210 -> ******* 3210
 *   9876543210 -> ****** 3210
 *   +1-555-123-4567 -> ******* 4567
 */
export function maskPhoneNumber(phone: string | null | undefined): string {
  if (!phone) {
    return 'N/A';
  }

  // Remove all non-digit characters to get just the numbers
  const digits = phone.replace(/\D/g, '');
  
  if (digits.length < 4) {
    // If less than 4 digits, mask everything
    return '*'.repeat(digits.length);
  }

  // Show last 4 digits
  const lastFour = digits.slice(-4);
  const maskedLength = digits.length - 4;
  
  return '*'.repeat(maskedLength) + ' ' + lastFour;
}

/**
 * Mask email showing only first 2 characters and domain
 * Example: john.doe@example.com -> jo*******@example.com
 */
export function maskEmail(email: string | null | undefined): string {
  if (!email) {
    return 'N/A';
  }

  const [localPart, domain] = email.split('@');
  
  if (!domain) {
    return email; // Invalid email format
  }

  if (localPart.length <= 2) {
    return '*'.repeat(localPart.length) + '@' + domain;
  }

  const visiblePart = localPart.slice(0, 2);
  const maskedPart = '*'.repeat(localPart.length - 2);
  
  return visiblePart + maskedPart + '@' + domain;
}

/**
 * Mask last name showing only first character
 * Example: Pradeep -> P******
 */
export function maskLastName(lastName: string | null | undefined): string {
  if (!lastName) {
    return 'N/A';
  }

  if (lastName.length <= 1) {
    return lastName;
  }

  const firstChar = lastName.charAt(0);
  const maskedPart = '*'.repeat(lastName.length - 1);
  
  return firstChar + maskedPart;
}
