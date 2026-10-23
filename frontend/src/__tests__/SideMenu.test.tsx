import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { SideMenu } from '../components/SideMenu';
import { useAuth } from '../hooks/useAuth';

vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../components/ManageTagsModal', () => ({
  ManageTagsModal: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) =>
    isOpen ? (
      <div data-testid="mock-tags-modal">
        <span>Modal de Tags Aberto</span>
        <button onClick={onClose} data-testid="close-tags-modal-btn">
          Fechar Tags
        </button>
      </div>
    ) : null,
}));

describe('SideMenu', () => {
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: {
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
      },
      logout: mockLogout,
    });
  });

  const renderComponent = (initialPath = '/dashboard') => {
    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <div data-testid="outside-area">Área Externa</div>
        <SideMenu />
        <Routes>
          <Route path="/dashboard" element={<div>Página Dashboard</div>} />
          <Route path="/equipamentos" element={<div>Página Equipamentos</div>} />
          <Route path="/importar" element={<div>Página Importar</div>} />
          <Route path="/login" element={<div>Página Login</div>} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('inicia recolhido com drawer fora da tela (-translate-x-full) e altura total de viewport', () => {
    renderComponent();

    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('-translate-x-full');
    expect(aside).toHaveClass('h-screen');
    expect(aside).toHaveClass('min-h-screen');
  });

  it('abre o menu ao clicar no botão hambúrguer alternando para translate-x-0', () => {
    renderComponent();

    const toggleBtn = screen.getByTestId('toggle-menu-btn');
    fireEvent.click(toggleBtn);

    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('translate-x-0');
    expect(screen.getByRole('button', { name: /fechar menu/i })).toBeInTheDocument();
  });

  it('fecha o menu ao clicar no botão de fechar (X)', () => {
    renderComponent();

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));
    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('translate-x-0');

    const closeBtn = screen.getByRole('button', { name: /fechar menu/i });
    fireEvent.click(closeBtn);

    expect(aside).toHaveClass('-translate-x-full');
  });

  it('fecha o menu ao pressionar a tecla Escape quando aberto', () => {
    renderComponent();

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));
    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('translate-x-0');

    // Pressiona Escape
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(aside).toHaveClass('-translate-x-full');
  });

  it('ignora outras teclas sem fechar o menu', () => {
    renderComponent();

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));
    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('translate-x-0');

    fireEvent.keyDown(window, { key: 'Enter' });
    expect(aside).toHaveClass('translate-x-0');
  });

  it('fecha o menu ao clicar fora no backdrop/área externa', () => {
    renderComponent();

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));
    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('translate-x-0');

    const outside = screen.getByTestId('outside-area');
    fireEvent.mouseDown(outside);

    expect(aside).toHaveClass('-translate-x-full');
  });

  it('não fecha o menu ao clicar dentro do próprio menu', () => {
    renderComponent();

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));
    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('translate-x-0');

    fireEvent.mouseDown(aside);
    expect(aside).toHaveClass('translate-x-0');
  });

  it('exibe todos os links administrativos quando o usuário é técnico (RBAC)', () => {
    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByTestId('patrimonio-menu-item')).toBeInTheDocument();
    expect(screen.getByTestId('importar-menu-item')).toBeInTheDocument();
    expect(screen.getByTestId('manage-tags-menu-item')).toBeInTheDocument();
  });

  it('oculta links de gestão quando o usuário é colaborador (RBAC)', () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: {
        id: 2,
        email: 'colaborador@empresa.com',
        role: 'colaborador',
      },
      logout: mockLogout,
    });

    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.queryByTestId('patrimonio-menu-item')).not.toBeInTheDocument();
    expect(screen.queryByTestId('importar-menu-item')).not.toBeInTheDocument();
    expect(screen.queryByTestId('manage-tags-menu-item')).not.toBeInTheDocument();
    expect(screen.getByText('colaborador')).toBeInTheDocument();
  });

  it('navega para a rota correspondente e fecha o menu ao clicar em um link', async () => {
    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    const patrimonioBtn = screen.getByTestId('patrimonio-menu-item');
    fireEvent.click(patrimonioBtn);

    const aside = screen.getByLabelText('Sidebar Menu');
    expect(aside).toHaveClass('-translate-x-full');
    expect(await screen.findByText('Página Equipamentos')).toBeInTheDocument();
  });

  it('navega para importar ao clicar no item importar planilha', async () => {
    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    const importarBtn = screen.getByTestId('importar-menu-item');
    fireEvent.click(importarBtn);

    expect(await screen.findByText('Página Importar')).toBeInTheDocument();
  });

  it('abre e fecha o ManageTagsModal ao clicar em Gerenciar Tags', () => {
    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    const manageTagsBtn = screen.getByTestId('manage-tags-menu-item');
    fireEvent.click(manageTagsBtn);

    expect(screen.getByTestId('mock-tags-modal')).toBeInTheDocument();

    // Fecha modal de tags
    const closeTagsBtn = screen.getByTestId('close-tags-modal-btn');
    fireEvent.click(closeTagsBtn);

    expect(screen.queryByTestId('mock-tags-modal')).not.toBeInTheDocument();
  });

  it('executa logout chamando logout() e redirecionando para /login', async () => {
    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    const logoutBtn = screen.getByRole('button', { name: /encerrar sessão/i });
    fireEvent.click(logoutBtn);

    await waitFor(() => {
      expect(mockLogout).toHaveBeenCalledTimes(1);
      expect(screen.getByText('Página Login')).toBeInTheDocument();
    });
  });

  it('renderiza fallback quando user não está definido', () => {
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      user: null,
      logout: mockLogout,
    });

    renderComponent('/dashboard');

    fireEvent.click(screen.getByTestId('toggle-menu-btn'));

    expect(screen.getByText('Usuário')).toBeInTheDocument();
    expect(screen.getByText('colaborador')).toBeInTheDocument();
    expect(screen.getByText('U')).toBeInTheDocument();
  });
});
