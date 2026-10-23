import axios from 'axios';
import { LoginRequest, TokenResponse, User, MessageResponse } from '../types/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/auth`,
  withCredentials: true, // Garante que Cookies HttpOnly sejam gravados e enviados automaticamente
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authApi = {
  login: async (credentials: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/login', credentials);
    return response.data;
  },

  refresh: async (): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/refresh');
    return response.data;
  },

  logout: async (): Promise<MessageResponse> => {
    const response = await api.post<MessageResponse>('/logout');
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await api.get<User>('/me');
    return response.data;
  },
};
