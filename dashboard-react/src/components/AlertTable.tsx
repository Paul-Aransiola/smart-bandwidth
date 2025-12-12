import React from "react";

export const AlertTable: React.FC<{
  alerts: any[];
  onSelect: (alert: any) => void;
}> = ({ alerts, onSelect }) => (
  <table className="alert-table">
    <thead>
      <tr>
        <th>Rule Name</th>
        <th>Type</th>
        <th>Status</th>
        <th>Enabled</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {alerts.length === 0 ? (
        <tr>
          <td colSpan={5}>No alerts found.</td>
        </tr>
      ) : (
        alerts.map((alert) => (
          <tr key={alert.id} onClick={() => onSelect(alert)}>
            <td>{alert.rule_name}</td>
            <td>{alert.type}</td>
            <td>{alert.status}</td>
            <td>{alert.enabled ? "Yes" : "No"}</td>
            <td>
              <button className="btn btn-sm">Actions</button>
            </td>
          </tr>
        ))
      )}
    </tbody>
  </table>
);
