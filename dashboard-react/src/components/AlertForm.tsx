import React, { useState } from "react";
import axios from "../lib/axios";

export const AlertForm: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [form, setForm] = useState({
    rule_name: "",
    type: "",
    enabled: true,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await axios.post("/alerts", form);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create alert rule");
    }
    setLoading(false);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h3>Add Alert Rule</h3>
        <form onSubmit={handleSubmit} className="alert-form">
          <input
            name="rule_name"
            placeholder="Rule Name"
            value={form.rule_name}
            onChange={handleChange}
            required
          />
          <select
            name="type"
            value={form.type}
            onChange={handleChange}
            required
          >
            <option value="">Select Type</option>
            <option value="threshold">Threshold</option>
            <option value="event">Event</option>
            {/* Add more types as needed */}
          </select>
          <label>
            <input
              type="checkbox"
              name="enabled"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            Enabled
          </label>
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
