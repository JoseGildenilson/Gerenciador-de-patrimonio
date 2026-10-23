import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider, useAuthContext } from '../context/AuthContext';
import { authApi } from '../api/authApi';
import axios from 'axios';

vi.mock('../api/authApi', () => ({
  authApi: {
    getMe: vi.fn(),
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
}));

const TestConsumer: React.FC = () => {
  const { user, login, logout, clearError, error } = useAuthContext();

  const handleLogin = async () => {
    try {
      await login({ email: 'a@b.com', password: '123' });
    } catch {
      // Ignora erro capturado no handler do botão para o estado do contexto
    }
  };

  return (
    <div>
      <span data-testid="user-email">{user ? user.email : 'deslogado'}</span>
      <span data-testid="error-msg">{error || ''}</span>
      <button onClick={handleLogin}>Login</button>
      <button onClick={() => logout()}>Logout</button>
      <button onClick={() => clearError()}>ClearError</button>
    </div>
  );
};

describe('Contexto AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Inicia sessão automaticamente se o refresh token for bem-sucedido', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('No me'));
    (authApi.refresh as ReturnType<typeof vi.fn>).mockResolvedValue({
      access_token: 'tok',
      token_type: 'bearer',
      user: { id: 2, email: 'refreshed@empresa.com', role: 'tecnico', is_active: true },
    });

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('refreshed@empresa.com');
    });
  });

  it('Trata erros 500 genéricos da API e erros não-Axios', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('No me'));
    (authApi.refresh as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('No ref'));

    const error500 = new axios.AxiosError('Server Error', '500', undefined, undefined, {
      status: 500,
      statusText: 'Internal Server Error',
      data: { detail: 'Erro interno do servidor.' },
      headers: {},
      config: { headers: {} as any },
    });

    (authApi.login as ReturnType<typeof vi.fn>).mockRejectedValue(error500);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('deslogado');
    });

    fireEvent.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByTestId('error-msg')).toHaveTextContent('Erro interno do servidor.');
    });

    fireEvent.click(screen.getByText('ClearError'));
    expect(screen.getByTestId('error-msg')).toHaveTextContent('');

    // Erro não-Axios
    (authApi.login as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Generic Error'));
    fireEvent.click(screen.getByText('Login'));
    await waitFor(() => {
      expect(screen.getByTestId('error-msg')).toHaveTextContent('Ocorreu um erro inesperado.');
    });
  });

  it('Trata exceção no logout', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({ id: 1, email: 'u@b.com', role: 't', is_active: true });
    (authApi.logout as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Logout failed'));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('u@b.com');
    });

    fireEvent.click(screen.getByText('Logout'));

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('deslogado');
    });
  });

  it('Lança exceção ao utilizar useAuthContext fora do AuthProvider', () => {
    const ComponentOutside = () => {
      useAuthContext();
      return null;
    };

    expect(() => render(<ComponentOutside />)).toThrow('useAuthContext deve ser utilizado dentro de um AuthProvider');
  });
});
