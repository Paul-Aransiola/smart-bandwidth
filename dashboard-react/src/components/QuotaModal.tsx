import React, { useState, useEffect } from "react";
import { DollarSign, X } from "lucide-react";
import axios from "../lib/axios";
import type { Device } from "../types/device";

interface BandwidthQuota {
  id?: number;
  device_id?: number;
  quota_name: string;
  quota_type: string;
  limit_bytes: number;
  used_bytes?: number;
  reset_day?: number;
  is_active: boolean;
  warning_threshold_percent?: number;
}

interface QuotaModalProps {
  quota?: BandwidthQuota;
  onClose: () => void;
  onSuccess: () => void;
}

export const QuotaModal: React.FC<QuotaModalProps> = ({
  quota,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<BandwidthQuota>({
    quota_name: quota?.quota_name || "",
    quota_type: quota?.quota_type || "monthly",
    limit_bytes: quota?.limit_bytes || 0,
    reset_day: quota?.reset_day || 1,
    is_active: quota?.is_active ?? true,
    warning_threshold_percent: quota?.warning_threshold_percent || 80,
    device_id: quota?.device_id,
  });

  const [limitMB, setLimitMB] = useState(
    quota?.limit_bytes ? (quota.limit_bytes / (1024 * 1024)).toFixed(0) : "1000"
  );
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

    const limitBytes = parseFloat(limitMB) * 1024 * 1024;
    if (isNaN(limitBytes) || limitBytes <= 0) {
      setError("Please enter a valid limit");
      setLoading(false);
      return;
    }

    try {
      const payload = {
        ...formData,
        limit_bytes: limitBytes,
      };

      if (quota?.id) {
        await axios.put(
          `/api/v1/advanced-controls/quotas/${quota.id}`,
          payload
        );
      } else {
        await axios.post("/api/v1/advanced-controls/quotas", payload);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save quota");
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
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <DollarSign className="text-blue-600" size={20} />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">
              {quota ? "Edit Bandwidth Quota" : "Create Bandwidth Quota"}
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

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label
                htmlFor="quota_name"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Quota Name *
              </label>
              <input
                id="quota_name"
                type="text"
                value={formData.quota_name}
                onChange={(e) =>
                  setFormData({ ...formData, quota_name: e.target.value })
                }
                placeholder="e.g., Monthly Data Cap"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label
                htmlFor="quota_type"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Quota Type *
              </label>
              <select
                id="quota_type"
                value={formData.quota_type}
                onChange={(e) =>
                  setFormData({ ...formData, quota_type: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="limit_mb"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Limit (MB) *
              </label>
              <input
                id="limit_mb"
                type="number"
                value={limitMB}
                onChange={(e) => setLimitMB(e.target.value)}
                min="1"
                placeholder="1000"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                htmlFor="reset_day"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Reset Day
              </label>
              <input
                id="reset_day"
                type="number"
                value={formData.reset_day || 1}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    reset_day: parseInt(e.target.value),
                  })
                }
                min="1"
                max="31"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Day of month to reset quota (1-31)
              </p>
            </div>

            <div>
              <label
                htmlFor="warning_threshold"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Warning Threshold (%)
              </label>
              <input
                id="warning_threshold"
                type="number"
                value={formData.warning_threshold_percent || 80}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    warning_threshold_percent: parseInt(e.target.value),
                  })
                }
                min="1"
                max="100"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-slate-500 mt-1">
                Alert when usage exceeds this %
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              id="is_active"
              type="checkbox"
              checked={formData.is_active}
              onChange={(e) =>
                setFormData({ ...formData, is_active: e.target.checked })
              }
              className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
            />
            <label
              htmlFor="is_active"
              className="text-sm font-medium text-slate-700"
            >
              Active
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
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Saving...
                </>
              ) : (
                <>
                  <DollarSign size={16} />
                  {quota ? "Update Quota" : "Create Quota"}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
