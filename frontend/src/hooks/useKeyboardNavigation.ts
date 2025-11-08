import { useEffect, useCallback } from 'react';

interface KeyboardNavigationOptions {
  enableSectionJumping?: boolean;
  enableModalClose?: boolean;
  enableFocusManagement?: boolean;
}

interface SectionMapping {
  [key: string]: string;
}

/**
 * Custom hook for keyboard navigation
 * Provides keyboard shortcuts for section navigation and accessibility
 */
export const useKeyboardNavigation = (options: KeyboardNavigationOptions = {}) => {
  const {
    enableSectionJumping = true,
    enableModalClose = true,
    enableFocusManagement = true
  } = options;

  // Section mappings for keyboard shortcuts
  const sectionMappings: SectionMapping = {
    '1': 'hero',
    '2': 'features', 
    '3': 'roles',
    '4': 'contact'
  };

  // Smooth scroll to section
  const scrollToSection = useCallback((sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      const headerOffset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  }, []);

  // Handle keyboard events
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    // Skip if user is typing in an input field
    const activeElement = document.activeElement;
    const isInputActive = activeElement && (
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.getAttribute('contenteditable') === 'true'
    );

    if (isInputActive) return;

    // Section jumping with number keys
    if (enableSectionJumping && sectionMappings[event.key]) {
      event.preventDefault();
      scrollToSection(sectionMappings[event.key]);
      return;
    }

    // Modal close with Escape key
    if (enableModalClose && event.key === 'Escape') {
      // This will be handled by individual modal components
      // We just ensure the event propagates
      return;
    }

    // Focus management with Tab key
    if (enableFocusManagement && event.key === 'Tab') {
      // Add keyboard navigation class for focus visibility
      document.body.classList.add('keyboard-navigation');
    }

    // Additional keyboard shortcuts
    switch (event.key) {
      case 'Home':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        break;
      
      case 'End':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          window.scrollTo({ 
            top: document.documentElement.scrollHeight, 
            behavior: 'smooth' 
          });
        }
        break;
      
      case 'ArrowUp':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          window.scrollBy({ top: -100, behavior: 'smooth' });
        }
        break;
      
      case 'ArrowDown':
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          window.scrollBy({ top: 100, behavior: 'smooth' });
        }
        break;
    }
  }, [enableSectionJumping, enableModalClose, enableFocusManagement, scrollToSection]);

  // Handle mouse events for focus management
  const handleMouseDown = useCallback(() => {
    if (enableFocusManagement) {
      document.body.classList.remove('keyboard-navigation');
    }
  }, [enableFocusManagement]);

  // Set up event listeners
  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, [handleKeyDown, handleMouseDown]);

  // Return utility functions for manual use
  return {
    scrollToSection,
    sectionMappings
  };
};

export default useKeyboardNavigation;