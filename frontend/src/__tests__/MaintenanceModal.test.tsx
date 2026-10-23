import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MaintenanceModal } from '../components/MaintenanceModal';
import { equipmentApi } from '../api/equipmentApi';

vi.mock('../api/equipmentApi', () => ({
  equipmentApi: {
    recordMaintenance: vi.fn(),
  },
}));

describe('MaintenanceModal', () => {
  const defaultProps = {
    isOpen: true,
    equipmentId: 42,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('não renderiza nada quando isOpen é false', () => {
    const { container } = render(
      <MaintenanceModal {...defaultProps} isOpen={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renderiza os campos com valores padrão quando aberto', () => {
    const { container } = render(<MaintenanceModal {...defaultProps} />);

    expect(screen.getByRole('heading', { name: /registrar manutenção/i })).toBeInTheDocument();
    expect(container.querySelector('input[type="date"]')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ex: Troca de SSD/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ex: Teste de estabilidade/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /salvar manutenção/i })).toBeInTheDocument();
  });

  it('valida campo de descrição obrigatório ao submeter com espaços vazios', async () => {
    render(<MaintenanceModal {...defaultProps} />);

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
    fireEvent.change(descInput, { target: { value: '   ' } });

    const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
    fireEvent.click(submitBtn);

    expect(
      screen.getByText('A descrição / lista de itens da manutenção é obrigatória.')
    ).toBeInTheDocument();
    expect(equipmentApi.recordMaintenance).not.toHaveBeenCalled();
    expect(defaultProps.onSuccess).not.toHaveBeenCalled();
  });

  it('envia dados com sucesso chamando equipmentApi.recordMaintenance e os callbacks', async () => {
    (equipmentApi.recordMaintenance as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ id: 10 });

    const { container } = render(<MaintenanceModal {...defaultProps} />);

    const dateInput = container.querySelector('input[type="date"]')!;
    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
    const notesInput = screen.getByPlaceholderText(/Ex: Teste de estabilidade/i);

    fireEvent.change(dateInput, { target: { value: '2026-08-20' } });
    fireEvent.change(descInput, { target: { value: 'Troca de cooler' } });
    fireEvent.change(notesInput, { target: { value: 'Peça original Lenovo' } });

    const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(equipmentApi.recordMaintenance).toHaveBeenCalledWith(42, {
        maintenance_type_id: 1,
        started_at: new Date('2026-08-20').toISOString(),
        description: 'Troca de cooler',
        notes: 'Peça original Lenovo',
      });
      expect(defaultProps.onSuccess).toHaveBeenCalled();
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  it('envia dados omitindo notes vazias como undefined', async () => {
    (equipmentApi.recordMaintenance as ReturnType<typeof vi.fn>).mockResolvedValueOnce({ id: 11 });

    render(<MaintenanceModal {...defaultProps} />);

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
    fireEvent.change(descInput, { target: { value: 'Limpeza interna' } });

    const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(equipmentApi.recordMaintenance).toHaveBeenCalledWith(
        42,
        expect.objectContaining({
          description: 'Limpeza interna',
          notes: undefined,
        })
      );
    });
  });

  it('exibe erro retornado pela API quando a requisição falha', async () => {
    (equipmentApi.recordMaintenance as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Equipamento inativo não pode receber manutenção',
        },
      },
    });

    render(<MaintenanceModal {...defaultProps} />);

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
    fireEvent.change(descInput, { target: { value: 'Troca de teclado' } });

    const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText('Equipamento inativo não pode receber manutenção')
    ).toBeInTheDocument();
    expect(defaultProps.onSuccess).not.toHaveBeenCalled();
  });

  it('exibe mensagem genérica de erro quando a API falha sem detail', async () => {
    (equipmentApi.recordMaintenance as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Network failure')
    );

    render(<MaintenanceModal {...defaultProps} />);

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
    fireEvent.change(descInput, { target: { value: 'Troca de pasta térmica' } });

    const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText('Erro ao registrar manutenção')).toBeInTheDocument();
  });

  it('chama onClose ao clicar no botão Cancelar e no botão Fechar (X)', () => {
    const { container } = render(<MaintenanceModal {...defaultProps} />);

    const cancelBtn = screen.getByRole('button', { name: /cancelar/i });
    fireEvent.click(cancelBtn);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);

    // Botão de fechar (X) no cabeçalho
    const closeBtn = container.querySelector('button svg.lucide-x')!.parentElement!;
    fireEvent.click(closeBtn);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(2);
  });
});
