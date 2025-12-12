import React, { useState, useEffect } from "react";
import { X, AlertTriangle } from "lucide-react";
import axios from "../lib/axios";

interface Device {
  id: number;
  ip_address: string;
  device_name?: string;
  hostname?: string;
}

interface AlertRule {
  id: number;
  name: string;
  description?: string;
  metric: string;
  condition: string;
  threshold_value: number;
  time_window_minutes: number;
  device_id?: number;
  severity: "info" | "warning" | "error" | "critical";
  notification_channels: string;
  cooldown_minutes: number;
  is_enabled: boolean;
}

interface AlertRuleModalProps {
  rule: AlertRule | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const AlertRuleModal: React.FC<AlertRuleModalProps> = ({
  rule,
  onClose,
  onSuccess,
}) => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    name: rule?.name || "",
    description: rule?.description || "",
    metric: rule?.metric || "bandwidth_usage",
    condition: rule?.condition || "greater_than",
    threshold_value: rule?.threshold_value || 100,
    time_window_minutes: rule?.time_window_minutes || 5,
    device_id: rule?.device_id || null,
    severity: rule?.severity || "warning",
    notification_channels: rule?.notification_channels || "websocket",
    cooldown_minutes: rule?.cooldown_minutes || 15,
    is_enabled: rule?.is_enabled !== undefined ? rule.is_enabled : true,
  });

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const res = await axios.get("/api/v1/devices/");
      setDevices(res.data.data || []);
    } catch (err) {
      console.error("Failed to fetch devices:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload: any = {
        name: formData.name,
        description: formData.description || undefined,
        metric: formData.metric,
        condition: formData.condition,
        threshold_value: formData.threshold_value,
        time_window_minutes: formData.time_window_minutes,
        severity: formData.severity,
        notification_channels: formData.notification_channels,
        cooldown_minutes: formData.cooldown_minutes,
        is_enabled: formData.is_enabled,
      };

      // Only include device_id if it's not null
      if (formData.device_id) {
        payload.device_id = formData.device_id;
      }

      if (rule) {
        await axios.put(`/api/v1/alerts/rules/${rule.id}`, payload);
      } else {
        await axios.post("/api/v1/alerts/rules", payload);
      }

      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save alert rule");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? (e.target as HTMLInputElement).checked
          : type === "number"
          ? parseFloat(value)
          : value === ""
          ? null
          : value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 sticky top-0 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
              <AlertTriangle className="text-orange-600" size={20} />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">
              {rule ? "Edit Alert Rule" : "Create Alert Rule"}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Rule Name *
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="High bandwidth usage"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              />
            </div>

            <div className="col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Alert when bandwidth exceeds threshold..."
                rows={2}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Metric *
              </label>
              <select
                name="metric"
                value={formData.metric}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              >
                <option value="bandwidth_usage">Bandwidth Usage</option>
                <option value="bandwidth_sent">Bandwidth Sent</option>
                <option value="bandwidth_received">Bandwidth Received</option>
                <option value="packet_loss">Packet Loss</option>
                <option value="latency">Latency</option>
                <option value="connection_count">Connection Count</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Condition *
              </label>
              <select
                name="condition"
                value={formData.condition}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              >
                <option value="greater_than">Greater Than</option>
                <option value="less_than">Less Than</option>
                <option value="equals">Equals</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Threshold Value *
              </label>
              <input
                type="number"
                name="threshold_value"
                value={formData.threshold_value}
                onChange={handleChange}
                step="0.01"
                placeholder="100"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Time Window (minutes) *
              </label>
              <input
                type="number"
                name="time_window_minutes"
                value={formData.time_window_minutes}
                onChange={handleChange}
                min="1"
                max="1440"
                placeholder="5"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Device (Optional)
              </label>
              <select
                name="device_id"
                value={formData.device_id || ""}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              >
                <option value="">All Devices</option>
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.device_name || device.hostname || device.ip_address}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Severity *
              </label>
              <select
                name="severity"
                value={formData.severity}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              >
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Notification Channels *
              </label>
              <select
                name="notification_channels"
                value={formData.notification_channels}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              >
                <option value="websocket">WebSocket</option>
                <option value="email">Email</option>
                <option value="webhook">Webhook</option>
                <option value="email,websocket">Email + WebSocket</option>
                <option value="webhook,websocket">Webhook + WebSocket</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Cooldown (minutes) *
              </label>
              <input
                type="number"
                name="cooldown_minutes"
                value={formData.cooldown_minutes}
                onChange={handleChange}
                min="1"
                max="1440"
                placeholder="15"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                required
              />
            </div>

            <div className="col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  name="is_enabled"
                  checked={formData.is_enabled}
                  onChange={handleChange}
                  className="w-4 h-4 text-orange-600 border-slate-300 rounded focus:ring-orange-500"
                />
                <span className="text-sm font-medium text-slate-700">
                  Enable this rule
                </span>
              </label>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-slate-200">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Saving...
                </>
              ) : (
                <>{rule ? "Update Rule" : "Create Rule"}</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
