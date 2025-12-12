import React, { useEffect, useState } from "react";
import axios from "../lib/axios";
import { UserTable } from "../components/UserTable";
import { UserActions } from "../components/UserActions";
import "../styles/legacy-theme.scss";

export const Users: React.FC = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await axios.get("/users");
      setUsers(res.data.data || []);
      setError("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to fetch users");
    }
    setLoading(false);
  };

  return (
    <div className="users-page blur-theme">
      <header className="page-header">
        <h2>Users</h2>
        <button onClick={() => setShowForm(true)} className="btn btn-primary">
          Add User
        </button>
      </header>
      {loading ? (
        <div className="loading">Loading users...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <UserTable users={users} onSelect={setSelectedUser} />
      )}
      {/* User form modal can be added here */}
      {selectedUser && (
        <UserActions
          user={selectedUser}
          onClose={() => setSelectedUser(null)}
          onSuccess={fetchUsers}
        />
      )}
    </div>
  );
};

export default Users;
