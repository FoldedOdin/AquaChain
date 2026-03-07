import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import TimeRangeSelector from "../TimeRangeSelector";
import { TimeRange } from "../../../types/dashboard";

describe("TimeRangeSelector", () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it("renders all time range options", () => {
    render(<TimeRangeSelector value="24h" onChange={mockOnChange} />);

    expect(screen.getByText("1 Hour")).toBeInTheDocument();
    expect(screen.getByText("6 Hours")).toBeInTheDocument();
    expect(screen.getByText("24 Hours")).toBeInTheDocument();
    expect(screen.getByText("7 Days")).toBeInTheDocument();
  });

  it("highlights the selected time range", () => {
    render(<TimeRangeSelector value="6h" onChange={mockOnChange} />);

    const selectedButton = screen.getByText("6 Hours");
    expect(selectedButton).toHaveClass("bg-blue-600", "text-white");
  });

  it("calls onChange when a time range is clicked", () => {
    render(<TimeRangeSelector value="24h" onChange={mockOnChange} />);

    const oneHourButton = screen.getByText("1 Hour");
    fireEvent.click(oneHourButton);

    expect(mockOnChange).toHaveBeenCalledWith("1h");
  });

  it("updates selection when value prop changes", () => {
    const { rerender } = render(
      <TimeRangeSelector value="1h" onChange={mockOnChange} />
    );

    expect(screen.getByText("1 Hour")).toHaveClass("bg-blue-600");

    rerender(<TimeRangeSelector value="7d" onChange={mockOnChange} />);

    expect(screen.getByText("7 Days")).toHaveClass("bg-blue-600");
    expect(screen.getByText("1 Hour")).not.toHaveClass("bg-blue-600");
  });

  it("has proper ARIA attributes for accessibility", () => {
    render(<TimeRangeSelector value="24h" onChange={mockOnChange} />);

    const group = screen.getByRole("group", { name: "Time range selector" });
    expect(group).toBeInTheDocument();

    const selectedButton = screen.getByText("24 Hours");
    expect(selectedButton).toHaveAttribute("aria-pressed", "true");

    const unselectedButton = screen.getByText("1 Hour");
    expect(unselectedButton).toHaveAttribute("aria-pressed", "false");
  });

  it("has descriptive aria-labels for each button", () => {
    render(<TimeRangeSelector value="24h" onChange={mockOnChange} />);

    expect(
      screen.getByLabelText("Select 1 Hour time range")
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Select 6 Hours time range")
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Select 24 Hours time range")
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Select 7 Days time range")
    ).toBeInTheDocument();
  });

  it("applies hover styles to unselected buttons", () => {
    render(<TimeRangeSelector value="24h" onChange={mockOnChange} />);

    const unselectedButton = screen.getByText("1 Hour");
    expect(unselectedButton).toHaveClass("hover:bg-gray-200");
  });

  it("handles rapid clicks correctly", () => {
    render(<TimeRangeSelector value="24h" onChange={mockOnChange} />);

    const oneHourButton = screen.getByText("1 Hour");
    const sevenDaysButton = screen.getByText("7 Days");

    fireEvent.click(oneHourButton);
    fireEvent.click(sevenDaysButton);
    fireEvent.click(oneHourButton);

    expect(mockOnChange).toHaveBeenCalledTimes(3);
    expect(mockOnChange).toHaveBeenNthCalledWith(1, "1h");
    expect(mockOnChange).toHaveBeenNthCalledWith(2, "7d");
    expect(mockOnChange).toHaveBeenNthCalledWith(3, "1h");
  });
});
