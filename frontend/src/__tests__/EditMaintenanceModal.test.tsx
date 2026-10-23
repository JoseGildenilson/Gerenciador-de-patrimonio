import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EditMaintenanceModal } from '../components/EditMaintenanceModal';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentMaintenance } from '../types/equipment';

vi.mock('../api/equipmentApi', () => ({
  equipmentApi: {
    updateMaintenance: vi.fn(),
  },
}));

describe('EditMaintenanceModal', () => {
  const mockMaintenance: EquipmentMaintenance = {
    id: 99,
    equipment_id: 42,
    maintenance_date: '2026-08-15T00:00:00Z',
    maintenance_type: 'Manutenção',
    description: 'Substituição de bateria',
    notes: 'Bateria modelo A123',
    created_at: '2026-08-15T00:00:00Z',
  };

  const defaultProps = {
    isOpen: true,
    equipmentId: 42,
    maintenance: mockMaintenance,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('não renderiza quando isOpen é false ou maintenance é null', () => {
    const { container: c1 } = render(
      <EditMaintenanceModal {...defaultProps} isOpen={false} />
    );
    expect(c1.firstChild).toBeNull();

    const { container: c2 } = render(
      <EditMaintenanceModal {...defaultProps} maintenance={null} />
    );
    expect(c2.firstChild).toBeNull();
  });

  it('preenche previamente os campos com os dados da manutenção existente', () => {
    const { container } = render(<EditMaintenanceModal {...defaultProps} />);

    expect(screen.getByRole('heading', { name: /editar manutenção/i })).toBeInTheDocument();
    expect(container.querySelector('input[type="date"]')).toHaveValue('2026-08-15');
    expect(screen.getByPlaceholderText(/Ex: Troca de SSD de 256 GB/i)).toHaveValue(
      'Substituição de bateria'
    );
    expect(screen.getByPlaceholderText(/Ex: Peça substituída/i)).toHaveValue('Bateria modelo A123');
  });

  it('trata manutenção com campos nulos/vazios', () => {
    const partialMaintenance: EquipmentMaintenance = {
      id: 100,
      equipment_id: 42,
      maintenance_date: '',
      maintenance_type: 'Manutenção',
      description: '',
      notes: null,
      created_at: '2026-08-15T00:00:00Z',
    };

    const { container } = render(
      <EditMaintenanceModal {...defaultProps} maintenance={partialMaintenance} />
    );

    expect(container.querySelector('input[type="date"]')).toHaveValue('');
    expect(screen.getByPlaceholderText(/Ex: Troca de SSD de 256 GB/i)).toHaveValue('');
    expect(screen.getByPlaceholderText(/Ex: Peça substituída/i)).toHaveValue('');
  });

  it('valida campo de descrição obrigatório', async () => {
    render(<EditMaintenanceModal {...defaultProps} />);

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD de 256 GB/i);
    fireEvent.change(descInput, { target: { value: '   ' } });

    const submitBtn = screen.getByRole('button', { name: /salvar alterações/i });
    fireEvent.click(submitBtn);

    expect(
      screen.getByText('A descrição da manutenção é obrigatória.')
    ).toBeInTheDocument();
    expect(equipmentApi.updateMaintenance).not.toHaveBeenCalled();
    expect(defaultProps.onSuccess).not.toHaveBeenCalled();
  });

  it('atualiza manutenção com sucesso chamando equipmentApi.updateMaintenance', async () => {
    (equipmentApi.updateMaintenance as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...mockMaintenance,
      description: 'Substituição de bateria e carcaça',
    });

    render(<EditMaintenanceModal {...defaultProps} />);

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD de 256 GB/i);
    fireEvent.change(descInput, { target: { value: 'Substituição de bateria e carcaça' } });

    const submitBtn = screen.getByRole('button', { name: /salvar alterações/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(equipmentApi.updateMaintenance).toHaveBeenCalledWith(42, 99, {
        maintenance_date: new Date('2026-08-15').toISOString(),
        description: 'Substituição de bateria e carcaça',
        notes: 'Bateria modelo A123',
      });
      expect(defaultProps.onSuccess).toHaveBeenCalled();
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  it('envia notes como undefined quando campo de notas estiver em branco', async () => {
    (equipmentApi.updateMaintenance as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...mockMaintenance,
    });

    render(<EditMaintenanceModal {...defaultProps} />);

    const notesInput = screen.getByPlaceholderText(/Ex: Peça substituída/i);
    fireEvent.change(notesInput, { target: { value: '' } });

    const submitBtn = screen.getByRole('button', { name: /salvar alterações/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(equipmentApi.updateMaintenance).toHaveBeenCalledWith(
        42,
        99,
        expect.objectContaining({
          notes: undefined,
        })
      );
    });
  });

  it('exibe erro retornado pela API quando atualização falha', async () => {
    (equipmentApi.updateMaintenance as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Registro de manutenção bloqueado para alteração',
        },
      },
    });

    render(<EditMaintenanceModal {...defaultProps} />);

    const submitBtn = screen.getByRole('button', { name: /salvar alterações/i });
    fireEvent.click(submitBtn);

    expect(
      await screen.findByText('Registro de manutenção bloqueado para alteração')
    ).toBeInTheDocument();
  });

  it('exibe erro genérico quando requisição rejeita sem detail', async () => {
    (equipmentApi.updateMaintenance as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Erro de rede')
    );

    render(<EditMaintenanceModal {...defaultProps} />);

    const submitBtn = screen.getByRole('button', { name: /salvar alterações/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText('Erro ao atualizar manutenção')).toBeInTheDocument();
  });

  it('chama onClose ao clicar no botão Cancelar e no ícone X', () => {
    const { container } = render(<EditMaintenanceModal {...defaultProps} />);

    const cancelBtn = screen.getByRole('button', { name: /cancelar/i });
    fireEvent.click(cancelBtn);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);

    const closeBtn = container.querySelector('button svg.lucide-x')!.parentElement!;
    fireEvent.click(closeBtn);
    expect(defaultProps.onClose).toHaveBeenCalledTimes(2);
  });
});
