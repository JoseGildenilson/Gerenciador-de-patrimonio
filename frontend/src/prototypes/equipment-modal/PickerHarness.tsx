import React, { useState, useEffect } from 'react';
import { Variant1Stepper } from './Variant1Stepper';
import { Variant2CommandDrawer } from './Variant2CommandDrawer';
import { Variant3LiveCardStudio } from './Variant3LiveCardStudio';
import { INITIAL_TAGS, BACKGROUND_MOCK_EQUIPMENTS, PrototypeTag } from './mockData';
import { Plus, Search, Filter, HardDrive, RefreshCw, Layers, Zap, Box, Check, ArrowRight } from 'lucide-react';

const VARIANTS = [
  { id: 1, name: 'Structured Stepper', subtitle: 'Wizard guiado em 3 etapas', icon: Layers, axis: 'Pacing & Density' },
  { id: 2, name: 'Command Drawer', subtitle: 'Slide-over lateral ágil para TI', icon: Zap, axis: 'Productivity & Speed' },
  { id: 3, name: 'Live Card Studio', subtitle: 'Split view com prévia viva do cartão', icon: Box, axis: 'Visual Hierarchy & Live Feedback' },
];

export const EquipmentModalPrototypeHarness: React.FC = () => {
  const [selectedVariant, setSelectedVariant] = useState<number>(1);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(true);
  const [tags, setTags] = useState<PrototypeTag[]>(INITIAL_TAGS);
  const [equipments, setEquipments] = useState(BACKGROUND_MOCK_EQUIPMENTS);
  const [lastCreated, setLastCreated] = useState<string | null>(null);

  // Keyboard navigation for picker (1, 2, 3)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if typing in an input
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        return;
      }
      if (e.key === '1') setSelectedVariant(1);
      if (e.key === '2') setSelectedVariant(2);
      if (e.key === '3') setSelectedVariant(3);
      if (e.key.toLowerCase() === 'o') setIsModalOpen((prev) => !prev);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handleAddTag = (category: 'tipo' | 'localizacao' | 'situacao', name: string) => {
    const newTag: PrototypeTag = {
      id: Date.now(),
      category,
      name,
    };
    setTags((prev) => [...prev, newTag]);
  };

  const handleCreatedEquipment = (payload: any) => {
    const newItem = {
      id: Date.now(),
      patrimony_number: payload.patrimonyNumber || `PAT-${Math.floor(1000 + Math.random() * 9000)}`,
      serial_number: payload.serialNumber,
      description: payload.description,
      equipment_type: payload.equipmentType,
      location: payload.location,
      status: payload.status,
      brand: payload.brand || 'Genérico',
      hostname: payload.hostname || null,
    };
    setEquipments((prev) => [newItem, ...prev]);
    setLastCreated(newItem.patrimony_number);
    setIsModalOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative font-sans">
      {/* Top Banner indicating Prototype Mode */}
      <div className="bg-slate-900/90 border-b border-slate-800 px-6 py-2.5 flex items-center justify-between text-xs backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
          <span className="font-semibold text-white tracking-wide">PROTÓTIPO: MODAL DE CADASTRO DE EQUIPAMENTO</span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400 hidden sm:inline">Use as teclas 1, 2, 3 para alternar instantaneamente</span>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="px-3 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 rounded-lg font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" /> Abrir Modal Novamente
        </button>
      </div>

      {/* Realistic Background Inventory Context */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8 space-y-6 opacity-60 pointer-events-auto">
        {/* Header with Title and Quick Add Button */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
              <HardDrive className="w-6 h-6 text-blue-500" />
              Inventário de Patrimônio
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Controle e rastreamento de ativos de TI corporativos
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Novo Equipamento
          </button>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-4">
            <span className="text-xs text-slate-400">Total de Ativos</span>
            <div className="text-2xl font-bold text-white mt-1">{equipments.length + 42}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-4">
            <span className="text-xs text-emerald-400">Em Uso</span>
            <div className="text-2xl font-bold text-white mt-1">38</div>
          </div>
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-4">
            <span className="text-xs text-blue-400">Em Estoque</span>
            <div className="text-2xl font-bold text-white mt-1">7</div>
          </div>
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-4">
            <span className="text-xs text-amber-400">Em Manutenção</span>
            <div className="text-2xl font-bold text-white mt-1">1</div>
          </div>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 bg-slate-900/50 p-2 rounded-2xl border border-slate-800">
          <div className="flex-1 flex items-center gap-2 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800 text-xs">
            <Search className="w-4 h-4 text-slate-500" />
            <input
              type="text"
              readOnly
              value=""
              placeholder="Buscar por descrição, patrimônio, serial ou hostname..."
              className="bg-transparent text-white outline-none w-full placeholder:text-slate-600"
            />
          </div>
          <button className="px-3.5 py-2 bg-slate-800 text-slate-300 text-xs font-semibold rounded-xl flex items-center gap-1.5 border border-slate-700/50">
            <Filter className="w-3.5 h-3.5" /> Filtros
          </button>
        </div>

        {/* Table of Equipments */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Patrimônio</th>
                <th className="py-3 px-4">Descrição</th>
                <th className="py-3 px-4">Tipo</th>
                <th className="py-3 px-4">Localização</th>
                <th className="py-3 px-4">Situação</th>
                <th className="py-3 px-4">Hostname</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {equipments.map((eq) => (
                <tr key={eq.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-blue-400">{eq.patrimony_number}</td>
                  <td className="py-3.5 px-4 font-medium text-white">{eq.description}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                      {eq.equipment_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-300">{eq.location}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2.5 py-0.5 rounded-full font-semibold ${
                        eq.status === 'Em uso'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : eq.status === 'Em estoque'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {eq.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-400">{eq.hostname || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* RENDER CURRENT VARIANT MODAL IF OPEN */}
      {isModalOpen && (
        <>
          {selectedVariant === 1 && (
            <Variant1Stepper
              tags={tags}
              onAddTag={handleAddTag}
              onClose={() => setIsModalOpen(false)}
              onSubmit={handleCreatedEquipment}
            />
          )}
          {selectedVariant === 2 && (
            <Variant2CommandDrawer
              tags={tags}
              onAddTag={handleAddTag}
              onClose={() => setIsModalOpen(false)}
              onSubmit={handleCreatedEquipment}
            />
          )}
          {selectedVariant === 3 && (
            <Variant3LiveCardStudio
              tags={tags}
              onAddTag={handleAddTag}
              onClose={() => setIsModalOpen(false)}
              onSubmit={handleCreatedEquipment}
            />
          )}
        </>
      )}

      {/* FLOATING VARIANT PICKER BAR AT BOTTOM */}
      <div className="fixed bottom-6 inset-x-0 z-50 flex justify-center px-4 pointer-events-none">
        <div className="bg-slate-900/95 border border-slate-700/80 rounded-2xl shadow-2xl backdrop-blur-xl p-2 flex items-center gap-1.5 pointer-events-auto max-w-xl w-full">
          <div className="px-3 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-widest hidden md:block">
            Variantes:
          </div>

          <div className="grid grid-cols-3 gap-1.5 flex-1">
            {VARIANTS.map((v) => {
              const isSelected = selectedVariant === v.id;
              const Icon = v.icon;
              return (
                <button
                  key={v.id}
                  onClick={() => {
                    setSelectedVariant(v.id);
                    setIsModalOpen(true);
                  }}
                  className={`flex items-center justify-between px-3 py-2 rounded-xl text-left transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30 font-bold'
                      : 'bg-slate-950/70 hover:bg-slate-800 text-slate-300 border border-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <Icon className={`w-4 h-4 shrink-0 ${isSelected ? 'text-white' : 'text-blue-400'}`} />
                    <div className="truncate">
                      <div className="text-xs truncate">{v.name}</div>
                    </div>
                  </div>
                  <span
                    className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-bold ml-1 shrink-0 ${
                      isSelected ? 'bg-blue-700 text-white' : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {v.id}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
