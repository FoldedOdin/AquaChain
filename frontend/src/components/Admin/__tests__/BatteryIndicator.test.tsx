/**
 * Battery Indicator Tests
 * Tests for BatteryIndicator component
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import BatteryIndicator from "../BatteryIndicator";

describe("BatteryIndicator", () => {
  test("renders high battery level (>50%) with green color", () => {
    render(<BatteryIndicator level={85} />);

    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 85% \(High\)/i)).toBeInTheDocument();
  });

  test("renders medium battery level (20-50%) with yellow color", () => {
    render(<BatteryIndicator level={35} />);

    expect(screen.getByText("35%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 35% \(Medium\)/i)).toBeInTheDocument();
  });

  test("renders low battery level (<20%) with red color", () => {
    render(<BatteryIndicator level={15} />);

    expect(screen.getByText("15%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 15% \(Low\)/i)).toBeInTheDocument();
  });

  test("renders battery level at 50% boundary as medium", () => {
    render(<BatteryIndicator level={50} />);

    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 50% \(Medium\)/i)).toBeInTheDocument();
  });

  test("renders battery level at 20% boundary as medium", () => {
    render(<BatteryIndicator level={20} />);

    expect(screen.getByText("20%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 20% \(Medium\)/i)).toBeInTheDocument();
  });

  test("renders 0% battery as low", () => {
    render(<BatteryIndicator level={0} />);

    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 0% \(Low\)/i)).toBeInTheDocument();
  });

  test("renders 100% battery as high", () => {
    render(<BatteryIndicator level={100} />);

    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText(/Battery level: 100% \(High\)/i)).toBeInTheDocument();
  });

  test("has accessible screen reader text", () => {
    render(<BatteryIndicator level={75} />);

    const srText = screen.getByText(/Battery level: 75% \(High\)/i);
    expect(srText).toHaveClass("sr-only");
  });
});
