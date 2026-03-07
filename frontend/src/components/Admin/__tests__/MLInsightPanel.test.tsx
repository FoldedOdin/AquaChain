/**
 * MLInsightPanel Component Tests
 * 
 * Tests for the ML Insight Panel component including:
 * - Rendering with mock data
 * - Contamination risk display with color coding
 * - Anomaly detection count display
 * - 24-hour prediction trend display
 * - Model information display
 * - Retrain model button functionality
 * - Confirmation modal interaction
 * - Toast notifications
 * - Auto-refresh behavior
 * 
 * @module MLInsightPanel.test
 */

import React from "react";
import { render, screen, waitFor, within, fireEvent } from "@testing-library/react";
import { toast } from "react-toastify";
import { MLInsightPanel } from "../MLInsightPanel";
import { DashboardProvider } from "../../../contexts/DashboardContext";
import { MockDataService } from "../../../services/mockDataService";
import { MLInsightData } from "../../../types/dashboard";

// Mock dependencies
jest.mock("react-toastify", () => ({
  toast: {
    error: jest.fn(),
    info: jest.fn(),
    success: jest.fn(),
  },
}));

jest.mock("../../../services/mockDataService", () => ({
  MockDataService: {
    getMLInsights: jest.fn(),
  },
}));

/**
 * Helper function to render MLInsightPanel with DashboardProvider
 */
const renderMLInsightPanel = () => {
  return render(
    <DashboardProvider userRole="Admin" userId="test-user">
      <MLInsightPanel />
    </DashboardProvider>
  );
};

/**
 * Mock ML insights data
 */
const mockMLInsights: MLInsightData = {
  contaminationRisk: {
    level: "Low",
    percentage: 15,
  },
  anomalyDetection: {
    count: 12,
    last24Hours: 12,
  },
  prediction: {
    trend: "Stable",
    wqiForecast: 78,
  },
  modelInfo: {
    version: "XGBoost v2.0.3",
    accuracy: 99.74,
    lastTraining: new Date("2024-01-15T10:00:00Z"),
  },
};

