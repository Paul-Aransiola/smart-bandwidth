import React from "react";

export const ThrottleScheduleTable: React.FC<{
  schedules: any[];
}> = ({ schedules }) => (
  <section>
    <h3>Throttle Schedules</h3>
    <table className="throttle-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Start</th>
          <th>End</th>
          <th>Rate</th>
          <th>Assigned Devices</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {schedules.length === 0 ? (
          <tr>
            <td colSpan={6}>No schedules found.</td>
          </tr>
        ) : (
          schedules.map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.start}</td>
              <td>{s.end}</td>
              <td>{s.rate}</td>
              <td>{s.devices?.length || 0}</td>
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
