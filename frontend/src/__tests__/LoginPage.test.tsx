import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { LoginPage } from '../pages/LoginPage';
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

describe('Tela de Login (LoginPage Component & BDD Scenarios)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (authApi.getMe as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Unauthenticated'));
    (authApi.refresh as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('No refresh token'));
  });

  const renderLoginPage = () => {
    return render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/dashboard" element={<div>Dashboard de Teste</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
  };

  it('Cenário 1: Renderiza o formulário de login com campos limpos e elementos da marca', async () => {
    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByText('Gestão de Patrimônio')).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/endereço de email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^senha$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /entrar no sistema/i })).toBeInTheDocument();
  });

  it('Cenário 2: Exibe validações visuais ao tentar submeter formulário em branco', async () => {
    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /entrar no sistema/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    expect(await screen.findByText('Email é obrigatório.')).toBeInTheDocument();
    expect(screen.getByText('Senha é obrigatória.')).toBeInTheDocument();
    expect(authApi.login).not.toHaveBeenCalled();
  });

  it('Cenário 3: Exibe estado isSubmitting desabilitando campos durante a requisição', async () => {
    (authApi.login as ReturnType<typeof vi.fn>).mockReturnValue(new Promise(() => {})); // Promise pendente

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/endereço de email/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/endereço de email/i), 'tecnico@empresa.com');
    await userEvent.type(screen.getByLabelText(/^senha$/i), 'Senha123!');

    fireEvent.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    await waitFor(() => {
      expect(screen.getByText(/validando credenciais/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/endereço de email/i)).toBeDisabled();
      expect(screen.getByLabelText(/^senha$/i)).toBeDisabled();
    });
  });

  it('Cenário 4: Exibe mensagem de erro genérica ao receber HTTP 401 da API', async () => {
    const error401 = new axios.AxiosError('Unauthorized', '401', undefined, undefined, {
      status: 401,
      statusText: 'Unauthorized',
      data: { detail: 'Credenciais de acesso inválidas.' },
      headers: {},
      config: { headers: {} as any },
    });

    (authApi.login as ReturnType<typeof vi.fn>).mockRejectedValue(error401);

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/endereço de email/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/endereço de email/i), 'tecnico@empresa.com');
    await userEvent.type(screen.getByLabelText(/^senha$/i), 'SenhaErrada!');

    fireEvent.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    expect(await screen.findByText('Credenciais inválidas. Verifique seu email e senha.')).toBeInTheDocument();
  });

  it('Cenário 5: Exibe alerta de bloqueio por força bruta ao receber HTTP 429 da API', async () => {
    const error429 = new axios.AxiosError('Too Many Requests', '429', undefined, undefined, {
      status: 429,
      statusText: 'Too Many Requests',
      data: { detail: 'Acesso temporariamente bloqueado por motivos de segurança.' },
      headers: {},
      config: { headers: {} as any },
    });

    (authApi.login as ReturnType<typeof vi.fn>).mockRejectedValue(error429);

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/endereço de email/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/endereço de email/i), 'tecnico@empresa.com');
    await userEvent.type(screen.getByLabelText(/^senha$/i), 'Senha123!');

    fireEvent.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    expect(await screen.findByText(/acesso temporariamente bloqueado por motivos de segurança/i)).toBeInTheDocument();
  });

  it('Cenário 6: Redireciona para o Dashboard após login bem-sucedido (HTTP 200)', async () => {
    (authApi.login as ReturnType<typeof vi.fn>).mockResolvedValue({
      access_token: 'fake_jwt',
      token_type: 'bearer',
      user: { id: 1, email: 'tecnico@empresa.com', role: 'tecnico', is_active: true },
    });

    renderLoginPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/endereço de email/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/endereço de email/i), 'tecnico@empresa.com');
    await userEvent.type(screen.getByLabelText(/^senha$/i), 'SenhaSegura123!');

    fireEvent.click(screen.getByRole('button', { name: /entrar no sistema/i }));

    expect(await screen.findByText('Dashboard de Teste')).toBeInTheDocument();
  });
});
