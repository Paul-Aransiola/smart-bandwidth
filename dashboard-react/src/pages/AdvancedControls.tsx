import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import { useAuth } from "../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import type { Device } from "../types/device";
import { BlockDeviceModal } from "../components/BlockDeviceModal";
import { ThrottleDeviceModal } from "../components/ThrottleDeviceModal";
import { QuotaModal } from "../components/QuotaModal";
import { QoSModal } from "../components/QoSModal";
import { ScheduleModal } from "../components/ScheduleModal";
import {
  Settings,
  Calendar,
  DollarSign,
  Gauge,
  Globe,
  Plus,
  Edit,
  Trash2,
  Power,
  Clock,
  Lock,
  Shield,
  ShieldOff,
  Zap,
  ZapOff,
} from "lucide-react";

interface BandwidthQuota {
  id: number;
  device_id?: number;
  quota_name: string;
  quota_type: string;
  limit_bytes: number;
  used_bytes: number;
  reset_day?: number;
  is_active: boolean;
  warning_threshold_percent?: number;
  last_reset_at?: string;
}

interface QoSPolicy {
  id: number;
  policy_name: string;
  device_id?: number;
  priority_level: number;
  bandwidth_limit_mbps?: number;
  burst_limit_mbps?: number;
  is_enabled: boolean;
}

