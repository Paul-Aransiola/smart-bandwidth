import axios from 'axios';
import type { ThresholdSettings, ThresholdStatus, GlobalThreshold } from '../types/device';

const API_BASE = '/api/v1/threshold';

export const thresholdService = {
  // Device-specific threshold operations
  async setDeviceThreshold(deviceId: number, settings: ThresholdSettings) {
    const params = new URLSearchParams({
      threshold_mbps: settings.threshold_mbps.toString(),
      auto_deactivate: settings.auto_deactivate.toString(),
      time_window_minutes: settings.time_window_minutes.toString(),
    });
    const response = await axios.post(`${API_BASE}/devices/${deviceId}/set?${params}`);
    return response.data;
  },

  async getDeviceThresholdStatus(deviceId: number): Promise<ThresholdStatus> {
    const response = await axios.get(`${API_BASE}/devices/${deviceId}/status`);
    return response.data.data;
  },

  async checkDeviceThreshold(deviceId: number) {
    const response = await axios.post(`${API_BASE}/devices/${deviceId}/check`);
    return response.data;
  },

  async removeDeviceThreshold(deviceId: number) {
    const response = await axios.delete(`${API_BASE}/devices/${deviceId}`);
    return response.data;
  },

  async reactivateDevice(deviceId: number, resetBreachCount: boolean = false) {
    const params = new URLSearchParams({
      reset_breach_count: resetBreachCount.toString(),
    });
    const response = await axios.post(`${API_BASE}/devices/${deviceId}/reactivate?${params}`);
    return response.data;
  },

  async listDevicesWithThresholds() {
    const response = await axios.get(`${API_BASE}/devices`);
    return response.data.data;
  },

  // Global threshold operations
  async getGlobalThreshold(): Promise<GlobalThreshold> {
    const response = await axios.get(`${API_BASE}/global`);
    return response.data.data;
  },

  async setGlobalThreshold(settings: ThresholdSettings) {
    const params = new URLSearchParams({
      threshold_mbps: settings.threshold_mbps.toString(),
      auto_deactivate: settings.auto_deactivate.toString(),
      time_window_minutes: settings.time_window_minutes.toString(),
    });
    const response = await axios.post(`${API_BASE}/global/set?${params}`);
    return response.data;
  },

  async removeGlobalThreshold() {
    const response = await axios.delete(`${API_BASE}/global`);
    return response.data;
  },
};
