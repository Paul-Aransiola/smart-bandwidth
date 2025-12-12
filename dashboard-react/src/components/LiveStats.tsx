import React from "react";

export const LiveStats: React.FC<{
  stats: any[];
}> = ({ stats }) => (
  <section>
    <h3>Live Stats</h3>
    {/* Replace with chart/graph integration as needed */}
    <table className="live-stats-table">
      <thead>
        <tr>
          <th>Metric</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        {stats.length === 0 ? (
          <tr>
            <td colSpan={2}>No live stats available.</td>
          </tr>
        ) : (
          stats.map((stat, idx) => (
            <tr key={idx}>
              <td>{stat.metric}</td>
              <td>{stat.value}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  </section>
);
