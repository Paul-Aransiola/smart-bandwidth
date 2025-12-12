import React, { useState, useEffect } from "react";
import { Gauge, X } from "lucide-react";
import axios from "../lib/axios";
import type { Device } from "../types/device";

interface QoSPolicy {
  id?: number;
  policy_name: string;
  device_id?: number;
  priority: "critical" | "high" | "medium" | "low";
  min_bandwidth_mbps?: number;
  max_bandwidth_mbps?: number;
  guaranteed_bandwidth_mbps?: number;
  is_enabled: boolean;
}

interface QoSModalProps {
  policy?: QoSPolicy;
  onClose: () => void;
  onSuccess: () => void;
}

export const QoSModal: React.FC<QoSModalProps> = ({
  policy,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<QoSPolicy>({
    policy_name: policy?.policy_name || "",
    device_id: policy?.device_id,
    priority: policy?.priority || "medium",
    min_bandwidth_mbps: policy?.min_bandwidth_mbps,
    max_bandwidth_mbps: policy?.max_bandwidth_mbps,
    guaranteed_bandwidth_mbps: policy?.guaranteed_bandwidth_mbps,
    is_enabled: policy?.is_enabled ?? true,
  });

  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await axios.get("/api/v1/devices");
      setDevices(response.data.data || []);
    } catch (err) {
      console.error("Failed to fetch devices:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      if (policy?.id) {
        await axios.put(
          `/api/v1/advanced-controls/qos-policies/${policy.id}`,
          formData
        );
      } else {
        await axios.post("/api/v1/advanced-controls/qos-policies", formData);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save QoS policy");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 sticky top-0 bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Gauge className="text-purple-600" size={20} />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">
              {policy ? "Edit QoS Policy" : "Create QoS Policy"}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}

          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>QoS (Quality of Service)</strong> policies control traffic
              priority and bandwidth allocation. Higher priority levels get
              preferential treatment during network congestion.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label
                htmlFor="policy_name"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Policy Name *
              </label>
              <input
                id="policy_name"
                type="text"
                value={formData.policy_name}
                onChange={(e) =>
                  setFormData({ ...formData, policy_name: e.target.value })
                }
                placeholder="e.g., High Priority Traffic"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label
                htmlFor="device_id"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Device (Optional)
              </label>
              <select
                id="device_id"
                value={formData.device_id || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    device_id: e.target.value
                      ? parseInt(e.target.value)
                      : undefined,
                  })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="">Global (All Devices)</option>
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.device_name || device.hostname || device.ip_address}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="priority"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Priority Level *
              </label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    priority: e.target.value as
                      | "critical"
                      | "high"
                      | "medium"
                      | "low",
                  })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value="critical">Critical (Highest)</option>
                <option value="high">High</option>
                <option value="medium">Medium (Normal)</option>
                <option value="low">Low (Lowest)</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="guaranteed_bandwidth"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Guaranteed Bandwidth (Mbps)
              </label>
              <input
                id="guaranteed_bandwidth"
                type="number"
                value={formData.guaranteed_bandwidth_mbps || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    guaranteed_bandwidth_mbps: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  })
                }
                min="0.1"
                step="0.1"
                placeholder="Optional"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Guaranteed bandwidth allocation
              </p>
            </div>

            <div>
              <label
                htmlFor="min_bandwidth"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Min Bandwidth (Mbps)
              </label>
              <input
                id="min_bandwidth"
                type="number"
                value={formData.min_bandwidth_mbps || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    min_bandwidth_mbps: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  })
                }
                min="0.1"
                step="0.1"
                placeholder="Optional"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Minimum bandwidth guarantee
              </p>
            </div>

            <div>
              <label
                htmlFor="max_bandwidth"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Max Bandwidth (Mbps)
              </label>
              <input
                id="max_bandwidth"
                type="number"
                value={formData.max_bandwidth_mbps || ""}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_bandwidth_mbps: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  })
                }
                min="0.1"
                step="0.1"
                placeholder="Optional"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Maximum bandwidth limit
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              id="is_enabled"
              type="checkbox"
              checked={formData.is_enabled}
              onChange={(e) =>
                setFormData({ ...formData, is_enabled: e.target.checked })
              }
              className="w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
            />
            <label
              htmlFor="is_enabled"
              className="text-sm font-medium text-slate-700"
            >
              Enabled
            </label>
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
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Gauge size={16} />
                  {policy ? "Update Policy" : "Create Policy"}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
