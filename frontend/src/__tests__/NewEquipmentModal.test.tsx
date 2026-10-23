import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NewEquipmentModal } from '../components/NewEquipmentModal';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentTag } from '../types/equipment';

vi.mock('../api/equipmentApi', () => ({
  equipmentApi: {
    getTags: vi.fn(),
    createTag: vi.fn(),
    createEquipment: vi.fn(),
  },
}));

const mockTags: EquipmentTag[] = [
  { id: 1, category: 'tipo', name: 'Desktop', created_at: '2026-08-01T00:00:00Z' },
  { id: 2, category: 'localizacao', name: 'TI', created_at: '2026-08-01T00:00:00Z' },
  { id: 3, category: 'situacao', name: 'Em uso', created_at: '2026-08-01T00:00:00Z' },
];

describe('Componente NewEquipmentModal', () => {
  const onClose = vi.fn();
  const onSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(equipmentApi.getTags).mockResolvedValue([...mockTags]);
  });

  it('Não renderiza quando isOpen é false', () => {
    const { container } = render(
      <NewEquipmentModal isOpen={false} onClose={onClose} onSuccess={onSuccess} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('Renderiza botões de criar tag inline sem duplicar + e permite cadastro rápido', async () => {
    vi.mocked(equipmentApi.createTag).mockResolvedValue({
      id: 4,
      category: 'tipo',
      name: 'Servidor',
      created_at: '2026-08-23T00:00:00Z',
    });

    render(
      <NewEquipmentModal isOpen={true} onClose={onClose} onSuccess={onSuccess} />
    );

    await waitFor(() => {
      expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
    });

    const createTipoBtn = screen.getByTestId('inline-create-tipo-btn');
    const createLocBtn = screen.getByTestId('inline-create-localizacao-btn');
    const createSitBtn = screen.getByTestId('inline-create-situacao-btn');

    expect(createTipoBtn.textContent).toContain('Criar tipo');
    expect(createTipoBtn.textContent).not.toContain('++');
    expect(createLocBtn.textContent).toContain('Criar local');
    expect(createLocBtn.textContent).not.toContain('++');
    expect(createSitBtn.textContent).toContain('Criar situação');
    expect(createSitBtn.textContent).not.toContain('++');

    // Clicar para criar tipo inline, cancelar com Escape e salvar com Enter
    fireEvent.click(createTipoBtn);
    const input = screen.getByPlaceholderText('Novo tipo');
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByPlaceholderText('Novo tipo')).not.toBeInTheDocument();

    fireEvent.click(createTipoBtn);
    const input2 = screen.getByPlaceholderText('Novo tipo');
    fireEvent.change(input2, { target: { value: 'Servidor' } });
    fireEvent.keyDown(input2, { key: 'Enter' });

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('tipo', 'Servidor');
    });

    // Clicar para criar localizacao inline e salvar com Enter
    vi.mocked(equipmentApi.createTag).mockResolvedValueOnce({
      id: 5,
      category: 'localizacao',
      name: 'Recepção',
      created_at: '2026-08-23T00:00:00Z',
    });
    fireEvent.click(createLocBtn);
    const locInput = screen.getByPlaceholderText('Nova localização');
    fireEvent.change(locInput, { target: { value: 'Recepção' } });
    fireEvent.keyDown(locInput, { key: 'Enter' });

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('localizacao', 'Recepção');
    });

    // Clicar para criar situacao inline, cancelar com Escape e salvar com Enter
    fireEvent.click(createSitBtn);
    const sitInput = screen.getByPlaceholderText('Nova situação');
    fireEvent.keyDown(sitInput, { key: 'Escape' });
    expect(screen.queryByPlaceholderText('Nova situação')).not.toBeInTheDocument();

    vi.mocked(equipmentApi.createTag).mockResolvedValueOnce({
      id: 6,
      category: 'situacao',
      name: 'Reserva',
      created_at: '2026-08-23T00:00:00Z',
    });
    fireEvent.click(screen.getByTestId('inline-create-situacao-btn'));
    const sitInput2 = screen.getByPlaceholderText('Nova situação');
    fireEvent.change(sitInput2, { target: { value: 'Reserva' } });
    fireEvent.keyDown(sitInput2, { key: 'Enter' });

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('situacao', 'Reserva');
    });
  });

  it('Permite preenchimento e submissão completa com campos opcionais', async () => {
    vi.mocked(equipmentApi.createEquipment).mockResolvedValue({
      id: 10,
      patrimony_number: 'PAT-999',
      equipment_type: 'Desktop',
      location: 'TI',
      status: 'Em uso',
      serial_number: 'SN-999',
      hostname: 'DESK-999',
      description: 'OptiPlex',
      brand: 'Dell',
      product_number: 'OPT-7090',
      movements: [],
      maintenances: [],
      created_at: '2026-08-23T00:00:00Z',
    });

    render(
      <NewEquipmentModal isOpen={true} onClose={onClose} onSuccess={onSuccess} />
    );

    await waitFor(() => {
      expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('ex: PAT-10342'), { target: { value: 'PAT-999' } });
    fireEvent.change(screen.getByPlaceholderText('ex: SN12345678'), { target: { value: 'SN-999' } });
    fireEvent.change(screen.getByPlaceholderText('ex: Dell OptiPlex 7090 Core i7 16GB SSD 512GB'), { target: { value: 'Dell OptiPlex' } });
    fireEvent.change(screen.getByPlaceholderText('ex: Dell, Lenovo, HP, Apple'), { target: { value: 'Dell' } });
    fireEvent.change(screen.getByPlaceholderText('ex: 20L50001BR'), { target: { value: 'OPT-7090' } });
    fireEvent.change(screen.getByPlaceholderText('ex: DESKTOP-TI01'), { target: { value: 'DESK-999' } });
    fireEvent.change(screen.getByPlaceholderText('ex: VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A'), { target: { value: 'VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A' } });

    const submitBtn = screen.getByRole('button', { name: /cadastrar equipamento/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(equipmentApi.createEquipment).toHaveBeenCalled();
      expect(onSuccess).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });
});

