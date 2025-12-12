import React, { useState } from "react";
import axios from "../lib/axios";

export const UserActions: React.FC<{
  user: any;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ user, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAction = async (action: string) => {
    setLoading(true);
    setError("");
    try {
      await axios.post(`/users/${user.id}/${action}`);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${action} user`);
    }
    setLoading(false);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h3>User Actions</h3>
        <ul>
          <li>
            <strong>Username:</strong> {user.username}
          </li>
          <li>
            <strong>Email:</strong> {user.email}
          </li>
          <li>
            <strong>Role:</strong> {user.role}
          </li>
          <li>
            <strong>Status:</strong> {user.status}
          </li>
        </ul>
        <button onClick={() => handleAction("activate")} disabled={loading}>
          Activate
        </button>
        <button onClick={() => handleAction("deactivate")} disabled={loading}>
          Deactivate
        </button>
        <button onClick={() => handleAction("delete")} disabled={loading}>
          Delete
        </button>
        <button onClick={onClose}>Close</button>
        {error && <div className="error">{error}</div>}
      </div>
    </div>
  );
};
