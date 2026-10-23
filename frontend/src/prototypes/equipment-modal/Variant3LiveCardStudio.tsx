import React, { useState } from 'react';
import { X, Check, QrCode, HardDrive, Cpu, ShieldCheck, Tag, MapPin, Sparkles, Box, CheckCircle2 } from 'lucide-react';
import { PrototypeTag } from './mockData';

interface VariantProps {
  tags: PrototypeTag[];
  onAddTag: (category: 'tipo' | 'localizacao' | 'situacao', name: string) => void;
  onClose: () => void;
  onSubmit: (data: any) => void;
}

export const Variant3LiveCardStudio: React.FC<VariantProps> = ({ tags, onAddTag, onClose, onSubmit }) => {
  // Form State
  const [serialNumber, setSerialNumber] = useState('5CD34091A8');
  const [patrimonyNumber, setPatrimonyNumber] = useState('PAT-3490');
  const [description, setDescription] = useState('Apple MacBook Pro 14" M3 Pro 18GB 512GB');
  const [brand, setBrand] = useState('Apple');
  const [productNumber, setProductNumber] = useState('MRX33BZ/A');

  const [equipmentType, setEquipmentType] = useState('Notebook');
  const [location, setLocation] = useState('Diretoria');
  const [status, setStatus] = useState('Em uso');

  const [hostname, setHostname] = useState('DIR-MBP-01');
  const [windowsKey, setWindowsKey] = useState('');
  const [notes, setNotes] = useState('Equipamento alocado para o Diretor de Operações. Apple Care+ ativo.');

  const [isSaved, setIsSaved] = useState(false);

  const types = tags.filter((t) => t.category === 'tipo');
  const locations = tags.filter((t) => t.category === 'localizacao');
  const statuses = tags.filter((t) => t.category === 'situacao');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
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
    }, 600);
  };

  const getStatusColor = (st: string) => {
    switch (st) {
      case 'Em uso':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'Em estoque':
        return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
      case 'Em manutenção':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      case 'Descarte':
        return 'bg-red-500/15 text-red-400 border-red-500/30';
      default:
        return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 sm:p-6 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl w-full max-w-5xl overflow-hidden flex flex-col max-h-[92vh]">
        {/* Studio Header */}
        <div className="px-8 py-5 border-b border-slate-800 bg-slate-950/70 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Box className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
                  Live Card Studio
                </span>
                <span className="text-xs text-slate-400">Split View com Prévia Física ao Vivo</span>
              </div>
              <h2 className="text-lg font-bold text-white tracking-tight mt-0.5">Cadastrar e Etiquetar Ativo</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Split Grid: Left Form (60%) + Right Live Asset Card (40%) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 flex-1 overflow-hidden">
          {/* Left Form Column */}
          <form onSubmit={handleSave} className="lg:col-span-7 overflow-y-auto p-7 space-y-6 border-b lg:border-b-0 lg:border-r border-slate-800">
            {/* Section 1: Dados Vitais */}
            <div className="bg-slate-950/50 p-5 rounded-2xl border border-slate-800/80 space-y-4">
              <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5" /> 1. Identificação Física
              </h3>
              <div className="grid grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Nº de Série *
                  </label>
                  <input
                    type="text"
                    required
                    value={serialNumber}
                    onChange={(e) => setSerialNumber(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:border-indigo-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Nº de Patrimônio
                  </label>
                  <input
                    type="text"
                    value={patrimonyNumber}
                    onChange={(e) => setPatrimonyNumber(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:border-indigo-500 outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Descrição do Equipamento *
                </label>
                <input
                  type="text"
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:border-indigo-500 outline-none transition-all"
                />
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Marca</label>
                  <input
                    type="text"
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Part Number</label>
                  <input
                    type="text"
                    value={productNumber}
                    onChange={(e) => setProductNumber(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>
            </div>

            {/* Section 2: Tags & Alocação */}
            <div className="bg-slate-950/50 p-5 rounded-2xl border border-slate-800/80 space-y-4">
              <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <Tag className="w-3.5 h-3.5" /> 2. Tags e Localização
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Tipo</label>
                  <select
                    value={equipmentType}
                    onChange={(e) => setEquipmentType(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:border-indigo-500 outline-none"
                  >
                    {types.map((t) => (
                      <option key={t.id} value={t.name}>{t.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Localização</label>
                  <select
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:border-indigo-500 outline-none"
                  >
                    {locations.map((l) => (
                      <option key={l.id} value={l.name}>{l.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Situação</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:border-indigo-500 outline-none"
                  >
                    {statuses.map((s) => (
                      <option key={s.id} value={s.name}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Section 3: Rede & Licença */}
            <div className="bg-slate-950/50 p-5 rounded-2xl border border-slate-800/80 space-y-4">
              <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> 3. Configurações Técnicas
              </h3>
              <div className="grid grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Hostname</label>
                  <input
                    type="text"
                    value={hostname}
                    onChange={(e) => setHostname(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Chave Windows</label>
                  <input
                    type="text"
                    value={windowsKey}
                    onChange={(e) => setWindowsKey(e.target.value)}
                    placeholder="Opcional"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white font-mono focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Notas</label>
                <textarea
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:border-indigo-500 outline-none resize-none"
                />
              </div>
            </div>
          </form>

          {/* Right Live Preview Column (40%) */}
          <div className="lg:col-span-5 bg-slate-950/90 p-7 flex flex-col justify-between overflow-y-auto space-y-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Prévia do Ativo
                </span>
                <span className="text-[11px] text-emerald-400 font-mono flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Atualizado em tempo real
                </span>
              </div>

              {/* Physical Asset Tag Card Mockup */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 border border-indigo-500/30 shadow-xl space-y-5 relative overflow-hidden">
                {/* Glow accent */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

                {/* Top Badge & Patrimony */}
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase tracking-widest font-mono">TAG DE PATRIMÔNIO</span>
                    <div className="text-xl font-black text-white font-mono tracking-tight mt-0.5">
                      {patrimonyNumber || 'PAT-PENDENTE'}
                    </div>
                  </div>
                  <div className="p-2.5 bg-white text-slate-950 rounded-xl shadow-md">
                    <QrCode className="w-7 h-7" />
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-sm font-bold text-slate-100 line-clamp-2">
                    {description || 'Sem descrição informada'}
                  </h4>
                  <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-400">
                    <span>{brand || 'Marca não informada'}</span>
                    <span>•</span>
                    <span className="font-mono text-slate-300">{serialNumber || 'SN---'}</span>
                  </div>
                </div>

                {/* Metadata Pills */}
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/80">
                  <div className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase font-semibold">Tipo</span>
                    <span className="text-xs font-semibold text-indigo-300">{equipmentType}</span>
                  </div>
                  <div className="bg-slate-950/70 p-2.5 rounded-xl border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase font-semibold">Localização</span>
                    <span className="text-xs font-semibold text-purple-300">{location}</span>
                  </div>
                </div>

                {/* Status Badge */}
                <div className="flex items-center justify-between pt-1">
                  <span className="text-[11px] text-slate-400">Situação Atual:</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(status)}`}>
                    {status}
                  </span>
                </div>
              </div>

              {/* Hostname info */}
              {hostname && (
                <div className="mt-4 p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center justify-between font-mono">
                  <span className="text-slate-500">Hostname:</span>
                  <span className="text-blue-400 font-semibold">{hostname}</span>
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 text-xs font-semibold text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors cursor-pointer"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSave}
                className={`px-6 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shadow-lg ${
                  isSaved
                    ? 'bg-emerald-600 text-white'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/25'
                }`}
              >
                {isSaved ? (
                  <>
                    <Check className="w-4 h-4" /> Salvo com Sucesso!
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" /> Confirmar e Cadastrar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
