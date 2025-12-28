import axios from "axios";

// Create axios instance
const axiosInstance = axios.create({
  baseURL: "",
});

// Request interceptor to add auth token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    console.log("[Axios Interceptor] Token from localStorage:", token ? "EXISTS" : "MISSING");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log("[Axios Interceptor] Added Authorization header");
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle 401 errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      const isAuthPage = currentPath.includes("/login") || currentPath.includes("/register");
      
      // If unauthorized and not on auth page, redirect to login
      if (!isAuthPage) {
        console.log("[Axios Interceptor] 401 detected, redirecting to login");
        localStorage.removeItem("token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
