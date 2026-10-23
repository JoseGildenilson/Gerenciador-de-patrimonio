import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MovementModal } from '../components/MovementModal';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentTag } from '../types/equipment';

vi.mock('../api/equipmentApi', () => ({
  equipmentApi: {
    createTag: vi.fn(),
    recordMovement: vi.fn(),
  },
}));

const mockLocations: EquipmentTag[] = [
  { id: 1, category: 'localizacao', name: 'TI', created_at: '2026-08-01T00:00:00Z' },
  { id: 2, category: 'localizacao', name: 'Comunicação', created_at: '2026-08-01T00:00:00Z' },
];

describe('Componente MovementModal', () => {
  const onClose = vi.fn();
  const onSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Não renderiza quando isOpen é false', () => {
    const { container } = render(
      <MovementModal
        isOpen={false}
        equipmentId={1}
        currentLocation="TI"
        locations={mockLocations}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('Renderiza botão de criar local com texto correto e permite criação inline', async () => {
    vi.mocked(equipmentApi.createTag).mockResolvedValue({
      id: 3,
      category: 'localizacao',
      name: 'Almoxarifado B',
      created_at: '2026-08-23T00:00:00Z',
    });

    render(
      <MovementModal
        isOpen={true}
        equipmentId={1}
        currentLocation="TI"
        locations={mockLocations}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    expect(screen.getByText('Registrar Movimentação')).toBeInTheDocument();

    // Verificar que o botão "Criar local" está visível e não contém duplo "+"
    const createBtn = screen.getByTestId('inline-create-location-btn');
    expect(createBtn).toBeInTheDocument();
    expect(createBtn.textContent).toContain('Criar local');
    expect(createBtn.textContent).not.toContain('++');

    // Clicar para abrir input inline
    fireEvent.click(createBtn);

    const input = screen.getByPlaceholderText('Nova localização');
    expect(input).toBeInTheDocument();

    fireEvent.change(input, { target: { value: 'Almoxarifado B' } });

    const saveBtn = screen.getByTestId('confirm-create-location-btn');
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('localizacao', 'Almoxarifado B');
    });
  });

  it('Registra movimentação com sucesso', async () => {
    vi.mocked(equipmentApi.recordMovement).mockResolvedValue({
      id: 1,
      equipment_id: 1,
      origin_location: 'TI',
      destination_location: 'Comunicação',
      movement_date: '2026-08-23T00:00:00.000Z',
      notes: 'Transferência de setor',
      created_at: '2026-08-23T00:00:00.000Z',
    });

    render(
      <MovementModal
        isOpen={true}
        equipmentId={1}
        currentLocation="TI"
        locations={mockLocations}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    // Usar getAllByDisplayValue para selecionar o select de destino (segundo elemento)
    const elements = screen.getAllByDisplayValue('TI');
    const selectElement = elements.find((el) => el.tagName === 'SELECT')!;
    fireEvent.change(selectElement, { target: { value: 'Comunicação' } });

    const notesInput = screen.getByPlaceholderText(/Equipamento transferido para o estúdio 2/i);
    fireEvent.change(notesInput, { target: { value: 'Transferência de setor' } });

    const submitBtn = screen.getByText('Salvar Movimentação');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(equipmentApi.recordMovement).toHaveBeenCalledWith(1, expect.objectContaining({
        origin_location: 'TI',
        destination_location: 'Comunicação',
        notes: 'Transferência de setor',
      }));
      expect(onSuccess).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('Cancela criação inline ao pressionar Escape e exibe erro ao falhar submissão', async () => {
    vi.mocked(equipmentApi.recordMovement).mockRejectedValueOnce({
      response: { data: { detail: 'Origem igual ao destino.' } },
    });

    render(
      <MovementModal
        isOpen={true}
        equipmentId={1}
        currentLocation="TI"
        locations={mockLocations}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    // Abrir input e cancelar com Escape
    const createBtn = screen.getByTestId('inline-create-location-btn');
    fireEvent.click(createBtn);
    const input = screen.getByPlaceholderText('Nova localização');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByPlaceholderText('Nova localização')).not.toBeInTheDocument();

    // Submeter com erro
    const submitBtn = screen.getByText('Salvar Movimentação');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Origem igual ao destino.')).toBeInTheDocument();
    });
  });
});

