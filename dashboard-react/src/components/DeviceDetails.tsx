import React from "react";
import "./ThresholdModal.css";

export const DeviceDetails: React.FC<{
  device: any;
  onClose: () => void;
}> = ({ device, onClose }) => (
  <div className="modal-overlay" onClick={onClose}>
    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
      <div className="modal-header">
        <h3>Device Details</h3>
        <button className="close-btn" onClick={onClose}>
          ×
        </button>
      </div>
      <div className="modal-body">
        <ul>
          <li>
            <strong>IP Address:</strong> {device.ip_address}
          </li>
          <li>
            <strong>MAC Address:</strong> {device.mac_address}
          </li>
          <li>
            <strong>Name:</strong> {device.device_name}
          </li>
          <li>
            <strong>Status:</strong> {device.status}
          </li>
          <li>
            <strong>Sent:</strong> {device.total_bytes_sent}
          </li>
          <li>
            <strong>Received:</strong> {device.total_bytes_received}
          </li>
          {/* Add quotas, QoS, throttle schedules, alerts, history here */}
        </ul>
      </div>
    </div>
  </div>
);
