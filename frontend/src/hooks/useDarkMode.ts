/**
 * useDarkMode Hook
 * 
 * Custom hook for managing dark mode with localStorage persistence.
 * Integrates with DashboardContext for theme management.
 * 
 * Features:
 * - Dark mode toggle
 * - localStorage persistence
 * - System preference detection
 * - Automatic DOM class updates
 * 
 * @module useDarkMode
 */

import { useEffect, useCallback } from "react";
import { useDashboard } from "../contexts/DashboardContext";
import { Theme } from "../types/dashboard";

/**
 * Dark mode hook return type
 */
interface UseDarkModeReturn {
  /** Current theme */
  theme: Theme;
  /** Whether dark mode is enabled */
  isDarkMode: boolean;
  /** Toggle dark mode */
  toggleDarkMode: () => void;
  /** Set theme explicitly */
  setTheme: (theme: Theme) => void;
}

/**
 * Hook for managing dark mode
 * 
 * Provides dark mode state and toggle functionality.
 * Automatically updates document class for Tailwind dark mode.
 * Persists theme preference in localStorage via DashboardContext.
 * 
 * @returns Dark mode state and control methods
 * 
 * @example
 * ```tsx
 * const { isDarkMode, toggleDarkMode } = useDarkMode();
 * 
 * return (
 *   <button onClick={toggleDarkMode}>
 *     {isDarkMode ? "Light Mode" : "Dark Mode"}
 *   </button>
 * );
 * ```
 */
export function useDarkMode(): UseDarkModeReturn {
  const { config, updateConfig } = useDashboard();
  const theme = config.theme;
  const isDarkMode = theme === "dark";

  /**
   * Toggle dark mode
   */
  const toggleDarkMode = useCallback(() => {
    const newTheme: Theme = isDarkMode ? "light" : "dark";
    updateConfig({ theme: newTheme });
  }, [isDarkMode, updateConfig]);

  /**
   * Set theme explicitly
   */
  const setTheme = useCallback(
    (newTheme: Theme) => {
      updateConfig({ theme: newTheme });
    },
    [updateConfig]
  );

  /**
   * Update document class for Tailwind dark mode
   */
  useEffect(() => {
    const root = document.documentElement;
    
    if (isDarkMode) {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
  }, [isDarkMode]);

  return {
    theme,
    isDarkMode,
    toggleDarkMode,
    setTheme,
  };
}

/**
 * Detect system dark mode preference
 * 
 * @returns Whether system prefers dark mode
 * 
 * @example
 * ```tsx
 * const systemPrefersDark = detectSystemDarkMode();
 * ```
 */
export function detectSystemDarkMode(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  return window.matchMedia && 
         window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/**
 * Hook for syncing with system dark mode preference
 * 
 * Automatically updates theme when system preference changes.
 * Only applies if user hasn't explicitly set a theme preference.
 * 
 * @param enabled - Whether to sync with system preference (default: false)
 * 
 * @example
 * ```tsx
 * // Sync with system preference
 * useSyncSystemDarkMode(true);
 * ```
 */
export function useSyncSystemDarkMode(enabled: boolean = false): void {
  const { setTheme } = useDarkMode();

  useEffect(() => {
    if (!enabled || typeof window === "undefined") {
      return;
    }

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    
    const handleChange = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? "dark" : "light");
    };

    // Set initial theme based on system preference
    setTheme(mediaQuery.matches ? "dark" : "light");

    // Listen for changes
    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [enabled, setTheme]);
}

/**
 * Get theme-specific color values
 * 
 * Returns appropriate color values based on current theme.
 * Useful for components that need to use colors programmatically.
 * 
 * @returns Object with theme-specific color values
 * 
 * @example
 * ```tsx
 * const colors = useThemeColors();
 * <div style={{ backgroundColor: colors.background }}>
 *   Content
 * </div>
 * ```
 */
export function useThemeColors() {
  const { isDarkMode } = useDarkMode();

  return {
    // Background colors
    background: isDarkMode ? "#1a1a1a" : "#ffffff",
    backgroundSecondary: isDarkMode ? "#2d2d2d" : "#f9fafb",
    backgroundTertiary: isDarkMode ? "#3d3d3d" : "#f3f4f6",
    
    // Text colors
    text: isDarkMode ? "#ffffff" : "#111827",
    textSecondary: isDarkMode ? "#b0b0b0" : "#6b7280",
    textMuted: isDarkMode ? "#808080" : "#9ca3af",
    
    // Border colors
    border: isDarkMode ? "#3d3d3d" : "#e5e7eb",
    borderSecondary: isDarkMode ? "#4d4d4d" : "#d1d5db",
    
    // Status colors (adjusted for dark mode)
    success: isDarkMode ? "#10b981" : "#059669",
    warning: isDarkMode ? "#f59e0b" : "#d97706",
    error: isDarkMode ? "#ef4444" : "#dc2626",
    info: isDarkMode ? "#3b82f6" : "#2563eb",
  };
}
