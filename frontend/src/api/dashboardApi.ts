import axios from 'axios';
import { DashboardMetrics } from '../types/dashboard';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const dashboardHttpClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/dashboard`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  getMetrics: async (): Promise<DashboardMetrics> => {
    const response = await dashboardHttpClient.get<DashboardMetrics>('/metrics');
    return response.data;
  },
};
