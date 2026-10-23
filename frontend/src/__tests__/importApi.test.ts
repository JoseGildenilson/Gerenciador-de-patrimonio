import { describe, it, expect, vi, beforeEach } from 'vitest';
import { importApi } from '../api/importApi';
import { equipmentHttpClient } from '../api/equipmentApi';

vi.mock('../api/equipmentApi', () => ({
  equipmentHttpClient: {
    post: vi.fn(),
  },
}));

describe('importApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('deve chamar previewSpreadsheet com multipart/form-data', async () => {
    const mockResponse = {
      data: {
        filename: 'patrimonio.xlsx',
        total_rows: 10,
        sample_rows: [],
        headers: ['TIPO', 'LOCALIZAÇÃO'],
      },
    };
    (equipmentHttpClient.post as any).mockResolvedValueOnce(mockResponse);

    const file = new File(['dummy content'], 'patrimonio.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const result = await importApi.previewSpreadsheet(file);

    expect(equipmentHttpClient.post).toHaveBeenCalledWith(
      '/import/preview',
      expect.any(FormData),
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    expect(result.total_rows).toBe(10);
  });

  it('deve chamar executeImport com multipart/form-data', async () => {
    const mockResult = {
      data: {
        success: true,
        total_rows: 10,
        created_count: 8,
        updated_count: 2,
        tags_created_count: 3,
        maintenances_created_count: 5,
        errors: [],
        message: 'Importação concluída com sucesso',
      },
    };
    (equipmentHttpClient.post as any).mockResolvedValueOnce(mockResult);

    const file = new File(['dummy content'], 'patrimonio.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const result = await importApi.executeImport(file);

    expect(equipmentHttpClient.post).toHaveBeenCalledWith(
      '/import/execute',
      expect.any(FormData),
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    expect(result.created_count).toBe(8);
    expect(result.updated_count).toBe(2);
  });
});
