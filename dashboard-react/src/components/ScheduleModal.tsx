import React, { useState, useEffect } from "react";
import { Calendar, X } from "lucide-react";
import axios from "../lib/axios";
import type { Device } from "../types/device";

interface ThrottleSchedule {
  id?: number;
  schedule_name: string;
  description?: string;
  device_id?: number;
  throttle_limit_mbps: number;
  start_time: string;
  end_time: string;
  recurrence: string;
  days_of_week?: string;
  is_enabled: boolean;
}

interface ScheduleModalProps {
  schedule?: ThrottleSchedule;
  onClose: () => void;
  onSuccess: () => void;
}

export const ScheduleModal: React.FC<ScheduleModalProps> = ({
  schedule,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<ThrottleSchedule>({
    schedule_name: schedule?.schedule_name || "",
    description: schedule?.description || "",
    device_id: schedule?.device_id,
    throttle_limit_mbps: schedule?.throttle_limit_mbps || 10,
    start_time: schedule?.start_time || "22:00",
    end_time: schedule?.end_time || "06:00",
    recurrence: schedule?.recurrence || "daily",
    days_of_week: schedule?.days_of_week || "",
    is_enabled: schedule?.is_enabled ?? true,
  });

  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const daysOfWeek = [
    { value: "monday", label: "Mon" },
    { value: "tuesday", label: "Tue" },
    { value: "wednesday", label: "Wed" },
    { value: "thursday", label: "Thu" },
    { value: "friday", label: "Fri" },
    { value: "saturday", label: "Sat" },
    { value: "sunday", label: "Sun" },
  ];

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

  const toggleDay = (day: string) => {
    const currentDays = formData.days_of_week
      ? formData.days_of_week.split(",")
      : [];
    const index = currentDays.indexOf(day);

    if (index > -1) {
      currentDays.splice(index, 1);
    } else {
      currentDays.push(day);
    }

    setFormData({ ...formData, days_of_week: currentDays.join(",") });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (formData.recurrence === "weekly" && !formData.days_of_week) {
      setError("Please select at least one day for weekly recurrence");
      setLoading(false);
      return;
    }

    try {
      if (schedule?.id) {
        await axios.put(
          `/api/v1/advanced-controls/schedules/${schedule.id}`,
          formData
        );
      } else {
        await axios.post("/api/v1/advanced-controls/schedules", formData);
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save schedule");
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
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Calendar className="text-green-600" size={20} />
            </div>
            <h2 className="text-xl font-semibold text-slate-900">
              {schedule ? "Edit Throttle Schedule" : "Create Throttle Schedule"}
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
              <strong>Throttle Schedules</strong> automatically apply bandwidth
              limits during specific time periods. Perfect for managing
              bandwidth during peak hours or overnight.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label
                htmlFor="schedule_name"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Schedule Name *
              </label>
              <input
                id="schedule_name"
                type="text"
                value={formData.schedule_name}
                onChange={(e) =>
                  setFormData({ ...formData, schedule_name: e.target.value })
                }
                placeholder="e.g., Night Time Throttle"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            <div className="col-span-2">
              <label
                htmlFor="description"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Description
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Optional description"
                rows={2}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
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
                htmlFor="throttle_limit"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Throttle Limit (Mbps) *
              </label>
              <input
                id="throttle_limit"
                type="number"
                value={formData.throttle_limit_mbps}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    throttle_limit_mbps: parseFloat(e.target.value),
                  })
                }
                min="0.1"
                step="0.1"
                placeholder="10"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label
                htmlFor="start_time"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Start Time *
              </label>
              <input
                id="start_time"
                type="time"
                value={formData.start_time}
                onChange={(e) =>
                  setFormData({ ...formData, start_time: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label
                htmlFor="end_time"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                End Time *
              </label>
              <input
                id="end_time"
                type="time"
                value={formData.end_time}
                onChange={(e) =>
                  setFormData({ ...formData, end_time: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                required
              />
            </div>

            <div className="col-span-2">
              <label
                htmlFor="recurrence"
                className="block text-sm font-medium text-slate-700 mb-2"
              >
                Recurrence *
              </label>
              <select
                id="recurrence"
                value={formData.recurrence}
                onChange={(e) =>
                  setFormData({ ...formData, recurrence: e.target.value })
                }
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="once">Once</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="weekdays">Weekdays (Mon-Fri)</option>
                <option value="weekends">Weekends (Sat-Sun)</option>
              </select>
            </div>

            {formData.recurrence === "weekly" && (
              <div className="col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Days of Week *
                </label>
                <div className="flex gap-2">
                  {daysOfWeek.map((day) => {
                    const isSelected = formData.days_of_week
                      ?.split(",")
                      .includes(day.value);
                    return (
                      <button
                        key={day.value}
                        type="button"
                        onClick={() => toggleDay(day.value)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          isSelected
                            ? "bg-green-600 text-white"
                            : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                        }`}
                      >
                        {day.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              id="is_enabled"
              type="checkbox"
              checked={formData.is_enabled}
              onChange={(e) =>
                setFormData({ ...formData, is_enabled: e.target.checked })
              }
              className="w-4 h-4 text-green-600 rounded focus:ring-2 focus:ring-green-500"
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
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Calendar size={16} />
                  {schedule ? "Update Schedule" : "Create Schedule"}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
