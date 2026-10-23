import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginRequest } from '../types/auth';
import { authApi } from '../api/authApi';
import axios from 'axios';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  rateLimitBlocked: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [rateLimitBlocked, setRateLimitBlocked] = useState<boolean>(false);

  const checkAuth = async () => {
    try {
      const currentUser = await authApi.getMe();
      setUser(currentUser);
    } catch {
      // Se não autenticado ou token expirado, tenta renovar via refresh token
      try {
        const refreshResponse = await authApi.refresh();
        setUser(refreshResponse.user);
      } catch {
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await authApi.login(credentials);
      setError(null);
      setRateLimitBlocked(false);
      setUser(response.user);
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        const status = err.response?.status;
        const detail = err.response?.data?.detail || 'Erro ao realizar login.';

        if (status === 429) {
          setRateLimitBlocked(true);
          setError('Acesso temporariamente bloqueado por motivos de segurança devido ao excesso de tentativas falhas. Tente novamente em 15 minutos.');
        } else if (status === 401) {
          setRateLimitBlocked(false);
          setError('Credenciais inválidas. Verifique seu email e senha.');
        } else {
          setRateLimitBlocked(false);
          setError(detail);
        }
      } else {
        setRateLimitBlocked(false);
        setError('Ocorreu um erro inesperado. Tente novamente.');
      }
      throw err;
    }
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.error('Erro no logout:', err);
    } finally {
      setUser(null);
    }
  };

  const clearError = () => {
    setError(null);
    setRateLimitBlocked(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        rateLimitBlocked,
        login,
        logout,
        clearError,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext deve ser utilizado dentro de um AuthProvider');
  }
  return context;
};
