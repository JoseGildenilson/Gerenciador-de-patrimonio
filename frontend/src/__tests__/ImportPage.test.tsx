import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ImportPage } from '../pages/ImportPage';
import { authApi } from '../api/authApi';
import { importApi } from '../api/importApi';

vi.mock('../api/authApi', () => ({
  authApi: {
    getMe: vi.fn(),
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('../api/importApi', () => ({
  importApi: {
    previewSpreadsheet: vi.fn(),
    executeImport: vi.fn(),
  },
}));

const mockPreviewData = {
  filename: 'patrimonio.xlsx',
  total_rows: 2,
  sample_rows: [
    {
      row_number: 2,
      equipment_type: 'DESKTOP',
      location: 'CTM',
      status: 'EM USO',
      description: 'PC Dell OptiPlex',
      patrimony_number: '2020001',
      serial_number: 'SN-001',
      brand: 'Dell',
      last_maintenance_at: '10/05/2023',
    },
    {
      row_number: 3,
      equipment_type: 'MONITOR',
      location: 'SALA 10',
      status: 'OCIOSO',
      description: 'Monitor LG 24',
      patrimony_number: null,
      serial_number: null,
      brand: 'LG',
      last_maintenance_at: null,
    },
  ],
  detected_sheet: 'Patrimônio',
  headers: ['TIPO', 'LOCALIZAÇÃO', 'SITUAÇÃO', 'DESCRIÇÃO', 'Nº PATRIMÔNIO', 'Nº SÉRIE', 'MARCA'],
};

const mockImportResult = {
  success: true,
  total_rows: 2,
  created_count: 1,
  updated_count: 1,
  tags_created_count: 2,
  maintenances_created_count: 1,
  errors: [],
  message: 'Importação concluída: 1 novos equipamentos, 1 atualizados e 2 tags cadastradas.',
};

describe('ImportPage (Frontend)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      email: 'tecnico@empresa.com',
      role: 'tecnico',
      is_active: true,
    });
  });

  it('Renderiza a área de upload de planilha', async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Importação de Planilha')).toBeInTheDocument();
      expect(screen.getByText('Carregar Arquivo de Inventário')).toBeInTheDocument();
      expect(screen.getByText('Clique para escolher o arquivo')).toBeInTheDocument();
    });
  });

  it('Gera pré-visualização ao selecionar arquivo com sucesso', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'patrimonio.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const fileInput = screen.getByTestId('spreadsheet-file-input');

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(importApi.previewSpreadsheet).toHaveBeenCalledWith(file);
    });

    // Deve exibir tabela de prévia e dados
    expect(await screen.findByText('Pré-visualização dos Dados')).toBeInTheDocument();
    expect(screen.getByText('PC Dell OptiPlex')).toBeInTheDocument();
    expect(screen.getByText('Monitor LG 24')).toBeInTheDocument();
    expect(screen.getByText('2020001')).toBeInTheDocument();
    expect(screen.getByTestId('confirm-import-button')).toBeInTheDocument();
  });

  it('Executa a importação e exibe card de sucesso com estatísticas', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData);
    (importApi.executeImport as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockImportResult);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
            <Route path="/equipamentos" element={<div>Página de Equipamentos</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'patrimonio.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const fileInput = screen.getByTestId('spreadsheet-file-input');
    fireEvent.change(fileInput, { target: { files: [file] } });

    const confirmBtn = await screen.findByTestId('confirm-import-button');
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(importApi.executeImport).toHaveBeenCalledWith(file);
    });

    expect(await screen.findByTestId('import-success-card')).toBeInTheDocument();
    expect(screen.getByText('Importação Concluída com Sucesso!')).toBeInTheDocument();
    expect(screen.getByText('Novos')).toBeInTheDocument();
    expect(screen.getByText('Atualizados')).toBeInTheDocument();

    // Testa botão de ir para lista de equipamentos
    const verListaBtn = screen.getByText('Ver Lista de Equipamentos');
    fireEvent.click(verListaBtn);
    expect(await screen.findByText('Página de Equipamentos')).toBeInTheDocument();
  });

  it('Permite resetar o estado e importar outro arquivo', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData);
    (importApi.executeImport as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockImportResult);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'patrimonio.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const fileInput = screen.getByTestId('spreadsheet-file-input');
    fireEvent.change(fileInput, { target: { files: [file] } });

    const confirmBtn = await screen.findByTestId('confirm-import-button');
    fireEvent.click(confirmBtn);

    const outroArquivoBtn = await screen.findByText('Importar Outro Arquivo');
    fireEvent.click(outroArquivoBtn);

    expect(screen.queryByTestId('import-success-card')).not.toBeInTheDocument();
    expect(screen.getByText('Carregar Arquivo de Inventário')).toBeInTheDocument();
  });

  it('Exibe banner de erro quando preview falha', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'A aba Patrimônio está vazia.',
        },
      },
    });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'invalido.xlsx');
    const fileInput = screen.getByTestId('spreadsheet-file-input');
    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(await screen.findByText('A aba Patrimônio está vazia.')).toBeInTheDocument();
  });

  it('Exibe banner de erro quando execução falha', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData);
    (importApi.executeImport as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: {
        data: {
          detail: 'Erro de integridade no banco.',
        },
      },
    });

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'patrimonio.xlsx');
    const fileInput = screen.getByTestId('spreadsheet-file-input');
    fireEvent.change(fileInput, { target: { files: [file] } });

    const confirmBtn = await screen.findByTestId('confirm-import-button');
    fireEvent.click(confirmBtn);

    expect(await screen.findByText('Erro de integridade no banco.')).toBeInTheDocument();
  });

  it('Suporta eventos de drag and drop na zona de upload', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const dropZone = screen.getByText('Clique para escolher o arquivo').closest('div')!.parentElement!;

    fireEvent.dragOver(dropZone);
    fireEvent.dragLeave(dropZone);

    const file = new File(['csv content'], 'dados.csv', { type: 'text/csv' });
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
      },
    });

    await waitFor(() => {
      expect(importApi.previewSpreadsheet).toHaveBeenCalledWith(file);
    });
  });

  it('Exibe fallback de erro genérico e limpa o input de arquivo ao reiniciar', async () => {
    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData);
    (importApi.executeImport as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Falha de rede sem resposta')
    );

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'patrimonio.xlsx');
    const fileInput = screen.getByTestId('spreadsheet-file-input');
    fireEvent.change(fileInput, { target: { files: [file] } });

    const confirmBtn = await screen.findByTestId('confirm-import-button');
    fireEvent.click(confirmBtn);

    expect(await screen.findByText('Falha de rede sem resposta')).toBeInTheDocument();

    // Clicar em reiniciar / cancelar pré-visualização
    const resetBtn = screen.getByRole('button', { name: 'Cancelar' });
    fireEvent.click(resetBtn);

    expect(screen.getByText('Carregar Arquivo de Inventário')).toBeInTheDocument();
  });

  it('cobre branches de linhas com campos vazios (linhas 368-378, 386)', async () => {
    const mockPreviewWithEmptyFields = {
      filename: 'vazio.xlsx',
      total_rows: 1,
      sample_rows: [
        {
          row_number: 99,
          equipment_type: '',
          location: '',
          status: '',
          description: '',
          patrimony_number: null,
          serial_number: null,
          brand: '',
          last_maintenance_at: '',
        },
      ],
      detected_sheet: 'Patrimônio',
      headers: ['TIPO', 'LOCALIZAÇÃO'],
    };

    (importApi.previewSpreadsheet as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewWithEmptyFields);

    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const file = new File(['mock content'], 'vazio.xlsx');
    const fileInput = screen.getByTestId('spreadsheet-file-input');
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('vazio.xlsx')).toBeInTheDocument();
    });

    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(4);
  });

  it('suporta drop com lista de arquivos vazia', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/importar']}>
          <Routes>
            <Route path="/importar" element={<ImportPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );

    const dropZone = screen.getByText('Clique para escolher o arquivo').closest('div')!.parentElement!;
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [],
      },
    });

    expect(importApi.previewSpreadsheet).not.toHaveBeenCalled();
  });
});


