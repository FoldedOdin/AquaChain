/**
 * StatusBadge Component Tests
 * 
 * Unit tests for StatusBadge component.
 * Tests color coding, icon display, size variants, and accessibility.
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { StatusBadge } from "../StatusBadge";

describe("StatusBadge", () => {
  describe("Device Status", () => {
    it("renders Online status with green color", () => {
      render(<StatusBadge status="Online" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Online");
      expect(badge).toHaveClass("text-green-700");
    });

    it("renders Warning status with yellow color", () => {
      render(<StatusBadge status="Warning" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Warning");
      expect(badge).toHaveClass("text-yellow-700");
    });

    it("renders Offline status with red color", () => {
      render(<StatusBadge status="Offline" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Offline");
      expect(badge).toHaveClass("text-red-700");
    });
  });

  describe("User Status", () => {
    it("renders Active status with green color", () => {
      render(<StatusBadge status="Active" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Active");
      expect(badge).toHaveClass("text-green-700");
    });

    it("renders Inactive status with gray color", () => {
      render(<StatusBadge status="Inactive" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Inactive");
      expect(badge).toHaveClass("text-gray-700");
    });
  });

  describe("Alert Severity", () => {
    it("renders Critical severity with red color", () => {
      render(<StatusBadge status="Critical" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Critical");
      expect(badge).toHaveClass("text-red-700");
    });

    it("renders Safe severity with green color", () => {
      render(<StatusBadge status="Safe" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Safe");
      expect(badge).toHaveClass("text-green-700");
    });
  });

  describe("Size Variants", () => {
    it("renders small size", () => {
      render(<StatusBadge status="Online" size="sm" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-xs");
    });

    it("renders medium size by default", () => {
      render(<StatusBadge status="Online" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-sm");
    });

    it("renders large size", () => {
      render(<StatusBadge status="Online" size="lg" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-base");
    });
  });

  describe("Icon Display", () => {
    it("shows icon by default", () => {
      const { container } = render(<StatusBadge status="Online" />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("hides icon when showIcon is false", () => {
      const { container } = render(<StatusBadge status="Online" showIcon={false} />);
      const svg = container.querySelector("svg");
      expect(svg).not.toBeInTheDocument();
    });

    it("renders custom icon when provided", () => {
      const CustomIcon = () => <span data-testid="custom-icon">Custom</span>;
      render(<StatusBadge status="Online" icon={<CustomIcon />} />);
      expect(screen.getByTestId("custom-icon")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has role status", () => {
      render(<StatusBadge status="Online" />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("has default aria-label", () => {
      render(<StatusBadge status="Online" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveAttribute("aria-label", "Status: Online");
    });

    it("uses custom aria-label when provided", () => {
      render(<StatusBadge status="Online" ariaLabel="Device is online" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveAttribute("aria-label", "Device is online");
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      render(<StatusBadge status="Online" className="custom-class" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("custom-class");
    });
  });

  describe("Unknown Status", () => {
    it("renders unknown status with default gray color", () => {
      render(<StatusBadge status="Unknown" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveTextContent("Unknown");
      expect(badge).toHaveClass("text-gray-700");
    });
  });
});
