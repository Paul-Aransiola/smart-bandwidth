import React from "react";

export const QuotaTable: React.FC<{
  quotas: any[];
}> = ({ quotas }) => (
  <section>
    <h3>Quotas</h3>
    <table className="quota-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Limit</th>
          <th>Assigned Devices</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {quotas.length === 0 ? (
          <tr>
            <td colSpan={4}>No quotas found.</td>
          </tr>
        ) : (
          quotas.map((quota) => (
            <tr key={quota.id}>
              <td>{quota.name}</td>
              <td>{quota.limit}</td>
              <td>{quota.devices?.length || 0}</td>
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
