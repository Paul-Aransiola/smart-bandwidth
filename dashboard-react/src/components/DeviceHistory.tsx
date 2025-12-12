import React from "react";

export const DeviceHistory: React.FC<{
  history: any[];
}> = ({ history }) => (
  <div className="device-history">
    <h4>Device History</h4>
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Action</th>
          <th>User</th>
        </tr>
      </thead>
      <tbody>
        {history.length === 0 ? (
          <tr>
            <td colSpan={3}>No history found.</td>
          </tr>
        ) : (
          history.map((h, idx) => (
            <tr key={idx}>
              <td>{h.timestamp}</td>
              <td>{h.action}</td>
              <td>{h.user}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  </div>
);
