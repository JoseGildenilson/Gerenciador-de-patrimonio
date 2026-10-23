import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { App } from '../App';
import { authApi } from '../api/authApi';
import { dashboardApi } from '../api/dashboardApi';

vi.mock('../api/authApi', () => ({
  authApi: {
    getMe: vi.fn(),
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('../api/dashboardApi', () => ({
  dashboardApi: {
    getMetrics: vi.fn(),
  },
}));

describe('Componente Raiz App & Proteção de Rotas', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Redireciona para /login se não houver usuário autenticado', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Unauthenticated'));
    (authApi.refresh as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('No refresh'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Gestão de Patrimônio')).toBeInTheDocument();
    });
  });

  it('Permite acesso ao Dashboard se a verificação inicial de autenticação for bem sucedida', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      email: 'tecnico@empresa.com',
      role: 'tecnico',
      is_active: true,
    });
    (dashboardApi.getMetrics as ReturnType<typeof vi.fn>).mockResolvedValue({
      tickets_pending: 1,
      tickets_in_progress: 1,
      equipments_total: 5,
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard de Controle')).toBeInTheDocument();
    });
  });

  it('Redireciona para /dashboard se usuário não possuir o role exigido pela rota', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 2,
      email: 'colab@empresa.com',
      role: 'colaborador',
      is_active: true,
    });
    (dashboardApi.getMetrics as ReturnType<typeof vi.fn>).mockResolvedValue({
      tickets_pending: 0,
      tickets_in_progress: 0,
      equipments_total: 2,
    });

    window.history.pushState({}, '', '/importar');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Dashboard de Controle')).toBeInTheDocument();
    });
  });

  it('Redireciona para /login ao tentar acessar rota protegida sem estar autenticado', async () => {
    (authApi.getMe as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Unauthenticated'));
    (authApi.refresh as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('No refresh'));

    window.history.pushState({}, '', '/equipamentos');
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Gestão de Patrimônio')).toBeInTheDocument();
    });
  });
});


