import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import {
  Bell,
  BellOff,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Plus,
  Filter,
  Eye,
  Edit2,
  Trash2,
  Clock,
  Activity,
  Settings,
} from "lucide-react";
import { AlertRuleModal } from "../components/AlertRuleModal";
import { AlertDetailsModal } from "../components/AlertDetailsModal";

interface Alert {
  id: number;
  title: string;
  message: string;
  severity: "info" | "warning" | "error" | "critical";
  status: "active" | "acknowledged" | "resolved" | "snoozed";
  triggered_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  rule_name?: string;
  device_ip?: string;
  device_name?: string;
  metric_value: number;
  threshold_value: number;
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
  is_enabled: boolean;
  last_triggered_at?: string;
  created_at: string;
}

interface Statistics {
  total_alerts: number;
  active_alerts: number;
  acknowledged_alerts: number;
  resolved_alerts: number;
  critical_alerts: number;
}

export const Alerts: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"alerts" | "rules">("alerts");
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  // Modals
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [selectedRule, setSelectedRule] = useState<AlertRule | null>(null);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    await Promise.all([fetchAlerts(), fetchRules(), fetchStatistics()]);
  };

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/api/v1/alerts/");
      setAlerts(res.data.data || []);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch alerts");
    } finally {
      setLoading(false);
    }
  };

  const fetchRules = async () => {
    try {
      const res = await axios.get("/api/v1/alerts/rules");
      setRules(res.data.data || []);
    } catch (err: any) {
      console.error("Failed to fetch rules:", err);
    }
  };

  const fetchStatistics = async () => {
    try {
      const res = await axios.get("/api/v1/alerts/statistics/summary");
      setStatistics(res.data.data);
    } catch (err: any) {
      console.error("Failed to fetch statistics:", err);
    }
  };

  const handleAcknowledge = async (alertId: number) => {
    try {
      await axios.put(`/api/v1/alerts/${alertId}/status`, {
        status: "acknowledged",
      });
      await fetchAlerts();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to acknowledge alert");
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await axios.put(`/api/v1/alerts/${alertId}/status`, {
        status: "resolved",
      });
      await fetchAlerts();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to resolve alert");
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!confirm("Are you sure you want to delete this alert rule?")) return;

    try {
      await axios.delete(`/api/v1/alerts/rules/${ruleId}`);
      await fetchRules();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to delete rule");
    }
  };

  const handleToggleRule = async (ruleId: number, isEnabled: boolean) => {
    try {
      await axios.put(`/api/v1/alerts/rules/${ruleId}`, {
        is_enabled: !isEnabled,
      });
      await fetchRules();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to toggle rule");
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "critical":
        return <AlertCircle className="text-red-600" size={18} />;
      case "error":
        return <AlertTriangle className="text-orange-600" size={18} />;
      case "warning":
        return <AlertTriangle className="text-yellow-600" size={18} />;
      default:
        return <Info className="text-blue-600" size={18} />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-100 text-red-800 border-red-200";
      case "error":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-blue-100 text-blue-800 border-blue-200";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-red-100 text-red-800";
      case "acknowledged":
        return "bg-yellow-100 text-yellow-800";
      case "resolved":
        return "bg-green-100 text-green-800";
      case "snoozed":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  const filteredAlerts = alerts.filter((alert) => {
    if (statusFilter !== "all" && alert.status !== statusFilter) return false;
    if (severityFilter !== "all" && alert.severity !== severityFilter)
      return false;
    return true;
  });

  const filteredRules = rules.filter((rule) => {
    if (severityFilter !== "all" && rule.severity !== severityFilter)
      return false;
    return true;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
          <p className="text-slate-600 mt-1">
            Monitor and manage system alerts and rules
          </p>
        </div>
        {activeTab === "rules" && (
          <button
            onClick={() => {
              setSelectedRule(null);
              setShowRuleModal(true);
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus size={20} />
            Add Rule
          </button>
        )}
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-4 border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Total Alerts</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">
                  {statistics.total_alerts}
                </p>
              </div>
              <Activity className="text-slate-400" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Active</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {statistics.active_alerts}
                </p>
              </div>
              <Bell className="text-red-400" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Acknowledged</p>
                <p className="text-2xl font-bold text-yellow-600 mt-1">
                  {statistics.acknowledged_alerts}
                </p>
              </div>
              <Clock className="text-yellow-400" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Resolved</p>
                <p className="text-2xl font-bold text-green-600 mt-1">
                  {statistics.resolved_alerts}
                </p>
              </div>
              <CheckCircle className="text-green-400" size={24} />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4 border border-slate-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600">Critical</p>
                <p className="text-2xl font-bold text-red-600 mt-1">
                  {statistics.critical_alerts}
                </p>
              </div>
              <AlertCircle className="text-red-400" size={24} />
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow border border-slate-200">
        <div className="border-b border-slate-200">
          <div className="flex">
            <button
              onClick={() => setActiveTab("alerts")}
              className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                activeTab === "alerts"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center gap-2">
                <Bell size={18} />
                Alerts
              </div>
            </button>
            <button
              onClick={() => setActiveTab("rules")}
              className={`px-6 py-3 font-medium transition-colors border-b-2 ${
                activeTab === "rules"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              <div className="flex items-center gap-2">
                <Settings size={18} />
                Alert Rules
              </div>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="p-4 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center gap-4">
            <Filter size={18} className="text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="snoozed">Snoozed</option>
            </select>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              <option value="all">All Severity</option>
              <option value="info">Info</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
              <option value="critical">Critical</option>
            </select>

            {(statusFilter !== "all" || severityFilter !== "all") && (
              <button
                onClick={() => {
                  setStatusFilter("all");
                  setSeverityFilter("all");
                }}
                className="text-sm text-blue-600 hover:text-blue-700"
              >
                Clear Filters
              </button>
            )}
          </div>
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
              <AlertCircle className="text-red-500 mx-auto" size={48} />
              <p className="text-red-600 mt-4">{error}</p>
            </div>
          ) : activeTab === "alerts" ? (
            <div className="space-y-3">
              {filteredAlerts.length === 0 ? (
                <div className="text-center py-12">
                  <BellOff className="text-slate-300 mx-auto" size={48} />
                  <p className="text-slate-600 mt-4">
                    No alerts found matching your filters
                  </p>
                </div>
              ) : (
                filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        {getSeverityIcon(alert.severity)}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-slate-900">
                              {alert.title}
                            </h3>
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(
                                alert.severity
                              )} border`}
                            >
                              {alert.severity.toUpperCase()}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                                alert.status
                              )}`}
                            >
                              {alert.status}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600 mb-2">
                            {alert.message}
                          </p>
                          <div className="flex items-center gap-4 text-xs text-slate-500">
                            {alert.rule_name && (
                              <span>Rule: {alert.rule_name}</span>
                            )}
                            {alert.device_name && (
                              <span>Device: {alert.device_name}</span>
                            )}
                            {alert.device_ip && (
                              <span>IP: {alert.device_ip}</span>
                            )}
                            <span>
                              Triggered:{" "}
                              {new Date(alert.triggered_at).toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedAlert(alert);
                            setShowDetailsModal(true);
                          }}
                          className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="View Details"
                        >
                          <Eye size={18} />
                        </button>
                        {alert.status === "active" && (
                          <button
                            onClick={() => handleAcknowledge(alert.id)}
                            className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
                          >
                            Acknowledge
                          </button>
                        )}
                        {(alert.status === "active" ||
                          alert.status === "acknowledged") && (
                          <button
                            onClick={() => handleResolve(alert.id)}
                            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredRules.length === 0 ? (
                <div className="text-center py-12">
                  <Settings className="text-slate-300 mx-auto" size={48} />
                  <p className="text-slate-600 mt-4">
                    No alert rules found. Create one to get started.
                  </p>
                </div>
              ) : (
                filteredRules.map((rule) => (
                  <div
                    key={rule.id}
                    className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-slate-900">
                            {rule.name}
                          </h3>
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium ${getSeverityColor(
                              rule.severity
                            )} border`}
                          >
                            {rule.severity.toUpperCase()}
                          </span>
                          {rule.is_enabled ? (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Enabled
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                              Disabled
                            </span>
                          )}
                        </div>
                        {rule.description && (
                          <p className="text-sm text-slate-600 mb-2">
                            {rule.description}
                          </p>
                        )}
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span>
                            Metric: {rule.metric} {rule.condition}{" "}
                            {rule.threshold_value}
                          </span>
                          <span>
                            Window: {rule.time_window_minutes} minutes
                          </span>
                          {rule.last_triggered_at && (
                            <span>
                              Last triggered:{" "}
                              {new Date(
                                rule.last_triggered_at
                              ).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() =>
                            handleToggleRule(rule.id, rule.is_enabled)
                          }
                          className={`p-2 rounded transition-colors ${
                            rule.is_enabled
                              ? "text-green-600 hover:text-green-700 hover:bg-green-50"
                              : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                          }`}
                          title={rule.is_enabled ? "Disable" : "Enable"}
                        >
                          {rule.is_enabled ? (
                            <Bell size={18} />
                          ) : (
                            <BellOff size={18} />
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setSelectedRule(rule);
                            setShowRuleModal(true);
                          }}
                          className="p-2 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          title="Edit"
                        >
                          <Edit2 size={18} />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(rule.id)}
                          className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      {showRuleModal && (
        <AlertRuleModal
          rule={selectedRule}
          onClose={() => {
            setShowRuleModal(false);
            setSelectedRule(null);
          }}
          onSuccess={() => {
            fetchRules();
            setShowRuleModal(false);
            setSelectedRule(null);
          }}
        />
      )}

      {showDetailsModal && selectedAlert && (
        <AlertDetailsModal
          alert={selectedAlert}
          onClose={() => {
            setShowDetailsModal(false);
            setSelectedAlert(null);
          }}
          onAcknowledge={handleAcknowledge}
          onResolve={handleResolve}
        />
      )}
    </div>
  );
};

export default Alerts;
