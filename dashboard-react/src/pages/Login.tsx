import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "../lib/axios";
import { useAuth } from "../contexts/AuthContext";
import { Lock, User, AlertCircle } from "lucide-react";

export const Login: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      console.log("[Login] Attempting login...");
      const response = await axios.post("/api/v1/auth/login", {
        username,
        password,
      });

      console.log("[Login] Login response:", response.data);
      console.log("[Login] Token:", response.data.access_token);

      // Use AuthContext login to store token and fetch user profile
      await login(response.data.access_token);

      console.log(
        "[Login] After login, token in localStorage:",
        localStorage.getItem("token")
      );

      // Redirect to dashboard
      navigate("/dashboard");
    } catch (err: any) {
      console.error("[Login] Login failed:", err);
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-emerald-100 p-4">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-emerald-500 mb-2 ">
            Smart Bandwidth
          </h1>
          <p className="text-emerald-600">Network Monitoring & Control</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-emerald-500 mb-6">Sign In</h2>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-emerald-400 mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="text-emerald-400" size={20} />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-emerald-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                  placeholder="Enter your username"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-emerald-400 mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="text-emerald-400" size={20} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-emerald-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-emerald-500 text-white py-3 rounded-lg font-medium hover:bg-emerald-600 transition-colors disabled:bg-emerald-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Signing in...</span>
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-slate-600 text-sm">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="text-emerald-500 hover:text-emerald-700 font-medium"
              >
                Create one
              </Link>
            </p>
          </div>
        </div>

        {/* Skip Login */}
        <div className="mt-4 text-center">
          <button
            onClick={() => navigate("/dashboard")}
            className="text-sm text-emerald-500 hover:text-emerald-700"
          >
            Continue without authentication
          </button>
        </div>
      </div>
    </div>
  );
};

export default Login;
