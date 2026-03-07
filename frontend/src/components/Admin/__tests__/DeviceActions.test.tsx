/**
 * Device Actions Tests
 * Tests for DeviceActions component
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ToastContainer } from "react-toastify";
import DeviceActions from "../DeviceActions";
import { Device } from "../../../types/device";

const mockDevice: Device = {
  deviceId: "ESP32-ABC123",
  location: "Mumbai Water Treatment Plant",
  status: "Online",
  lastData: new Date(),
  battery: 85,
  coordinates: { lat: 19.076, lng: 72.8777 },
  wqi: 78,
};

// Mock window.location.href
delete (window as any).location;
window.location = { href: "" } as any;

describe("DeviceActions", () => {
  beforeEach(() => {
    window.location.href = "";
  });

  test("renders all action buttons when not read-only", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    expect(screen.getByLabelText(/View device/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Restart device/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Calibrate sensors/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Disable device/i)).toBeInTheDocument();
  });

  test("renders only view button when read-only", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={true} />
        <ToastContainer />
      </>
    );

    expect(screen.getByLabelText(/View device/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Restart device/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Calibrate sensors/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Disable device/i)).not.toBeInTheDocument();
  });

  test("navigates to device detail page on view click", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const viewButton = screen.getByLabelText(/View device/i);
    fireEvent.click(viewButton);

    expect(window.location.href).toBe("/devices/ESP32-ABC123");
  });

  test("shows restart confirmation modal on restart click", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const restartButton = screen.getByLabelText(/Restart device/i);
    fireEvent.click(restartButton);

    expect(screen.getByText("Restart Device")).toBeInTheDocument();
    expect(
      screen.getByText(/Are you sure you want to restart ESP32-ABC123/i)
    ).toBeInTheDocument();
  });

  test("shows calibrate sensor modal on calibrate click", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const calibrateButton = screen.getByLabelText(/Calibrate sensors/i);
    fireEvent.click(calibrateButton);

    expect(screen.getByText("Calibrate Sensors")).toBeInTheDocument();
    expect(screen.getByText(/Select sensors to calibrate/i)).toBeInTheDocument();
  });

  test("shows disable confirmation modal on disable click", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const disableButton = screen.getByLabelText(/Disable device/i);
    fireEvent.click(disableButton);

    expect(screen.getByText("Disable Device")).toBeInTheDocument();
    expect(
      screen.getByText(/Are you sure you want to disable ESP32-ABC123/i)
    ).toBeInTheDocument();
  });

  test("closes restart modal on cancel", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const restartButton = screen.getByLabelText(/Restart device/i);
    fireEvent.click(restartButton);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(screen.queryByText("Restart Device")).not.toBeInTheDocument();
  });

  test("shows success toast on restart confirm", async () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const restartButton = screen.getByLabelText(/Restart device/i);
    fireEvent.click(restartButton);

    const confirmButton = screen.getByText("Restart");
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Device ESP32-ABC123 restart initiated/i)
      ).toBeInTheDocument();
    });
  });

  test("shows success toast on calibrate confirm", async () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const calibrateButton = screen.getByLabelText(/Calibrate sensors/i);
    fireEvent.click(calibrateButton);

    // Select pH sensor
    const phCheckbox = screen.getByLabelText(/pH Sensor/i);
    fireEvent.click(phCheckbox);

    const confirmButton = screen.getByText("Start Calibration");
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Calibration started for ESP32-ABC123: pH/i)
      ).toBeInTheDocument();
    });
  });

  test("shows warning toast on disable confirm", async () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const disableButton = screen.getByLabelText(/Disable device/i);
    fireEvent.click(disableButton);

    const confirmButton = screen.getByText("Disable");
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(
        screen.getByText(/Device ESP32-ABC123 has been disabled/i)
      ).toBeInTheDocument();
    });
  });

  test("calibrate modal requires at least one sensor selection", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const calibrateButton = screen.getByLabelText(/Calibrate sensors/i);
    fireEvent.click(calibrateButton);

    const confirmButton = screen.getByText("Start Calibration");
    expect(confirmButton).toBeDisabled();

    // Select a sensor
    const phCheckbox = screen.getByLabelText(/pH Sensor/i);
    fireEvent.click(phCheckbox);

    expect(confirmButton).not.toBeDisabled();
  });

  test("calibrate modal allows multiple sensor selection", () => {
    render(
      <>
        <DeviceActions device={mockDevice} readOnly={false} />
        <ToastContainer />
      </>
    );

    const calibrateButton = screen.getByLabelText(/Calibrate sensors/i);
    fireEvent.click(calibrateButton);

    // Select multiple sensors
    const phCheckbox = screen.getByLabelText(/pH Sensor/i);
    const turbidityCheckbox = screen.getByLabelText(/Turbidity Sensor/i);

    fireEvent.click(phCheckbox);
    fireEvent.click(turbidityCheckbox);

    const confirmButton = screen.getByText("Start Calibration");
    fireEvent.click(confirmButton);

    // Both sensors should be in the toast message
    waitFor(() => {
      const toast = screen.getByText(/Calibration started/i);
      expect(toast).toHaveTextContent("pH");
      expect(toast).toHaveTextContent("turbidity");
    });
  });
});
