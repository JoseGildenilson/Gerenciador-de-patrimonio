import { describe, it, expect, vi, beforeEach } from 'vitest';
import { equipmentApi, equipmentHttpClient } from '../api/equipmentApi';

describe('Módulo de API equipmentApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('Executa requisições de equipamentos e tags com sucesso', async () => {
    vi.spyOn(equipmentHttpClient, 'get').mockImplementation((url) => {
      if (url === '') return Promise.resolve({ data: { items: [], total: 0, page: 1, limit: 25, pages: 1 } }) as any;
      if (url === '/1') return Promise.resolve({ data: { id: 1, serial_number: 'SN123' } }) as any;
      if (url === '/tags') return Promise.resolve({ data: [{ id: 1, category: 'tipo', name: 'Notebook' }] }) as any;
      if (url === '/suggestions') return Promise.resolve({ data: ['PAT001', 'PAT002'] }) as any;
      return Promise.reject(new Error('Unknown'));
    });


    vi.spyOn(equipmentHttpClient, 'post').mockImplementation((url) => {
      if (url === '') return Promise.resolve({ data: { id: 1, serial_number: 'SN123' } }) as any;
      if (url === '/tags') return Promise.resolve({ data: { id: 2, category: 'tipo', name: 'Desktop' } }) as any;
      if (url.includes('/movements')) return Promise.resolve({ data: { id: 1, destination_location: 'TI' } }) as any;
      if (url.includes('/maintenances')) return Promise.resolve({ data: { id: 1, description: 'SSD' } }) as any;
      return Promise.reject(new Error('Unknown'));
    });

    vi.spyOn(equipmentHttpClient, 'put').mockImplementation((url) => {
      if (url.includes('/maintenances/')) return Promise.resolve({ data: { id: 1, description: 'SSD Alterado' } }) as any;
      if (url.includes('/tags/')) return Promise.resolve({ data: { id: 1, category: 'tipo', name: 'Notebook Pro' } }) as any;
      return Promise.resolve({ data: { id: 1, description: 'Updated' } }) as any;
    });

    vi.spyOn(equipmentHttpClient, 'delete').mockResolvedValue({ data: { message: 'Manutenção excluída com sucesso.' } });

    const list = await equipmentApi.getEquipments({ type: ['Notebook', 'Desktop'] });
    expect(list.total).toBe(0);

    const detail = await equipmentApi.getEquipmentDetail(1);
    expect(detail.serial_number).toBe('SN123');

    const created = await equipmentApi.createEquipment({
      serial_number: 'SN123',
      description: 'Notebook',
      equipment_type: 'Notebook',
      location: 'TI',
      status: 'Em uso',
    });
    expect(created.id).toBe(1);

    const updated = await equipmentApi.updateEquipment(1, { description: 'Updated' });
    expect(updated.description).toBe('Updated');

    const tags = await equipmentApi.getTags('tipo');
    expect(tags.length).toBe(1);

    const newTag = await equipmentApi.createTag('tipo', 'Desktop');
    expect(newTag.name).toBe('Desktop');

    const updatedTag = await equipmentApi.updateTag(1, 'Notebook Pro');
    expect(updatedTag.name).toBe('Notebook Pro');

    const delTag = await equipmentApi.deleteTag(1);
    expect(delTag.message).toContain('sucesso');

    const mov = await equipmentApi.recordMovement(1, { origin_location: 'TI', destination_location: 'Rádio', movement_date: '2026-08-13' });
    expect(mov.destination_location).toBe('TI');

    const maint = await equipmentApi.recordMaintenance(1, { maintenance_date: '2026-08-13', maintenance_type: 'Manutenção', description: 'SSD' });
    expect(maint.description).toBe('SSD');

    const updatedMaint = await equipmentApi.updateMaintenance(1, 1, { description: 'SSD Alterado' });
    expect(updatedMaint.description).toBe('SSD Alterado');

    const delRes = await equipmentApi.deleteMaintenance(1, 1);
    expect(delRes.message).toContain('sucesso');

    const suggestions = await equipmentApi.getSuggestions('patrimony_number', 'PA', 10);
    expect(suggestions).toEqual(['PAT001', 'PAT002']);
  });

  it('Executa exportação de planilha com sucesso e extrai filename', async () => {
    const mockBlob = new Blob(['excel-binary'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    vi.spyOn(equipmentHttpClient, 'get').mockImplementation((url) => {
      if (url === '/export') {
        return Promise.resolve({
          data: mockBlob,
          headers: {
            'content-disposition': 'attachment; filename="PATRIMONIO_2026-08-23_2230.xlsx"',
          },
        }) as any;
      }
      return Promise.reject(new Error('Unknown'));
    });

    const res = await equipmentApi.exportEquipments({ type: ['Notebook'] });
    expect(res.filename).toBe('PATRIMONIO_2026-08-23_2230.xlsx');
    expect(res.data).toBe(mockBlob);

    // Teste com fallback de filename se header ausente
    vi.spyOn(equipmentHttpClient, 'get').mockResolvedValue({
      data: mockBlob,
      headers: {},
    });
    const resFallback = await equipmentApi.exportEquipments();
    expect(resFallback.filename).toBe('patrimonio_export.xlsx');
  });
});


