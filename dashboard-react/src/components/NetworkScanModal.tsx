import React, { useState } from "react";
import axios from "../lib/axios";
import "./ThresholdModal.css"; // Reuse same styling

interface DiscoveredDevice {
  ip_address: string;
  mac_address?: string;
  hostname?: string;
  discovery_method?: string;
  last_seen?: string;
}

export const NetworkScanModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [scanning, setScanning] = useState(false);
  const [usePing, setUsePing] = useState(false);
  const [autoAdd, setAutoAdd] = useState(true);
  const [discoveredDevices, setDiscoveredDevices] = useState<
    DiscoveredDevice[]
  >([]);
  const [scanStatus, setScanStatus] = useState<string>("");
  const [error, setError] = useState("");

  const handleScan = async () => {
    setScanning(true);
    setError("");
    setDiscoveredDevices([]);
    setScanStatus("Scanning network...");

    try {
      const response = await axios.post(
        `/api/v1/devices/scan/network?use_ping=${usePing}&auto_add=${autoAdd}`
      );

      if (response.data.success) {
        const data = response.data.data;
        setDiscoveredDevices(data.devices || []);
        setScanStatus(
          data.full_scan_running
            ? `Found ${data.devices_found} devices. Full scan running in background...`
            : `Scan complete! Found ${data.devices_found} devices.`
        );

        if (autoAdd && data.devices_found > 0) {
          // Refresh parent device list after auto-add
          setTimeout(() => {
            onSuccess();
          }, 1000);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Network scan failed");
      setScanStatus("");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content large-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h3>Network Device Scanner</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="scan-options">
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={usePing}
                  onChange={(e) => setUsePing(e.target.checked)}
                  disabled={scanning}
                />
                <span>Use ping sweep (slower but more thorough)</span>
              </label>
              <small className="help-text">
                Ping sweep actively probes all IPs. Without it, only ARP cache
                and active connections are scanned.
              </small>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={autoAdd}
                  onChange={(e) => setAutoAdd(e.target.checked)}
                  disabled={scanning}
                />
                <span>Automatically add discovered devices</span>
              </label>
              <small className="help-text">
                New devices will be added to the database automatically.
              </small>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}
          {scanStatus && <div className="info-message">{scanStatus}</div>}

          {discoveredDevices.length > 0 && (
            <div className="discovered-devices">
              <h4>Discovered Devices ({discoveredDevices.length})</h4>
              <div className="device-list">
                <table className="scan-results-table">
                  <thead>
                    <tr>
                      <th>IP Address</th>
                      <th>MAC Address</th>
                      <th>Hostname</th>
                      <th>Method</th>
                    </tr>
                  </thead>
                  <tbody>
                    {discoveredDevices.map((device, idx) => (
                      <tr key={idx}>
                        <td>{device.ip_address}</td>
                        <td>{device.mac_address || "-"}</td>
                        <td>{device.hostname || "-"}</td>
                        <td>
                          <span className="badge badge-info">
                            {device.discovery_method || "unknown"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          <div className="form-actions">
            <button
              className="btn btn-primary"
              onClick={handleScan}
              disabled={scanning}
            >
              {scanning ? "Scanning..." : "Start Scan"}
            </button>
            <button
              className="btn btn-secondary"
              onClick={onClose}
              disabled={scanning}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
