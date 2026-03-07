/**
 * MockDataBadge Component Tests
 * 
 * Unit tests for MockDataBadge component.
 * Tests tooltip display, size variants, and accessibility.
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { MockDataBadge } from "../MockDataBadge";

describe("MockDataBadge", () => {
  describe("Rendering", () => {
    it("renders MOCK DATA text", () => {
      render(<MockDataBadge />);
      expect(screen.getByText("MOCK DATA")).toBeInTheDocument();
    });

    it("renders info icon", () => {
      const { container } = render(<MockDataBadge />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });

    it("has purple color scheme", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-purple-700");
      expect(badge).toHaveClass("bg-purple-100");
    });
  });

  describe("Size Variants", () => {
    it("renders small size", () => {
      render(<MockDataBadge size="sm" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-xs");
    });

    it("renders medium size by default", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-xs");
    });

    it("renders large size", () => {
      render(<MockDataBadge size="lg" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("text-sm");
    });
  });

  describe("Tooltip", () => {
    it("shows tooltip on mouse enter", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      
      fireEvent.mouseEnter(badge);
      
      const tooltip = screen.getByRole("tooltip");
      expect(tooltip).toBeInTheDocument();
      expect(tooltip).toHaveTextContent(
        "This data is simulated for demonstration purposes"
      );
    });

    it("hides tooltip on mouse leave", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      
      fireEvent.mouseEnter(badge);
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
      
      fireEvent.mouseLeave(badge);
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    });

    it("shows tooltip on focus", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      
      fireEvent.focus(badge);
      
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
    });

    it("hides tooltip on blur", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      
      fireEvent.focus(badge);
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
      
      fireEvent.blur(badge);
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    });

    it("displays custom tooltip text", () => {
      const customText = "Custom mock data message";
      render(<MockDataBadge tooltipText={customText} />);
      const badge = screen.getByRole("status");
      
      fireEvent.mouseEnter(badge);
      
      const tooltip = screen.getByRole("tooltip");
      expect(tooltip).toHaveTextContent(customText);
    });
  });

  describe("Accessibility", () => {
    it("has role status", () => {
      render(<MockDataBadge />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("has aria-label", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveAttribute("aria-label", "Mock data indicator");
    });

    it("is keyboard accessible with tabIndex", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveAttribute("tabIndex", "0");
    });

    it("has cursor-help style", () => {
      render(<MockDataBadge />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("cursor-help");
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      render(<MockDataBadge className="custom-class" />);
      const badge = screen.getByRole("status");
      expect(badge).toHaveClass("custom-class");
    });
  });
});
