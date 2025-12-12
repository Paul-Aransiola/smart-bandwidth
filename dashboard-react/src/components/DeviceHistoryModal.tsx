import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import "./ThresholdModal.css";

interface ControlHistory {
  id: number;
  ip_address: string;
  action: "block" | "unblock" | "throttle" | "unthrottle";
  reason?: string;
  throttle_limit_mbps?: number;
  timestamp: string;
  performed_by?: string;
}

interface DeviceHistoryModalProps {
  ipAddress: string;
  deviceName?: string;
  onClose: () => void;
}

const DeviceHistoryModal: React.FC<DeviceHistoryModalProps> = ({
  ipAddress,
  deviceName,
  onClose,
}) => {
  const [history, setHistory] = useState<ControlHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  console.log("[DeviceHistoryModal] Rendering with:", {
    ipAddress,
    deviceName,
  });

  useEffect(() => {
    console.log("[DeviceHistoryModal] Fetching history for:", ipAddress);
    fetchHistory();
  }, [ipAddress]);

  const fetchHistory = async () => {
    try {
      console.log("[DeviceHistoryModal] START fetch for:", ipAddress);
      setLoading(true);
      setError("");
      const response = await axios.get(`/api/v1/control/history/${ipAddress}`);
      console.log("[DeviceHistoryModal] Got response:", response.data);

      // API returns { success, message, data } - we need the data field
      const historyData = response.data.data || response.data;
      console.log("[DeviceHistoryModal] History data:", historyData);
      setHistory(Array.isArray(historyData) ? historyData : []);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || "Failed to fetch history";
      console.error("[DeviceHistoryModal] FETCH ERROR:", err);
      console.error("[DeviceHistoryModal] Error message:", errorMsg);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getActionBadge = (action: string) => {
    const badges: Record<string, { class: string; label: string }> = {
      block: { class: "badge-danger", label: "🚫 Blocked" },
      unblock: { class: "badge-success", label: "✅ Unblocked" },
      throttle: { class: "badge-warning", label: "⚠️ Throttled" },
      unthrottle: { class: "badge-info", label: "🔓 Unthrottled" },
    };
    const badge = badges[action] || { class: "badge-secondary", label: action };
    return <span className={`badge ${badge.class}`}>{badge.label}</span>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content large-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3>Control History</h3>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="device-info">
            <strong>Device:</strong> {deviceName || ipAddress} ({ipAddress})
          </div>

          {loading ? (
            <div className="loading">Loading history...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : history.length === 0 ? (
            <div className="info-message">
              No control actions have been performed on this device.
            </div>
          ) : (
            <div className="history-timeline">
              {history.map((entry) => (
                <div key={entry.id} className="history-entry">
                  <div className="history-header">
                    <div className="history-action">
                      {getActionBadge(entry.action)}
                    </div>
                    <div className="history-timestamp">
                      {formatTimestamp(entry.timestamp)}
                    </div>
                  </div>

                  {entry.reason && (
                    <div className="history-detail">
                      <strong>Reason:</strong> {entry.reason}
                    </div>
                  )}

                  {entry.throttle_limit_mbps && (
                    <div className="history-detail">
                      <strong>Throttle Limit:</strong>{" "}
                      {entry.throttle_limit_mbps} Mbps
                    </div>
                  )}

                  {entry.performed_by && (
                    <div className="history-detail">
                      <strong>Performed By:</strong> {entry.performed_by}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-actions">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeviceHistoryModal;
