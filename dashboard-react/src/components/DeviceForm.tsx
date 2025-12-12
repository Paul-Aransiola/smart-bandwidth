import React, { useState } from "react";
import axios from "../lib/axios";

export const DeviceForm: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [form, setForm] = useState({
    ip_address: "",
    mac_address: "",
    device_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await axios.post("/devices", form);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create device");
    }
    setLoading(false);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h3>Add Device</h3>
        <form onSubmit={handleSubmit} className="device-form">
          <input
            name="ip_address"
            placeholder="IP Address"
            value={form.ip_address}
            onChange={handleChange}
            required
          />
          <input
            name="mac_address"
            placeholder="MAC Address"
            value={form.mac_address}
            onChange={handleChange}
            required
          />
          <input
            name="device_name"
            placeholder="Device Name"
            value={form.device_name}
            onChange={handleChange}
            required
          />
          <button type="submit" disabled={loading}>
            Add
          </button>
          <button type="button" onClick={onClose}>
            Cancel
          </button>
        </form>
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
};
