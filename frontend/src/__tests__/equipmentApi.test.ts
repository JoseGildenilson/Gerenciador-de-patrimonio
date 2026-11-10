import { describe, it, expect, vi, beforeEach } from 'vitest';
import { equipmentApi, equipmentHttpClient } from '../api/equipmentApi';

describe('Módulo de API equipmentApi', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    equipmentApi.invalidateCache();
  });

  it('Executa requisições de equipamentos e tags com sucesso', async () => {
    vi.spyOn(equipmentHttpClient, 'get').mockImplementation((url) => {
      if (url === '/assets') return Promise.resolve({ data: { items: [], total: 0, page: 1, limit: 25, pages: 1 } }) as any;
      if (url === '/assets/1') return Promise.resolve({ data: { id: 1, serial_number: 'SN123', specs: { hostname: 'H1' } } }) as any;
      if (url === '/categories') return Promise.resolve({ data: [{ id: 1, category: 'tipo', name: 'Notebook' }] }) as any;
      if (url === '/locations') return Promise.resolve({ data: [{ id: 2, building: 'B1', floor: '1', sector: 'TI' }] }) as any;
      if (url === '/users') return Promise.resolve({ data: [{ id: 1, name: 'Admin', email: 'a@b.com', role: 'administrador' }] }) as any;
      if (url === '/assets/suggestions') return Promise.resolve({ data: ['PAT001', 'PAT002'] }) as any;
      return Promise.reject(new Error('Unknown'));
    });


    vi.spyOn(equipmentHttpClient, 'post').mockImplementation((url) => {
      if (url === '/assets') return Promise.resolve({ data: { id: 1, serial_number: 'SN123' } }) as any;
      if (url === '/categories') return Promise.resolve({ data: { id: 2, category: 'tipo', name: 'Desktop' } }) as any;
      if (url === '/locations') return Promise.resolve({ data: { id: 3, building: 'B1', floor: '1', sector: 'Rádio' } }) as any;
      if (url.includes('/renumber')) return Promise.resolve({ data: { id: 1, old_patrimony_number: 'P1', new_patrimony_number: 'P2' } }) as any;
      if (url.includes('/accept-term')) return Promise.resolve({ data: { id: 1, accepted_at: '2026-08-13T00:00:00Z' } }) as any;
      if (url.includes('/movements')) return Promise.resolve({ data: { id: 1, destination_location: 'TI' } }) as any;
      if (url.includes('/maintenances')) return Promise.resolve({ data: { id: 1, description: 'SSD' } }) as any;
      return Promise.reject(new Error('Unknown'));
    });

    vi.spyOn(equipmentHttpClient, 'put').mockImplementation((url) => {
      if (url.includes('/maintenances/')) return Promise.resolve({ data: { id: 1, description: 'SSD Alterado' } }) as any;
      if (url.includes('/categories/')) return Promise.resolve({ data: { id: 1, category: 'tipo', name: 'Notebook Pro' } }) as any;
      if (url.includes('/locations/')) return Promise.resolve({ data: { id: 2, sector: 'TI Central' } }) as any;
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

    const renum = await equipmentApi.renumberPatrimony(1, { new_patrimony_number: 'P2', reason: 'Troca' });
    expect(renum.new_patrimony_number).toBe('P2');

    const term = await equipmentApi.acceptCustodyTerm(1);
    expect(term.accepted_at).toBeDefined();

    const users = await equipmentApi.getUsers();
    expect(users.length).toBe(1);

    const cats = await equipmentApi.getCategories();
    expect(cats.length).toBe(1);

    const locs = await equipmentApi.getLocations();
    expect(locs.length).toBe(1);

    const maintTags = await equipmentApi.getTags('tipo_manutencao');
    expect(maintTags.length).toBe(2);

    const sitTags = await equipmentApi.getTags('situacao');
    expect(sitTags.length).toBe(4);

    const locTag = await equipmentApi.createTag('localizacao', 'Rádio');
    expect(locTag.category).toBe('localizacao');

    const sitTag = await equipmentApi.createTag('situacao', 'em_manutencao');
    expect(sitTag.name).toBe('em_manutencao');

    const upLocTag = await equipmentApi.updateTag(2, 'TI Central', 'localizacao');
    expect(upLocTag.name).toBe('TI Central');

    const delLocTag = await equipmentApi.deleteTag(2, 'localizacao');
    expect(delLocTag.message).toContain('sucesso');
  });

  it('Executa exportação de planilha com sucesso e extrai filename', async () => {
    const mockBlob = new Blob(['excel-binary'], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    vi.spyOn(equipmentHttpClient, 'get').mockImplementation((url) => {
      if (url === '/assets/export') {
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

  describe('Cache de dados de referência e deduplicação de requisições', () => {
    it('reutiliza cache de categorias e deduplica chamadas simultâneas', async () => {
      let getCalls = 0;
      vi.spyOn(equipmentHttpClient, 'get').mockImplementation(async (url) => {
        if (url === '/categories') {
          getCalls++;
          return { data: [{ id: 1, name: 'Notebook' }] } as any;
        }
        return { data: [] } as any;
      });

      // 1. Duas chamadas simultâneas (deduplicação em voo)
      const [res1, res2] = await Promise.all([
        equipmentApi.getCategories(),
        equipmentApi.getCategories(),
      ]);
      expect(res1).toEqual([{ id: 1, name: 'Notebook' }]);
      expect(res2).toEqual([{ id: 1, name: 'Notebook' }]);
      expect(getCalls).toBe(1);

      // 2. Chamada subsequente utiliza o cache síncrono
      const res3 = await equipmentApi.getCategories();
      expect(res3).toEqual([{ id: 1, name: 'Notebook' }]);
      expect(getCalls).toBe(1);

      // 3. Force refresh contorna o cache
      const res4 = await equipmentApi.getCategories({ forceRefresh: true });
      expect(res4).toEqual([{ id: 1, name: 'Notebook' }]);
      expect(getCalls).toBe(2);
    });

    it('reutiliza cache de localizações e invalida após escrita', async () => {
      let locCalls = 0;
      vi.spyOn(equipmentHttpClient, 'get').mockImplementation(async (url) => {
        if (url === '/locations') {
          locCalls++;
          return { data: [{ id: 10, building: 'B1', floor: '1', sector: 'TI' }] } as any;
        }
        return { data: [] } as any;
      });

      vi.spyOn(equipmentHttpClient, 'post').mockResolvedValue({
        data: { id: 11, building: 'B1', floor: '1', sector: 'RH' },
      });

      // 1. Primeira chamada carrega e popula cache
      const locs1 = await equipmentApi.getLocations();
      expect(locs1.length).toBe(1);
      expect(locCalls).toBe(1);

      // 2. Segunda chamada vem do cache
      const locs2 = await equipmentApi.getLocations();
      expect(locs2.length).toBe(1);
      expect(locCalls).toBe(1);

      // 3. Criar localização invalida o cache
      await equipmentApi.createTag('localizacao', 'RH');

      // 4. Nova chamada busca do backend novamente
      const locs3 = await equipmentApi.getLocations();
      expect(locs3.length).toBe(1);
      expect(locCalls).toBe(2);
    });

    it('limpa in-flight promise em caso de erro na requisição', async () => {
      let attempts = 0;
      vi.spyOn(equipmentHttpClient, 'get').mockImplementation(async (url) => {
        if (url === '/categories') {
          attempts++;
          if (attempts === 1) throw new Error('Falha de rede');
          return { data: [{ id: 5, name: 'Servidor' }] } as any;
        }
        return { data: [] } as any;
      });

      await expect(equipmentApi.getCategories()).rejects.toThrow('Falha de rede');

      // Segunda chamada após erro deve tentar novamente
      const retryRes = await equipmentApi.getCategories();
      expect(retryRes).toEqual([{ id: 5, name: 'Servidor' }]);
      expect(attempts).toBe(2);
    });
  });
});


