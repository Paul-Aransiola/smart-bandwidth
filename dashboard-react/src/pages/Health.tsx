import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import { Card, CardHeader, CardBody, CardTitle } from "../components/Card";
import { StatCard } from "../components/StatCard";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface HealthData {
  status: string;
  version: string;
  uptime: number;
  services: {
    database: string;
    cache: string;
    api: string;
  };
}

export const Health: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Sample performance data
  const [performanceData] = useState([
    { time: "12:00", cpu: 45, memory: 62, network: 38 },
    { time: "12:05", cpu: 52, memory: 64, network: 42 },
    { time: "12:10", cpu: 48, memory: 66, network: 55 },
    { time: "12:15", cpu: 61, memory: 68, network: 48 },
    { time: "12:20", cpu: 55, memory: 65, network: 52 },
    { time: "12:25", cpu: 58, memory: 70, network: 45 },
    { time: "12:30", cpu: 50, memory: 67, network: 58 },
  ]);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(() => {
      fetchHealth();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await axios.get("/health");
      setHealth(res.data.data || null);
      setLastUpdated(new Date());
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch health status");
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === "healthy" || status === "online") {
      return <Badge variant="success">● Online</Badge>;
    }
    if (status === "warning") {
      return <Badge variant="warning">⚠ Warning</Badge>;
    }
    return <Badge variant="danger">● Offline</Badge>;
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
          <p className="mt-4 text-slate-600">Loading health status...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardBody>
          <div className="flex items-center gap-3">
            <svg
              className="w-6 h-6 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <p className="font-semibold text-red-900">
                Error Loading Health Status
              </p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">System Health</h2>
          <p className="text-sm text-slate-600 mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <Button onClick={fetchHealth} size="sm">
          <svg
            className="w-4 h-4 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </Button>
      </div>

      {/* Overall Status Card */}
      <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 border-none">
        <CardBody>
          <div className="flex items-center justify-between text-white">
            <div>
              <h3 className="text-lg font-semibold opacity-90">
                System Status
              </h3>
              <p className="text-3xl font-bold mt-2">
                {health?.status || "Unknown"}
              </p>
              <p className="text-emerald-100 mt-1">All systems operational</p>
            </div>
            <div className="text-6xl opacity-20">
              <svg
                className="w-24 h-24"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
              </svg>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="System Uptime"
          value={health?.uptime ? formatUptime(health.uptime) : "N/A"}
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          }
          trend="up"
          change={99.9}
          changeLabel="uptime"
        />

        <StatCard
          title="API Version"
          value={health?.version || "N/A"}
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
          }
        />

        <StatCard
          title="Active Connections"
          value="156"
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          }
          trend="up"
          change={12}
          changeLabel="vs yesterday"
        />

        <StatCard
          title="Response Time"
          value="23ms"
          icon={
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          }
          trend="down"
          change={-15}
          changeLabel="improvement"
        />
      </div>

      {/* Services Status */}
      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            {health?.services &&
              Object.entries(health.services).map(([service, status]) => (
                <div
                  key={service}
                  className="flex items-center justify-between p-4 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        status === "online" || status === "healthy"
                          ? "bg-green-500"
                          : "bg-red-500"
                      }`}
                    ></div>
                    <div>
                      <p className="font-medium text-slate-900 capitalize">
                        {service}
                      </p>
                      <p className="text-sm text-slate-600">
                        Service is operational
                      </p>
                    </div>
                  </div>
                  {getStatusBadge(status)}
                </div>
              ))}
          </div>
        </CardBody>
      </Card>

      {/* System Metrics Chart */}
      <Card>
        <CardHeader>
          <CardTitle>📊 Performance Metrics</CardTitle>
        </CardHeader>
        <CardBody>
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={performanceData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="time"
                  stroke="#64748b"
                  style={{ fontSize: "12px" }}
                />
                <YAxis
                  stroke="#64748b"
                  style={{ fontSize: "12px" }}
                  label={{
                    value: "Usage (%)",
                    angle: -90,
                    position: "insideLeft",
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#fff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "8px",
                    boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="CPU"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Memory"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="network"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  name="Network"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-emerald-50 rounded-lg">
              <div className="flex items-center justify-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                <span className="text-sm font-medium text-slate-700">CPU</span>
              </div>
              <p className="text-2xl font-bold text-emerald-600">50%</p>
              <p className="text-xs text-slate-500">Average</p>
            </div>
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-sm font-medium text-slate-700">
                  Memory
                </span>
              </div>
              <p className="text-2xl font-bold text-blue-600">66%</p>
              <p className="text-xs text-slate-500">Average</p>
            </div>
            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <div className="flex items-center justify-center gap-2 mb-1">
                <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                <span className="text-sm font-medium text-slate-700">
                  Network
                </span>
              </div>
              <p className="text-2xl font-bold text-amber-600">48%</p>
              <p className="text-xs text-slate-500">Average</p>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
};

export default Health;
