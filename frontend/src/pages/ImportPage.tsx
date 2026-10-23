import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  RefreshCw,
  Layers,
  HardDrive,
  Tag,
  Wrench,
  X,
} from 'lucide-react';
import { SideMenu } from '../components/SideMenu';
import { AlertBanner } from '../components/AlertBanner';
import {
  importApi,
  SpreadsheetImportPreviewResponse,
  SpreadsheetImportResultResponse,
} from '../api/importApi';

export const ImportPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingExecute, setLoadingExecute] = useState(false);
  const [previewData, setPreviewData] = useState<SpreadsheetImportPreviewResponse | null>(null);
  const [importResult, setImportResult] = useState<SpreadsheetImportResultResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setErrorMessage(null);
    setImportResult(null);
    setFile(selectedFile);
    setLoadingPreview(true);

    try {
      const data = await importApi.previewSpreadsheet(selectedFile);
      setPreviewData(data);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Não foi possível ler a planilha. Verifique o formato do arquivo.';
      setErrorMessage(msg);
      setPreviewData(null);
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelect(droppedFile);
    }
  };

  const handleConfirmImport = async () => {
    if (!file) return;
    setLoadingExecute(true);
    setErrorMessage(null);

    try {
      const result = await importApi.executeImport(file);
      setImportResult(result);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Erro ao processar importação no banco de dados.';
      setErrorMessage(msg);
    } finally {
      setLoadingExecute(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreviewData(null);
    setImportResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="min-h-screen bg-[#121212] text-[#E0E0E0] font-sans pb-16">
      {/* Header Superior */}
      <header className="sticky top-0 z-30 bg-[#1E1E1E]/90 backdrop-blur-md border-b border-[#333333] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <SideMenu />
            <div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => navigate('/equipamentos')}
                  className="text-xs text-[#9E9E9E] hover:text-white flex items-center gap-1 transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Patrimônio
                </button>
                <span className="text-[#555555]">/</span>
                <span className="text-xs font-medium text-white">Importação</span>
              </div>
              <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2 mt-0.5">
                <FileSpreadsheet className="w-5 h-5 text-blue-400" />
                Importação de Planilha
              </h1>
            </div>
          </div>
        </div>
      </header>

      {/* Conteúdo Principal */}
      <main className="max-w-6xl mx-auto px-6 pt-8 space-y-6">
        {errorMessage && (
          <AlertBanner
            type="error"
            message={errorMessage}
            onClose={() => setErrorMessage(null)}
          />
        )}

        {/* 1. Estado de Conclusão / Sucesso */}
        {importResult && (
          <div
            data-testid="import-success-card"
            className="bg-[#1E1E1E] border border-green-500/30 rounded-xl p-8 shadow-xl space-y-6"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-green-500/10 border border-green-500/20 flex items-center justify-center text-green-400">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Importação Concluída com Sucesso!</h2>
                <p className="text-sm text-[#9E9E9E]">{importResult.message}</p>
              </div>
            </div>

            {/* Grid de Estatísticas */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-[#121212] border border-[#333333] p-4 rounded-lg">
                <div className="flex items-center gap-2 text-blue-400 mb-1">
                  <HardDrive className="w-4 h-4" />
                  <span className="text-xs font-mono uppercase tracking-wider text-[#9E9E9E]">Novos</span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {importResult.created_count}
                </div>
                <div className="text-[11px] text-[#757575] mt-0.5">Equipamentos inseridos</div>
              </div>

              <div className="bg-[#121212] border border-[#333333] p-4 rounded-lg">
                <div className="flex items-center gap-2 text-amber-400 mb-1">
                  <RefreshCw className="w-4 h-4" />
                  <span className="text-xs font-mono uppercase tracking-wider text-[#9E9E9E]">Atualizados</span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {importResult.updated_count}
                </div>
                <div className="text-[11px] text-[#757575] mt-0.5">Registros mesclados (upsert)</div>
              </div>

              <div className="bg-[#121212] border border-[#333333] p-4 rounded-lg">
                <div className="flex items-center gap-2 text-purple-400 mb-1">
                  <Tag className="w-4 h-4" />
                  <span className="text-xs font-mono uppercase tracking-wider text-[#9E9E9E]">Novas Tags</span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {importResult.tags_created_count}
                </div>
                <div className="text-[11px] text-[#757575] mt-0.5">Categorias cadastradas</div>
              </div>

              <div className="bg-[#121212] border border-[#333333] p-4 rounded-lg">
                <div className="flex items-center gap-2 text-emerald-400 mb-1">
                  <Wrench className="w-4 h-4" />
                  <span className="text-xs font-mono uppercase tracking-wider text-[#9E9E9E]">Manutenções</span>
                </div>
                <div className="text-2xl font-bold text-white font-mono">
                  {importResult.maintenances_created_count}
                </div>
                <div className="text-[11px] text-[#757575] mt-0.5">Históricos consolidados</div>
              </div>
            </div>

            {/* Ações após importação */}
            <div className="flex flex-wrap items-center justify-end gap-3 pt-4 border-t border-[#333333]">
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg bg-[#2A2A2A] hover:bg-[#333333] text-sm text-[#E0E0E0] hover:text-white transition-colors cursor-pointer"
              >
                Importar Outro Arquivo
              </button>
              <button
                onClick={() => navigate('/equipamentos')}
                className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm font-semibold text-white shadow-md transition-colors cursor-pointer flex items-center gap-2"
              >
                <HardDrive className="w-4 h-4" />
                <span>Ver Lista de Equipamentos</span>
              </button>
            </div>
          </div>
        )}

        {/* 2. Área de Upload (caso ainda não tenha importado com sucesso) */}
        {!importResult && (
          <div className="bg-[#1E1E1E] border border-[#333333] rounded-xl p-6 shadow-md space-y-6">
            <div>
              <h2 className="text-base font-semibold text-white">Carregar Arquivo de Inventário</h2>
              <p className="text-xs text-[#9E9E9E] mt-1">
                Suporta planilhas no formato <span className="text-white font-mono">.xlsx</span> ou{' '}
                <span className="text-white font-mono">.csv</span>. Mapeia automaticamente as colunas da aba
                Patrimônio e cria novos equipamentos ou atualiza existentes.
              </p>
            </div>

            {/* Drag and Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all ${
                isDragging
                  ? 'border-blue-500 bg-blue-500/10'
                  : file
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'border-[#444444] hover:border-[#666666] bg-[#161616]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                className="hidden"
                data-testid="spreadsheet-file-input"
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
              />

              {loadingPreview ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm font-medium text-white">Lendo e validando estrutura da planilha...</span>
                </div>
              ) : file ? (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                    <FileSpreadsheet className="w-6 h-6" />
                  </div>
                  <div className="font-semibold text-white text-sm">{file.name}</div>
                  <div className="text-xs text-[#9E9E9E] font-mono">
                    {(file.size / 1024).toFixed(1)} KB — Clique ou arraste para substituir
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-[#2A2A2A] border border-[#333333] flex items-center justify-center text-[#9E9E9E]">
                    <UploadCloud className="w-6 h-6" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-white">
                      Clique para escolher o arquivo
                    </span>{' '}
                    <span className="text-sm text-[#9E9E9E]">ou arraste-o até aqui</span>
                  </div>
                  <p className="text-xs text-[#757575] font-mono">Formatos aceitos: .xlsx, .xls, .csv</p>
                </div>
              )}
            </div>

            {/* Painel de Prévia */}
            {previewData && (
              <div className="space-y-4 pt-4 border-t border-[#333333]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Layers className="w-4 h-4 text-blue-400" />
                      Pré-visualização dos Dados
                    </h3>
                    <p className="text-xs text-[#9E9E9E]">
                      Total de{' '}
                      <span className="text-white font-bold font-mono">
                        {previewData.total_rows}
                      </span>{' '}
                      linhas com dados identificadas.{' '}
                      {previewData.detected_sheet && (
                        <span>
                          (Aba: <strong className="text-blue-300 font-mono">{previewData.detected_sheet}</strong>)
                        </span>
                      )}
                    </p>
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleReset}
                      disabled={loadingExecute}
                      className="px-3.5 py-1.5 rounded-lg bg-[#2A2A2A] hover:bg-[#333333] text-xs font-medium text-[#E0E0E0] hover:text-white transition-colors cursor-pointer"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleConfirmImport}
                      disabled={loadingExecute}
                      data-testid="confirm-import-button"
                      className="px-5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-xs font-semibold text-white shadow-md transition-colors cursor-pointer flex items-center gap-2"
                    >
                      {loadingExecute ? (
                        <>
                          <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Gravando no banco...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Confirmar e Importar {previewData.total_rows} Itens</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Tabela de Amostra */}
                <div className="border border-[#333333] rounded-lg overflow-x-auto bg-[#161616]">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#1E1E1E] text-[#9E9E9E] font-mono uppercase text-[10px] border-b border-[#333333]">
                      <tr>
                        <th className="p-2.5">#</th>
                        <th className="p-2.5">Tipo</th>
                        <th className="p-2.5">Localização</th>
                        <th className="p-2.5">Situação</th>
                        <th className="p-2.5">Descrição</th>
                        <th className="p-2.5">Patrimônio</th>
                        <th className="p-2.5">Nº Série</th>
                        <th className="p-2.5">Marca</th>
                        <th className="p-2.5">Última Manut.</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#2A2A2A]">
                      {previewData.sample_rows.map((row) => (
                        <tr key={row.row_number} className="hover:bg-white/5 transition-colors">
                          <td className="p-2.5 text-[#757575] font-mono">{row.row_number}</td>
                          <td className="p-2.5">
                            <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 font-medium text-[11px]">
                              {row.equipment_type || '—'}
                            </span>
                          </td>
                          <td className="p-2.5 text-white font-medium">{row.location || '—'}</td>
                          <td className="p-2.5">
                            <span className="px-2 py-0.5 rounded bg-[#2A2A2A] text-[#E0E0E0] text-[11px]">
                              {row.status || '—'}
                            </span>
                          </td>
                          <td className="p-2.5 max-w-[200px] truncate text-[#D0D0D0]">
                            {row.description || '—'}
                          </td>
                          <td className="p-2.5 font-mono text-white">
                            {row.patrimony_number || <span className="text-[#555555]">vazio</span>}
                          </td>
                          <td className="p-2.5 font-mono text-[#A0A0A0]">
                            {row.serial_number || <span className="text-[#555555]">vazio</span>}
                          </td>
                          <td className="p-2.5 text-[#B0B0B0]">{row.brand || '—'}</td>
                          <td className="p-2.5 font-mono text-[#9E9E9E]">
                            {row.last_maintenance_at || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="text-[11px] text-[#757575] text-right font-mono">
                  Mostrando primeiras {previewData.sample_rows.length} de {previewData.total_rows} linhas
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};
