import React from "react";

export const HealthStatus: React.FC<{
  health: any;
}> = ({ health }) => (
  <section>
    <h3>API Health</h3>
    {health ? (
      <ul>
        <li>
          <strong>Status:</strong> {health.status}
        </li>
        <li>
          <strong>Uptime:</strong> {health.uptime}
        </li>
        <li>
          <strong>Version:</strong> {health.version}
        </li>
        {/* Add more health details as needed */}
      </ul>
    ) : (
      <div>No health data available.</div>
    )}
  </section>
);
