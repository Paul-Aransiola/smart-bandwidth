import React from "react";

export const AuditLogTable: React.FC<{
  logs: any[];
}> = ({ logs }) => (
  <table className="audit-log-table">
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>User</th>
        <th>Action</th>
        <th>Resource</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {logs.length === 0 ? (
        <tr>
          <td colSpan={5}>No logs found.</td>
        </tr>
      ) : (
        logs.map((log, idx) => (
          <tr key={idx}>
            <td>{log.timestamp}</td>
            <td>{log.user}</td>
            <td>{log.action}</td>
            <td>{log.resource}</td>
            <td>{log.status}</td>
          </tr>
        ))
      )}
    </tbody>
  </table>
);
