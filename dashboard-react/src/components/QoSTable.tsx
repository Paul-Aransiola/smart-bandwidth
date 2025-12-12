import React from "react";

export const QoSTable: React.FC<{
  qos: any[];
}> = ({ qos }) => (
  <section>
    <h3>QoS</h3>
    <table className="qos-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Value</th>
          <th>Assigned Devices</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {qos.length === 0 ? (
          <tr>
            <td colSpan={5}>No QoS found.</td>
          </tr>
        ) : (
          qos.map((q) => (
            <tr key={q.id}>
              <td>{q.name}</td>
              <td>{q.type}</td>
              <td>{q.value}</td>
              <td>{q.devices?.length || 0}</td>
              <td>
                <button className="btn btn-sm">Actions</button>
              </td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  </section>
);
