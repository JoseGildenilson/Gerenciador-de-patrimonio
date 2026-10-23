import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AlertBanner } from '../components/AlertBanner';

describe('Componente AlertBanner', () => {
  it('Retorna null se a mensagem for vazia', () => {
    const { container } = render(<AlertBanner message="" />);
    expect(container.firstChild).toBeNull();
  });

  it('Renderiza mensagem de erro padrão com botão fechar', () => {
    const handleClose = vi.fn();
    render(<AlertBanner message="Erro genérico" onClose={handleClose} />);

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Erro genérico')).toBeInTheDocument();

    const closeBtn = screen.getByRole('button', { name: /fechar alerta/i });
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('Renderiza estilo de Rate Limit para isRateLimit=true', () => {
    render(<AlertBanner message="Bloqueado" isRateLimit={true} />);
    expect(screen.getByRole('alert')).toHaveClass('bg-amber-950/70');
  });
});
