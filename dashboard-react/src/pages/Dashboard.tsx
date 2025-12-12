import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Users,
  Shield,
  AlertTriangle,
  Wifi,
  Database,
  Clock,
  Zap,
} from "lucide-react";
import { Card } from "../components/Card";
import { StatCard } from "../components/StatCard";
import { Badge } from "../components/Badge";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

interface DashboardStats {
  total_devices: number;
  active_devices: number;
  blocked_devices: number;
  total_bandwidth: number;
  total_bandwidth_sent: number;
  total_bandwidth_received: number;
  average_bandwidth_per_device: number;
}

interface TopConsumer {
  id: number;
  ip_address: string;
  device_name: string;
  total_bytes: number;
  total_bytes_sent: number;
  total_bytes_received: number;
}

interface ProtocolStats {
  [key: string]: number;
}

interface ApplicationStats {
  [key: string]: number;
}

interface TrendData {
  value: number;
  is_positive: boolean;
}

interface Trends {
  total_devices?: TrendData;
  active_devices?: TrendData;
  total_bandwidth?: TrendData;
  average_bandwidth_per_device?: TrendData;
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<Trends | null>(null);
  const [topConsumers, setTopConsumers] = useState<TopConsumer[]>([]);
  const [protocols, setProtocols] = useState<ProtocolStats>({});
  const [applications, setApplications] = useState<ApplicationStats>({});
  const [loading, setLoading] = useState(true);
  const [realtimeData, setRealtimeData] = useState<any[]>([]);
  const [wsConnected, setWsConnected] = useState(false);

  // Format bytes to human readable
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch all dashboard data from single endpoint
        const response = await axios.get("/api/v1/dashboard/overview");
        const dashboardData = response.data.data;

        // Set all state from the aggregated response
        setStats(dashboardData.statistics);
        setTrends(dashboardData.trends || null);
        setTopConsumers(dashboardData.top_consumers || []);
        setProtocols(dashboardData.protocols);
        setApplications(dashboardData.applications);

        // Set bandwidth history from backend
        if (
          dashboardData.bandwidth_history &&
          dashboardData.bandwidth_history.length > 0
        ) {
          console.log(
            "Initial bandwidth history from API:",
            dashboardData.bandwidth_history
          );
          setRealtimeData(dashboardData.bandwidth_history);
        } else {
          // Initialize with current stats if no history yet
          console.log(
            "No bandwidth history from API, initializing with current stats"
          );
          const currentTime = new Date().toLocaleTimeString("en-US", {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
          setRealtimeData([
            {
              time: currentTime,
              bandwidth: 0,
              devices: dashboardData.statistics?.active_devices || 0,
            },
          ]);
        }
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        // Don't set static fallback data - just log the error
        // The backend should provide live data even on partial failure
      } finally {
        setLoading(false);
      }
    };

    // WebSocket connection for real-time updates
    let ws: WebSocket | null = null;
    let reconnectTimeout: NodeJS.Timeout;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;

    const connectWebSocket = () => {
      // Stop reconnecting after max attempts
      if (reconnectAttempts >= maxReconnectAttempts) {
        console.log("Max reconnection attempts reached");
        setWsConnected(false);
        return;
      }

      const wsUrl = `ws://localhost:8000/api/v1/ws/stats`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected");
        setWsConnected(true);
        reconnectAttempts = 0; // Reset on successful connection

        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 30000);

        // Store interval ID on ws object for cleanup
        (ws as any).pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log("WebSocket message received:", message);

