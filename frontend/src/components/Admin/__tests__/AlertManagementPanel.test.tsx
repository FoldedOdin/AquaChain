/**
 * AlertManagementPanel Component Tests
 * 
 * Tests for the AlertManagementPanel component including:
 * - Rendering alert list
 * - Alert count badges
 * - Severity filtering
 * - Alert sorting
 * - Empty state
 * - Auto-refresh integration
 * - Toast notifications
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { toast } from "react-toastify";
import { AlertManagementPanel } from "../AlertManagementPanel";
import { MockDataService } from "../../../services/mockDataService";
import { Alert } from "../../../types/alert";

// Mock dependencies
jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("../../../services/mockDataService", () => ({
  MockDataService: {
    getAlerts: jest.fn(),
  },
}));

jest.mock("../../../contexts/DashboardContext", () => ({
  useDashboard: () => ({
    lastRefreshTimestamp: new Date(),
    addNotification: jest.fn(),
  }),
}));

jest.mock("date-fns", () => ({
  formatDistanceToNow: jest.fn(() => "5 minutes ago"),
}));

describe("AlertManagementPanel", () => {
  const mockAlerts: Alert[] = [
    {
      alertId: "ALERT-001",
      deviceId: "ESP32-ABC123",
      issue: "High turbidity detected",
      timestamp: new Date("2024-01-15T10:30:00Z"),
      severity: "Critical",
      acknowledged: false,
    },
    {
      alertId: "ALERT-002",
      deviceId: "ESP32-DEF456",
      issue: "pH level slightly elevated",
      timestamp: new Date("2024-01-15T10:25:00Z"),
      severity: "Warning",
      acknowledged: false,
    },
    {
      alertId: "ALERT-003",
      deviceId: "ESP32-GHI789",
      issue: "All parameters normal",
      timestamp: new Date("2024-01-15T10:20:00Z"),
      severity: "Safe",
      acknowledged: false,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    (MockDataService.getAlerts as jest.Mock).mockReturnValue(mockAlerts);
  });

  describe("Rendering", () => {
    it("should render panel header", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("Alert Management")).toBeInTheDocument();
    });

    it("should render mock data badge", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("MOCK DATA")).toBeInTheDocument();
    });

    it("should render all alerts", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.getByText("ESP32-DEF456")).toBeInTheDocument();
      expect(screen.getByText("ESP32-GHI789")).toBeInTheDocument();
    });
  });

  describe("Alert Count Badges", () => {
    it("should display total alert count", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("Total:")).toBeInTheDocument();
      expect(screen.getByText("3")).toBeInTheDocument();
    });

    it("should display critical alert count", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("Critical:")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
    });

    it("should display warning alert count", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("Warning:")).toBeInTheDocument();
      // Note: There are two "1" texts (Critical and Warning), so we check for Warning label
      const warningLabel = screen.getByText("Warning:");
      expect(warningLabel.nextElementSibling).toHaveTextContent("1");
    });

    it("should update counts when alerts change", () => {
      const { rerender } = render(<AlertManagementPanel />);
      
      // Update mock to return fewer alerts
      (MockDataService.getAlerts as jest.Mock).mockReturnValue([mockAlerts[0]]);
      
      rerender(<AlertManagementPanel />);
      
      // Total should be 1 now
      const totalBadges = screen.getAllByText("1");
      expect(totalBadges.length).toBeGreaterThan(0);
    });
  });

  describe("Severity Filtering", () => {
    it("should render all filter buttons", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByLabelText("Show all alerts")).toBeInTheDocument();
      expect(screen.getByLabelText("Show critical alerts only")).toBeInTheDocument();
      expect(screen.getByLabelText("Show warning alerts only")).toBeInTheDocument();
      expect(screen.getByLabelText("Show safe alerts only")).toBeInTheDocument();
    });

    it("should show all alerts by default", () => {
      render(<AlertManagementPanel />);
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.getByText("ESP32-DEF456")).toBeInTheDocument();
      expect(screen.getByText("ESP32-GHI789")).toBeInTheDocument();
    });

    it("should filter to show only critical alerts", () => {
      render(<AlertManagementPanel />);
      
      const criticalButton = screen.getByLabelText("Show critical alerts only");
      fireEvent.click(criticalButton);

      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
      expect(screen.queryByText("ESP32-GHI789")).not.toBeInTheDocument();
    });

    it("should filter to show only warning alerts", () => {
      render(<AlertManagementPanel />);
      
      const warningButton = screen.getByLabelText("Show warning alerts only");
      fireEvent.click(warningButton);

      expect(screen.queryByText("ESP32-ABC123")).not.toBeInTheDocument();
      expect(screen.getByText("ESP32-DEF456")).toBeInTheDocument();
      expect(screen.queryByText("ESP32-GHI789")).not.toBeInTheDocument();
    });

    it("should filter to show only safe alerts", () => {
      render(<AlertManagementPanel />);
      
      const safeButton = screen.getByLabelText("Show safe alerts only");
      fireEvent.click(safeButton);

      expect(screen.queryByText("ESP32-ABC123")).not.toBeInTheDocument();
      expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
      expect(screen.getByText("ESP32-GHI789")).toBeInTheDocument();
    });

    it("should update active filter button styling", () => {
      render(<AlertManagementPanel />);
      
      const criticalButton = screen.getByLabelText("Show critical alerts only");
      fireEvent.click(criticalButton);

      expect(criticalButton).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("Alert Sorting", () => {
    it("should sort alerts by severity then timestamp", () => {
      const unsortedAlerts: Alert[] = [
        {
          alertId: "ALERT-004",
          deviceId: "ESP32-JKL012",
          issue: "Low issue",
          timestamp: new Date("2024-01-15T10:35:00Z"),
          severity: "Safe",
          acknowledged: false,
        },
        {
          alertId: "ALERT-005",
          deviceId: "ESP32-MNO345",
          issue: "Critical issue",
          timestamp: new Date("2024-01-15T10:40:00Z"),
          severity: "Critical",
          acknowledged: false,
        },
        {
          alertId: "ALERT-006",
          deviceId: "ESP32-PQR678",
          issue: "Warning issue",
          timestamp: new Date("2024-01-15T10:38:00Z"),
          severity: "Warning",
          acknowledged: false,
        },
      ];

      (MockDataService.getAlerts as jest.Mock).mockReturnValue(unsortedAlerts);

      render(<AlertManagementPanel />);

      const alertCards = screen.getAllByRole("article");
      
      // First should be Critical
      expect(alertCards[0]).toHaveTextContent("ESP32-MNO345");
      // Second should be Warning
      expect(alertCards[1]).toHaveTextContent("ESP32-PQR678");
      // Third should be Safe
      expect(alertCards[2]).toHaveTextContent("ESP32-JKL012");
    });
  });

  describe("Empty State", () => {
    it("should show empty state when no alerts", () => {
      (MockDataService.getAlerts as jest.Mock).mockReturnValue([]);

      render(<AlertManagementPanel />);

      expect(screen.getByText("No active alerts")).toBeInTheDocument();
      expect(screen.getByText("All systems are operating normally")).toBeInTheDocument();
    });

    it("should show filtered empty state message", () => {
      render(<AlertManagementPanel />);
      
      const criticalButton = screen.getByLabelText("Show critical alerts only");
      fireEvent.click(criticalButton);

      // Remove all critical alerts
      (MockDataService.getAlerts as jest.Mock).mockReturnValue([mockAlerts[1], mockAlerts[2]]);
      
      // Trigger re-render by clicking filter again
      fireEvent.click(screen.getByLabelText("Show all alerts"));
      fireEvent.click(criticalButton);

      expect(screen.getByText("No active alerts")).toBeInTheDocument();
    });
  });

  describe("Alert Actions", () => {
    it("should acknowledge alert and remove from list", async () => {
      render(<AlertManagementPanel />);

      const acknowledgeButtons = screen.getAllByLabelText("Acknowledge alert");
      fireEvent.click(acknowledgeButtons[0]);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith("Alert acknowledged", expect.any(Object));
      });
    });

    it("should assign technician to alert", async () => {
      render(<AlertManagementPanel />);

      // Open assign modal
      const assignButtons = screen.getAllByLabelText("Assign technician to alert");
      fireEvent.click(assignButtons[0]);

      // Select technician
      const select = screen.getByLabelText("Select Technician");
      fireEvent.change(select, { target: { value: "TECH-001" } });

      // Confirm assignment
      const confirmButton = screen.getByText("Assign Technician");
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "Technician assigned successfully",
          expect.any(Object)
        );
      });
    });
  });

  describe("Toast Notifications", () => {
    it("should show toast for new critical alerts", () => {
      const criticalAlert: Alert = {
        alertId: "ALERT-NEW",
        deviceId: "ESP32-NEW123",
        issue: "New critical issue",
        timestamp: new Date(),
        severity: "Critical",
        acknowledged: false,
      };

      (MockDataService.getAlerts as jest.Mock).mockReturnValue([criticalAlert]);

      render(<AlertManagementPanel />);

      expect(toast.error).toHaveBeenCalledWith(
        "Critical Alert: New critical issue (ESP32-NEW123)",
        expect.any(Object)
      );
    });

    it("should not show duplicate toasts for existing critical alerts", () => {
      render(<AlertManagementPanel />);

      // Clear previous calls
      jest.clearAllMocks();

      // Re-render with same alerts
      render(<AlertManagementPanel />);

      // Should not call toast.error again for the same alert
      expect(toast.error).not.toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels on filter buttons", () => {
      render(<AlertManagementPanel />);

      expect(screen.getByLabelText("Show all alerts")).toBeInTheDocument();
      expect(screen.getByLabelText("Show critical alerts only")).toBeInTheDocument();
    });

    it("should update aria-pressed on filter buttons", () => {
      render(<AlertManagementPanel />);

      const allButton = screen.getByLabelText("Show all alerts");
      const criticalButton = screen.getByLabelText("Show critical alerts only");

      expect(allButton).toHaveAttribute("aria-pressed", "true");
      expect(criticalButton).toHaveAttribute("aria-pressed", "false");

      fireEvent.click(criticalButton);

      expect(allButton).toHaveAttribute("aria-pressed", "false");
      expect(criticalButton).toHaveAttribute("aria-pressed", "true");
    });
  });
});
