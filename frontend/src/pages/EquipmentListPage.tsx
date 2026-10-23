import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  HardDrive,
  Plus,
  Search,
  RotateCcw,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  ArrowLeft,
  Monitor,
  Laptop,
  Smartphone,
  Printer,
  Calendar,
  MapPin,
  Tag,
  FileSpreadsheet,
  Loader2,
} from 'lucide-react';
import { equipmentApi } from '../api/equipmentApi';
import { Equipment, EquipmentFilterParams, EquipmentTag } from '../types/equipment';
import { SideMenu } from '../components/SideMenu';
import { NewEquipmentModal } from '../components/NewEquipmentModal';
import { ManageTagsModal } from '../components/ManageTagsModal';
import { MultiSelectFilterDropdown } from '../components/MultiSelectFilterDropdown';
import { AutocompleteFilterInput } from '../components/AutocompleteFilterInput';

export const EquipmentListPage: React.FC = () => {
  const navigate = useNavigate();

  // Data states
  const [equipments, setEquipments] = useState<Equipment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Tag filter options
  const [types, setTypes] = useState<EquipmentTag[]>([]);
  const [locations, setLocations] = useState<EquipmentTag[]>([]);
  const [statuses, setStatuses] = useState<EquipmentTag[]>([]);

  // Multi-select filter states (RN-09 / RN-12)
  const [filterTypes, setFilterTypes] = useState<string[]>([]);
  const [filterLocations, setFilterLocations] = useState<string[]>([]);
  const [filterStatuses, setFilterStatuses] = useState<string[]>([]);
  const [filterPatrimonies, setFilterPatrimonies] = useState<string[]>([]);
  const [filterSerials, setFilterSerials] = useState<string[]>([]);
  const [filterProducts, setFilterProducts] = useState<string[]>([]);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Modals & Actions
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [isTagsModalOpen, setIsTagsModalOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);


  useEffect(() => {
    fetchTags();
  }, []);

  useEffect(() => {
    fetchEquipments();
  }, [
    page,
    filterTypes,
    filterLocations,
    filterStatuses,
    filterPatrimonies,
    filterSerials,
    filterProducts,
    search,
    sortBy,
    sortDir,
  ]);

  const fetchTags = async () => {
    try {
      const allTags = await equipmentApi.getTags();
      setTypes(allTags.filter((t) => t.category === 'tipo'));
      setLocations(allTags.filter((t) => t.category === 'localizacao'));
      setStatuses(allTags.filter((t) => t.category === 'situacao'));
    } catch (err) {
      console.error('Erro ao carregar tags:', err);
    }
  };

  const fetchEquipments = async () => {
    setLoading(true);
    try {
      const params: EquipmentFilterParams = {
        page,
        limit: 25,
        type: filterTypes.length > 0 ? filterTypes : undefined,
        location: filterLocations.length > 0 ? filterLocations : undefined,
        status: filterStatuses.length > 0 ? filterStatuses : undefined,
        patrimony_number: filterPatrimonies.length > 0 ? filterPatrimonies : undefined,
        serial_number: filterSerials.length > 0 ? filterSerials : undefined,
        product_number: filterProducts.length > 0 ? filterProducts : undefined,
        search: search || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      };

      const res = await equipmentApi.getEquipments(params);
      setEquipments(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err) {
      console.error('Erro ao buscar equipamentos:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilters = () => {
    setFilterTypes([]);
    setFilterLocations([]);
    setFilterStatuses([]);
    setFilterPatrimonies([]);
    setFilterSerials([]);
    setFilterProducts([]);
    setSearch('');
    setSortBy('created_at');
    setSortDir('desc');
    setPage(1);
  };


  const hasActiveFilters =
    filterTypes.length > 0 ||
    filterLocations.length > 0 ||
    filterStatuses.length > 0 ||
    filterPatrimonies.length > 0 ||
    filterSerials.length > 0 ||
    filterProducts.length > 0 ||
    Boolean(search);

  const getEquipmentIcon = (type?: any) => {
    const raw = typeof type === 'object' && type !== null ? type.name : type;
    const t = String(raw || '').toLowerCase();
    if (t.includes('notebook') || t.includes('laptop')) return <Laptop className="w-5 h-5 text-zinc-300" />;
    if (t.includes('monitor') || t.includes('tela')) return <Monitor className="w-5 h-5 text-zinc-300" />;
    if (t.includes('impressora')) return <Printer className="w-5 h-5 text-zinc-300" />;
    if (t.includes('celular') || t.includes('tablet')) return <Smartphone className="w-5 h-5 text-zinc-300" />;
    return <HardDrive className="w-5 h-5 text-zinc-300" />;
  };

  const renderStatusPill = (status?: any) => {
    const raw = typeof status === 'object' && status !== null ? status.name : status;
    const safeStatus = String(raw || 'Não definido');
    const s = safeStatus.toLowerCase();
    if (s.includes('uso') || s.includes('ativo')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
          {safeStatus}
        </span>
      );
    }
    if (s.includes('manuten') || s.includes('repar') || s.includes('recolhimento')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          {safeStatus}
        </span>
      );
    }
    if (s.includes('ocioso') || s.includes('estoque') || s.includes('dispon')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          {safeStatus}
        </span>
      );
    }
    if (s.includes('baixado') || s.includes('descarte') || s.includes('inativ')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-zinc-600/20 text-zinc-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
          {safeStatus}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 font-medium text-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
        {safeStatus}
      </span>
    );
  };

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'Não registrada';
    const date = new Date(dateStr);
    return date.toLocaleDateString('pt-BR');
  };

  const handleAddTextFilter = (
    value: string,
    currentList: string[],
    setList: (val: string[]) => void
  ) => {
    const clean = value.trim();
    if (!clean) return;
    if (!currentList.includes(clean)) {
      setList([...currentList, clean]);
      setPage(1);
    }
  };

  const handleExport = async () => {
    try {
      setIsExporting(true);
      const params: Omit<EquipmentFilterParams, 'page' | 'limit'> = {
        type: filterTypes.length > 0 ? filterTypes : undefined,
        location: filterLocations.length > 0 ? filterLocations : undefined,
        status: filterStatuses.length > 0 ? filterStatuses : undefined,
        patrimony_number: filterPatrimonies.length > 0 ? filterPatrimonies : undefined,
        serial_number: filterSerials.length > 0 ? filterSerials : undefined,
        product_number: filterProducts.length > 0 ? filterProducts : undefined,
        search: search.trim() || undefined,
        sort_by: sortBy,
        sort_dir: sortDir,
      };

      const { data, filename } = await equipmentApi.exportEquipments(params);
      const blobUrl = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement('a');
      link.href = blobUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error('Erro ao exportar planilha:', err);
    } finally {
      setIsExporting(false);
    }
  };


  return (
    <div className="min-h-screen bg-[#121212] text-[#E0E0E0] font-sans antialiased flex flex-col selection:bg-zinc-800 selection:text-white">
      {/* Top Navigation Bar */}
      <header className="border-b border-[#333333] bg-[#1E1E1E] px-6 py-4 flex items-center justify-between sticky top-0 z-30">
        <div className="flex items-center gap-4">
          <SideMenu />

          {/* Back to Dashboard */}
          <button
            onClick={() => navigate('/dashboard')}
            data-testid="back-to-dashboard-btn"
            className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[#333333] hover:bg-[#333333] transition-colors text-sm font-medium text-[#E0E0E0] cursor-pointer"
            title="Voltar ao Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Voltar ao Dashboard</span>
          </button>

          {/* Page Title & Count */}
          <div className="flex items-center gap-3 ml-2">
            <h1 className="text-xl font-semibold text-white">Equipamentos</h1>
            <span className="px-2 py-0.5 rounded bg-[#333333] text-xs text-[#9E9E9E] font-medium font-mono">
              {total} {total === 1 ? 'item' : 'itens'}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={handleExport}
            disabled={isExporting}
            data-testid="export-spreadsheet-btn"
            className="flex items-center gap-2 px-3 py-2 bg-[#1E1E1E] border border-[#333333] hover:bg-[#333333] text-[#E0E0E0] hover:text-white rounded-md transition-colors text-sm font-medium cursor-pointer shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            title="Exportar Planilha"
          >
            {isExporting ? (
              <Loader2 className="w-4 h-4 animate-spin text-[#9E9E9E]" />
            ) : (
              <FileSpreadsheet className="w-4 h-4" />
            )}
            <span className="hidden sm:inline">Exportar Planilha</span>
          </button>

          <button
            onClick={() => setIsTagsModalOpen(true)}
            data-testid="manage-tags-btn"
            className="flex items-center gap-2 px-3 py-2 bg-[#1E1E1E] border border-[#333333] hover:bg-[#333333] text-[#E0E0E0] hover:text-white rounded-md transition-colors text-sm font-medium cursor-pointer shadow-sm"
            title="Gerenciar Tags"
          >
            <Tag className="w-4 h-4" />
            <span className="hidden sm:inline">Gerenciar Tags</span>
          </button>

          <button
            onClick={() => setIsNewModalOpen(true)}
            data-testid="new-equipment-btn"
            className="flex items-center gap-2 px-4 py-2 bg-white text-[#121212] font-semibold rounded-md hover:bg-gray-200 transition-colors text-sm cursor-pointer shadow-sm active:scale-[0.99]"
          >
            <Plus className="w-4 h-4" />
            <span>Novo Equipamento</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto p-6 max-w-7xl mx-auto w-full space-y-5">
        {/* Filters & Search Section */}
        <section className="bg-[#1E1E1E] border border-[#333333] rounded-lg p-4 mb-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-[#9E9E9E] font-medium text-sm">
              <SlidersHorizontal className="w-4 h-4 text-[#9E9E9E]" />
              <span>Filtros &amp; Busca</span>
            </div>

            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="text-xs text-[#9E9E9E] hover:text-white flex items-center gap-1 transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Limpar filtros</span>
              </button>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            {/* Multi-Select Dropdowns */}
            <MultiSelectFilterDropdown
              label="Tipo"
              options={types.map((t) => t.name)}
              selectedValues={filterTypes}
              onChange={(vals) => { setFilterTypes(vals); setPage(1); }}
              placeholder="Pesquisar tipo..."
              testId="filter-type-dropdown"
            />

            <MultiSelectFilterDropdown
              label="Localização"
              options={locations.map((l) => l.name)}
              selectedValues={filterLocations}
              onChange={(vals) => { setFilterLocations(vals); setPage(1); }}
              placeholder="Pesquisar localização..."
              testId="filter-location-dropdown"
            />

            <MultiSelectFilterDropdown
              label="Situação"
              options={statuses.map((s) => s.name)}
              selectedValues={filterStatuses}
              onChange={(vals) => { setFilterStatuses(vals); setPage(1); }}
              placeholder="Pesquisar situação..."
              testId="filter-status-dropdown"
            />

            {/* Autocomplete Input Filters (RN-AC-01 a RN-AC-07) */}
            <AutocompleteFilterInput
              field="patrimony_number"
              placeholder="Patrimônio..."
              selectedValues={filterPatrimonies}
              onAddValue={(val) => handleAddTextFilter(val, filterPatrimonies, setFilterPatrimonies)}
              testId="filter-patrimony-input"
            />

            <AutocompleteFilterInput
              field="serial_number"
              placeholder="Série..."
              selectedValues={filterSerials}
              onAddValue={(val) => handleAddTextFilter(val, filterSerials, setFilterSerials)}
              testId="filter-serial-input"
            />

            <AutocompleteFilterInput
              field="product_number"
              placeholder="Produto..."
              selectedValues={filterProducts}
              onAddValue={(val) => handleAddTextFilter(val, filterProducts, setFilterProducts)}
              testId="filter-product-input"
            />


            {/* Global Search */}
            <div className="relative flex-1 min-w-[200px]">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#9E9E9E]">
                <Search className="w-4 h-4" />
              </div>
              <input
                type="text"
                placeholder="Pesquisar..."
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                className="bg-[#121212] border border-[#333333] text-[#E0E0E0] text-sm rounded-md pl-9 pr-3 py-2 w-full focus:ring-1 focus:ring-[#9E9E9E] focus:border-[#9E9E9E] focus:outline-none placeholder-[#9E9E9E]/50"
              />
            </div>
          </div>

          {/* Active Chips */}
          {(filterPatrimonies.length > 0 || filterSerials.length > 0 || filterProducts.length > 0) && (
            <div className="flex items-center gap-1.5 flex-wrap pt-3 border-t border-[#333333] mt-3 text-[11px]">
              {filterPatrimonies.map((pat) => (
                <span key={pat} className="px-2 py-0.5 rounded bg-[#121212] border border-[#333333] text-white font-mono flex items-center gap-1">
                  Patrimônio: {pat}
                  <button onClick={() => setFilterPatrimonies(filterPatrimonies.filter((p) => p !== pat))} className="hover:text-red-400">×</button>
                </span>
              ))}
              {filterSerials.map((ser) => (
                <span key={ser} className="px-2 py-0.5 rounded bg-[#121212] border border-[#333333] text-white font-mono flex items-center gap-1">
                  Série: {ser}
                  <button onClick={() => setFilterSerials(filterSerials.filter((s) => s !== ser))} className="hover:text-red-400">×</button>
                </span>
              ))}
              {filterProducts.map((prod) => (
                <span key={prod} className="px-2 py-0.5 rounded bg-[#121212] border border-[#333333] text-white font-mono flex items-center gap-1">
                  Produto: {prod}
                  <button onClick={() => setFilterProducts(filterProducts.filter((pr) => pr !== prod))} className="hover:text-red-400">×</button>
                </span>
              ))}
            </div>
          )}
        </section>

        {/* List Header Controls */}
        <div className="flex items-center justify-between mb-4 px-1">
          <div className="flex items-center gap-3">
            <span className="text-sm text-[#9E9E9E]">Ordenar por:</span>
            <div className="relative">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="appearance-none bg-[#1E1E1E] border border-[#333333] text-[#E0E0E0] text-sm rounded-md pl-3 pr-8 py-1.5 focus:ring-1 focus:ring-[#9E9E9E] focus:border-[#9E9E9E] focus:outline-none cursor-pointer"
              >
                <option value="created_at">Mais recentes / Antigos</option>
                <option value="last_maintenance_at">Última manutenção</option>
                <option value="serial_number">Nº Série</option>
                <option value="patrimony_number">Nº Patrimônio</option>
                <option value="equipment_type">Tipo</option>
                <option value="location">Localização</option>
              </select>
            </div>

            <button
              onClick={() => setSortDir(sortDir === 'asc' ? 'desc' : 'asc')}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1E1E1E] border border-[#333333] rounded-md text-sm text-[#E0E0E0] hover:bg-[#333333] transition-colors cursor-pointer"
            >
              {sortDir === 'asc' ? '↑ Crescente' : '↓ Decrescente'}
            </button>
          </div>

          <div className="text-sm text-[#9E9E9E]">
            Pág. <span className="text-white font-medium font-mono">{page}</span> de <span className="text-white font-medium font-mono">{pages}</span>
          </div>
        </div>

        {/* Equipment List */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center gap-3 text-[#9E9E9E]">
            <div className="w-6 h-6 border-2 border-[#333333] border-t-white rounded-full animate-spin" />
            <p className="text-xs">Carregando equipamentos...</p>
          </div>
        ) : equipments.length === 0 ? (
          <div className="py-16 text-center bg-[#1E1E1E] border border-[#333333] rounded-lg space-y-2">
            <HardDrive className="w-8 h-8 text-[#9E9E9E] mx-auto" />
            <p className="text-sm font-semibold text-white">Nenhum equipamento encontrado</p>
            <p className="text-xs text-[#9E9E9E]">Tente ajustar os filtros de pesquisa para visualizar outros ativos.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {equipments.map((item, index) => {
              return (
                <article
                  key={item.id}
                  onClick={() => navigate(`/equipamentos/${item.id}`)}
                  style={{ animationDelay: `${index * 20}ms` }}
                  data-testid={`equipment-card-${item.id}`}
                  className="bg-[#1E1E1E] border border-[#333333] rounded-lg p-4 flex items-start gap-4 hover:border-gray-500 transition-colors cursor-pointer animate-slide-in-right opacity-0"
                >
                  {/* Icon Box */}
                  <div className="w-12 h-12 rounded-lg bg-[#121212] border border-[#333333] flex items-center justify-center shrink-0 text-[#9E9E9E]">
                    {getEquipmentIcon(item.equipment_type)}
                  </div>

                  {/* Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3 className="text-base font-medium text-white truncate">
                        {item.description}
                      </h3>
                      {item.brand && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-white/10 text-gray-300">
                          {item.brand}
                        </span>
                      )}
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-white/10 text-gray-300 font-mono">
                        {typeof item.equipment_type === 'object' && item.equipment_type !== null
                          ? (item.equipment_type as any).name
                          : item.equipment_type}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-[#9E9E9E] mt-2 flex-wrap">
                      {/* Status with Dot */}
                      {renderStatusPill(item.status)}

                      <span className="text-[#333333]">•</span>

                      {/* Location with Icon */}
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-[#9E9E9E]" />
                        <span className="text-[#E0E0E0]">
                          {typeof (item as any).sector === 'object' && (item as any).sector !== null
                            ? (item as any).sector.name
                            : typeof item.location === 'object' && item.location !== null
                            ? (item.location as any).name
                            : item.location || (item as any).sector || 'Não definido'}
                        </span>
                      </span>

                      {item.patrimony_number && (
                        <>
                          <span className="text-[#333333]">•</span>
                          <span>Patrimônio: <span className="text-white font-mono font-medium">{item.patrimony_number}</span></span>
                        </>
                      )}

                      <span className="text-[#333333]">•</span>
                      <span>SN: <span className="text-white font-mono font-medium">{item.serial_number}</span></span>
                    </div>
                  </div>

                  {/* Meta Info: Última Manutenção */}
                  <div className="shrink-0 text-right flex flex-col justify-between h-full py-1 min-w-[120px]">
                    <span className="text-[10px] font-medium text-[#9E9E9E] uppercase tracking-wider mb-1 font-mono">
                      Última Manutenção
                    </span>
                    <div className="flex items-center justify-end gap-1.5 text-xs text-[#E0E0E0] font-mono">
                      <Calendar className="w-3.5 h-3.5 text-[#9E9E9E]" />
                      <span>{formatDate(item.last_maintenance_at)}</span>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        {/* Pagination Controls */}
        {pages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-[#333333]">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="px-3 py-1.5 bg-[#1E1E1E] border border-[#333333] hover:bg-[#333333] text-[#E0E0E0] disabled:opacity-40 rounded-md text-xs flex items-center gap-1 transition-colors cursor-pointer"
            >
              <ChevronLeft className="w-3.5 h-3.5" /> Anterior
            </button>

            <span className="text-xs text-[#9E9E9E] font-mono">
              Página <strong className="text-white">{page}</strong> de <strong className="text-white">{pages}</strong>
            </span>

            <button
              disabled={page >= pages}
              onClick={() => setPage((p) => Math.min(pages, p + 1))}
              className="px-3 py-1.5 bg-[#1E1E1E] border border-[#333333] hover:bg-[#333333] text-[#E0E0E0] disabled:opacity-40 rounded-md text-xs flex items-center gap-1 transition-colors cursor-pointer"
            >
              Próxima <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </main>

      {/* Modal de Cadastro de Equipamento */}
      <NewEquipmentModal
        isOpen={isNewModalOpen}
        onClose={() => setIsNewModalOpen(false)}
        onSuccess={() => {
          fetchEquipments();
          fetchTags();
        }}
      />

      {/* Modal de Gerenciamento de Tags */}
      <ManageTagsModal
        isOpen={isTagsModalOpen}
        onClose={() => setIsTagsModalOpen(false)}
        onTagsUpdated={() => {
          fetchTags();
          fetchEquipments();
        }}
      />
    </div>
  );
};
