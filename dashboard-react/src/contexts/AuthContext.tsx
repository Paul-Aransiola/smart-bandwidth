import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "../lib/axios";

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if token exists and fetch user profile
    const token = localStorage.getItem("token");
    if (token) {
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async () => {
    try {
      console.log("[AuthContext] Fetching user profile...");
      const response = await axios.get("/api/v1/auth/profile");
      console.log("[AuthContext] Profile fetched:", response.data);
      setUser(response.data);
      setLoading(false);
    } catch (error: any) {
      console.error(
        "[AuthContext] Failed to fetch user profile:",
        error.response?.status
      );
      // Token might be invalid, clear it
      localStorage.removeItem("token");
      setUser(null);
      setLoading(false);
      // Don't redirect here, let the interceptor handle it
    }
  };

  const login = async (token: string) => {
    console.log("[AuthContext] login() called with token:", token);
    localStorage.setItem("token", token);
    console.log(
      "[AuthContext] Token stored in localStorage:",
      localStorage.getItem("token")
    );
    await fetchUserProfile();
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
