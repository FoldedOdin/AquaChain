/**
 * KPICard Component Tests
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { KPICard } from "../KPICard";
import { Server } from "lucide-react";

describe("KPICard", () => {
  it("renders label and value correctly", () => {
    render(
      <KPICard
        label="Total Devices"
        value={500}
        icon={<Server />}
        color="blue"
      />
    );

    expect(screen.getByText("Total Devices")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
  });

  it("displays unit when provided", () => {
    render(
      <KPICard
        label="System Latency"
        value={150}
        icon={<Server />}
        color="orange"
        unit="ms"
      />
    );

    expect(screen.getByText("ms")).toBeInTheDocument();
  });

  it("displays subtitle when provided", () => {
    render(
      <KPICard
        label="Active Devices"
        value={450}
        icon={<Server />}
        color="green"
        subtitle="90.0%"
      />
    );

    expect(screen.getByText("90.0%")).toBeInTheDocument();
  });

  it("formats value with specified precision", () => {
    render(
      <KPICard
        label="Average WQI"
        value={78.456}
        icon={<Server />}
        color="cyan"
        precision={1}
      />
    );

    expect(screen.getByText("78.5")).toBeInTheDocument();
  });

  it("displays upward trend indicator when value increases", () => {
    render(
      <KPICard
        label="Total Devices"
        value={510}
        previousValue={500}
        icon={<Server />}
        color="blue"
      />
    );

    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByLabelText(/Trend: up by 10/i)).toBeInTheDocument();
  });

  it("displays downward trend indicator when value decreases", () => {
    render(
      <KPICard
        label="Critical Alerts"
        value={5}
        previousValue={10}
        icon={<Server />}
        color="red"
      />
    );

    const valueElement = screen.getByLabelText(/Trend: down by 5/i);
    expect(valueElement).toBeInTheDocument();
    expect(valueElement).toHaveTextContent("5");
  });

  it("does not display trend when previousValue is not provided", () => {
    render(
      <KPICard
        label="Total Devices"
        value={500}
        icon={<Server />}
        color="blue"
      />
    );

    expect(screen.queryByLabelText(/Trend:/i)).not.toBeInTheDocument();
  });

  it("does not display trend when value is unchanged", () => {
    render(
      <KPICard
        label="Total Devices"
        value={500}
        previousValue={500}
        icon={<Server />}
        color="blue"
      />
    );

    expect(screen.queryByLabelText(/Trend:/i)).not.toBeInTheDocument();
  });

  it("applies correct color classes", () => {
    const { container } = render(
      <KPICard
        label="Total Devices"
        value={500}
        icon={<Server />}
        color="blue"
      />
    );

    const iconContainer = container.querySelector(".bg-blue-50");
    expect(iconContainer).toBeInTheDocument();
  });

  it("has aria-live attribute for value updates", () => {
    render(
      <KPICard
        label="Total Devices"
        value={500}
        icon={<Server />}
        color="blue"
      />
    );

    const valueElement = screen.getByText("500");
    expect(valueElement).toHaveAttribute("aria-live", "polite");
  });

  it("formats trend with precision", () => {
    render(
      <KPICard
        label="Average WQI"
        value={78.5}
        previousValue={77.2}
        icon={<Server />}
        color="cyan"
        precision={1}
      />
    );

    expect(screen.getByText("1.3")).toBeInTheDocument();
  });
});
