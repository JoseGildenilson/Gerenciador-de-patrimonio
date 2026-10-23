import React, { useState, useEffect } from 'react';
import { X, Wrench, AlertCircle } from 'lucide-react';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentTag } from '../types/equipment';
import { formatApiError } from '../utils/errorUtils';

interface MaintenanceModalProps {
  isOpen: boolean;
  equipmentId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const MaintenanceModal: React.FC<MaintenanceModalProps> = ({
  isOpen,
  equipmentId,
  onClose,
  onSuccess,
}) => {
  const [maintenanceDate, setMaintenanceDate] = useState(new Date().toISOString().substring(0, 10));
  const [description, setDescription] = useState('');
  const [notes, setNotes] = useState('');
  const [maintenanceTypes, setMaintenanceTypes] = useState<EquipmentTag[]>([]);
  const [selectedTypeId, setSelectedTypeId] = useState<number>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && typeof equipmentApi.getTags === 'function') {
      equipmentApi
        .getTags('tipo_manutencao')
        ?.then?.((tags) => {
          if (Array.isArray(tags)) {
            setMaintenanceTypes(tags);
            if (tags.length > 0) {
              setSelectedTypeId(tags[0].id);
            }
          }
        })
        ?.catch?.(() => {
          // Fallback if tag loading fails
        });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!description.trim()) {
      setError('A descrição / lista de itens da manutenção é obrigatória.');
      return;
    }

    setLoading(true);

    try {
      await equipmentApi.recordMaintenance(equipmentId, {
        maintenance_type_id: selectedTypeId || 1,
        started_at: new Date(maintenanceDate).toISOString(),
        description: description.trim(),
        notes: notes.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao registrar manutenção'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in-overlay">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl shadow-dropdown w-full max-w-md overflow-hidden animate-fade-in">
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-zinc-800 bg-zinc-900/60">
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-lg">
              <Wrench className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold text-zinc-100 tracking-tight uppercase">Registrar Manutenção</h2>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="mx-5 mt-3.5 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-5 space-y-3.5">
          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Data da Manutenção *</label>
            <input
              type="date"
              required
              value={maintenanceDate}
              onChange={(e) => setMaintenanceDate(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Tipo de Manutenção *</label>
            <select
              value={selectedTypeId}
              onChange={(e) => setSelectedTypeId(Number(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none"
            >
              {maintenanceTypes.map((mt) => (
                <option key={mt.id} value={mt.id}>
                  {mt.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Descrição / Itens Realizados *</label>
            <textarea
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Ex: Troca de SSD, Limpeza interna, Troca de pasta térmica..."
              rows={3}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none resize-none placeholder:text-zinc-500"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Observações Técnicas</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Teste de estabilidade concluído."
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none placeholder:text-zinc-500"
            />
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 rounded-xl text-xs font-medium transition-all cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-semibold transition-all shadow-sm disabled:opacity-50 cursor-pointer flex items-center gap-1.5 active:scale-[0.99]"
            >
              {loading ? <div className="w-3.5 h-3.5 border-2 border-zinc-400 border-t-zinc-950 rounded-full animate-spin" /> : 'Salvar Manutenção'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
