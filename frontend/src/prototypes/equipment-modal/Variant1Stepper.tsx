import React, { useState } from 'react';
import { X, Check, ArrowRight, ArrowLeft, Layers, ShieldCheck, Cpu, HardDrive, Plus, Sparkles } from 'lucide-react';
import { PrototypeTag } from './mockData';

interface VariantProps {
  tags: PrototypeTag[];
  onAddTag: (category: 'tipo' | 'localizacao' | 'situacao', name: string) => void;
  onClose: () => void;
  onSubmit: (data: any) => void;
}

export const Variant1Stepper: React.FC<VariantProps> = ({ tags, onAddTag, onClose, onSubmit }) => {
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Form Fields
  const [serialNumber, setSerialNumber] = useState('SN-89410294');
  const [patrimonyNumber, setPatrimonyNumber] = useState('PAT-1092');
  const [description, setDescription] = useState('Dell Precision 5570 i7 32GB RTX A2000');
  const [brand, setBrand] = useState('Dell');
  const [productNumber, setProductNumber] = useState('21B40019BR');

  const [equipmentType, setEquipmentType] = useState('Notebook');
  const [location, setLocation] = useState('TI - Suporte');
  const [status, setStatus] = useState('Em uso');

  const [hostname, setHostname] = useState('TI-DEV-09');
  const [windowsKey, setWindowsKey] = useState('VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A');
  const [notes, setNotes] = useState('Atribuído ao desenvolvedor sênior. Setup de dual-boot configurado.');

  // Inline Tag creation
  const [creatingTag, setCreatingTag] = useState<{ category: 'tipo' | 'localizacao' | 'situacao'; name: string } | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const types = tags.filter((t) => t.category === 'tipo');
  const locations = tags.filter((t) => t.category === 'localizacao');
  const statuses = tags.filter((t) => t.category === 'situacao');

  const handleNext = () => {
    if (currentStep < 3) setCurrentStep((prev) => (prev + 1) as any);
  };

  const handleBack = () => {
    if (currentStep > 1) setCurrentStep((prev) => (prev - 1) as any);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
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

  const handleInlineTagAdd = (cat: 'tipo' | 'localizacao' | 'situacao') => {
    if (creatingTag && creatingTag.name.trim()) {
      onAddTag(cat, creatingTag.name.trim());
      if (cat === 'tipo') setEquipmentType(creatingTag.name.trim());
      if (cat === 'localizacao') setLocation(creatingTag.name.trim());
      if (cat === 'situacao') setStatus(creatingTag.name.trim());
      setCreatingTag(null);
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 sm:p-6 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800/90 rounded-3xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[92vh] transition-all">
        {/* Header with Step Tracker */}
        <div className="px-8 pt-6 pb-5 border-b border-slate-800/80 bg-slate-950/60">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                <Layers className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                    Wizard Guiado
                  </span>
                  <span className="text-xs text-slate-500 font-mono">Etapa {currentStep} de 3</span>
                </div>
                <h2 className="text-lg font-bold text-white tracking-tight mt-0.5">Cadastrar Novo Equipamento</h2>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Stepper Dots & Labels */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { num: 1, label: '1. Identificação', icon: HardDrive },
              { num: 2, label: '2. Categorização', icon: ShieldCheck },
              { num: 3, label: '3. Rede & Licença', icon: Cpu },
            ].map((step) => {
              const isActive = currentStep === step.num;
              const isPast = currentStep > step.num;
              const Icon = step.icon;
              return (
                <button
                  key={step.num}
                  type="button"
                  onClick={() => setCurrentStep(step.num as any)}
                  className={`flex items-center gap-2.5 p-2 rounded-xl text-left text-xs transition-all border ${
                    isActive
                      ? 'bg-blue-600/15 border-blue-500/40 text-blue-400 font-medium'
                      : isPast
                      ? 'bg-slate-800/40 border-slate-700/60 text-slate-300'
                      : 'bg-slate-950/40 border-transparent text-slate-500'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-semibold shrink-0 ${
                      isActive
                        ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                        : isPast
                        ? 'bg-slate-700 text-emerald-400'
                        : 'bg-slate-800 text-slate-500'
                    }`}
                  >
                    {isPast ? <Check className="w-3.5 h-3.5" /> : step.num}
                  </div>
                  <span className="truncate hidden sm:inline">{step.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-8 space-y-6">
          {/* STEP 1: Identificação */}
          {currentStep === 1 && (
            <div className="space-y-5 animate-in fade-in slide-in-from-right-2 duration-150">
              <div className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 text-xs text-slate-300 flex items-start gap-3">
                <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <span>
                  Informe os dados básicos de identificação física do ativo. O <strong>Número de Série</strong> e a <strong>Descrição</strong> são essenciais para rastreabilidade.
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Número de Série (SN) <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={serialNumber}
                    onChange={(e) => setSerialNumber(e.target.value)}
                    placeholder="Ex: 5CG21890X4"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Número de Patrimônio</label>
                  <input
                    type="text"
                    value={patrimonyNumber}
                    onChange={(e) => setPatrimonyNumber(e.target.value)}
                    placeholder="Ex: PAT-0892"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Descrição Completa do Ativo <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Ex: Dell Precision 5570 i7 32GB RTX A2000"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Marca / Fabricante</label>
                  <input
                    type="text"
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                    placeholder="Ex: Dell, Lenovo, HP, Apple"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Product Number (PN)</label>
                  <input
                    type="text"
                    value={productNumber}
                    onChange={(e) => setProductNumber(e.target.value)}
                    placeholder="Ex: 21B40019BR"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Categorização */}
          {currentStep === 2 && (
            <div className="space-y-6 animate-in fade-in slide-in-from-right-2 duration-150">
              {/* Tipo Selector */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-slate-200">Tipo de Equipamento</label>
                  <span className="text-[11px] text-slate-400">Clique para selecionar rápido</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {types.map((t) => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setEquipmentType(t.name)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                        equipmentType === t.name
                          ? 'bg-blue-600 text-white border-blue-500 shadow-md shadow-blue-600/20'
                          : 'bg-slate-950 hover:bg-slate-800 border-slate-800 text-slate-300'
                      }`}
                    >
                      {t.name}
                    </button>
                  ))}
                  {creatingTag?.category === 'tipo' ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        autoFocus
                        value={creatingTag.name}
                        onChange={(e) => setCreatingTag({ category: 'tipo', name: e.target.value })}
                        placeholder="Nome do tipo"
                        className="bg-slate-950 border border-blue-500 rounded-lg px-2.5 py-1 text-xs text-white outline-none w-28"
                      />
                      <button
                        type="button"
                        onClick={() => handleInlineTagAdd('tipo')}
                        className="p-1 bg-blue-600 rounded-lg text-white text-xs"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setCreatingTag({ category: 'tipo', name: '' })}
                      className="px-2.5 py-1 rounded-xl text-xs text-blue-400 hover:text-blue-300 border border-dashed border-blue-500/40 hover:border-blue-500 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Novo
                    </button>
                  )}
                </div>
              </div>

              {/* Localização Selector */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-slate-200">Localização Inicial</label>
                  <span className="text-[11px] text-slate-400">Setor ou departamento</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {locations.map((l) => (
                    <button
                      key={l.id}
                      type="button"
                      onClick={() => setLocation(l.name)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                        location === l.name
                          ? 'bg-purple-600 text-white border-purple-500 shadow-md shadow-purple-600/20'
                          : 'bg-slate-950 hover:bg-slate-800 border-slate-800 text-slate-300'
                      }`}
                    >
                      {l.name}
                    </button>
                  ))}
                  {creatingTag?.category === 'localizacao' ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        autoFocus
                        value={creatingTag.name}
                        onChange={(e) => setCreatingTag({ category: 'localizacao', name: e.target.value })}
                        placeholder="Nome do local"
                        className="bg-slate-950 border border-purple-500 rounded-lg px-2.5 py-1 text-xs text-white outline-none w-28"
                      />
                      <button
                        type="button"
                        onClick={() => handleInlineTagAdd('localizacao')}
                        className="p-1 bg-purple-600 rounded-lg text-white text-xs"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setCreatingTag({ category: 'localizacao', name: '' })}
                      className="px-2.5 py-1 rounded-xl text-xs text-purple-400 hover:text-purple-300 border border-dashed border-purple-500/40 hover:border-purple-500 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Novo
                    </button>
                  )}
                </div>
              </div>

              {/* Situação Selector */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-semibold text-slate-200">Situação Operacional</label>
                  <span className="text-[11px] text-slate-400">Estado inicial do equipamento</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {statuses.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setStatus(s.name)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                        status === s.name
                          ? 'bg-emerald-600 text-white border-emerald-500 shadow-md shadow-emerald-600/20'
                          : 'bg-slate-950 hover:bg-slate-800 border-slate-800 text-slate-300'
                      }`}
                    >
                      {s.name}
                    </button>
                  ))}
                  {creatingTag?.category === 'situacao' ? (
                    <div className="flex items-center gap-1">
                      <input
                        type="text"
                        autoFocus
                        value={creatingTag.name}
                        onChange={(e) => setCreatingTag({ category: 'situacao', name: e.target.value })}
                        placeholder="Nova situação"
                        className="bg-slate-950 border border-emerald-500 rounded-lg px-2.5 py-1 text-xs text-white outline-none w-28"
                      />
                      <button
                        type="button"
                        onClick={() => handleInlineTagAdd('situacao')}
                        className="p-1 bg-emerald-600 rounded-lg text-white text-xs"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setCreatingTag({ category: 'situacao', name: '' })}
                      className="px-2.5 py-1 rounded-xl text-xs text-emerald-400 hover:text-emerald-300 border border-dashed border-emerald-500/40 hover:border-emerald-500 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Novo
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Rede & Observações */}
          {currentStep === 3 && (
            <div className="space-y-5 animate-in fade-in slide-in-from-right-2 duration-150">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Hostname na Rede</label>
                  <input
                    type="text"
                    value={hostname}
                    onChange={(e) => setHostname(e.target.value)}
                    placeholder="Ex: TI-NOTE-09"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Chave Windows / Licença OEM</label>
                  <input
                    type="text"
                    value={windowsKey}
                    onChange={(e) => setWindowsKey(e.target.value)}
                    placeholder="Ex: VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white font-mono placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Observações Técnicas & Detalhes</label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Informações de garantia, acessórios inclusos, usuário responsável..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder:text-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none resize-none transition-all"
                />
              </div>

              {/* Summary Card */}
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Resumo Pré-Salvar</h4>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="font-semibold text-white">{description || 'Sem descrição'}</span>
                  <span className="text-slate-500">•</span>
                  <span className="px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">{equipmentType}</span>
                  <span className="px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20">{location}</span>
                  <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{status}</span>
                </div>
              </div>
            </div>
          )}
        </form>

        {/* Footer Navigation */}
        <div className="px-8 py-4 border-t border-slate-800/80 bg-slate-950/60 flex items-center justify-between">
          <div>
            {currentStep > 1 ? (
              <button
                type="button"
                onClick={handleBack}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> Voltar
              </button>
            ) : (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-transparent hover:bg-slate-800 text-slate-400 rounded-xl text-xs font-medium transition-all"
              >
                Cancelar
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {currentStep < 3 ? (
              <button
                type="button"
                onClick={handleNext}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-blue-500/20"
              >
                Continuar <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={handleSave}
                className={`px-6 py-2.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 cursor-pointer ${
                  savedSuccess
                    ? 'bg-emerald-600 text-white'
                    : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/25'
                }`}
              >
                {savedSuccess ? (
                  <>
                    <Check className="w-4 h-4" /> Cadastrado!
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" /> Concluir Cadastro
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
