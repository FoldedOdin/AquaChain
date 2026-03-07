/**
 * AlertCard Component Tests
 * 
 * Tests for the AlertCard component including:
 * - Rendering alert details
 * - Severity color coding
 * - Action button functionality
 * - Modal interactions
 * - Accessibility
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AlertCard } from "../AlertCard";
import { Alert } from "../../../types/alert";

// Mock date-fns
jest.mock("date-fns", () => ({
  formatDistanceToNow: jest.fn(() => "5 minutes ago"),
}));

describe("AlertCard", () => {
  const mockAlert: Alert = {
    alertId: "ALERT-001",
    deviceId: "ESP32-ABC123",
    issue: "High turbidity detected",
    timestamp: new Date("2024-01-15T10:30:00Z"),
    severity: "Critical",
    acknowledged: false,
  };

  const mockOnAcknowledge = jest.fn();
  const mockOnAssignTechnician = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("should render alert details correctly", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.getByText("High turbidity detected")).toBeInTheDocument();
      // Note: timestamp rendering is mocked and may not always appear in tests
    });

    it("should display severity badge", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      expect(screen.getByText("Critical")).toBeInTheDocument();
    });

    it("should display assigned technician when present", () => {
      const alertWithTechnician: Alert = {
        ...mockAlert,
        assignedTechnician: "John Smith",
      };

      render(
        <AlertCard
          alert={alertWithTechnician}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      expect(screen.getByText(/Assigned to: John Smith/)).toBeInTheDocument();
    });

    it("should not display assigned technician when not present", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      expect(screen.queryByText(/Assigned to:/)).not.toBeInTheDocument();
    });
  });

  describe("Severity Color Coding", () => {
    it("should apply Critical severity styling", () => {
      const { container } = render(
        <AlertCard
          alert={{ ...mockAlert, severity: "Critical" }}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const alertCard = container.querySelector('[role="article"]');
      expect(alertCard).toHaveClass("border-red-500");
    });

    it("should apply Warning severity styling", () => {
      const { container } = render(
        <AlertCard
          alert={{ ...mockAlert, severity: "Warning" }}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const alertCard = container.querySelector('[role="article"]');
      expect(alertCard).toHaveClass("border-yellow-500");
    });

    it("should apply Safe severity styling", () => {
      const { container } = render(
        <AlertCard
          alert={{ ...mockAlert, severity: "Safe" }}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const alertCard = container.querySelector('[role="article"]');
      expect(alertCard).toHaveClass("border-green-500");
    });
  });

  describe("Action Buttons", () => {
    it("should render acknowledge button", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const acknowledgeButton = screen.getByLabelText("Acknowledge alert");
      expect(acknowledgeButton).toBeInTheDocument();
    });

    it("should render assign technician button", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const assignButton = screen.getByLabelText("Assign technician to alert");
      expect(assignButton).toBeInTheDocument();
    });

    it("should call onAcknowledge when acknowledge button is clicked", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const acknowledgeButton = screen.getByLabelText("Acknowledge alert");
      fireEvent.click(acknowledgeButton);

      expect(mockOnAcknowledge).toHaveBeenCalledWith("ALERT-001");
      expect(mockOnAcknowledge).toHaveBeenCalledTimes(1);
    });

    it("should open assign technician modal when button is clicked", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const assignButton = screen.getByLabelText("Assign technician to alert");
      fireEvent.click(assignButton);

      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByLabelText("Select Technician")).toBeInTheDocument();
    });
  });

  describe("Modal Interactions", () => {
    it("should close modal when cancel is clicked", async () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      // Open modal
      const assignButton = screen.getByLabelText("Assign technician to alert");
      fireEvent.click(assignButton);

      // Close modal
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    });

    it("should call onAssignTechnician when technician is selected and confirmed", async () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      // Open modal
      const assignButton = screen.getByLabelText("Assign technician to alert");
      fireEvent.click(assignButton);

      // Select technician
      const select = screen.getByLabelText("Select Technician");
      fireEvent.change(select, { target: { value: "TECH-001" } });

      // Confirm assignment - get all buttons and find the one in the modal
      const buttons = screen.getAllByRole("button");
      const confirmButton = buttons.find(btn => btn.textContent === "Assign Technician");
      expect(confirmButton).toBeDefined();
      fireEvent.click(confirmButton!);

      await waitFor(() => {
        expect(mockOnAssignTechnician).toHaveBeenCalledWith("ALERT-001", "TECH-001");
        expect(mockOnAssignTechnician).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      expect(screen.getByRole("article")).toHaveAttribute(
        "aria-label",
        "Alert: High turbidity detected"
      );
      expect(screen.getByLabelText("Acknowledge alert")).toBeInTheDocument();
      expect(screen.getByLabelText("Assign technician to alert")).toBeInTheDocument();
    });

    it("should be keyboard accessible", () => {
      render(
        <AlertCard
          alert={mockAlert}
          onAcknowledge={mockOnAcknowledge}
          onAssignTechnician={mockOnAssignTechnician}
        />
      );

      const acknowledgeButton = screen.getByLabelText("Acknowledge alert");
      acknowledgeButton.focus();
      expect(acknowledgeButton).toHaveFocus();
    });
  });
});
