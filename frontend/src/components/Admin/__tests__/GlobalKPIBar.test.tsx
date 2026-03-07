/**
 * GlobalKPIBar Component Tests
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { GlobalKPIBar } from "../GlobalKPIBar";
import { DashboardProvider } from "../../../contexts/DashboardContext";
import { MockDataService } from "../../../services/mockDataService";

jest.mock("../../../services/mockDataService");

describe("GlobalKPIBar", () => {
  const mockKPIMetrics = {
    totalDevices: 500,
    activeDevices: 450,
    criticalAlerts: 12,
    dataIngestRate: 450,
    averageWQI: 78.5,
    systemLatency: 150,
  };

  beforeEach(() => {
    (MockDataService.getKPIMetrics as jest.Mock).mockReturnValue(
      mockKPIMetrics
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders all 6 KPI cards", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Total Devices")).toBeInTheDocument();
      expect(screen.getByText("Active Devices")).toBeInTheDocument();
      expect(screen.getByText("Critical Alerts")).toBeInTheDocument();
      expect(screen.getByText("Data Ingest Rate")).toBeInTheDocument();
      expect(screen.getByText("Average WQI")).toBeInTheDocument();
      expect(screen.getByText("System Latency")).toBeInTheDocument();
    });
  });

  it("displays correct metric values", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      // Use getAllByText and check count for values that appear multiple times
      const values450 = screen.getAllByText("450");
      expect(values450).toHaveLength(2); // Active Devices and Data Ingest Rate
      
      expect(screen.getByText("500")).toBeInTheDocument(); // Total Devices
      expect(screen.getByText("12")).toBeInTheDocument(); // Critical Alerts
      expect(screen.getByText("78.5")).toBeInTheDocument(); // Average WQI
      expect(screen.getByText("150")).toBeInTheDocument(); // System Latency
    });
  });

  it("displays units for appropriate metrics", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("msg/min")).toBeInTheDocument(); // Data Ingest Rate
      expect(screen.getByText("ms")).toBeInTheDocument(); // System Latency
    });
  });

  it("displays active devices percentage subtitle", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("90.0%")).toBeInTheDocument();
    });
  });

  it("displays System Overview heading", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("System Overview")).toBeInTheDocument();
    });
  });

  it("displays MockDataBadge", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("MOCK DATA")).toBeInTheDocument();
    });
  });

  it("shows loading skeleton initially", () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    // Loading skeleton should be present before data loads
    const skeletons = screen.getAllByRole("status");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("fetches metrics on mount", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(MockDataService.getKPIMetrics).toHaveBeenCalledTimes(1);
    });
  });

  it("has proper ARIA region label", async () => {
    render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: "Key Performance Indicators" })
      ).toBeInTheDocument();
    });
  });

  it("uses responsive grid classes", async () => {
    const { container } = render(
      <DashboardProvider userRole="Admin" userId="test-user">
        <GlobalKPIBar />
      </DashboardProvider>
    );

    await waitFor(() => {
      const grid = container.querySelector(".grid-cols-6");
      expect(grid).toBeInTheDocument();
      expect(grid).toHaveClass("lg:grid-cols-3");
      expect(grid).toHaveClass("md:grid-cols-2");
    });
  });
});
