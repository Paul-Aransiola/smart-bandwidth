export interface Device {
  id: number;
  ip_address: string;
  mac_address: string;
  hostname: string;
  device_name?: string;
  status: 'active' | 'throttled' | 'blocked' | 'deactivated' | 'inactive';
  device_type?: string;
  manufacturer?: string;
  os_type?: string;
  first_seen: string;
  last_seen: string;
  total_bytes_sent: number;
  total_bytes_received: number;
  is_blocked: boolean;
  is_throttled: boolean;
  throttle_limit_mbps?: number;
  
  // Bandwidth threshold fields
  bandwidth_threshold_mbps?: number;
  auto_deactivate_on_threshold?: boolean;
  threshold_time_window_minutes?: number;
  threshold_breach_count?: number;
  last_threshold_breach?: string;
}

export interface ThresholdStatus {
  device_id: number;
  device_hostname: string;
  device_ip: string;
  threshold_configured: boolean;
  current_usage_mbps: number;
  threshold_mbps?: number;
  time_window_minutes?: number;
  threshold_breached: boolean;
  auto_deactivate_enabled: boolean;
  breach_count: number;
  last_breach?: string;
}

export interface GlobalThreshold {
  threshold_mbps?: number;
  auto_deactivate: boolean;
  time_window_minutes: number;
  devices_using_global_threshold: number;
  total_active_devices: number;
}

export interface ThresholdSettings {
  threshold_mbps: number;
  auto_deactivate: boolean;
  time_window_minutes: number;
}
