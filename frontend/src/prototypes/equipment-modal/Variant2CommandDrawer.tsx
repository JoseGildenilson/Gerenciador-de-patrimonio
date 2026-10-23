import React, { useState, useEffect } from 'react';
import { X, Check, Command, Plus, Sparkles, Server, Zap } from 'lucide-react';
import { PrototypeTag } from './mockData';

interface VariantProps {
  tags: PrototypeTag[];
  onAddTag: (category: 'tipo' | 'localizacao' | 'situacao', name: string) => void;
  onClose: () => void;
  onSubmit: (data: any) => void;
}

export const Variant2CommandDrawer: React.FC<VariantProps> = ({ tags, onAddTag, onClose, onSubmit }) => {
  // Form State
  const [serialNumber, setSerialNumber] = useState('SN-99823101');
  const [patrimonyNumber, setPatrimonyNumber] = useState('PAT-2041');
  const [description, setDescription] = useState('Lenovo ThinkPad T14s Gen 3 Ryzen 7 Pro 32GB');
  const [brand, setBrand] = useState('Lenovo');
  const [productNumber, setProductNumber] = useState('21CQ000EBR');

  const [equipmentType, setEquipmentType] = useState('Notebook');
  const [location, setLocation] = useState('TI - Suporte');
  const [status, setStatus] = useState('Em estoque');

  const [hostname, setHostname] = useState('LNV-T14S-02');
  const [windowsKey, setWindowsKey] = useState('NPPR9-FWDCX-D2C8J-H872K-2YT43');
  const [notes, setNotes] = useState('Equipamento novo recebido da fábrica. Selo de garantia intacto.');

  const [createAnother, setCreateAnother] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [newTagInput, setNewTagInput] = useState<{ category: 'tipo' | 'localizacao' | 'situacao'; name: string } | null>(null);

  const types = tags.filter((t) => t.category === 'tipo');
  const locations = tags.filter((t) => t.category === 'localizacao');
  const statuses = tags.filter((t) => t.category === 'situacao');

  // Keyboard shortcut listener for Cmd+Enter / Ctrl+Enter
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault();
        handleQuickSubmit();
      } else if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [serialNumber, description, equipmentType, location, status]);

  const handleQuickSubmit = () => {
    setIsSaved(true);
    setTimeout(() => {
      onSubmit({
        serialNumber,
        patrimonyNumber,
        description,
        brand,
        productNumber,
        equipmentType,
        location,
        status,
        hostname,
        windowsKey,
        notes,
      });
      if (createAnother) {
        setIsSaved(false);
        setSerialNumber('');
        setPatrimonyNumber('');
        setDescription('');
      }
    }, 400);
  };

  const handleTagCreate = (category: 'tipo' | 'localizacao' | 'situacao') => {
    if (newTagInput && newTagInput.name.trim()) {
      onAddTag(category, newTagInput.name.trim());
      if (category === 'tipo') setEquipmentType(newTagInput.name.trim());
      if (category === 'localizacao') setLocation(newTagInput.name.trim());
      if (category === 'situacao') setStatus(newTagInput.name.trim());
      setNewTagInput(null);
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      {/* Click outside backdrop */}
      <div className="flex-1 hidden md:block" onClick={onClose} />

      {/* Slide-over Drawer Panel */}
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-250">
        {/* Top Header with Quick Shortcuts */}
        <div className="p-6 border-b border-slate-800/80 bg-slate-950/70">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider">
                    Command Drawer
                  </span>
                  <span className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                    <Command className="w-3 h-3" /> + Enter salva
                  </span>
                </div>
                <h2 className="text-base font-bold text-white tracking-tight mt-0.5">Novo Registro de Patrimônio</h2>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <p className="text-xs text-slate-400">
            Painel lateral compacto com foco contínuo no inventário de fundo.
          </p>
        </div>

        {/* Scrollable Form Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Hardware Core Section */}
          <div className="space-y-3.5">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5" /> Hardware & Identificação
            </h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Serial Number (SN) *
                </label>
                <input
                  type="text"
                  required
                  value={serialNumber}
                  onChange={(e) => setSerialNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:border-amber-500 outline-none transition-colors"
                  placeholder="SN-000000"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Patrimônio (Tag ID)
                </label>
                <input
                  type="text"
                  value={patrimonyNumber}
                  onChange={(e) => setPatrimonyNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:border-amber-500 outline-none transition-colors"
                  placeholder="PAT-0000"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                Descrição Completa *
              </label>
              <input
                type="text"
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-600 focus:border-amber-500 outline-none transition-colors"
                placeholder="Ex: ThinkPad T14s Ryzen 7 32GB"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Fabricante / Marca</label>
                <input
                  type="text"
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-600 focus:border-amber-500 outline-none"
                  placeholder="Dell, HP, Lenovo"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Part Number (PN)</label>
                <input
                  type="text"
                  value={productNumber}
                  onChange={(e) => setProductNumber(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:border-amber-500 outline-none"
                  placeholder="21CQ000EBR"
                />
              </div>
            </div>
          </div>

          {/* Quick Filter Tag Matrix */}
          <div className="space-y-4 pt-4 border-t border-slate-800/80">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Classificação Instantânea</h3>

            {/* Quick Type Selection */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-300">Tipo de Ativo</span>
                <span className="text-[10px] text-amber-400 font-semibold">{equipmentType}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {types.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setEquipmentType(t.name)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                      equipmentType === t.name
                        ? 'bg-amber-500 text-slate-950 font-bold shadow-md shadow-amber-500/20'
                        : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Location Selection */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-300">Localização</span>
                <span className="text-[10px] text-purple-400 font-semibold">{location}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {locations.slice(0, 6).map((l) => (
                  <button
                    key={l.id}
                    type="button"
                    onClick={() => setLocation(l.name)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                      location === l.name
                        ? 'bg-purple-600 text-white font-bold shadow-md shadow-purple-600/20'
                        : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {l.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Status Selection */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-300">Situação</span>
                <span className="text-[10px] text-emerald-400 font-semibold">{status}</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {statuses.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setStatus(s.name)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                      status === s.name
                        ? 'bg-emerald-500 text-slate-950 font-bold shadow-md shadow-emerald-500/20'
                        : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    {s.name}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Network & License */}
          <div className="space-y-3.5 pt-4 border-t border-slate-800/80">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider">Rede & Licença</h3>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Hostname</label>
                <input
                  type="text"
                  value={hostname}
                  onChange={(e) => setHostname(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:border-amber-500 outline-none"
                  placeholder="LNV-T14S-02"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">Chave Windows OEM</label>
                <input
                  type="text"
                  value={windowsKey}
                  onChange={(e) => setWindowsKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono placeholder:text-slate-600 focus:border-amber-500 outline-none"
                  placeholder="NPPR9-FWDCX-..."
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 mb-1">Observações Gerais</label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-600 focus:border-amber-500 outline-none resize-none"
                placeholder="Observações adicionais..."
              />
            </div>
          </div>
        </div>

        {/* Footer Actions with Continuous Add mode */}
        <div className="p-5 border-t border-slate-800/80 bg-slate-950/80 flex items-center justify-between">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={createAnother}
              onChange={(e) => setCreateAnother(e.target.checked)}
              className="rounded bg-slate-900 border-slate-700 text-amber-500 focus:ring-0"
            />
            <span>Criar outro em seguida</span>
          </label>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-xs font-medium text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              Fechar (Esc)
            </button>
            <button
              type="button"
              onClick={handleQuickSubmit}
              className={`px-5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-lg ${
                isSaved
                  ? 'bg-emerald-500 text-slate-950'
                  : 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
              }`}
            >
              {isSaved ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
              {isSaved ? 'Registrado!' : 'Salvar Ativo'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
