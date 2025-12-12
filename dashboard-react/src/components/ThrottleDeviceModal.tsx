import React, { useState } from "react";
import { Zap, X } from "lucide-react";
import type { Device } from "../types/device";

interface ThrottleDeviceModalProps {
  device: Device;
  onClose: () => void;
  onConfirm: (limitMbps: number) => Promise<void>;
}

export const ThrottleDeviceModal: React.FC<ThrottleDeviceModalProps> = ({
  device,
  onClose,
  onConfirm,
}) => {
  const [limitMbps, setLimitMbps] = useState(
    device.throttle_limit_mbps?.toString() || "10"
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const limit = parseFloat(limitMbps);
    if (isNaN(limit) || limit <= 0) {
      setError("Please enter a valid bandwidth limit greater than 0");
      setLoading(false);
      return;
    }

    try {
      await onConfirm(limit);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to throttle device");
    } finally {
      setLoading(false);
    }
  };

  // Preset bandwidth limits
  const presets = [
    { label: "1 Mbps", value: "1" },
    { label: "5 Mbps", value: "5" },
    { label: "10 Mbps", value: "10" },
    { label: "25 Mbps", value: "25" },
    { label: "50 Mbps", value: "50" },
    { label: "100 Mbps", value: "100" },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
              <Zap className="text-yellow-600" size={20} />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Throttle Device
              </h2>
              <p className="text-sm text-slate-600">
                {device.device_name || device.hostname || device.ip_address}
              </p>
            </div>
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
              <strong>Info:</strong> Throttling will limit the bandwidth for
              this device. The device will still have network access but at a
              reduced speed.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              IP Address
            </label>
            <input
              type="text"
              value={device.ip_address}
              disabled
              className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-slate-50 text-slate-600"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Current Status
            </label>
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  device.status === "throttled"
                    ? "bg-yellow-100 text-yellow-800"
                    : device.status === "active"
                    ? "bg-green-100 text-green-800"
                    : "bg-slate-100 text-slate-800"
                }`}
              >
                {device.status}
              </span>
              {device.is_throttled && device.throttle_limit_mbps && (
                <span className="text-sm text-slate-600">
                  (Currently: {device.throttle_limit_mbps} Mbps)
                </span>
              )}
            </div>
          </div>

          <div>
            <label
              htmlFor="limitMbps"
              className="block text-sm font-medium text-slate-700 mb-2"
            >
              Bandwidth Limit (Mbps)
            </label>
            <input
              id="limitMbps"
              type="number"
              value={limitMbps}
              onChange={(e) => setLimitMbps(e.target.value)}
              min="0.1"
              step="0.1"
              placeholder="Enter bandwidth limit in Mbps"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              required
            />
          </div>

          {/* Preset buttons */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Quick Presets
            </label>
            <div className="grid grid-cols-3 gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => setLimitMbps(preset.value)}
                  className={`px-3 py-2 text-sm rounded-lg border transition-colors ${
                    limitMbps === preset.value
                      ? "border-yellow-500 bg-yellow-50 text-yellow-700"
                      : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
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
              className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Throttling...
                </>
              ) : (
                <>
                  <Zap size={16} />
                  Apply Throttle
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
