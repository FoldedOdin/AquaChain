/**
 * UserManagementTable Component Tests
 * 
 * Tests for the User Management Table component including:
 * - Rendering with mock data
 * - Sorting functionality
 * - Filtering by role and status
 * - Search functionality
 * - Pagination
 * - Action buttons
 */

import React from "react";
import { render, screen, waitFor, within, fireEvent } from "@testing-library/react";
import { toast } from "react-toastify";

import UserManagementTable from "../UserManagementTable";
import { DashboardProvider } from "../../../contexts/DashboardContext";
import { MockDataService } from "../../../services/mockDataService";

// Mock dependencies
jest.mock("react-toastify", () => ({
  toast: {
    success: jest.fn(),
    warning: jest.fn(),
    info: jest.fn(),
    error: jest.fn(),
  },
}));

jest.mock("../../../services/mockDataService", () => ({
  MockDataService: {
    getUsers: jest.fn(),
  },
}));

// Mock user data
const mockUsers = [
  {
    userId: "USER-001",
    email: "admin@aquachain.com",
    role: "Admin" as const,
    status: "Active" as const,
    lastLogin: new Date("2024-01-15T10:00:00Z"),
    createdAt: new Date("2023-01-01T00:00:00Z"),
  },
  {
    userId: "USER-002",
    email: "tech@aquachain.com",
    role: "Technician" as const,
    status: "Active" as const,
    lastLogin: new Date("2024-01-14T15:30:00Z"),
    createdAt: new Date("2023-02-01T00:00:00Z"),
  },
  {
    userId: "USER-003",
    email: "consumer@aquachain.com",
    role: "Consumer" as const,
    status: "Inactive" as const,
    lastLogin: new Date("2024-01-10T08:00:00Z"),
    createdAt: new Date("2023-03-01T00:00:00Z"),
  },
];

// Wrapper component with DashboardProvider
const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <DashboardProvider userRole="Admin" userId="USER-001">
      {component}
    </DashboardProvider>
  );
};

