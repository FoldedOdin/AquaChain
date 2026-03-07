/**
 * ML Insight Panel Component
 * 
 * Displays machine learning predictions and insights for water quality monitoring.
 * Shows contamination risk, anomaly detection, 24-hour predictions, and model information.
 * 
 * Features:
 * - Contamination risk with color-coded levels (Low/Medium/High)
 * - Anomaly detection count for last 24 hours
 * - 24-hour WQI prediction trend (Improving/Stable/Declining)
 * - Model version, accuracy, and last training timestamp
 * - Retrain model button with confirmation modal
 * - Auto-refresh every 5 minutes
 * - Toast notifications for high contamination risk
 * 
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11
 * 
 * @module MLInsightPanel
 */

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  RefreshCw,
} from "lucide-react";
import { format } from "date-fns";
import { toast } from "react-toastify";
import { MockDataBadge } from "../common/MockDataBadge";
import { LoadingSkeleton } from "../common/LoadingSkeleton";
import ConfirmationModal from "./modals/ConfirmationModal";
import { useDashboard } from "../../contexts/DashboardContext";
import { MockDataService } from "../../services/mockDataService";
import { MLInsightData } from "../../types/dashboard";

/**
 * MLInsightPanel Component
 * 
 * Displays ML predictions including contamination risk, anomaly detection,
 * 24-hour predictions, and model information with retrain capability.
 */
export const MLInsightPanel: React.FC = () => {
  const { lastRefreshTimestamp, addNotification } = useDashboard();
  const [insights, setInsights] = useState<MLInsightData | null>(null);
  const [prevInsights, setPrevInsights] = useState<MLInsightData | null>(null);
  const [showRetrainModal, setShowRetrainModal] = useState(false);
  const [isRetraining, setIsRetraining] = useState(false);

  /**
   * Fetch ML insights on component mount and refresh
   * Updates every 5 minutes via DashboardContext auto-refresh
   */
  useEffect(() => {
    const newInsights = MockDataService.getMLInsights();

    // Only process if we have valid insights
    if (newInsights) {
      // Notify on high contamination risk (only if changed to High)
      if (
        newInsights.contaminationRisk.level === "High" &&
        prevInsights?.contaminationRisk.level !== "High"
      ) {
        toast.error(
          `High contamination risk detected: ${newInsights.contaminationRisk.percentage}%`,
          {
            autoClose: 10000, // 10 seconds for critical alerts
          }
        );
        addNotification({
          type: "error",
          message: `High contamination risk: ${newInsights.contaminationRisk.percentage}%`,
        });
      }

      setPrevInsights(insights);
      setInsights(newInsights);
    }
  }, [lastRefreshTimestamp]);

  /**
   * Handle model retraining
   * Simulates model retraining process with progress indication
   */
  const handleRetrain = () => {
    setIsRetraining(true);
    toast.info("Model retraining initiated...", {
      autoClose: 3000,
    });

    // Simulate retraining delay (3 seconds)
    setTimeout(() => {
      setIsRetraining(false);
      toast.success("Model retraining completed successfully", {
        autoClose: 5000,
      });
      addNotification({
        type: "success",
        message: "ML model retraining completed",
      });

      // Refresh insights after retraining
      const updatedInsights = MockDataService.getMLInsights();
      setInsights(updatedInsights);
    }, 3000);

    setShowRetrainModal(false);
  };

  if (!insights) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <LoadingSkeleton count={1} />
      </div>
    );
  }

  /**
   * Color classes for contamination risk levels
   */
  const riskColors = {
    Low: "text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800",
    Medium:
      "text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800",
    High: "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800",
  };

  /**
   * Icons for prediction trends
   */
  const predictionIcons = {
    Improving: <TrendingUp className="text-green-600 dark:text-green-400" size={20} />,
    Stable: <Minus className="text-blue-600 dark:text-blue-400" size={20} />,
    Declining: <TrendingDown className="text-red-600 dark:text-red-400" size={20} />,
  };

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
      role="region"
      aria-label="Machine Learning Insights"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          ML Insights
        </h2>
        <MockDataBadge />
      </div>

      <div className="space-y-4">
        {/* Contamination Risk */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Contamination Risk
          </h3>
          <div
            className={`p-4 rounded-lg border ${
              riskColors[insights.contaminationRisk.level]
            }`}
            role="status"
            aria-label={`Contamination risk: ${insights.contaminationRisk.level} at ${insights.contaminationRisk.percentage} percent`}
          >
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">
                {insights.contaminationRisk.percentage}%
              </span>
              <span className="text-sm font-medium">
                {insights.contaminationRisk.level}
              </span>
            </div>
          </div>
        </div>

        {/* Anomaly Detection */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Anomalies Detected (24h)
          </h3>
          <div
            className="flex items-center gap-2"
            role="status"
            aria-label={`${insights.anomalyDetection.count} anomalies detected in last 24 hours`}
          >
            <AlertTriangle
              className="text-orange-600 dark:text-orange-400"
              size={20}
              aria-hidden="true"
            />
            <span className="text-xl font-semibold text-gray-900 dark:text-white">
              {insights.anomalyDetection.count}
            </span>
          </div>
        </div>

        {/* 24-Hour Prediction */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            24-Hour Prediction
          </h3>
          <div
            className="flex items-center gap-2"
            role="status"
            aria-label={`Water quality trend: ${insights.prediction.trend}`}
          >
            {predictionIcons[insights.prediction.trend]}
            <span className="text-lg font-medium text-gray-900 dark:text-white">
              {insights.prediction.trend}
            </span>
          </div>
        </div>

        {/* Model Info */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">
                Model Version:
              </span>
              <p className="font-medium text-gray-900 dark:text-white">
                {insights.modelInfo.version}
              </p>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Accuracy:</span>
              <p className="font-medium text-gray-900 dark:text-white">
                {insights.modelInfo.accuracy}%
              </p>
            </div>
            <div className="col-span-2">
              <span className="text-gray-600 dark:text-gray-400">
                Last Training:
              </span>
              <p className="font-medium text-gray-900 dark:text-white">
                {format(insights.modelInfo.lastTraining, "PPpp")}
              </p>
            </div>
          </div>
        </div>

        {/* Retrain Button */}
        <button
          onClick={() => setShowRetrainModal(true)}
          disabled={isRetraining}
          className={`
            w-full px-4 py-2 rounded-lg
            flex items-center justify-center gap-2
            transition-colors
            ${
              isRetraining
                ? "bg-purple-400 cursor-not-allowed"
                : "bg-purple-600 hover:bg-purple-700"
            }
            text-white
          `}
          aria-label="Retrain machine learning model"
        >
          <RefreshCw
            size={16}
            className={isRetraining ? "animate-spin" : ""}
            aria-hidden="true"
          />
          {isRetraining ? "Retraining..." : "Retrain Model"}
        </button>
      </div>

      {/* Retrain Confirmation Modal */}
      {showRetrainModal && (
        <ConfirmationModal
          title="Retrain ML Model"
          message="This will initiate model retraining with the latest data. The process may take several minutes. Continue?"
          confirmLabel="Retrain"
          cancelLabel="Cancel"
          confirmVariant="warning"
          onConfirm={handleRetrain}
          onCancel={() => setShowRetrainModal(false)}
        />
      )}
    </div>
  );
};

export default MLInsightPanel;
