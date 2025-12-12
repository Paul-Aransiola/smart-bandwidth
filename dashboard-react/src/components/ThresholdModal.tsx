import React, { useState, useEffect } from "react";
import { thresholdService } from "../utils/thresholdService";
import type { Device, ThresholdStatus } from "../types/device";
import "./ThresholdModal.css";

interface ThresholdModalProps {
  device: Device;
  onClose: () => void;
  onSuccess: () => void;
}

export const ThresholdModal: React.FC<ThresholdModalProps> = ({
  device,
  onClose,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<ThresholdStatus | null>(null);
  const [error, setError] = useState("");

  // Form state
  const [thresholdMbps, setThresholdMbps] = useState<number>(
    device.bandwidth_threshold_mbps || 50
  );
  const [autoDeactivate, setAutoDeactivate] = useState<boolean>(
    device.auto_deactivate_on_threshold || false
  );
  const [timeWindow, setTimeWindow] = useState<number>(
    device.threshold_time_window_minutes || 5
  );

  useEffect(() => {
    loadThresholdStatus();
  }, [device.id]);

  const loadThresholdStatus = async () => {
    try {
      const data = await thresholdService.getDeviceThresholdStatus(device.id);
      setStatus(data);
    } catch (err: any) {
      console.error("Failed to load threshold status:", err);
    }
  };

  const handleSetThreshold = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await thresholdService.setDeviceThreshold(device.id, {
        threshold_mbps: thresholdMbps,
        auto_deactivate: autoDeactivate,
        time_window_minutes: timeWindow,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to set threshold");
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveThreshold = async () => {
    if (!confirm("Remove bandwidth threshold for this device?")) return;

    setLoading(true);
    setError("");

    try {
      await thresholdService.removeDeviceThreshold(device.id);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to remove threshold");
    } finally {
      setLoading(false);
    }
  };

  const handleCheckNow = async () => {
    setLoading(true);
    setError("");

    try {
      await thresholdService.checkDeviceThreshold(device.id);
      await loadThresholdStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to check threshold");
    } finally {
      setLoading(false);
    }
  };

  const handleReactivate = async () => {
    if (!confirm("Reactivate this device and reset breach count?")) return;

    setLoading(true);
    setError("");

    try {
      await thresholdService.reactivateDevice(device.id, true);
      onSuccess();
      await loadThresholdStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to reactivate device");
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    const mbps = (bytes * 8) / 1_000_000;
    return mbps.toFixed(2);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content threshold-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3>Bandwidth Threshold - {device.hostname}</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          {error && <div className="alert alert-error">{error}</div>}

          {/* Current Status */}
          {status && (
            <div className="threshold-status">
              <h4>Current Status</h4>
              <div className="status-grid">
                <div className="status-item">
                  <span className="label">Current Usage:</span>
                  <span
                    className={`value ${
                      status.threshold_breached ? "text-danger" : ""
                    }`}
                  >
                    {status.current_usage_mbps?.toFixed(2) || "0.00"} Mbps
                  </span>
                </div>
                <div className="status-item">
                  <span className="label">Threshold:</span>
                  <span className="value">
                    {status.threshold_mbps
                      ? `${status.threshold_mbps} Mbps`
                      : "Not set"}
                  </span>
                </div>
                <div className="status-item">
                  <span className="label">Status:</span>
                  <span
                    className={`badge ${
                      status.threshold_breached
                        ? "badge-danger"
                        : "badge-success"
                    }`}
                  >
                    {status.threshold_breached ? "BREACHED" : "OK"}
                  </span>
                </div>
                <div className="status-item">
                  <span className="label">Breach Count:</span>
                  <span className="value">{status.breach_count || 0}</span>
                </div>
                {status.last_breach && (
                  <div className="status-item">
                    <span className="label">Last Breach:</span>
                    <span className="value">
                      {new Date(status.last_breach).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
              <div className="status-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={handleCheckNow}
                  disabled={loading}
                >
                  Check Now
                </button>
                {device.status === "deactivated" && (
                  <button
                    className="btn btn-warning btn-sm"
                    onClick={handleReactivate}
                    disabled={loading}
                  >
                    Reactivate Device
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Threshold Configuration Form */}
          <form onSubmit={handleSetThreshold} className="threshold-form">
            <h4>Configure Threshold</h4>

            <div className="form-group">
              <label htmlFor="threshold">
                Bandwidth Threshold (Mbps)
                <span className="help-text">
                  Maximum average bandwidth over time window
                </span>
              </label>
              <input
                id="threshold"
                type="number"
                min="0.1"
                step="0.1"
                value={thresholdMbps}
                onChange={(e) => setThresholdMbps(parseFloat(e.target.value))}
                required
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="timeWindow">
                Time Window (minutes)
                <span className="help-text">
                  Period to calculate average bandwidth (1-1440)
                </span>
              </label>
              <input
                id="timeWindow"
                type="number"
                min="1"
                max="1440"
                value={timeWindow}
                onChange={(e) => setTimeWindow(parseInt(e.target.value))}
                required
                className="form-control"
              />
            </div>

            <div className="form-group checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={autoDeactivate}
                  onChange={(e) => setAutoDeactivate(e.target.checked)}
                />
                <span>Auto-deactivate when threshold exceeded</span>
              </label>
              <p className="help-text">
                Automatically block device at network level when threshold is
                breached
              </p>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading}
              >
                {loading ? "Saving..." : "Save Threshold"}
              </button>

              {device.bandwidth_threshold_mbps && (
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={handleRemoveThreshold}
                  disabled={loading}
                >
                  Remove Threshold
                </button>
              )}

              <button
                type="button"
                className="btn btn-secondary"
                onClick={onClose}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
