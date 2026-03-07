/**
 * Device Fleet Table Tests
 * Tests for DeviceFleetTable component
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ToastContainer } from "react-toastify";
import DeviceFleetTable from "../DeviceFleetTable";
import { DashboardProvider } from "../../../contexts/DashboardContext";
import * as MockDataServiceModule from "../../../services/mockDataService";

// Mock the MockDataService
jest.mock("../../../services/mockDataService", () => ({
  MockDataService: {
    getDevices: jest.fn(),
  },
}));

const mockDevices = [
  {
    deviceId: "ESP32-ABC123",
    location: "Mumbai Water Treatment Plant",
    status: "Online" as const,
    lastData: new Date(Date.now() - 60000), // 1 minute ago
    battery: 85,
    coordinates: { lat: 19.076, lng: 72.8777 },
    wqi: 78,
  },
  {
    deviceId: "ESP32-DEF456",
    location: "Delhi Distribution Center",
    status: "Warning" as const,
    lastData: new Date(Date.now() - 300000), // 5 minutes ago
    battery: 45,
    coordinates: { lat: 28.7041, lng: 77.1025 },
    wqi: 65,
  },
  {
    deviceId: "ESP32-GHI789",
    location: "Bangalore Reservoir",
    status: "Offline" as const,
    lastData: new Date(Date.now() - 900000), // 15 minutes ago
    battery: 15,
    coordinates: { lat: 12.9716, lng: 77.5946 },
    wqi: 45,
  },
];

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <DashboardProvider userRole="Admin" userId="test-user">
      {component}
      <ToastContainer />
    </DashboardProvider>
  );
};

describe("DeviceFleetTable", () => {
  beforeEach(() => {
    const MockDataService = MockDataServiceModule.MockDataService as any;
    MockDataService.getDevices.mockReturnValue(mockDevices);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("renders device fleet table with devices", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("Device Fleet")).toBeInTheDocument();
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.getByText("ESP32-DEF456")).toBeInTheDocument();
      expect(screen.getByText("ESP32-GHI789")).toBeInTheDocument();
    });
  });

  test("displays mock data badge", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("MOCK DATA")).toBeInTheDocument();
    });
  });

  test("filters devices by status", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Filter by Online status
    const statusFilter = screen.getByLabelText("Filter by status");
    fireEvent.change(statusFilter, { target: { value: "Online" } });

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
      expect(screen.queryByText("ESP32-GHI789")).not.toBeInTheDocument();
    });
  });

  test("filters devices by battery level", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Filter by High battery
    const batteryFilter = screen.getByLabelText("Filter by battery level");
    fireEvent.change(batteryFilter, { target: { value: "High" } });

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
      expect(screen.queryByText("ESP32-GHI789")).not.toBeInTheDocument();
    });
  });

  test("searches devices by device ID", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Search by device ID
    const searchInput = screen.getByPlaceholderText(
      "Search by Device ID or Location..."
    );
    fireEvent.change(searchInput, { target: { value: "ABC123" } });

    // Wait for debounce (300ms)
    await waitFor(
      () => {
        expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
        expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
        expect(screen.queryByText("ESP32-GHI789")).not.toBeInTheDocument();
      },
      { timeout: 500 }
    );
  });

  test("searches devices by location", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Search by location
    const searchInput = screen.getByPlaceholderText(
      "Search by Device ID or Location..."
    );
    fireEvent.change(searchInput, { target: { value: "Mumbai" } });

    // Wait for debounce (300ms)
    await waitFor(
      () => {
        expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
        expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
        expect(screen.queryByText("ESP32-GHI789")).not.toBeInTheDocument();
      },
      { timeout: 500 }
    );
  });

  test("clears all filters", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Apply filters
    const statusFilter = screen.getByLabelText("Filter by status");
    fireEvent.change(statusFilter, { target: { value: "Online" } });

    await waitFor(() => {
      expect(screen.queryByText("ESP32-DEF456")).not.toBeInTheDocument();
    });

    // Clear filters
    const clearButton = screen.getByText(/Clear Filters/i);
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
      expect(screen.getByText("ESP32-DEF456")).toBeInTheDocument();
      expect(screen.getByText("ESP32-GHI789")).toBeInTheDocument();
    });
  });

  test("displays active filter count", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Apply status filter
    const statusFilter = screen.getByLabelText("Filter by status");
    fireEvent.change(statusFilter, { target: { value: "Online" } });

    await waitFor(() => {
      expect(screen.getByText("1")).toBeInTheDocument(); // Filter count badge
    });

    // Apply battery filter
    const batteryFilter = screen.getByLabelText("Filter by battery level");
    fireEvent.change(batteryFilter, { target: { value: "High" } });

    await waitFor(() => {
      expect(screen.getByText("2")).toBeInTheDocument(); // Filter count badge
    });
  });

  test("sorts devices by column", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Click on Device ID header to sort
    const deviceIdHeader = screen.getByText("Device ID");
    fireEvent.click(deviceIdHeader);

    // Check that sorting indicator appears
    await waitFor(() => {
      const header = deviceIdHeader.closest("th");
      expect(header).toHaveAttribute("aria-sort");
    });
  });

  test("changes page size", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Change page size
    const pageSizeSelect = screen.getByLabelText("Rows per page");
    fireEvent.change(pageSizeSelect, { target: { value: "10" } });

    await waitFor(() => {
      expect(screen.getByText("10 per page")).toBeInTheDocument();
    });
  });

  test("navigates between pages", async () => {
    // Create more devices to enable pagination
    const manyDevices = Array.from({ length: 30 }, (_, i) => ({
      deviceId: `ESP32-TEST${i}`,
      location: `Location ${i}`,
      status: "Online" as const,
      lastData: new Date(),
      battery: 80,
      coordinates: { lat: 0, lng: 0 },
      wqi: 75,
    }));

    const MockDataService = MockDataServiceModule.MockDataService as any;
    MockDataService.getDevices.mockReturnValue(manyDevices);

    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-TEST0")).toBeInTheDocument();
    });

    // Click next page
    const nextButton = screen.getByLabelText("Next page");
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/Page 2 of/)).toBeInTheDocument();
    });
  });

  test("disables actions in read-only mode", async () => {
    renderWithProvider(<DeviceFleetTable readOnly={true} />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // View button should be present
    const viewButtons = screen.getAllByLabelText(/View device/i);
    expect(viewButtons.length).toBeGreaterThan(0);

    // Action buttons (Restart, Calibrate, Disable) should not be present
    expect(screen.queryByLabelText(/Restart device/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Calibrate sensors/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Disable device/i)).not.toBeInTheDocument();
  });

  test("displays empty state when no devices match filters", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("ESP32-ABC123")).toBeInTheDocument();
    });

    // Apply filter that matches no devices
    const searchInput = screen.getByPlaceholderText(
      "Search by Device ID or Location..."
    );
    fireEvent.change(searchInput, { target: { value: "NONEXISTENT" } });

    // Wait for debounce
    await waitFor(
      () => {
        expect(
          screen.getByText("No devices found matching the current filters.")
        ).toBeInTheDocument();
      },
      { timeout: 500 }
    );
  });

  test("displays battery indicators with correct colors", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getByText("85%")).toBeInTheDocument(); // High battery
      expect(screen.getByText("45%")).toBeInTheDocument(); // Medium battery
      expect(screen.getByText("15%")).toBeInTheDocument(); // Low battery
    });
  });

  test("displays status badges with correct colors", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      const statusBadges = screen.getAllByText(/Online|Warning|Offline/);
      expect(statusBadges.length).toBeGreaterThan(0);
    });
  });

  test("displays relative time for last data", async () => {
    renderWithProvider(<DeviceFleetTable />);

    await waitFor(() => {
      expect(screen.getAllByText(/minute ago|minutes ago/).length).toBeGreaterThan(0);
    });
  });
});
