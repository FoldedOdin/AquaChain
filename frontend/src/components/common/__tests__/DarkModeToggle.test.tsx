/**
 * DarkModeToggle Component Tests
 * 
 * Unit tests for DarkModeToggle component.
 * Tests toggle functionality, size variants, and integration with useDarkMode hook.
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import {
  DarkModeToggle,
  DarkModeButton,
  DarkModeMenuItem,
} from "../DarkModeToggle";
import { DashboardProvider } from "../../../contexts/DashboardContext";

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

describe("DarkModeToggle", () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Remove dark class from document
    document.documentElement.classList.remove("dark");
  });

  describe("Rendering", () => {
    it("renders toggle switch", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toBeInTheDocument();
    });

    it("shows sun icon in light mode", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveAttribute("aria-checked", "false");
    });

    it("renders without label by default", () => {
      renderWithProvider(<DarkModeToggle />);
      expect(screen.queryByText(/Mode/)).not.toBeInTheDocument();
    });

    it("renders with label when showLabel is true", () => {
      renderWithProvider(<DarkModeToggle showLabel />);
      expect(screen.getByText(/Light Mode/)).toBeInTheDocument();
    });
  });

  describe("Toggle Functionality", () => {
    it("toggles dark mode when clicked", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      
      expect(toggle).toHaveAttribute("aria-checked", "false");
      
      fireEvent.click(toggle);
      
      expect(toggle).toHaveAttribute("aria-checked", "true");
    });

    it("updates label text when toggled", () => {
      renderWithProvider(<DarkModeToggle showLabel />);
      const toggle = screen.getByRole("switch");
      
      expect(screen.getByText(/Light Mode/)).toBeInTheDocument();
      
      fireEvent.click(toggle);
      
      expect(screen.getByText(/Dark Mode/)).toBeInTheDocument();
    });

    it("adds dark class to document when enabled", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      
      fireEvent.click(toggle);
      
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });

    it("removes dark class from document when disabled", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      
      // Enable dark mode
      fireEvent.click(toggle);
      expect(document.documentElement.classList.contains("dark")).toBe(true);
      
      // Disable dark mode
      fireEvent.click(toggle);
      expect(document.documentElement.classList.contains("dark")).toBe(false);
    });
  });

  describe("Size Variants", () => {
    it("renders small size", () => {
      renderWithProvider(<DarkModeToggle size="sm" />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveClass("w-10", "h-6");
    });

    it("renders medium size by default", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveClass("w-14", "h-7");
    });

    it("renders large size", () => {
      renderWithProvider(<DarkModeToggle size="lg" />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveClass("w-16", "h-9");
    });
  });

  describe("Accessibility", () => {
    it("has role switch", () => {
      renderWithProvider(<DarkModeToggle />);
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    it("has aria-checked attribute", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveAttribute("aria-checked");
    });

    it("has descriptive aria-label", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveAttribute("aria-label", "Switch to dark mode");
    });

    it("updates aria-label when toggled", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      
      fireEvent.click(toggle);
      
      expect(toggle).toHaveAttribute("aria-label", "Switch to light mode");
    });

    it("has title attribute for tooltip", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveAttribute("title", "Switch to dark mode");
    });

    it("has focus ring styles", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveClass("focus:ring-2", "focus:ring-blue-500");
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      renderWithProvider(<DarkModeToggle className="custom-class" />);
      const container = screen.getByRole("switch").parentElement;
      expect(container).toHaveClass("custom-class");
    });
  });

  describe("localStorage Persistence", () => {
    it("persists theme preference in localStorage", () => {
      renderWithProvider(<DarkModeToggle />);
      const toggle = screen.getByRole("switch");
      
      fireEvent.click(toggle);
      
      const savedConfig = localStorage.getItem("dashboardConfig");
      expect(savedConfig).toBeTruthy();
      
      const config = JSON.parse(savedConfig!);
      expect(config.theme).toBe("dark");
    });
  });
});

describe("DarkModeButton", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  describe("Rendering", () => {
    it("renders button", () => {
      renderWithProvider(<DarkModeButton />);
      const button = screen.getByRole("button");
      expect(button).toBeInTheDocument();
    });

    it("shows sun icon in light mode", () => {
      const { container } = renderWithProvider(<DarkModeButton />);
      const svg = container.querySelector("svg");
      expect(svg).toBeInTheDocument();
    });
  });

  describe("Toggle Functionality", () => {
    it("toggles dark mode when clicked", () => {
      renderWithProvider(<DarkModeButton />);
      const button = screen.getByRole("button");
      
      fireEvent.click(button);
      
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });
  });

  describe("Size Variants", () => {
    it("renders small size", () => {
      renderWithProvider(<DarkModeButton size="sm" />);
      const button = screen.getByRole("button");
      expect(button).toHaveClass("p-1.5");
    });

    it("renders medium size by default", () => {
      renderWithProvider(<DarkModeButton />);
      const button = screen.getByRole("button");
      expect(button).toHaveClass("p-2");
    });

    it("renders large size", () => {
      renderWithProvider(<DarkModeButton size="lg" />);
      const button = screen.getByRole("button");
      expect(button).toHaveClass("p-3");
    });
  });

  describe("Accessibility", () => {
    it("has descriptive aria-label", () => {
      renderWithProvider(<DarkModeButton />);
      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("aria-label", "Switch to dark mode");
    });

    it("has title attribute", () => {
      renderWithProvider(<DarkModeButton />);
      const button = screen.getByRole("button");
      expect(button).toHaveAttribute("title", "Switch to dark mode");
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      renderWithProvider(<DarkModeButton className="custom-button" />);
      const button = screen.getByRole("button");
      expect(button).toHaveClass("custom-button");
    });
  });
});

describe("DarkModeMenuItem", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  describe("Rendering", () => {
    it("renders menu item button", () => {
      renderWithProvider(<DarkModeMenuItem />);
      const button = screen.getByRole("menuitem");
      expect(button).toBeInTheDocument();
    });

    it("shows Light Mode text in light mode", () => {
      renderWithProvider(<DarkModeMenuItem />);
      expect(screen.getByText("Light Mode")).toBeInTheDocument();
    });

    it("shows Off status in light mode", () => {
      renderWithProvider(<DarkModeMenuItem />);
      expect(screen.getByText("Off")).toBeInTheDocument();
    });
  });

  describe("Toggle Functionality", () => {
    it("toggles dark mode when clicked", () => {
      renderWithProvider(<DarkModeMenuItem />);
      const button = screen.getByRole("menuitem");
      
      fireEvent.click(button);
      
      expect(document.documentElement.classList.contains("dark")).toBe(true);
    });

    it("updates text when toggled", () => {
      renderWithProvider(<DarkModeMenuItem />);
      const button = screen.getByRole("menuitem");
      
      fireEvent.click(button);
      
      expect(screen.getByText("Dark Mode")).toBeInTheDocument();
      expect(screen.getByText("On")).toBeInTheDocument();
    });
  });

  describe("Custom Styling", () => {
    it("applies custom className", () => {
      renderWithProvider(<DarkModeMenuItem className="custom-menu-item" />);
      const button = screen.getByRole("menuitem");
      expect(button).toHaveClass("custom-menu-item");
    });
  });
});
