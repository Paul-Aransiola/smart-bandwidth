import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import { ReportTable } from "../components/ReportTable";
import { TrendChart } from "../components/TrendChart";
import { TopConsumersTable } from "../components/TopConsumersTable";
import { Card, CardHeader, CardBody, CardTitle } from "../components/Card";
import { Button } from "../components/Button";
import { StatCard } from "../components/StatCard";
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export const Reports: React.FC = () => {
  const [reports, setReports] = useState([]);
  const [trends, setTrends] = useState([]);
  const [topConsumers, setTopConsumers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const [stats, setStats] = useState({
    totalBandwidth: "0 GB",
    activeDevices: 0,
    avgUsage: "0 MB",
    peakTime: "N/A",
  });

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    setLoading(true);
    try {
      const [reportsRes, trendsRes, consumersRes] = await Promise.all([
        axios.get("/api/reports", { params: { filter } }),
        axios.get("/api/trends", { params: { filter } }),
        axios.get("/api/top-consumers", { params: { filter } }),
      ]);
      setReports(reportsRes.data.data || []);
      setTrends(trendsRes.data.data || []);
      setTopConsumers(consumersRes.data.data || []);

      // Calculate stats from data
      if (reportsRes.data.data && reportsRes.data.data.length > 0) {
        // Add your stats calculation logic here
      }

      setError("");
    } catch (err: any) {
      console.log("Using sample data for demonstration");
      // Use sample data for demonstration
      setTrends([
        { label: "Mon", value: 45 },
        { label: "Tue", value: 52 },
        { label: "Wed", value: 48 },
        { label: "Thu", value: 65 },
        { label: "Fri", value: 58 },
        { label: "Sat", value: 42 },
        { label: "Sun", value: 38 },
      ]);
    }
    setLoading(false);
  };

  const handleFilter = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAll();
  };

  // Sample data for device type distribution
  const deviceTypeData = [
    { name: "Mobile", value: 35, color: "#10b981" },
    { name: "Desktop", value: 30, color: "#3b82f6" },
    { name: "Tablet", value: 20, color: "#f59e0b" },
    { name: "IoT", value: 15, color: "#8b5cf6" },
  ];

  // Sample data for bandwidth by time
  const bandwidthByHour = [
    { hour: "00:00", bandwidth: 25 },
    { hour: "04:00", bandwidth: 15 },
    { hour: "08:00", bandwidth: 55 },
    { hour: "12:00", bandwidth: 85 },
    { hour: "16:00", bandwidth: 95 },
    { hour: "20:00", bandwidth: 75 },
  ];

  return (
    <div className="p-8 space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            📊 Reports & Statistics
          </h1>
          <p className="text-slate-600 mt-1">
            Comprehensive network usage analytics and insights
          </p>
        </div>
        <form onSubmit={handleFilter} className="flex gap-2">
          <input
            type="text"
            placeholder="Filter by device or type..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="input"
            style={{ width: "300px" }}
          />
          <Button type="submit" variant="primary">
            🔍 Apply Filter
          </Button>
        </form>
      </div>

      {loading ? (
        <Card>
          <CardBody>
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
              <p className="mt-4 text-slate-600">Loading reports...</p>
            </div>
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Bandwidth"
              value={stats.totalBandwidth}
              icon="📡"
              trend="up"
              change="+12.5%"
            />
            <StatCard
              title="Active Devices"
              value={stats.activeDevices.toString()}
              icon="📱"
              trend="up"
              change="+3"
            />
            <StatCard
              title="Avg Usage"
              value={stats.avgUsage}
              icon="📊"
              trend="down"
              change="-5.2%"
            />
            <StatCard title="Peak Time" value={stats.peakTime} icon="⏰" />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Bandwidth by Time */}
            <Card>
              <CardHeader>
                <CardTitle>📈 Bandwidth Usage by Time</CardTitle>
              </CardHeader>
              <CardBody>
                <div style={{ width: "100%", height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={bandwidthByHour}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis
                        dataKey="hour"
                        stroke="#64748b"
                        style={{ fontSize: "12px" }}
                      />
                      <YAxis stroke="#64748b" style={{ fontSize: "12px" }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#fff",
                          border: "1px solid #e2e8f0",
                          borderRadius: "8px",
                          boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                        }}
                      />
                      <Bar
                        dataKey="bandwidth"
                        fill="#10b981"
                        radius={[8, 8, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>

            {/* Device Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>🔄 Device Type Distribution</CardTitle>
              </CardHeader>
              <CardBody>
                <div style={{ width: "100%", height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={deviceTypeData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) =>
                          `${name} ${(percent * 100).toFixed(0)}%`
                        }
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {deviceTypeData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardBody>
            </Card>
          </div>

          {/* Trend Chart */}
          <TrendChart trends={trends} />

          {/* Tables Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TopConsumersTable consumers={topConsumers} />
            <ReportTable reports={reports} />
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;