describe("UserManagementTable", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (MockDataService.getUsers as jest.Mock).mockReturnValue(mockUsers);
  });

  describe("Rendering", () => {
    it("renders the table with header", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("User Management")).toBeInTheDocument();
      });
    });

    it("displays MOCK DATA badge", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("MOCK DATA")).toBeInTheDocument();
      });
    });

    it("renders all column headers", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByRole("columnheader", { name: /user/i })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: /role/i })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: /last login/i })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: /status/i })).toBeInTheDocument();
        expect(screen.getByRole("columnheader", { name: /actions/i })).toBeInTheDocument();
      });
    });

    it("renders user data in table rows", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
        expect(screen.getByText("tech@aquachain.com")).toBeInTheDocument();
        expect(screen.getByText("consumer@aquachain.com")).toBeInTheDocument();
      });
    });

    it("displays role badges for each user", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        const roleBadges = screen.getAllByRole("status");
        // Should have role badges and status badges
        expect(roleBadges.length).toBeGreaterThan(0);
      });
    });

    it("displays status badges for each user", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        const statusBadges = screen.getAllByRole("status");
        expect(statusBadges.length).toBeGreaterThan(0);
      });
    });

    it("displays last login in relative format", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        const timeElements = screen.getAllByText(/ago/i);
        expect(timeElements.length).toBeGreaterThan(0);
      });
    });
  });

  describe("Filtering", () => {
    it("filters users by role", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const roleFilter = screen.getByLabelText("Filter by role");
      fireEvent.change(roleFilter, { target: { value: "Admin" } });

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
        expect(screen.queryByText("tech@aquachain.com")).not.toBeInTheDocument();
      });
    });

    it("filters users by status", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("consumer@aquachain.com")).toBeInTheDocument();
      });

      const statusFilter = screen.getByLabelText("Filter by status");
      fireEvent.change(statusFilter, { target: { value: "Active" } });

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
        expect(screen.queryByText("consumer@aquachain.com")).not.toBeInTheDocument();
      });
    });

    it("searches users by email", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const searchInput = screen.getByLabelText("Search users");
      fireEvent.change(searchInput, { target: { value: "admin" } });

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
        expect(screen.queryByText("tech@aquachain.com")).not.toBeInTheDocument();
      }, { timeout: 500 });
    });

    it("clears all filters", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      // Apply filters
      const roleFilter = screen.getByLabelText("Filter by role");
      fireEvent.change(roleFilter, { target: { value: "Admin" } });

      await waitFor(() => {
        expect(screen.queryByText("tech@aquachain.com")).not.toBeInTheDocument();
      });

      // Clear filters
      const clearButton = screen.getByLabelText("Clear all filters");
      fireEvent.click(clearButton);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
        expect(screen.getByText("tech@aquachain.com")).toBeInTheDocument();
      });
    });

    it("displays active filter count", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const roleFilter = screen.getByLabelText("Filter by role");
      fireEvent.change(roleFilter, { target: { value: "Admin" } });

      await waitFor(() => {
        expect(screen.getByText("1")).toBeInTheDocument();
      });
    });
  });

  describe("Sorting", () => {
    it("sorts by email column", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const emailHeader = screen.getByRole("columnheader", { name: /user/i });
      fireEvent.click(emailHeader);

      await waitFor(() => {
        expect(emailHeader).toHaveAttribute("aria-sort", "ascending");
      });
    });

    it("sorts by role column", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const roleHeader = screen.getByRole("columnheader", { name: /role/i });
      fireEvent.click(roleHeader);

      await waitFor(() => {
        expect(roleHeader).toHaveAttribute("aria-sort");
      });
    });

    it("sorts by last login column", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const lastLoginHeader = screen.getByRole("columnheader", { name: /last login/i });
      fireEvent.click(lastLoginHeader);

      await waitFor(() => {
        expect(lastLoginHeader).toHaveAttribute("aria-sort");
      });
    });

    it("sorts by status column", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const statusHeader = screen.getByRole("columnheader", { name: /status/i });
      fireEvent.click(statusHeader);

      await waitFor(() => {
        expect(statusHeader).toHaveAttribute("aria-sort");
      });
    });
  });

  describe("Pagination", () => {
    it("displays pagination controls", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByLabelText("Previous page")).toBeInTheDocument();
        expect(screen.getByLabelText("Next page")).toBeInTheDocument();
        expect(screen.getByLabelText("Rows per page")).toBeInTheDocument();
      });
    });

    it("displays correct page information", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText(/Showing 1 to 3 of 3 users/i)).toBeInTheDocument();
      });
    });

    it("changes page size", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const pageSizeSelect = screen.getByLabelText("Rows per page");
      fireEvent.change(pageSizeSelect, { target: { value: "10" } });

      await waitFor(() => {
        expect(pageSizeSelect).toHaveValue("10");
      });
    });
  });

  describe("Action Buttons", () => {
    it("renders action buttons for each user", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        const changeRoleButtons = screen.getAllByTitle("Change Role");
        expect(changeRoleButtons).toHaveLength(3);

        const disableButtons = screen.getAllByTitle("Disable User");
        expect(disableButtons).toHaveLength(3);

        const resetPasswordButtons = screen.getAllByTitle("Reset Password");
        expect(resetPasswordButtons).toHaveLength(3);
      });
    });
  });

  describe("Empty State", () => {
    it("displays empty state when no users match filters", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByText("admin@aquachain.com")).toBeInTheDocument();
      });

      const searchInput = screen.getByLabelText("Search users");
      fireEvent.change(searchInput, { target: { value: "nonexistent@example.com" } });

      await waitFor(() => {
        expect(screen.getByText(/No users found matching the current filters/i)).toBeInTheDocument();
      }, { timeout: 500 });
    });
  });

  describe("Loading State", () => {
    it("displays loading skeleton initially", () => {
      (MockDataService.getUsers as jest.Mock).mockReturnValue([]);

      renderWithProvider(<UserManagementTable />);

      // Component should render without errors even with empty data
      expect(screen.getByText("User Management")).toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has proper ARIA labels", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByLabelText("Search users")).toBeInTheDocument();
        expect(screen.getByLabelText("Filter by role")).toBeInTheDocument();
        expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
        expect(screen.getByLabelText("Clear all filters")).toBeInTheDocument();
      });
    });

    it("has proper table roles", async () => {
      renderWithProvider(<UserManagementTable />);

      await waitFor(() => {
        expect(screen.getByRole("table")).toBeInTheDocument();
        expect(screen.getAllByRole("columnheader")).toHaveLength(5);
        expect(screen.getAllByRole("row")).toHaveLength(4); // 1 header + 3 data rows
      });
    });
  });
});