          if (message.type === "bandwidth_stats") {
            // Update real-time data from WebSocket
            const data = message.data;
            console.log("Bandwidth stats data:", data);

            // Add new bandwidth history point and maintain max 20 points
            if (data.bandwidth_history && data.bandwidth_history.length > 0) {
              console.log("Adding bandwidth history:", data.bandwidth_history);
              setRealtimeData((prev) => {
                const newData = [...prev, ...data.bandwidth_history];
                console.log("New realtime data array:", newData);
                // Keep only last 20 data points for the chart
                return newData.slice(-20);
              });
            }

            if (data.protocols) {
              setProtocols(data.protocols);
            }

            // Update stats with real-time values
            if (
              data.active_devices !== undefined ||
              data.total_devices !== undefined
            ) {
              console.log(
                "Updating stats - active:",
                data.active_devices,
                "total:",
                data.total_devices
              );
              setStats((prev) => ({
                ...prev!,
                active_devices:
                  data.active_devices ?? prev?.active_devices ?? 0,
                total_devices: data.total_devices ?? prev?.total_devices ?? 0,
              }));
            }
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setWsConnected(false);
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setWsConnected(false);

        // Clear ping interval
        if ((ws as any)?.pingInterval) {
          clearInterval((ws as any).pingInterval);
        }

        // Attempt to reconnect after 5 seconds (with limit)
        reconnectAttempts++;
        if (reconnectAttempts < maxReconnectAttempts) {
          console.log(`Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`);
          reconnectTimeout = setTimeout(connectWebSocket, 5000);
        }
      };
    };

    // Initial data fetch
    fetchDashboardData();

    // Connect WebSocket for real-time updates
    connectWebSocket();

    // Fallback: Refresh full dashboard data every 30 seconds
    // (WebSocket handles real-time bandwidth/protocol updates)
    const refreshInterval = setInterval(() => {
      fetchDashboardData();
    }, 30000);

    return () => {
      clearInterval(refreshInterval);
      clearTimeout(reconnectTimeout);
      if (ws) {
        if ((ws as any).pingInterval) {
          clearInterval((ws as any).pingInterval);
        }
        ws.close();
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  // Prepare chart data
  const protocolData = Object.entries(protocols || {}).map(([name, value]) => ({
    name,
    value,
  }));

  const applicationData = Object.entries(applications || {}).map(
    ([name, value]) => ({
      name,
      value,
    })
  );

  const COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-3">
            <Activity className="text-emerald-500" size={32} />
            Dashboard
          </h1>
          <p className="text-slate-600 mt-1">
            Real-time network monitoring and analytics
          </p>
        </div>

        {/* WebSocket Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100">
          <div
            className={`w-2 h-2 rounded-full ${
              wsConnected ? "bg-emerald-500 animate-pulse" : "bg-slate-400"
            }`}
          />
          <span className="text-sm text-slate-600">
            {wsConnected ? "Live" : "Reconnecting..."}
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Devices"
          value={stats?.total_devices || 0}
          icon={<Wifi className="text-emerald-500" size={24} />}
          trend={
            trends?.total_devices
              ? {
                  value: trends.total_devices.value,
                  isPositive: trends.total_devices.is_positive,
                }
              : undefined
          }
          subtitle={`${stats?.active_devices || 0} active`}
        />

        <StatCard
          title="Total Bandwidth"
          value={formatBytes(stats?.total_bandwidth || 0)}
          icon={<Database className="text-blue-500" size={24} />}
          trend={
            trends?.total_bandwidth
              ? {
                  value: trends.total_bandwidth.value,
                  isPositive: trends.total_bandwidth.is_positive,
                }
              : undefined
          }
          subtitle="Since monitoring started"
        />

        <StatCard
          title="Active Devices"
          value={stats?.active_devices || 0}
          icon={<Zap className="text-amber-500" size={24} />}
          trend={
            trends?.active_devices
              ? {
                  value: trends.active_devices.value,
                  isPositive: trends.active_devices.is_positive,
                }
              : undefined
          }
          subtitle={`${stats?.blocked_devices || 0} blocked`}
        />

        <StatCard
          title="Avg per Device"
          value={formatBytes(stats?.average_bandwidth_per_device || 0)}
          icon={<TrendingUp className="text-purple-500" size={24} />}
          trend={
            trends?.average_bandwidth_per_device
              ? {
                  value: trends.average_bandwidth_per_device.value,
                  isPositive: trends.average_bandwidth_per_device.is_positive,
                }
              : undefined
          }
          subtitle="Per device usage"
        />
      </div>

      {/* Real-time Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-time Bandwidth */}
        <Card variant="default">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                  <Activity className="text-emerald-500" size={20} />
                  Real-time Bandwidth
                </h3>
                <p className="text-sm text-slate-600 mt-1">
                  Live network usage (Mbps)
                </p>
              </div>
              <Badge variant="success">
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                  Live
                </span>
              </Badge>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={realtimeData}>
                <defs>
                  <linearGradient
                    id="bandwidthGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="bandwidth"
                  stroke="#10b981"
                  strokeWidth={2}
                  fill="url(#bandwidthGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Active Devices Timeline */}
        <Card variant="default">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                  <Users className="text-blue-500" size={20} />
                  Active Devices
                </h3>
                <p className="text-sm text-slate-600 mt-1">
                  Connected device count
                </p>
              </div>
              <Badge variant="info">Real-time</Badge>
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={realtimeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="devices"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Protocol & Application Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Protocol Distribution */}
        <Card variant="default">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                  <Shield className="text-purple-500" size={20} />
                  Protocol Distribution
                </h3>
                <p className="text-sm text-slate-600 mt-1">
                  Network protocol breakdown
                </p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={protocolData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {protocolData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Application Usage */}
        <Card variant="default">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                  <Database className="text-emerald-500" size={20} />
                  Application Usage
                </h3>
                <p className="text-sm text-slate-600 mt-1">
                  Top application types
                </p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={applicationData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#64748b", fontSize: 12 }}
                />
                <YAxis tick={{ fill: "#64748b", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                  }}
                />
                <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Top Consumers Table */}
      <Card variant="default">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <TrendingUp className="text-amber-500" size={20} />
                Top Bandwidth Consumers
              </h3>
              <p className="text-sm text-slate-600 mt-1">
                Highest usage devices in your network
              </p>
            </div>
            <Badge variant="warning">Top 5</Badge>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                    Rank
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                    Device
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-slate-700">
                    IP Address
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-slate-700">
                    Total Usage
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-slate-700">
                    Sent
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-slate-700">
                    Received
                  </th>
                </tr>
              </thead>
              <tbody>
                {topConsumers?.map((device, index) => (
                  <tr
                    key={device.id}
                    className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <span className="text-slate-600 font-medium">
                        #{index + 1}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-slate-800">
                        {device.device_name}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <code className="text-sm text-slate-600 bg-slate-100 px-2 py-1 rounded">
                        {device.ip_address}
                      </code>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="font-semibold text-slate-800">
                        {formatBytes(device.total_bytes)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-slate-600">
                      {formatBytes(device.total_bytes_sent)}
                    </td>
                    <td className="py-3 px-4 text-right text-slate-600">
                      {formatBytes(device.total_bytes_received)}
                    </td>
                  </tr>
                ))}
                {(!topConsumers || topConsumers.length === 0) && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500">
                      No data available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </Card>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card variant="success">
          <div className="p-6">
            <div className="flex items-center gap-4">
              <div className="bg-emerald-100 p-3 rounded-lg">
                <Shield className="text-emerald-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-slate-600">Network Status</p>
                <p className="text-xl font-bold text-slate-800">Healthy</p>
              </div>
            </div>
          </div>
        </Card>

        <Card variant="warning">
          <div className="p-6">
            <div className="flex items-center gap-4">
              <div className="bg-amber-100 p-3 rounded-lg">
                <AlertTriangle className="text-amber-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-slate-600">Active Alerts</p>
                <p className="text-xl font-bold text-slate-800">
                  {stats?.blocked_devices || 0}
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card variant="info">
          <div className="p-6">
            <div className="flex items-center gap-4">
              <div className="bg-blue-100 p-3 rounded-lg">
                <Clock className="text-blue-600" size={24} />
              </div>
              <div>
                <p className="text-sm text-slate-600">Uptime</p>
                <p className="text-xl font-bold text-slate-800">99.9%</p>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