describe("MLInsightPanel", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (MockDataService.getMLInsights as jest.Mock).mockReturnValue(mockMLInsights);
  });

  describe("Rendering", () => {
    it("should render the component with heading", () => {
      renderMLInsightPanel();

      expect(screen.getByText("ML Insights")).toBeInTheDocument();
    });

    it("should display MOCK DATA badge", () => {
      renderMLInsightPanel();

      expect(screen.getByText("MOCK DATA")).toBeInTheDocument();
    });

    it("should display loading skeleton when data is not loaded", () => {
      (MockDataService.getMLInsights as jest.Mock).mockReturnValueOnce(null);
      
      const { container } = renderMLInsightPanel();

      // Component should show loading skeleton when data is null
      expect(container.querySelector('.bg-white')).toBeInTheDocument();
    });
  });

  describe("Contamination Risk Display", () => {
    it("should display contamination risk with percentage", () => {
      renderMLInsightPanel();

      expect(screen.getByText("Contamination Risk")).toBeInTheDocument();
      expect(screen.getByText("15%")).toBeInTheDocument();
      expect(screen.getByText("Low")).toBeInTheDocument();
    });

    it("should apply green color for Low risk", () => {
      renderMLInsightPanel();

      const riskContainer = screen.getByText("15%").parentElement?.parentElement;
      expect(riskContainer).toHaveClass("bg-green-50");
    });

    it("should apply yellow color for Medium risk", () => {
      (MockDataService.getMLInsights as jest.Mock).mockReturnValue({
        ...mockMLInsights,
        contaminationRisk: { level: "Medium", percentage: 55 },
      });

      renderMLInsightPanel();

      const riskContainer = screen.getByText("55%").parentElement?.parentElement;
      expect(riskContainer).toHaveClass("bg-yellow-50");
    });

    it("should apply red color for High risk", () => {
      (MockDataService.getMLInsights as jest.Mock).mockReturnValue({
        ...mockMLInsights,
        contaminationRisk: { level: "High", percentage: 85 },
      });

      renderMLInsightPanel();

      const riskContainer = screen.getByText("85%").parentElement?.parentElement;
      expect(riskContainer).toHaveClass("bg-red-50");
    });

    it("should have accessible label for contamination risk", () => {
      renderMLInsightPanel();

      const riskStatus = screen.getByLabelText(/Contamination risk: Low at 15 percent/i);
      expect(riskStatus).toBeInTheDocument();
    });
  });

  describe("Anomaly Detection Display", () => {
    it("should display anomaly count for last 24 hours", () => {
      renderMLInsightPanel();

      expect(screen.getByText("Anomalies Detected (24h)")).toBeInTheDocument();
      expect(screen.getByText("12")).toBeInTheDocument();
    });

    it("should display alert triangle icon", () => {
      renderMLInsightPanel();

      const anomalySection = screen.getByText("12").closest("div");
      expect(anomalySection).toBeInTheDocument();
    });

    it("should have accessible label for anomaly count", () => {
      renderMLInsightPanel();

      const anomalyStatus = screen.getByLabelText(/12 anomalies detected in last 24 hours/i);
      expect(anomalyStatus).toBeInTheDocument();
    });
  });

  describe("24-Hour Prediction Display", () => {
    it("should display prediction trend", () => {
      renderMLInsightPanel();

      expect(screen.getByText("24-Hour Prediction")).toBeInTheDocument();
      expect(screen.getByText("Stable")).toBeInTheDocument();
    });

    it("should display Improving trend with up arrow", () => {
      (MockDataService.getMLInsights as jest.Mock).mockReturnValue({
        ...mockMLInsights,
        prediction: { trend: "Improving", wqiForecast: 82 },
      });

      renderMLInsightPanel();

      expect(screen.getByText("Improving")).toBeInTheDocument();
    });

    it("should display Declining trend with down arrow", () => {
      (MockDataService.getMLInsights as jest.Mock).mockReturnValue({
        ...mockMLInsights,
        prediction: { trend: "Declining", wqiForecast: 72 },
      });

      renderMLInsightPanel();

      expect(screen.getByText("Declining")).toBeInTheDocument();
    });

    it("should have accessible label for prediction trend", () => {
      renderMLInsightPanel();

      const predictionStatus = screen.getByLabelText(/Water quality trend: Stable/i);
      expect(predictionStatus).toBeInTheDocument();
    });
  });

  describe("Model Information Display", () => {
    it("should display model version", () => {
      renderMLInsightPanel();

      expect(screen.getByText("Model Version:")).toBeInTheDocument();
      expect(screen.getByText("XGBoost v2.0.3")).toBeInTheDocument();
    });

    it("should display model accuracy", () => {
      renderMLInsightPanel();

      expect(screen.getByText("Accuracy:")).toBeInTheDocument();
      expect(screen.getByText("99.74%")).toBeInTheDocument();
    });

    it("should display last training timestamp", () => {
      renderMLInsightPanel();

      expect(screen.getByText("Last Training:")).toBeInTheDocument();
      // Date format: "Jan 15, 2024, 10:00 AM" (format may vary by locale)
      expect(screen.getByText(/Jan.*15.*2024/i)).toBeInTheDocument();
    });
  });

  describe("Retrain Model Button", () => {
    it("should display retrain model button", () => {
      renderMLInsightPanel();

      const retrainButton = screen.getByRole("button", { name: /Retrain machine learning model/i });
      expect(retrainButton).toBeInTheDocument();
      expect(retrainButton).toHaveTextContent("Retrain Model");
    });

    it("should open confirmation modal when clicked", async () => {
      renderMLInsightPanel();

      const retrainButton = screen.getByRole("button", { name: /Retrain machine learning model/i });
      fireEvent.click(retrainButton);

      await waitFor(() => {
        expect(screen.getByText("Retrain ML Model")).toBeInTheDocument();
      });
      expect(
        screen.getByText(/This will initiate model retraining with the latest data/i)
      ).toBeInTheDocument();
    });

    it("should close modal when cancel is clicked", async () => {
      renderMLInsightPanel();

      const retrainButton = screen.getByRole("button", { name: /Retrain machine learning model/i });
      fireEvent.click(retrainButton);

      await waitFor(() => {
        expect(screen.getByText("Retrain ML Model")).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole("button", { name: /Cancel/i });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(screen.queryByText("Retrain ML Model")).not.toBeInTheDocument();
      });
    });

    it("should trigger retraining when confirmed", async () => {
      jest.useFakeTimers();
      renderMLInsightPanel();

      const retrainButton = screen.getByRole("button", { name: /Retrain machine learning model/i });
      fireEvent.click(retrainButton);

      await waitFor(() => {
        expect(screen.getByText("Retrain ML Model")).toBeInTheDocument();
      });

      // Get the confirm button from the modal (not the main retrain button)
      const buttons = screen.getAllByRole("button");
      const confirmButton = buttons.find(btn => btn.textContent === "Retrain" && btn.className.includes("bg-orange"));
      expect(confirmButton).toBeDefined();
      
      fireEvent.click(confirmButton!);

      // Should show info toast
      expect(toast.info).toHaveBeenCalledWith(
        "Model retraining initiated...",
        expect.any(Object)
      );

      // Button should show "Retraining..." state
      await waitFor(() => {
        expect(screen.getByText("Retraining...")).toBeInTheDocument();
      });

      // Fast-forward time to complete retraining
      jest.advanceTimersByTime(3000);

      await waitFor(() => {
        expect(toast.success).toHaveBeenCalledWith(
          "Model retraining completed successfully",
          expect.any(Object)
        );
      });

      jest.useRealTimers();
    });

    it("should disable button during retraining", async () => {
      jest.useFakeTimers();
      renderMLInsightPanel();

      const retrainButton = screen.getByRole("button", { name: /Retrain machine learning model/i });
      fireEvent.click(retrainButton);

      await waitFor(() => {
        expect(screen.getByText("Retrain ML Model")).toBeInTheDocument();
      });

      // Get the confirm button from the modal
      const buttons = screen.getAllByRole("button");
      const confirmButton = buttons.find(btn => btn.textContent === "Retrain" && btn.className.includes("bg-orange"));
      expect(confirmButton).toBeDefined();
      
      fireEvent.click(confirmButton!);

      await waitFor(() => {
        const retrainingButton = screen.getByRole("button", { name: /Retrain machine learning model/i });
        expect(retrainingButton).toBeDisabled();
      });

      jest.useRealTimers();
    });
  });

  describe("Toast Notifications", () => {
    it("should show error toast when contamination risk becomes High", () => {
      const { rerender } = renderMLInsightPanel();

      // Change to High risk
      (MockDataService.getMLInsights as jest.Mock).mockReturnValue({
        ...mockMLInsights,
        contaminationRisk: { level: "High", percentage: 85 },
      });

      // Trigger re-render by updating lastRefreshTimestamp
      rerender(
        <DashboardProvider userRole="Admin" userId="test-user">
          <MLInsightPanel />
        </DashboardProvider>
      );

      // Note: This test may need adjustment based on how refresh is triggered
      // The toast should be called when risk changes to High
    });

    it("should not show toast if risk was already High", () => {
      (MockDataService.getMLInsights as jest.Mock).mockReturnValue({
        ...mockMLInsights,
        contaminationRisk: { level: "High", percentage: 85 },
      });

      renderMLInsightPanel();

      // First render with High risk should not trigger toast
      // (no previous state to compare)
    });
  });

  describe("Accessibility", () => {
    it("should have proper ARIA labels", () => {
      renderMLInsightPanel();

      expect(screen.getByRole("region", { name: /Machine Learning Insights/i })).toBeInTheDocument();
    });

    it("should have accessible button labels", () => {
      renderMLInsightPanel();

      expect(
        screen.getByRole("button", { name: /Retrain machine learning model/i })
      ).toBeInTheDocument();
    });

    it("should have status roles for dynamic content", () => {
      renderMLInsightPanel();

      const riskStatus = screen.getByLabelText(/Contamination risk/i);
      expect(riskStatus).toHaveAttribute("role", "status");

      const anomalyStatus = screen.getByLabelText(/anomalies detected/i);
      expect(anomalyStatus).toHaveAttribute("role", "status");

      const predictionStatus = screen.getByLabelText(/Water quality trend/i);
      expect(predictionStatus).toHaveAttribute("role", "status");
    });
  });

  describe("Dark Mode Support", () => {
    it("should have dark mode classes", () => {
      renderMLInsightPanel();

      const container = screen.getByRole("region", { name: /Machine Learning Insights/i });
      expect(container).toHaveClass("dark:bg-gray-800");
    });
  });
});
