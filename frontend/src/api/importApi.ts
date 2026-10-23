import { equipmentHttpClient } from './equipmentApi';

export interface SpreadsheetRowPreview {
  row_number: number;
  equipment_type?: string | null;
  location?: string | null;
  status?: string | null;
  description?: string | null;
  patrimony_number?: string | null;
  serial_number?: string | null;
  brand?: string | null;
  last_maintenance_at?: string | null;
  windows_key?: string | null;
  product_number?: string | null;
  hist_mov?: string | null;
  hostname?: string | null;
  notes?: string | null;
}

export interface SpreadsheetImportPreviewResponse {
  filename: string;
  total_rows: number;
  sample_rows: SpreadsheetRowPreview[];
  detected_sheet?: string | null;
  headers: string[];
}

export interface SpreadsheetImportResultResponse {
  success: boolean;
  total_rows: number;
  created_count: number;
  updated_count: number;
  tags_created_count: number;
  maintenances_created_count: number;
  errors: string[];
  message: string;
}

export const importApi = {
  previewSpreadsheet: async (file: File): Promise<SpreadsheetImportPreviewResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await equipmentHttpClient.post<SpreadsheetImportPreviewResponse>(
      '/import/preview',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  executeImport: async (file: File): Promise<SpreadsheetImportResultResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await equipmentHttpClient.post<SpreadsheetImportResultResponse>(
      '/import/execute',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};
