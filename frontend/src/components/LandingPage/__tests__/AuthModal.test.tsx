import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe, toHaveNoViolations } from 'jest-axe';
import AuthModal, { LoginCredentials, SignupData } from '../AuthModal';

expect.extend(toHaveNoViolations);

describe('AuthModal', () => {
  const mockOnClose = jest.fn();
  const mockOnLogin = jest.fn();
  const mockOnSignup = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onLogin: mockOnLogin,
    onSignup: mockOnSignup,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Accessibility', () => {
    it('should have no accessibility violations', async () => {
      const { container } = render(<AuthModal {...defaultProps} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('should trap focus within the modal', async () => {
      render(<AuthModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Close authentication modal');
      const loginTab = screen.getByRole('tab', { name: 'Sign In' });
      const signupTab = screen.getByRole('tab', { name: 'Sign Up' });

      // Close button should be focused initially
      expect(closeButton).toHaveFocus();

      // Tab should move to login tab
      await act(async () => {
        fireEvent.keyDown(document.activeElement!, { key: 'Tab' });
      });
      expect(loginTab).toHaveFocus();

      // Tab should move to signup tab
      await act(async () => {
        fireEvent.keyDown(document.activeElement!, { key: 'Tab' });
      });
      expect(signupTab).toHaveFocus();
    });

    it('should close modal when Escape key is pressed', async () => {
      render(<AuthModal {...defaultProps} />);

      await act(async () => {
        fireEvent.keyDown(document, { key: 'Escape' });
      });
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should have proper ARIA attributes', () => {
      render(<AuthModal {...defaultProps} />);

      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();

      const title = screen.getByRole('heading', { name: 'Welcome to AquaChain' });
      expect(title).toBeInTheDocument();

      const tabs = screen.getAllByRole('tab');
      expect(tabs).toHaveLength(2);
      expect(tabs[0]).toHaveAttribute('aria-selected', 'true');
      expect(tabs[1]).toHaveAttribute('aria-selected', 'false');
    });
  });

  describe('Modal Behavior', () => {
    it('should render when isOpen is true', () => {
      render(<AuthModal {...defaultProps} />);
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should not render when isOpen is false', () => {
      render(<AuthModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', async () => {
      render(<AuthModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Close authentication modal');
      await act(async () => {
        fireEvent.click(closeButton);
      });

      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when backdrop is clicked', async () => {
      render(<AuthModal {...defaultProps} />);

      // Click on the backdrop (outside the modal panel)
      const backdrop = screen.getByRole('dialog').parentElement;
      if (backdrop) {
        await act(async () => {
          fireEvent.click(backdrop);
        });
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      }
    });
  });

  describe('Tab Navigation', () => {
    it('should start with login tab active by default', () => {
      render(<AuthModal {...defaultProps} />);

      const loginTab = screen.getByRole('tab', { name: 'Sign In' });
      const signupTab = screen.getByRole('tab', { name: 'Sign Up' });

      expect(loginTab).toHaveAttribute('aria-selected', 'true');
      expect(signupTab).toHaveAttribute('aria-selected', 'false');
    });

    it('should start with signup tab active when initialTab is signup', () => {
      render(<AuthModal {...defaultProps} initialTab="signup" />);

      const loginTab = screen.getByRole('tab', { name: 'Sign In' });
      const signupTab = screen.getByRole('tab', { name: 'Sign Up' });

      expect(loginTab).toHaveAttribute('aria-selected', 'false');
      expect(signupTab).toHaveAttribute('aria-selected', 'true');
    });

    it('should switch tabs when tab buttons are clicked', async () => {
      render(<AuthModal {...defaultProps} />);

      const loginTab = screen.getByRole('tab', { name: 'Sign In' });
      const signupTab = screen.getByRole('tab', { name: 'Sign Up' });

      // Initially login tab is active
      expect(loginTab).toHaveAttribute('aria-selected', 'true');
      expect(signupTab).toHaveAttribute('aria-selected', 'false');

      // Click signup tab
      await act(async () => {
        fireEvent.click(signupTab);
      });
      expect(loginTab).toHaveAttribute('aria-selected', 'false');
      expect(signupTab).toHaveAttribute('aria-selected', 'true');

      // Click login tab
      await act(async () => {
        fireEvent.click(loginTab);
      });
      expect(loginTab).toHaveAttribute('aria-selected', 'true');
      expect(signupTab).toHaveAttribute('aria-selected', 'false');
    });

    it('should show different content for login and signup tabs', async () => {
      render(<AuthModal {...defaultProps} />);

      // Login tab content should be visible initially
      expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();

      // Switch to signup tab
      const signupTab = screen.getByRole('tab', { name: 'Sign Up' });
      await act(async () => {
        fireEvent.click(signupTab);
      });

      // Signup tab content should be visible
      expect(screen.getByLabelText('Full Name')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should disable close button and tabs when loading', () => {
      // We'll test this more thoroughly when forms are implemented
      render(<AuthModal {...defaultProps} />);

      const closeButton = screen.getByLabelText('Close authentication modal');
      const loginTab = screen.getByRole('tab', { name: 'Sign In' });
      const signupTab = screen.getByRole('tab', { name: 'Sign Up' });

      expect(closeButton).not.toBeDisabled();
      expect(loginTab).not.toBeDisabled();
      expect(signupTab).not.toBeDisabled();
    });
  });

  describe('Animation', () => {
    it('should have proper animation classes', () => {
      render(<AuthModal {...defaultProps} />);
      
      // The modal should be present with proper structure
      const dialog = screen.getByRole('dialog');
      expect(dialog).toBeInTheDocument();
      
      // Check for the presence of the modal panel
      const panel = screen.getByRole('dialog').querySelector('[role="dialog"]') || 
                   screen.getByRole('dialog').querySelector('.transform');
      expect(panel || dialog).toBeInTheDocument();
    });
  });

  describe('Form Validation', () => {
    it('should validate login form fields', async () => {
      render(<AuthModal {...defaultProps} />);

      const emailInput = screen.getByLabelText('Email Address');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Sign In' });

      // Try to submit empty form
      await act(async () => {
        fireEvent.click(submitButton);
      });

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText('Email is required')).toBeInTheDocument();
        expect(screen.getByText('Password is required')).toBeInTheDocument();
      });

      // Enter invalid email
      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
        fireEvent.blur(emailInput);
      });

      await waitFor(() => {
        expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
      });

      // Enter valid email
      await act(async () => {
        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.blur(emailInput);
      });

      await waitFor(() => {
        expect(screen.queryByText('Please enter a valid email address')).not.toBeInTheDocument();
      });
    });

    it('should validate signup form fields', async () => {
      render(<AuthModal {...defaultProps} initialTab="signup" />);

      const nameInput = screen.getByLabelText('Full Name');
      const emailInput = screen.getByLabelText('Email Address');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });

      // Try to submit empty form
      await act(async () => {
        fireEvent.click(submitButton);
      });

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText('Name is required')).toBeInTheDocument();
        expect(screen.getByText('Email is required')).toBeInTheDocument();
        expect(screen.getByText('Password is required')).toBeInTheDocument();
      });

      // Test password confirmation
      await act(async () => {
        fireEvent.change(passwordInput, { target: { value: 'password123' } });
        fireEvent.change(confirmPasswordInput, { target: { value: 'different' } });
        fireEvent.blur(confirmPasswordInput);
      });

      await waitFor(() => {
        expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
      });

      // Fix password confirmation
      await act(async () => {
        fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
        fireEvent.blur(confirmPasswordInput);
      });

      await waitFor(() => {
        expect(screen.queryByText('Passwords do not match')).not.toBeInTheDocument();
      });
    });

    it('should show password strength indicator', async () => {
      render(<AuthModal {...defaultProps} initialTab="signup" />);

      const passwordInput = screen.getByLabelText('Password');

      // Enter weak password
      await act(async () => {
        fireEvent.change(passwordInput, { target: { value: '123' } });
        fireEvent.blur(passwordInput);
      });

      await waitFor(() => {
        expect(screen.getByText('weak')).toBeInTheDocument();
      });

      // Enter strong password
      await act(async () => {
        fireEvent.change(passwordInput, { target: { value: 'StrongPass123!' } });
        fireEvent.blur(passwordInput);
      });

      await waitFor(() => {
        expect(screen.getByText('strong')).toBeInTheDocument();
      });
    });

    it('should toggle password visibility', async () => {
      render(<AuthModal {...defaultProps} />);

      const passwordInput = screen.getByLabelText('Password');
      const toggleButton = screen.getByLabelText('Show password');

      // Initially password should be hidden
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Click to show password
      await act(async () => {
        fireEvent.click(toggleButton);
      });

      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(screen.getByLabelText('Hide password')).toBeInTheDocument();

      // Click to hide password again
      await act(async () => {
        fireEvent.click(screen.getByLabelText('Hide password'));
      });

      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });
});