interface ThrottleSchedule {
  id: number;
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

interface GlobalSettings {
  global_bandwidth_threshold_mbps?: number;
  global_auto_deactivate_on_threshold?: boolean;
  global_threshold_time_window_minutes?: number;
}

export const AdvancedControls: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<
    "controls" | "quotas" | "qos" | "schedules" | "global"
  >("controls");
  const [quotas, setQuotas] = useState<BandwidthQuota[]>([]);
  const [qosPolicies, setQosPolicies] = useState<QoSPolicy[]>([]);
  const [throttleSchedules, setThrottleSchedules] = useState<
    ThrottleSchedule[]
  >([]);
  const [globalSettings, setGlobalSettings] = useState<GlobalSettings>({});
  const [devices, setDevices] = useState<Device[]>([]);
  const [blockDevice, setBlockDevice] = useState<Device | null>(null);
  const [throttleDevice, setThrottleDevice] = useState<Device | null>(null);
  const [quotaModal, setQuotaModal] = useState<{
    open: boolean;
    quota?: BandwidthQuota;
  }>({ open: false });
  const [qosModal, setQosModal] = useState<{
    open: boolean;
    policy?: QoSPolicy;
  }>({ open: false });
  const [scheduleModal, setScheduleModal] = useState<{
    open: boolean;
    schedule?: ThrottleSchedule;
  }>({ open: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    setError("");

    console.log(
      "[AdvancedControls] Token in localStorage:",
      localStorage.getItem("token")
    );
    console.log("[AdvancedControls] isAuthenticated:", isAuthenticated);

    try {
      const [quotasRes, qosRes, schedulesRes, globalRes, devicesRes] =
        await Promise.all([
          axios.get("/api/v1/advanced-controls/quotas"),
          axios.get("/api/v1/advanced-controls/qos-policies"),
          axios.get("/api/v1/advanced-controls/schedules"),
          axios.get("/api/v1/threshold/global"),
          axios.get("/api/v1/devices"),
        ]);

      console.log("[AdvancedControls] Successfully fetched data");
      setQuotas(quotasRes.data.data || []);
      setQosPolicies(qosRes.data.data || []);
      setThrottleSchedules(schedulesRes.data.data || []);
      setGlobalSettings(globalRes.data.data || {});
      setDevices(devicesRes.data.data || []);
      setLoading(false);
    } catch (err: any) {
      console.error("[AdvancedControls] Failed to fetch:", err);
      console.error("[AdvancedControls] Error response:", err.response);
      // Don't set error for 401 as interceptor will redirect to login
      if (err.response?.status !== 401) {
        setError(
          err.response?.data?.detail || "Failed to fetch advanced controls"
        );
      }
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  const getUsagePercentage = (used: number, limit: number) => {
    return limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  };

  // Device control functions
  const handleBlockDevice = (device: Device) => {
    setBlockDevice(device);
  };

  const confirmBlockDevice = async (reason: string) => {
    if (!blockDevice) return;

    await axios.post(`/api/v1/control/block/${blockDevice.ip_address}`, {
      reason: reason,
    });
    await fetchAll(); // Refresh all data including devices
  };

  const handleUnblockDevice = async (device: Device) => {
    if (!confirm(`Unblock device ${device.ip_address}?`)) return;

    try {
      await axios.post(`/api/v1/control/unblock/${device.ip_address}`);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to unblock device");
    }
  };

  const handleThrottleDevice = (device: Device) => {
    setThrottleDevice(device);
  };

  const confirmThrottleDevice = async (limitMbps: number) => {
    if (!throttleDevice) return;

    await axios.post(`/api/v1/control/throttle/${throttleDevice.ip_address}`, {
      limit_mbps: limitMbps,
      reason: "Throttled from Advanced Controls",
    });
    await fetchAll();
  };

  const handleUnthrottleDevice = async (device: Device) => {
    if (!confirm(`Remove throttle from device ${device.ip_address}?`)) return;

    try {
      await axios.post(`/api/v1/control/unthrottle/${device.ip_address}`);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to unthrottle device");
    }
  };

  // CRUD handlers for quotas, QoS, and schedules
  const handleDeleteQuota = async (id: number) => {
    if (!confirm("Are you sure you want to delete this quota?")) return;
    try {
      await axios.delete(`/api/v1/advanced-controls/quotas/${id}`);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete quota");
    }
  };

  const handleDeleteQoS = async (id: number) => {
    if (!confirm("Are you sure you want to delete this QoS policy?")) return;
    try {
      await axios.delete(`/api/v1/advanced-controls/qos-policies/${id}`);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete QoS policy");
    }
  };

  const handleDeleteSchedule = async (id: number) => {
    if (!confirm("Are you sure you want to delete this schedule?")) return;
    try {
      await axios.delete(`/api/v1/advanced-controls/schedules/${id}`);
      await fetchAll();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete schedule");
    }
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Advanced Controls
          </h1>
          <p className="text-slate-600 mt-1">
            Manage device controls, quotas, QoS policies, schedules, and global
            settings
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200">
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => setActiveTab("controls")}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === "controls"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Shield size={20} />
            Device Controls
          </button>
          <button
            onClick={() => setActiveTab("quotas")}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === "quotas"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <DollarSign size={20} />
            Bandwidth Quotas
          </button>
          <button
            onClick={() => setActiveTab("qos")}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === "qos"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Gauge size={20} />
            QoS Policies
          </button>
          <button
            onClick={() => setActiveTab("schedules")}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === "schedules"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Calendar size={20} />
            Throttle Schedules
          </button>
          <button
            onClick={() => setActiveTab("global")}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === "global"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <Globe size={20} />
            Global Settings
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-slate-600 mt-4">Loading...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                  <Lock className="text-red-600" size={32} />
                </div>
                <div>
                  <p className="text-xl font-semibold text-slate-900 mb-2">
                    Authentication Required
                  </p>
                  <p className="text-slate-600 mb-4">{error}</p>
                </div>
                {!isAuthenticated && (
                  <div className="flex gap-3">
                    <button
                      onClick={() => navigate("/login")}
                      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                    >
                      Sign In
                    </button>
                    <button
                      onClick={() => navigate("/register")}
                      className="px-6 py-2 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors font-medium"
                    >
                      Register
                    </button>
                  </div>
                )}
                {isAuthenticated && (
                  <button
                    onClick={fetchAll}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                  >
                    Retry
                  </button>
                )}
              </div>
            </div>
          ) : (
            <>
              {activeTab === "controls" && (
                <DeviceControlsSection
                  devices={devices}
                  onBlock={handleBlockDevice}
                  onUnblock={handleUnblockDevice}
                  onThrottle={handleThrottleDevice}
                  onUnthrottle={handleUnthrottleDevice}
                />
              )}
              {activeTab === "quotas" && (
                <QuotasSection
                  quotas={quotas}
                  onRefresh={fetchAll}
                  onAdd={() => setQuotaModal({ open: true })}
                  onEdit={(quota) => setQuotaModal({ open: true, quota })}
                  onDelete={handleDeleteQuota}
                  formatBytes={formatBytes}
                  getUsagePercentage={getUsagePercentage}
                />
              )}
              {activeTab === "qos" && (
                <QoSSection
                  policies={qosPolicies}
                  onRefresh={fetchAll}
                  onAdd={() => setQosModal({ open: true })}
                  onEdit={(policy) => setQosModal({ open: true, policy })}
                  onDelete={handleDeleteQoS}
                />
              )}
              {activeTab === "schedules" && (
                <SchedulesSection
                  schedules={throttleSchedules}
                  onRefresh={fetchAll}
                  onAdd={() => setScheduleModal({ open: true })}
                  onEdit={(schedule) =>
                    setScheduleModal({ open: true, schedule })
                  }
                  onDelete={handleDeleteSchedule}
                />
              )}
              {activeTab === "global" && (
                <GlobalSettingsSection
                  settings={globalSettings}
                  onRefresh={fetchAll}
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* Modals */}
      {blockDevice && (
        <BlockDeviceModal
          device={blockDevice}
          onClose={() => setBlockDevice(null)}
          onConfirm={confirmBlockDevice}
        />
      )}

      {throttleDevice && (
        <ThrottleDeviceModal
          device={throttleDevice}
          onClose={() => setThrottleDevice(null)}
          onConfirm={confirmThrottleDevice}
        />
      )}

      {quotaModal.open && (
        <QuotaModal
          quota={quotaModal.quota}
          onClose={() => setQuotaModal({ open: false })}
          onSuccess={fetchAll}
        />
      )}

      {qosModal.open && (
        <QoSModal
          policy={qosModal.policy}
          onClose={() => setQosModal({ open: false })}
          onSuccess={fetchAll}
        />
      )}

      {scheduleModal.open && (
        <ScheduleModal
          schedule={scheduleModal.schedule}
          onClose={() => setScheduleModal({ open: false })}
          onSuccess={fetchAll}
        />
      )}
    </div>
  );
};

// Device Controls Section Component
const DeviceControlsSection: React.FC<{
  devices: Device[];
  onBlock: (device: Device) => void;
  onUnblock: (device: Device) => void;
  onThrottle: (device: Device) => void;
  onUnthrottle: (device: Device) => void;
}> = ({ devices, onBlock, onUnblock, onThrottle, onUnthrottle }) => {
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredDevices = devices.filter((device) => {
    const matchesStatus =
      filterStatus === "all" || device.status === filterStatus;
    const matchesSearch =
      device.device_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.hostname?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.ip_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.mac_address?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      active: "bg-green-100 text-green-800",
      throttled: "bg-yellow-100 text-yellow-800",
      blocked: "bg-red-100 text-red-800",
      deactivated: "bg-red-100 text-red-800",
      inactive: "bg-slate-100 text-slate-800",
    };
    return colors[status] || "bg-slate-100 text-slate-800";
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-800">
          Device Controls
        </h3>
        <div className="text-sm text-slate-600">
          {filteredDevices.length} of {devices.length} devices
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-4">
        <input
          type="text"
          placeholder="Search by name, IP, or MAC..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="throttled">Throttled</option>
          <option value="blocked">Blocked</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      {filteredDevices.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          {searchTerm || filterStatus !== "all"
            ? "No devices match your filters"
            : "No devices found"}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                  Device
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                  IP Address
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                  Bandwidth
                </th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredDevices.map((device) => (
                <tr
                  key={device.id}
                  className="border-b border-slate-200 hover:bg-slate-50"
                >
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-900">
                      {device.device_name || device.hostname || "Unknown"}
                    </div>
                    <div className="text-sm text-slate-500">
                      {device.mac_address || "N/A"}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {device.ip_address}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(
                        device.status
                      )}`}
                    >
                      {device.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-slate-700">
                      ↓ {formatBytes(device.total_bytes_received || 0)}
                    </div>
                    <div className="text-sm text-slate-700">
                      ↑ {formatBytes(device.total_bytes_sent || 0)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {device.status === "blocked" ? (
                        <button
                          onClick={() => onUnblock(device)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                          title="Unblock device"
                        >
                          <ShieldOff size={14} />
                          Unblock
                        </button>
                      ) : (
                        <button
                          onClick={() => onBlock(device)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                          title="Block device"
                        >
                          <Shield size={14} />
                          Block
                        </button>
                      )}

                      {device.status === "throttled" ? (
                        <button
                          onClick={() => onUnthrottle(device)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-sm"
                          title="Remove throttle"
                        >
                          <ZapOff size={14} />
                          Unthrottle
                        </button>
                      ) : (
                        <button
                          onClick={() => onThrottle(device)}
                          className="flex items-center gap-1 px-3 py-1.5 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors text-sm"
                          title="Throttle device"
                          disabled={device.status === "blocked"}
                        >
                          <Zap size={14} />
                          Throttle
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// Quotas Section Component
const QuotasSection: React.FC<{
  quotas: BandwidthQuota[];
  onRefresh: () => void;
  onAdd: () => void;
  onEdit: (quota: BandwidthQuota) => void;
  onDelete: (id: number) => void;
  formatBytes: (bytes: number) => string;
  getUsagePercentage: (used: number, limit: number) => number;
}> = ({
  quotas,
  onRefresh,
  onAdd,
  onEdit,
  onDelete,
  formatBytes,
  getUsagePercentage,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800">
          Bandwidth Quotas
        </h3>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Quota
        </button>
      </div>

      {quotas.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          No bandwidth quotas configured
        </div>
      ) : (
        <div className="space-y-4">
          {quotas.map((quota) => {
            const percentage = getUsagePercentage(
              quota.used_bytes,
              quota.limit_bytes
            );
            const isWarning =
              quota.warning_threshold_percent &&
              percentage >= quota.warning_threshold_percent;

            return (
              <div
                key={quota.id}
                className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        quota.is_active
                          ? "bg-green-100 text-green-700"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {quota.is_active ? "Active" : "Inactive"}
                    </div>
                    <h4 className="font-semibold text-slate-800">
                      {quota.quota_name}
                    </h4>
                    <span className="text-sm text-slate-500">
                      ({quota.quota_type})
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onEdit(quota)}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                      title="Edit quota"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => onDelete(quota.id)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete quota"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">Usage</span>
                    <span
                      className={`font-medium ${
                        isWarning ? "text-amber-600" : "text-slate-800"
                      }`}
                    >
                      {formatBytes(quota.used_bytes)} /{" "}
                      {formatBytes(quota.limit_bytes)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        percentage >= 90
                          ? "bg-red-500"
                          : isWarning
                          ? "bg-amber-500"
                          : "bg-green-500"
                      }`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>{percentage.toFixed(1)}% used</span>
                    {quota.reset_day && (
                      <span>Resets on day {quota.reset_day}</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// QoS Section Component
const QoSSection: React.FC<{
  policies: QoSPolicy[];
  onRefresh: () => void;
  onAdd: () => void;
  onEdit: (policy: QoSPolicy) => void;
  onDelete: (id: number) => void;
}> = ({ policies, onRefresh, onAdd, onEdit, onDelete }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800">QoS Policies</h3>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Policy
        </button>
      </div>

      {policies.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          No QoS policies configured
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                  Policy Name
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                  Priority
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                  Bandwidth Limit
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                  Burst Limit
                </th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-slate-700">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {policies.map((policy) => (
                <tr
                  key={policy.id}
                  className="border-b border-slate-100 hover:bg-slate-50"
                >
                  <td className="py-3 px-4">
                    <div
                      className={`inline-flex items-center gap-2 px-2 py-1 rounded-full text-xs font-medium ${
                        policy.is_enabled
                          ? "bg-green-100 text-green-700"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      <Power size={12} />
                      {policy.is_enabled ? "Enabled" : "Disabled"}
                    </div>
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-800">
                    {policy.policy_name}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        policy.priority_level <= 3
                          ? "bg-red-100 text-red-700"
                          : policy.priority_level <= 6
                          ? "bg-amber-100 text-amber-700"
                          : "bg-green-100 text-green-700"
                      }`}
                    >
                      {policy.priority_level}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {policy.bandwidth_limit_mbps
                      ? `${policy.bandwidth_limit_mbps} Mbps`
                      : "Unlimited"}
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {policy.burst_limit_mbps
                      ? `${policy.burst_limit_mbps} Mbps`
                      : "None"}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onEdit(policy)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Edit policy"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => onDelete(policy.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete policy"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// Schedules Section Component
const SchedulesSection: React.FC<{
  schedules: ThrottleSchedule[];
  onRefresh: () => void;
  onAdd: () => void;
  onEdit: (schedule: ThrottleSchedule) => void;
  onDelete: (id: number) => void;
}> = ({ schedules, onRefresh, onAdd, onEdit, onDelete }) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800">
          Throttle Schedules
        </h3>
        <button
          onClick={onAdd}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
          Add Schedule
        </button>
      </div>

      {schedules.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          No throttle schedules configured
        </div>
      ) : (
        <div className="grid gap-4">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      schedule.is_enabled
                        ? "bg-green-100 text-green-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {schedule.is_enabled ? "Enabled" : "Disabled"}
                  </div>
                  <h4 className="font-semibold text-slate-800">
                    {schedule.schedule_name}
                  </h4>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onEdit(schedule)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Edit schedule"
                  >
                    <Edit size={16} />
                  </button>
                  <button
                    onClick={() => onDelete(schedule.id)}
                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete schedule"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>

              {schedule.description && (
                <p className="text-sm text-slate-600 mb-3">
                  {schedule.description}
                </p>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Clock size={16} className="text-slate-400" />
                  <span className="text-slate-600">
                    {schedule.start_time} - {schedule.end_time}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Gauge size={16} className="text-slate-400" />
                  <span className="text-slate-600">
                    Limit: {schedule.throttle_limit_mbps} Mbps
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-slate-400" />
                  <span className="text-slate-600">{schedule.recurrence}</span>
                </div>
                {schedule.days_of_week && (
                  <div className="flex items-center gap-2">
                    <span className="text-slate-600">
                      Days: {schedule.days_of_week}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Global Settings Section Component
const GlobalSettingsSection: React.FC<{
  settings: GlobalSettings;
  onRefresh: () => void;
}> = ({ settings, onRefresh }) => {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-800">
        Global Threshold Settings
      </h3>

      <div className="bg-slate-50 rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Bandwidth Threshold (Mbps)
            </label>
            <div className="text-2xl font-bold text-slate-900">
              {settings.global_bandwidth_threshold_mbps || "Not set"}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Auto-Deactivate
            </label>
            <div
              className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
                settings.global_auto_deactivate_on_threshold
                  ? "bg-red-100 text-red-700"
                  : "bg-slate-100 text-slate-600"
              }`}
            >
              {settings.global_auto_deactivate_on_threshold
                ? "Enabled"
                : "Disabled"}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Time Window (minutes)
            </label>
            <div className="text-2xl font-bold text-slate-900">
              {settings.global_threshold_time_window_minutes || 5}
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200">
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <Settings size={16} />
            Edit Global Settings
          </button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        <strong>Note:</strong> Global settings apply to all devices that don't
        have individual threshold configurations.
      </div>
    </div>
  );
};

export default AdvancedControls;
