/**
 * DashboardContext Tests
 * 
 * Unit tests for DashboardContext and useDashboard hook.
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { DashboardProvider, useDashboard } from "../DashboardContext";
import { ReactNode } from "react";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

describe("DashboardContext", () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllTimers();
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <DashboardProvider userRole="Admin" userId="test-user-123">
      {children}
    </DashboardProvider>
  );

  describe("useDashboard hook", () => {
    it("should throw error when used outside provider", () => {
      // Suppress console.error for this test
      const consoleSpy = jest.spyOn(console, "error").mockImplementation();

      expect(() => {
        renderHook(() => useDashboard());
      }).toThrow("useDashboard must be used within DashboardProvider");

      consoleSpy.mockRestore();
    });

    it("should provide default config on initial render", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.config).toEqual({
        refreshInterval: 30,
        theme: "light",
        visibleComponents: expect.any(Array),
        filterPresets: [],
      });
    });

    it("should provide user role and userId", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.userRole).toBe("Admin");
      expect(result.current.userId).toBe("test-user-123");
    });

    it("should have auto-refresh enabled by default", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.autoRefreshEnabled).toBe(true);
    });
  });

  describe("updateConfig", () => {
    it("should update config with partial updates", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        result.current.updateConfig({ refreshInterval: 60 });
      });

      expect(result.current.config.refreshInterval).toBe(60);
      expect(result.current.config.theme).toBe("light"); // Other fields unchanged
    });

    it("should persist config to localStorage", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        result.current.updateConfig({ theme: "dark" });
      });

      const saved = localStorageMock.getItem("dashboardConfig");
      expect(saved).toBeTruthy();
      
      const parsed = JSON.parse(saved!);
      expect(parsed.theme).toBe("dark");
    });
  });

  describe("toggleAutoRefresh", () => {
    it("should toggle auto-refresh state", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.autoRefreshEnabled).toBe(true);

      act(() => {
        result.current.toggleAutoRefresh();
      });

      expect(result.current.autoRefreshEnabled).toBe(false);

      act(() => {
        result.current.toggleAutoRefresh();
      });

      expect(result.current.autoRefreshEnabled).toBe(true);
    });
  });

  describe("triggerManualRefresh", () => {
    it("should update lastRefreshTimestamp", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      const initialTimestamp = result.current.lastRefreshTimestamp;

      // Wait a bit to ensure timestamp difference
      act(() => {
        jest.advanceTimersByTime(100);
        result.current.triggerManualRefresh();
      });

      expect(result.current.lastRefreshTimestamp.getTime()).toBeGreaterThan(
        initialTimestamp.getTime()
      );
    });
  });

  describe("addNotification", () => {
    it("should add notification to history", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        result.current.addNotification({
          type: "success",
          message: "Test notification",
        });
      });

      expect(result.current.notificationHistory).toHaveLength(1);
      expect(result.current.notificationHistory[0]).toMatchObject({
        type: "success",
        message: "Test notification",
        read: false,
      });
      expect(result.current.notificationHistory[0].id).toBeTruthy();
      expect(result.current.notificationHistory[0].timestamp).toBeInstanceOf(Date);
    });

    it("should limit notification history to 50 items", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        // Add 60 notifications
        for (let i = 0; i < 60; i++) {
          result.current.addNotification({
            type: "info",
            message: `Notification ${i}`,
          });
        }
      });

      expect(result.current.notificationHistory).toHaveLength(50);
    });

    it("should add new notifications to the beginning of the list", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        result.current.addNotification({
          type: "info",
          message: "First",
        });
      });

      act(() => {
        result.current.addNotification({
          type: "info",
          message: "Second",
        });
      });

      expect(result.current.notificationHistory[0].message).toBe("Second");
      expect(result.current.notificationHistory[1].message).toBe("First");
    });
  });

  describe("auto-refresh timer", () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it("should update lastRefreshTimestamp after refresh interval", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      const initialTimestamp = result.current.lastRefreshTimestamp;

      act(() => {
        jest.advanceTimersByTime(30000); // 30 seconds
      });

      expect(result.current.lastRefreshTimestamp.getTime()).toBeGreaterThan(
        initialTimestamp.getTime()
      );
    });

    it("should not update when auto-refresh is disabled", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        result.current.toggleAutoRefresh(); // Disable
      });

      const timestampAfterDisable = result.current.lastRefreshTimestamp;

      act(() => {
        jest.advanceTimersByTime(30000);
      });

      expect(result.current.lastRefreshTimestamp).toEqual(timestampAfterDisable);
    });

    it("should respect custom refresh interval", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      act(() => {
        result.current.updateConfig({ refreshInterval: 60 });
      });

      const initialTimestamp = result.current.lastRefreshTimestamp;

      act(() => {
        jest.advanceTimersByTime(59000); // Just before 60 seconds
      });

      // Should not have refreshed yet
      expect(result.current.lastRefreshTimestamp).toEqual(initialTimestamp);

      act(() => {
        jest.advanceTimersByTime(1000); // Complete 60 seconds
      });

      // Should have refreshed now
      expect(result.current.lastRefreshTimestamp.getTime()).toBeGreaterThan(
        initialTimestamp.getTime()
      );
    });
  });

  describe("localStorage persistence", () => {
    it("should load config from localStorage on mount", () => {
      const savedConfig = {
        refreshInterval: 120,
        theme: "dark",
        visibleComponents: ["test"],
        filterPresets: [],
      };

      localStorageMock.setItem("dashboardConfig", JSON.stringify(savedConfig));

      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.config).toEqual(savedConfig);
    });

    it("should use default config if localStorage is empty", () => {
      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.config.refreshInterval).toBe(30);
      expect(result.current.config.theme).toBe("light");
    });

    it("should use default config if localStorage has invalid data", () => {
      localStorageMock.setItem("dashboardConfig", "invalid json");

      const { result } = renderHook(() => useDashboard(), { wrapper });

      expect(result.current.config.refreshInterval).toBe(30);
      expect(result.current.config.theme).toBe("light");
    });
  });
});
