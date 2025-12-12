import React from "react";
import {
  X,
  AlertCircle,
  AlertTriangle,
  Info,
  Clock,
  CheckCircle,
  Eye,
} from "lucide-react";

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

interface AlertDetailsModalProps {
  alert: Alert;
  onClose: () => void;
  onAcknowledge: (id: number) => void;
  onResolve: (id: number) => void;
}

export const AlertDetailsModal: React.FC<AlertDetailsModalProps> = ({
  alert,
  onClose,
  onAcknowledge,
  onResolve,
}) => {
  const getSeverityIcon = () => {
    switch (alert.severity) {
      case "critical":
        return <AlertCircle className="text-red-600" size={24} />;
      case "error":
        return <AlertTriangle className="text-orange-600" size={24} />;
      case "warning":
        return <AlertTriangle className="text-yellow-600" size={24} />;
      default:
        return <Info className="text-blue-600" size={24} />;
    }
  };

  const getSeverityColor = () => {
    switch (alert.severity) {
      case "critical":
        return "bg-red-100 text-red-600";
      case "error":
        return "bg-orange-100 text-orange-600";
      case "warning":
        return "bg-yellow-100 text-yellow-600";
      default:
        return "bg-blue-100 text-blue-600";
    }
  };

  const getStatusColor = () => {
    switch (alert.status) {
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 ${getSeverityColor()} rounded-lg flex items-center justify-center`}
            >
              {getSeverityIcon()}
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Alert Details
              </h2>
              <p className="text-sm text-slate-600">Alert #{alert.id}</p>
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
        <div className="p-6 space-y-6">
          {/* Status and Severity */}
          <div className="flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor()} border border-current`}
            >
              {alert.severity.toUpperCase()}
            </span>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}
            >
              {alert.status.toUpperCase()}
            </span>
          </div>

          {/* Title and Message */}
          <div>
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              {alert.title}
            </h3>
            <p className="text-slate-700">{alert.message}</p>
          </div>

          {/* Metrics */}
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <h4 className="text-sm font-semibold text-slate-700 mb-3">
              Metric Information
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-600 mb-1">Current Value</p>
                <p className="text-lg font-semibold text-slate-900">
                  {alert.metric_value.toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-600 mb-1">Threshold</p>
                <p className="text-lg font-semibold text-slate-900">
                  {alert.threshold_value.toFixed(2)}
                </p>
              </div>
            </div>
          </div>

          {/* Device Information */}
          {(alert.device_name || alert.device_ip) && (
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">
                Device Information
              </h4>
              <div className="space-y-2">
                {alert.device_name && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Device Name:</span>
                    <span className="text-sm font-medium text-slate-900">
                      {alert.device_name}
                    </span>
                  </div>
                )}
                {alert.device_ip && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">IP Address:</span>
                    <span className="text-sm font-medium text-slate-900">
                      {alert.device_ip}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Rule Information */}
          {alert.rule_name && (
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">
                Rule Information
              </h4>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Rule Name:</span>
                <span className="text-sm font-medium text-slate-900">
                  {alert.rule_name}
                </span>
              </div>
            </div>
          )}

          {/* Timeline */}
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <h4 className="text-sm font-semibold text-slate-700 mb-3">
              Timeline
            </h4>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="text-red-600" size={16} />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-900">
                    Alert Triggered
                  </p>
                  <p className="text-xs text-slate-600">
                    {new Date(alert.triggered_at).toLocaleString()}
                  </p>
                </div>
              </div>

              {alert.acknowledged_at && (
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Eye className="text-yellow-600" size={16} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900">
                      Acknowledged
                    </p>
                    <p className="text-xs text-slate-600">
                      {new Date(alert.acknowledged_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              )}

              {alert.resolved_at && (
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <CheckCircle className="text-green-600" size={16} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-900">
                      Resolved
                    </p>
                    <p className="text-xs text-slate-600">
                      {new Date(alert.resolved_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 p-6 border-t border-slate-200">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
          >
            Close
          </button>
          {alert.status === "active" && (
            <>
              <button
                onClick={() => {
                  onAcknowledge(alert.id);
                  onClose();
                }}
                className="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
              >
                Acknowledge
              </button>
              <button
                onClick={() => {
                  onResolve(alert.id);
                  onClose();
                }}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Resolve
              </button>
            </>
          )}
          {alert.status === "acknowledged" && (
            <button
              onClick={() => {
                onResolve(alert.id);
                onClose();
              }}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Resolve
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
