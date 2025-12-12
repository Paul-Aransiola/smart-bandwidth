import React, { useState } from "react";
import axios from "../lib/axios";
import "../styles/legacy-theme.scss";

export const Auth: React.FC = () => {
  const [view, setView] = useState<"login" | "register" | "reset">("login");
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
  });
  const [message, setMessage] = useState<string>("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await axios.post("/auth/login", {
        username: form.username,
        password: form.password,
      });
      setMessage("Login successful!");
      // Save token, redirect, etc.
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "Login failed");
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post("/auth/register", {
        username: form.username,
        email: form.email,
        password: form.password,
      });
      setMessage("Registration successful!");
      setView("login");
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "Registration failed");
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post("/auth/reset-password", { email: form.email });
      setMessage("Password reset token sent to email.");
    } catch (err: any) {
      setMessage(err.response?.data?.detail || "Reset failed");
    }
  };

  return (
    <div className="auth-page blur-theme">
      <div className="auth-card">
        <div className="auth-tabs">
          <button onClick={() => setView("login")}>Login</button>
          <button onClick={() => setView("register")}>Register</button>
          <button onClick={() => setView("reset")}>Reset Password</button>
        </div>
        {view === "login" && (
          <form onSubmit={handleLogin} className="auth-form">
            <input
              name="username"
              placeholder="Username"
              value={form.username}
              onChange={handleChange}
            />
            <input
              name="password"
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={handleChange}
            />
            <button type="submit">Login</button>
          </form>
        )}
        {view === "register" && (
          <form onSubmit={handleRegister} className="auth-form">
            <input
              name="username"
              placeholder="Username"
              value={form.username}
              onChange={handleChange}
            />
            <input
              name="email"
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={handleChange}
            />
            <input
              name="password"
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={handleChange}
            />
            <button type="submit">Register</button>
          </form>
        )}
        {view === "reset" && (
          <form onSubmit={handleReset} className="auth-form">
            <input
              name="email"
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={handleChange}
            />
            <button type="submit">Reset Password</button>
          </form>
        )}
        {message && <div className="auth-message">{message}</div>}
      </div>
    </div>
  );
};
