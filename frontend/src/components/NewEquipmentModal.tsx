import React, { useState, useEffect } from 'react';
import { X, Plus, HardDrive, Check, AlertCircle } from 'lucide-react';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentCreatePayload, EquipmentTag } from '../types/equipment';
import { formatApiError } from '../utils/errorUtils';

interface NewEquipmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const NewEquipmentModal: React.FC<NewEquipmentModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [types, setTypes] = useState<EquipmentTag[]>([]);
  const [locations, setLocations] = useState<EquipmentTag[]>([]);
  const [statuses, setStatuses] = useState<EquipmentTag[]>([]);

  // Form State
  const [serialNumber, setSerialNumber] = useState('');
  const [patrimonyNumber, setPatrimonyNumber] = useState('');
  const [hostname, setHostname] = useState('');
  const [description, setDescription] = useState('');
  const [brand, setBrand] = useState('');
  const [productNumber, setProductNumber] = useState('');
  const [equipmentType, setEquipmentType] = useState('Desktop');
  const [location, setLocation] = useState('TI');
  const [status, setStatus] = useState('Em uso');
  const [windowsKey, setWindowsKey] = useState('');
  const [notes, setNotes] = useState('');

  // New Tag inline input state
  const [newTagInput, setNewTagInput] = useState<{ category: string; value: string } | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchTags();
      resetForm();
    }
  }, [isOpen]);

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

  const resetForm = () => {
    setSerialNumber('');
    setPatrimonyNumber('');
    setHostname('');
    setDescription('');
    setBrand('');
    setProductNumber('');
    setEquipmentType('Desktop');
    setLocation('TI');
    setStatus('Em uso');
    setWindowsKey('');
    setNotes('');
    setError(null);
    setNewTagInput(null);
  };

  const handleCreateTag = async (category: string) => {
    if (!newTagInput || !newTagInput.value.trim()) return;
    try {
      const created = await equipmentApi.createTag(category, newTagInput.value.trim());
      await fetchTags();
      if (category === 'tipo') setEquipmentType(created.name);
      if (category === 'localizacao') setLocation(created.name);
      if (category === 'situacao') setStatus(created.name);
      setNewTagInput(null);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao criar nova tag'));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!patrimonyNumber.trim() && !serialNumber.trim()) {
      setError('Número de patrimônio ou número de série é obrigatório.');
      return;
    }

    setLoading(true);
    try {
      const typeMatch = types.find((t) => t.name.trim().toLowerCase() === equipmentType.trim().toLowerCase());
      const locMatch = locations.find((l) => l.name.trim().toLowerCase() === location.trim().toLowerCase());
      const statusMatch = statuses.find((s) => s.name.trim().toLowerCase() === status.trim().toLowerCase());

      const payload: EquipmentCreatePayload = {
        serial_number: serialNumber.trim() || null,
        patrimony_number: (patrimonyNumber.trim() || serialNumber.trim()),
        hostname: hostname.trim() || null,
        description: description.trim() || null,
        brand: brand.trim() || null,
        model: productNumber.trim() || null,
        product_number: productNumber.trim() || null,
        equipment_type: equipmentType,
        equipment_type_id: typeMatch?.id || 1,
        location: location,
        sector_id: locMatch?.id || 1,
        status: status,
        status_id: statusMatch?.id || 1,
        windows_product_key: windowsKey.trim() || null,
        windows_key: windowsKey.trim() || null,
        notes: notes.trim() || null,
      };

      await equipmentApi.createEquipment(payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao cadastrar equipamento'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/70 backdrop-blur-sm animate-fade-in-overlay overflow-y-auto">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl shadow-dropdown w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden animate-fade-in my-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-lg">
              <HardDrive className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-zinc-100 tracking-tight">Novo Equipamento</h2>
              <p className="text-[11px] text-zinc-500 font-mono">CADASTRO DE ATIVO</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Alert Error */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          {/* Seção: Identificação */}
          <div className="space-y-3">
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">1. Identificação</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Nº de Série (SN) *</label>
                <input
                  type="text"
                  required
                  value={serialNumber}
                  onChange={(e) => setSerialNumber(e.target.value)}
                  placeholder="ex: SN12345678"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono placeholder:text-zinc-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Nº de Patrimônio</label>
                <input
                  type="text"
                  value={patrimonyNumber}
                  onChange={(e) => setPatrimonyNumber(e.target.value)}
                  placeholder="ex: PAT-10342"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono placeholder:text-zinc-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-zinc-300 mb-1">Descrição / Modelo *</label>
              <input
                type="text"
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="ex: Dell OptiPlex 7090 Core i7 16GB SSD 512GB"
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none placeholder:text-zinc-500"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Marca</label>
                <input
                  type="text"
                  value={brand}
                  onChange={(e) => setBrand(e.target.value)}
                  placeholder="ex: Dell, Lenovo, HP, Apple"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none placeholder:text-zinc-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Nº do Produto</label>
                <input
                  type="text"
                  value={productNumber}
                  onChange={(e) => setProductNumber(e.target.value)}
                  placeholder="ex: 20L50001BR"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono placeholder:text-zinc-500"
                />
              </div>
            </div>
          </div>

          {/* Seção: Categorização e Estado Atual */}
          <div className="space-y-3 pt-3 border-t border-zinc-800">
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">2. Categoria & Estado</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
              {/* Tipo */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Tipo *</label>
                {newTagInput?.category === 'tipo' ? (
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      value={newTagInput.value}
                      onChange={(e) => setNewTagInput({ category: 'tipo', value: e.target.value })}
                      placeholder="Novo tipo"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleCreateTag('tipo');
                        }
                        if (e.key === 'Escape') setNewTagInput(null);
                      }}
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1 text-xs text-zinc-100 outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handleCreateTag('tipo')}
                      disabled={!newTagInput.value.trim()}
                      className="px-2.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-50 flex items-center justify-center transition-colors"
                      title="Salvar Tipo"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setNewTagInput(null)}
                      className="px-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs cursor-pointer flex items-center justify-center transition-colors"
                      title="Cancelar"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <select
                      value={equipmentType}
                      onChange={(e) => setEquipmentType(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none"
                    >
                      {types.map((t) => (
                        <option key={t.id} value={t.name}>{t.name}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setNewTagInput({ category: 'tipo', value: '' })}
                      data-testid="inline-create-tipo-btn"
                      className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg transition-all cursor-pointer shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                      <span>Criar tipo</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Localização */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Localização *</label>
                {newTagInput?.category === 'localizacao' ? (
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      value={newTagInput.value}
                      onChange={(e) => setNewTagInput({ category: 'localizacao', value: e.target.value })}
                      placeholder="Nova localização"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleCreateTag('localizacao');
                        }
                        if (e.key === 'Escape') setNewTagInput(null);
                      }}
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1 text-xs text-zinc-100 outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handleCreateTag('localizacao')}
                      disabled={!newTagInput.value.trim()}
                      className="px-2.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-50 flex items-center justify-center transition-colors"
                      title="Salvar Localização"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setNewTagInput(null)}
                      className="px-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs cursor-pointer flex items-center justify-center transition-colors"
                      title="Cancelar"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <select
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none"
                    >
                      {locations.map((l) => (
                        <option key={l.id} value={l.name}>{l.name}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setNewTagInput({ category: 'localizacao', value: '' })}
                      data-testid="inline-create-localizacao-btn"
                      className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg transition-all cursor-pointer shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                      <span>Criar local</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Situação */}
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Situação *</label>
                {newTagInput?.category === 'situacao' ? (
                  <div className="flex gap-1.5">
                    <input
                      type="text"
                      value={newTagInput.value}
                      onChange={(e) => setNewTagInput({ category: 'situacao', value: e.target.value })}
                      placeholder="Nova situação"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleCreateTag('situacao');
                        }
                        if (e.key === 'Escape') setNewTagInput(null);
                      }}
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1 text-xs text-zinc-100 outline-none"
                    />
                    <button
                      type="button"
                      onClick={() => handleCreateTag('situacao')}
                      disabled={!newTagInput.value.trim()}
                      className="px-2.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-50 flex items-center justify-center transition-colors"
                      title="Salvar Situação"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setNewTagInput(null)}
                      className="px-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs cursor-pointer flex items-center justify-center transition-colors"
                      title="Cancelar"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="space-y-1.5">
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value)}
                      className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none"
                    >
                      {statuses.map((s) => (
                        <option key={s.id} value={s.name}>{s.name}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setNewTagInput({ category: 'situacao', value: '' })}
                      data-testid="inline-create-situacao-btn"
                      className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg transition-all cursor-pointer shadow-sm"
                    >
                      <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                      <span>Criar situação</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Seção: Rede & Licenciamento */}
          <div className="space-y-3 pt-3 border-t border-zinc-800">
            <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider">3. Rede & Licença</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Hostname</label>
                <input
                  type="text"
                  value={hostname}
                  onChange={(e) => setHostname(e.target.value)}
                  placeholder="ex: DESKTOP-TI01"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono placeholder:text-zinc-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-zinc-300 mb-1">Chave Windows</label>
                <input
                  type="text"
                  value={windowsKey}
                  onChange={(e) => setWindowsKey(e.target.value)}
                  placeholder="ex: VK9X2-N8Y4R-W3M2T-K7P1Q-L9Z0A"
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono placeholder:text-zinc-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-zinc-300 mb-1">Observações Gerais</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Observações técnicas gerais..."
                rows={2}
                className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none resize-none placeholder:text-zinc-500"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded-xl text-xs font-medium transition-all cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-semibold transition-all shadow-sm disabled:opacity-50 cursor-pointer flex items-center gap-1.5 active:scale-[0.99]"
            >
              {loading ? <div className="w-3.5 h-3.5 border-2 border-zinc-400 border-t-zinc-950 rounded-full animate-spin" /> : 'Cadastrar Equipamento'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
