import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import { AuditLogTable } from "../components/AuditLogTable";
import "../styles/legacy-theme.scss";

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/audit-logs", { params: { search } });
      setLogs(res.data.data || []);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch audit logs");
    }
    setLoading(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  return (
    <div className="audit-logs-page blur-theme">
      <header className="page-header">
        <h2>Audit Logs</h2>
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search logs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
      </header>
      {loading ? (
        <div className="loading">Loading logs...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <AuditLogTable logs={logs} />
      )}
    </div>
  );
};

export default AuditLogs;
