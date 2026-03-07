/**
 * AutoRefreshIndicator Component Tests
 * 
 * Unit tests for AutoRefreshIndicator component.
 * Tests countdown timer, controls, and integration with DashboardContext.
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AutoRefreshIndicator, CompactAutoRefreshIndicator } from "../AutoRefreshIndicator";
import { DashboardProvider } from "../../../contexts/DashboardContext";

// Mock date-fns
jest.mock("date-fns", () => ({
  formatDistanceToNow: jest.fn(() => "2 minutes ago"),
}));

// Helper to render with DashboardProvider
const renderWithProvider = (
  component: React.ReactElement,
  providerProps = {}
) => {
  const defaultProps = {
    userRole: "Admin" as const,
    userId: "test-user",
    ...providerProps,
  };

  return render(
    <DashboardProvider {...defaultProps}>
      {component}
    </DashboardProvider>
  );
};

describe("AutoRefreshIndicator", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe("Rendering", () => {
    it("renders with default props", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("displays last update time", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      expect(screen.getByText(/Last updated/)).toBeInTheDocument();
    });

    it("displays countdown timer", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      expect(screen.getByText(/Next refresh in/)).toBeInTheDocument();
    });

    it("has refresh icon", () => {
      const { container } = renderWithProvider(<AutoRefreshIndicator />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("Countdown Timer", () => {
    it("displays initial countdown", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      
      // Should show countdown in seconds
      expect(screen.getByText(/30s/)).toBeInTheDocument();
    });

    it("formats countdown correctly", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      
      // Initial countdown should be visible
      const countdown = screen.getByText(/\d+s/);
      expect(countdown).toBeInTheDocument();
    });
  });

  describe("Controls", () => {
    it("shows pause/play button by default", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      const button = screen.getByRole("button", { name: /Pause auto-refresh/ });
      expect(button).toBeInTheDocument();
    });

    it("hides controls when showControls is false", () => {
      renderWithProvider(<AutoRefreshIndicator showControls={false} />);
      const button = screen.queryByRole("button");
      expect(button).not.toBeInTheDocument();
    });

    it("toggles auto-refresh when button is clicked", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      const button = screen.getByRole("button", { name: /Pause auto-refresh/ });
      
      fireEvent.click(button);
      
      expect(screen.getByText(/Auto-refresh paused/)).toBeInTheDocument();
    });

    it("changes button label when paused", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      const button = screen.getByRole("button", { name: /Pause auto-refresh/ });
      
      fireEvent.click(button);
      
      expect(
        screen.getByRole("button", { name: /Resume auto-refresh/ })
      ).toBeInTheDocument();
    });
  });

  describe("Compact Mode", () => {
    it("renders in compact mode", () => {
      renderWithProvider(<AutoRefreshIndicator compact />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveClass("text-xs");
    });

    it("shows simplified countdown in compact mode", () => {
      renderWithProvider(<AutoRefreshIndicator compact />);
      expect(screen.getByText(/30s/)).toBeInTheDocument();
    });

    it("does not show controls in compact mode by default", () => {
      renderWithProvider(<AutoRefreshIndicator compact />);
      const button = screen.queryByRole("button");
      expect(button).not.toBeInTheDocument();
    });
  });

  describe("Progress Indicator", () => {
    it("renders circular progress indicator", () => {
      const { container } = renderWithProvider(<AutoRefreshIndicator />);
      const circles = container.querySelectorAll("circle");
      expect(circles.length).toBeGreaterThan(0);
    });

    it("updates progress as countdown decreases", async () => {
      const { container } = renderWithProvider(<AutoRefreshIndicator />);
      
      // Get progress circle
      const progressCircle = container.querySelectorAll("circle")[1];
      const initialOffset = progressCircle?.getAttribute("stroke-dashoffset");
      
      // Advance timer
      jest.advanceTimersByTime(5000);
      
      await waitFor(() => {
        const newOffset = progressCircle?.getAttribute("stroke-dashoffset");
        expect(newOffset).not.toBe(initialOffset);
      });
    });
  });

  describe("Accessibility", () => {
    it("has role status", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("has descriptive aria-label", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveAttribute("aria-label");
      expect(indicator.getAttribute("aria-label")).toContain("Last updated");
    });

    it("updates aria-label when paused", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      const button = screen.getByRole("button", { name: /Pause auto-refresh/ });
      
      fireEvent.click(button);
      
      const indicator = screen.getByRole("status");
      expect(indicator.getAttribute("aria-label")).toContain("Auto-refresh paused");
    });

    it("has accessible button labels", () => {
      renderWithProvider(<AutoRefreshIndicator />);
      const button = screen.getByRole("button", { name: /Pause auto-refresh/ });
      expect(button).toHaveAttribute("aria-label", "Pause auto-refresh");
      expect(button).toHaveAttribute("title", "Pause auto-refresh");
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      renderWithProvider(<AutoRefreshIndicator className="custom-class" />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveClass("custom-class");
    });
  });
});

describe("CompactAutoRefreshIndicator", () => {
  it("renders in compact mode", () => {
    renderWithProvider(<CompactAutoRefreshIndicator />);
    const indicator = screen.getByRole("status");
    expect(indicator).toHaveClass("text-xs");
  });

  it("applies custom className", () => {
    renderWithProvider(<CompactAutoRefreshIndicator className="custom-compact" />);
    const indicator = screen.getByRole("status");
    expect(indicator).toHaveClass("custom-compact");
  });
});
