import React, { useEffect, useState, useCallback } from "react";
import axios from "../lib/axios";
import { DeviceTable } from "../components/DeviceTable";
import { DeviceForm } from "../components/DeviceForm";
import { DeviceDetails } from "../components/DeviceDetails";
import { ThresholdModal } from "../components/ThresholdModal";
import { ThrottleModal } from "../components/ThrottleModal";
import { BlockModal } from "../components/BlockModal";
import { NetworkScanModal } from "../components/NetworkScanModal";
import DeviceHistoryModal from "../components/DeviceHistoryModal";
import type { Device, GlobalThreshold } from "../types/device";
import { thresholdService } from "../utils/thresholdService";
import { useWebSocket } from "../hooks/useWebSocket";
import "../styles/legacy-theme.scss";
import "../styles/devices.css";
import "../styles/responsive.css";

const Devices: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [thresholdDevice, setThresholdDevice] = useState<Device | null>(null);
  const [historyDevice, setHistoryDevice] = useState<Device | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showScanModal, setShowScanModal] = useState(false);
  const [globalThreshold, setGlobalThreshold] =
    useState<GlobalThreshold | null>(null);
  const [showGlobalThreshold, setShowGlobalThreshold] = useState(false);
  const [bulkMode, setBulkMode] = useState(false);
  const [selectedDeviceIds, setSelectedDeviceIds] = useState<Set<number>>(
    new Set()
  );

  // Filters and sorting
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [sortField, setSortField] = useState<
    "ip" | "name" | "status" | "usage"
  >("ip");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  const handleWebSocketMessage = useCallback((message: any) => {
    console.log("WebSocket message received:", message);

    if (
      message.type === "device_update" ||
      message.type === "device_blocked" ||
      message.type === "device_unblocked" ||
      message.type === "device_throttled" ||
      message.type === "device_unthrottled"
    ) {
      fetchDevices();
    }
  }, []);

  useWebSocket("/ws/monitor", handleWebSocketMessage, true);

  useEffect(() => {
    fetchDevices();
    fetchGlobalThreshold();
  }, []);

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/api/v1/devices");
      setDevices(res.data.data || []);
      setError("");
    } catch (err: any) {
      console.error("Failed to fetch devices:", err);
      setError(err.response?.data?.detail || "Failed to fetch devices");
    }
    setLoading(false);
  };

  const fetchGlobalThreshold = async () => {
    try {
      const data = await thresholdService.getGlobalThreshold();
      setGlobalThreshold(data);
    } catch (err) {
      console.error("Failed to fetch global threshold:", err);
    }
  };

  const handleSetGlobalThreshold = async (
    thresholdMbps: number,
    autoDeactivate: boolean,
    timeWindow: number
  ) => {
    try {
      await thresholdService.setGlobalThreshold({
        threshold_mbps: thresholdMbps,
        auto_deactivate: autoDeactivate,
        time_window_minutes: timeWindow,
      });
      await fetchGlobalThreshold();
      setShowGlobalThreshold(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to set global threshold");
    }
  };

  const handleRemoveGlobalThreshold = async () => {
    if (!confirm("Remove the global bandwidth threshold?")) return;
    try {
      await thresholdService.removeGlobalThreshold();
      await fetchGlobalThreshold();
      setShowGlobalThreshold(false);
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to remove global threshold");
    }
  };

  // Block/Throttle controls moved to Advanced Controls page

  const handleToggleSelect = (deviceId: number) => {
    const newSelected = new Set(selectedDeviceIds);
    if (newSelected.has(deviceId)) {
      newSelected.delete(deviceId);
    } else {
      newSelected.add(deviceId);
    }
    setSelectedDeviceIds(newSelected);
  };

  const handleToggleSelectAll = () => {
    if (selectedDeviceIds.size === devices.length) {
      setSelectedDeviceIds(new Set());
    } else {
      setSelectedDeviceIds(new Set(devices.map((d) => d.id)));
    }
  };

  // Bulk block/unblock operations moved to Advanced Controls page

  const handleBulkDelete = async () => {
    if (selectedDeviceIds.size === 0) return;

    if (
      !confirm(
        `Delete ${selectedDeviceIds.size} selected device(s)? This cannot be undone.`
      )
    )
      return;

    const selectedDevices = devices.filter((d) => selectedDeviceIds.has(d.id));
    let successCount = 0;

    for (const device of selectedDevices) {
      try {
        await axios.delete(`/api/v1/devices/${device.id}`);
        successCount++;
      } catch (err) {
        console.error(`Failed to delete device ${device.id}:`, err);
      }
    }

    alert(
      `Successfully deleted ${successCount} of ${selectedDeviceIds.size} devices`
    );
    setSelectedDeviceIds(new Set());
    await fetchDevices();
  };

  // Filter and sort devices
  const filteredAndSortedDevices = React.useMemo(() => {
    let result = [...devices];

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (d) =>
          d.ip_address.toLowerCase().includes(query) ||
          d.hostname?.toLowerCase().includes(query) ||
          d.device_name?.toLowerCase().includes(query) ||
          d.mac_address.toLowerCase().includes(query)
      );
    }

    // Apply status filter
    if (statusFilter) {
      result = result.filter(
        (d) => d.status.toLowerCase() === statusFilter.toLowerCase()
      );
    }

    // Apply sorting
    result.sort((a, b) => {
      let aVal: any;
      let bVal: any;

      switch (sortField) {
        case "ip":
          aVal = a.ip_address;
          bVal = b.ip_address;
          break;
        case "name":
          aVal = a.device_name || a.hostname || "";
          bVal = b.device_name || b.hostname || "";
          break;
        case "status":
          aVal = a.status;
          bVal = b.status;
          break;
        case "usage":
          aVal = a.total_bytes_sent + a.total_bytes_received;
          bVal = b.total_bytes_sent + b.total_bytes_received;
          break;
      }

      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    return result;
  }, [devices, searchQuery, statusFilter, sortField, sortDirection]);

  const handleSort = (field: "ip" | "name" | "status" | "usage") => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const clearFilters = () => {
    setSearchQuery("");
    setStatusFilter("");
  };

  const exportToCSV = () => {
    const headers = [
      "IP Address",
      "MAC Address",
      "Hostname",
      "Device Name",
      "Status",
      "Total Sent (bytes)",
      "Total Received (bytes)",
      "Total Bandwidth (MB)",
      "Threshold (Mbps)",
      "Is Blocked",
      "Is Throttled",
      "Throttle Limit (Mbps)",
      "Last Seen",
      "First Seen",
    ];

    const rows = filteredAndSortedDevices.map((d) => [
      d.ip_address,
      d.mac_address,
      d.hostname || "",
      d.device_name || "",
      d.status,
      d.total_bytes_sent,
      d.total_bytes_received,
      ((d.total_bytes_sent + d.total_bytes_received) / (1024 * 1024)).toFixed(
        2
      ),
      d.bandwidth_threshold_mbps || "",
      d.is_blocked ? "Yes" : "No",
      d.is_throttled ? "Yes" : "No",
      d.throttle_limit_mbps || "",
      d.last_seen,
      d.first_seen,
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `devices_export_${new Date().toISOString().split("T")[0]}.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToJSON = () => {
    const exportData = filteredAndSortedDevices.map((d) => ({
      ip_address: d.ip_address,
      mac_address: d.mac_address,
      hostname: d.hostname,
      device_name: d.device_name,
      status: d.status,
      total_bytes_sent: d.total_bytes_sent,
      total_bytes_received: d.total_bytes_received,
      total_bandwidth_mb: (
        (d.total_bytes_sent + d.total_bytes_received) /
        (1024 * 1024)
      ).toFixed(2),
      threshold_mbps: d.bandwidth_threshold_mbps,
      is_blocked: d.is_blocked,
      is_throttled: d.is_throttled,
      throttle_limit_mbps: d.throttle_limit_mbps,
      last_seen: d.last_seen,
      first_seen: d.first_seen,
    }));

    const jsonContent = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `devices_export_${new Date().toISOString().split("T")[0]}.json`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="devices-page blur-theme">
      <header className="page-header">
        <div>
          <h2>Devices</h2>
          {globalThreshold?.threshold_mbps && (
            <div className="global-threshold-info">
              <span className="badge badge-info">
                Global: {globalThreshold.threshold_mbps} Mbps
              </span>
              <span className="text-muted">
                ({globalThreshold.devices_using_global_threshold} of{" "}
                {globalThreshold.total_active_devices} devices)
              </span>
            </div>
          )}
        </div>
        <div className="header-actions">
          <button
            onClick={() => {
              setBulkMode(!bulkMode);
              setSelectedDeviceIds(new Set());
            }}
            className={`btn ${bulkMode ? "btn-warning" : "btn-secondary"}`}
          >
            {bulkMode ? "Exit Bulk Mode" : "Bulk Actions"}
          </button>
          <button
            onClick={() => setShowScanModal(true)}
            className="btn btn-info"
          >
            Scan Network
          </button>
          <button
            onClick={() => setShowGlobalThreshold(!showGlobalThreshold)}
            className="btn btn-secondary"
          >
            Global Threshold
          </button>
          <button onClick={() => setShowForm(true)} className="btn btn-primary">
            Add Device
          </button>
          <button onClick={exportToCSV} className="btn btn-secondary">
            Export CSV
          </button>
          <button onClick={exportToJSON} className="btn btn-secondary">
            Export JSON
          </button>
        </div>
      </header>

      {showGlobalThreshold && (
        <div className="global-threshold-panel">
          <h3>Global Bandwidth Threshold</h3>
          <p className="help-text">
            Set a bandwidth limit that applies to all devices without individual
            thresholds.
          </p>
          <ThresholdModal
            isGlobal
            globalThreshold={globalThreshold}
            onSave={handleSetGlobalThreshold}
            onRemove={handleRemoveGlobalThreshold}
            onClose={() => setShowGlobalThreshold(false)}
          />
        </div>
      )}

      <div className="filters-bar">
        <div className="filter-group">
          <label>Search</label>
          <input
            type="text"
            className="filter-input"
            placeholder="IP, hostname, MAC..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Status</label>
          <select
            className="filter-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="throttled">Throttled</option>
            <option value="blocked">Blocked</option>
            <option value="deactivated">Deactivated</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>

        {(searchQuery || statusFilter) && (
          <button onClick={clearFilters} className="clear-filters-btn">
            Clear Filters
          </button>
        )}

        <div className="filter-group" style={{ marginLeft: "auto" }}>
          <label>Sort By</label>
          <select
            className="filter-select"
            value={sortField}
            onChange={(e) => handleSort(e.target.value as any)}
          >
            <option value="ip">IP Address</option>
            <option value="name">Device Name</option>
            <option value="status">Status</option>
            <option value="usage">Bandwidth Usage</option>
          </select>
        </div>
      </div>

      {bulkMode && selectedDeviceIds.size > 0 && (
        <div className="bulk-actions-bar">
          <div className="selected-count">
            {selectedDeviceIds.size} device(s) selected
          </div>
          <div className="bulk-buttons">
            <button onClick={handleBulkDelete} className="btn btn-danger">
              Delete Selected
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading devices...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <div className="devices-info">
            Showing {filteredAndSortedDevices.length} of {devices.length}{" "}
            devices
          </div>
          <DeviceTable
            devices={filteredAndSortedDevices}
            onSelect={setSelectedDevice}
            onSetThreshold={setThresholdDevice}
            bulkMode={bulkMode}
            selectedDevices={selectedDeviceIds}
            onToggleSelect={handleToggleSelect}
            onToggleSelectAll={handleToggleSelectAll}
            onViewHistory={setHistoryDevice}
          />
        </>
      )}

      {showForm && (
        <DeviceForm
          onClose={() => setShowForm(false)}
          onSuccess={fetchDevices}
        />
      )}

      {selectedDevice && (
        <DeviceDetails
          device={selectedDevice}
          onClose={() => setSelectedDevice(null)}
        />
      )}

      {thresholdDevice && (
        <ThresholdModal
          device={thresholdDevice}
          onClose={() => setThresholdDevice(null)}
          onSuccess={fetchDevices}
        />
      )}

      {showScanModal && (
        <NetworkScanModal
          onClose={() => setShowScanModal(false)}
          onSuccess={fetchDevices}
        />
      )}

      {historyDevice && (
        <DeviceHistoryModal
          ipAddress={historyDevice.ip_address}
          deviceName={historyDevice.device_name || historyDevice.hostname}
          onClose={() => setHistoryDevice(null)}
        />
      )}
    </div>
  );
};

export default Devices;
