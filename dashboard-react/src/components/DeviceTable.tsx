import React from "react";
import type { Device } from "../types/device";

export const DeviceTable: React.FC<{
  devices: Device[];
  onSelect: (device: Device) => void;
  onSetThreshold?: (device: Device) => void;
  onBlock?: (device: Device) => void;
  onUnblock?: (device: Device) => void;
  onThrottle?: (device: Device) => void;
  onUnthrottle?: (device: Device) => void;
  onViewHistory?: (device: Device) => void;
  selectedDevices?: Set<number>;
  onToggleSelect?: (deviceId: number) => void;
  onToggleSelectAll?: () => void;
  bulkMode?: boolean;
}> = ({
  devices,
  onSelect,
  onSetThreshold,
  onBlock,
  onUnblock,
  onThrottle,
  onUnthrottle,
  onViewHistory,
  selectedDevices = new Set(),
  onToggleSelect,
  onToggleSelectAll,
  bulkMode = false,
}) => {
  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      active: "badge-success",
      throttled: "badge-warning",
      blocked: "badge-danger",
      deactivated: "badge-danger",
      inactive: "badge-secondary",
    };
    return statusColors[status] || "badge-secondary";
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <div className="device-table-wrapper">
      <table className="device-table">
        <thead>
          <tr>
            {bulkMode && onToggleSelectAll && (
              <th style={{ width: "50px" }}>
                <input
                  type="checkbox"
                  checked={
                    selectedDevices.size === devices.length &&
                    devices.length > 0
                  }
                  onChange={onToggleSelectAll}
                  title="Select all devices"
                />
              </th>
            )}
            <th>IP Address</th>
            <th>MAC Address</th>
            <th>Device Name</th>
            <th>Status</th>
            <th>Bandwidth</th>
            <th>Threshold</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.length === 0 ? (
            <tr>
              <td colSpan={bulkMode ? 8 : 7}>No devices found.</td>
            </tr>
          ) : (
            devices.map((device) => (
              <tr key={device.id}>
                {bulkMode && onToggleSelect && (
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedDevices.has(device.id)}
                      onChange={() => onToggleSelect(device.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </td>
                )}
                <td onClick={() => onSelect(device)} className="clickable-cell">
                  {device.ip_address}
                </td>
                <td>{device.mac_address}</td>
                <td>{device.hostname || device.device_name || "-"}</td>
                <td>
                  <span className={`badge ${getStatusBadge(device.status)}`}>
                    {device.status}
                  </span>
                </td>
                <td>
                  <div style={{ fontSize: "0.875rem" }}>
                    <div>↓ {formatBytes(device.total_bytes_received)}</div>
                    <div>↑ {formatBytes(device.total_bytes_sent)}</div>
                  </div>
                </td>
                <td>
                  {device.bandwidth_threshold_mbps ? (
                    <span className="threshold-badge">
                      {device.bandwidth_threshold_mbps} Mbps
                      {device.threshold_breach_count &&
                        device.threshold_breach_count > 0 && (
                          <span
                            className="breach-count"
                            title={`Breached ${device.threshold_breach_count} times`}
                          >
                            ⚠️ {device.threshold_breach_count}
                          </span>
                        )}
                    </span>
                  ) : (
                    <span className="text-muted">None</span>
                  )}
                </td>
                <td>
                  <div className="action-buttons">
                    {device.is_blocked
                      ? onUnblock && (
                          <button
                            className="btn btn-sm btn-success"
                            onClick={() => onUnblock(device)}
                            title="Unblock device"
                          >
                            Unblock
                          </button>
                        )
                      : onBlock && (
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => onBlock(device)}
                            title="Block device"
                          >
                            Block
                          </button>
                        )}

                    {!device.is_blocked &&
                      (device.is_throttled
                        ? onUnthrottle && (
                            <button
                              className="btn btn-sm btn-info"
                              onClick={() => onUnthrottle(device)}
                              title="Remove throttle"
                            >
                              Unthrottle
                            </button>
                          )
                        : onThrottle && (
                            <button
                              className="btn btn-sm btn-warning"
                              onClick={() => onThrottle(device)}
                              title="Throttle bandwidth"
                            >
                              Throttle
                            </button>
                          ))}

                    {onSetThreshold && (
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => onSetThreshold(device)}
                        title="Set bandwidth threshold"
                      >
                        Threshold
                      </button>
                    )}
                    {onViewHistory && (
                      <button
                        className="btn btn-sm btn-info"
                        onClick={() => onViewHistory(device)}
                        title="View control history"
                      >
                        History
                      </button>
                    )}
                    <button
                      className="btn btn-sm btn-secondary"
                      onClick={() => onSelect(device)}
                    >
                      Details
                    </button>
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
