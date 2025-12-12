import React from "react";

export const UserTable: React.FC<{
  users: any[];
  onSelect: (user: any) => void;
}> = ({ users, onSelect }) => (
  <table className="user-table">
    <thead>
      <tr>
        <th>Username</th>
        <th>Email</th>
        <th>Role</th>
        <th>Status</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {users.length === 0 ? (
        <tr>
          <td colSpan={5}>No users found.</td>
        </tr>
      ) : (
        users.map((user) => (
          <tr key={user.id} onClick={() => onSelect(user)}>
            <td>{user.username}</td>
            <td>{user.email}</td>
            <td>{user.role}</td>
            <td>{user.status}</td>
            <td>
              <button className="btn btn-sm">Actions</button>
            </td>
          </tr>
        ))
      )}
    </tbody>
  </table>
);
