import React, { useState, useEffect } from 'react';
import { X, ArrowRightLeft, AlertCircle, Plus, Check } from 'lucide-react';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentTag } from '../types/equipment';
import { formatApiError } from '../utils/errorUtils';

interface MovementModalProps {
  isOpen: boolean;
  equipmentId: number;
  currentLocation: string;
  locations: EquipmentTag[];
  onClose: () => void;
  onSuccess: () => void;
}

export const MovementModal: React.FC<MovementModalProps> = ({
  isOpen,
  equipmentId,
  currentLocation,
  locations,
  onClose,
  onSuccess,
}) => {
  const [localLocations, setLocalLocations] = useState<EquipmentTag[]>(locations);
  const [destinationLocation, setDestinationLocation] = useState(locations[0]?.name || 'TI');
  const [newLocationInput, setNewLocationInput] = useState<string | null>(null);
  const [creatingLocation, setCreatingLocation] = useState(false);
  const [movementDate, setMovementDate] = useState(new Date().toISOString().substring(0, 10));
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalLocations(locations);
    if (locations.length > 0 && !destinationLocation) {
      setDestinationLocation(locations[0].name);
    }
  }, [locations]);

  const handleCreateLocation = async () => {
    if (!newLocationInput || !newLocationInput.trim()) return;
    setError(null);
    setCreatingLocation(true);
    try {
      const created = await equipmentApi.createTag('localizacao', newLocationInput.trim());
      setLocalLocations((prev) => [...prev, created]);
      setDestinationLocation(created.name);
      setNewLocationInput(null);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao criar nova localização.'));
    } finally {
      setCreatingLocation(false);
    }
  };

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Find sector IDs from localLocations
      const originMatch = localLocations.find(
        (l) => l.name.trim().toLowerCase() === (currentLocation || '').trim().toLowerCase()
      );
      const destMatch = localLocations.find(
        (l) => l.name.trim().toLowerCase() === (destinationLocation || '').trim().toLowerCase()
      );

      const originId = originMatch?.id || 1;
      const destId = destMatch?.id || 1;

      await equipmentApi.recordMovement(equipmentId, {
        origin_sector_id: originId,
        destination_sector_id: destId,
        origin_location: currentLocation,
        destination_location: destinationLocation,
        movement_date: new Date(movementDate).toISOString(),
        notes: notes.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao registrar movimentação'));
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
              <ArrowRightLeft className="w-4 h-4" />
            </div>
            <h2 className="text-xs font-bold text-zinc-100 tracking-tight uppercase">Registrar Movimentação</h2>
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
            <label className="block text-[11px] font-medium text-zinc-400 mb-1">Origem (Atual)</label>
            <input
              type="text"
              disabled
              value={currentLocation}
              className="w-full bg-zinc-900/40 border border-zinc-800/80 rounded-lg px-3 py-1.5 text-xs text-zinc-400 cursor-not-allowed font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Destino *</label>
            {newLocationInput !== null ? (
              <div className="flex gap-1.5">
                <input
                  type="text"
                  value={newLocationInput}
                  onChange={(e) => setNewLocationInput(e.target.value)}
                  placeholder="Nova localização"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleCreateLocation();
                    }
                    if (e.key === 'Escape') setNewLocationInput(null);
                  }}
                  className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-2.5 py-1 text-xs text-zinc-100 outline-none"
                />
                <button
                  type="button"
                  onClick={handleCreateLocation}
                  disabled={creatingLocation || !newLocationInput.trim()}
                  data-testid="confirm-create-location-btn"
                  className="px-2.5 bg-zinc-100 hover:bg-white text-zinc-950 rounded-lg text-xs font-semibold cursor-pointer disabled:opacity-50 flex items-center justify-center"
                  title="Salvar Localização"
                >
                  <Check className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => setNewLocationInput(null)}
                  className="px-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-xs cursor-pointer flex items-center justify-center"
                  title="Cancelar"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="space-y-1">
                <select
                  value={destinationLocation}
                  onChange={(e) => setDestinationLocation(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none"
                >
                  {localLocations.map((loc) => (
                    <option key={loc.id} value={loc.name}>{loc.name}</option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => setNewLocationInput('')}
                  data-testid="inline-create-location-btn"
                  className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-zinc-900/80 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg transition-all cursor-pointer shadow-sm"
                >
                  <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                  <span>Criar local</span>
                </button>
              </div>
            )}
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Data da Movimentação *</label>
            <input
              type="date"
              required
              value={movementDate}
              onChange={(e) => setMovementDate(e.target.value)}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none font-mono"
            />
          </div>

          <div>
            <label className="block text-[11px] font-medium text-zinc-300 mb-1">Observações</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ex: Equipamento transferido para o estúdio 2."
              rows={2}
              className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-100 focus:border-zinc-500 outline-none resize-none placeholder:text-zinc-500"
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
              {loading ? <div className="w-3.5 h-3.5 border-2 border-zinc-400 border-t-zinc-950 rounded-full animate-spin" /> : 'Salvar Movimentação'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
