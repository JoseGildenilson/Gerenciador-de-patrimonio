import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  HardDrive,
  Eye,
  EyeOff,
  ArrowRightLeft,
  Wrench,
  MapPin,
  Calendar,
  Key,
  Edit,
  Trash2,
  Save,
  X,
  AlertCircle,
  Plus,
  Check,
  History,
  Tag as TagIcon,
  FileText,
  Laptop,
  Monitor,
  Printer,
  Smartphone,
  ArrowRight,
} from 'lucide-react';
import { equipmentApi } from '../api/equipmentApi';
import { Equipment, EquipmentMaintenance, EquipmentMovement, EquipmentTag } from '../types/equipment';
import { MovementModal } from '../components/MovementModal';
import { MaintenanceModal } from '../components/MaintenanceModal';
import { EditMaintenanceModal } from '../components/EditMaintenanceModal';
import { formatApiError } from '../utils/errorUtils';

type ActivityItem =
  | {
      id: string;
      itemType: 'movement';
      date: string;
      movement: EquipmentMovement;
    }
  | {
      id: string;
      itemType: 'maintenance';
      date: string;
      maintenance: EquipmentMaintenance;
    };

export const EquipmentDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [equipment, setEquipment] = useState<Equipment | null>(null);
  const [types, setTypes] = useState<EquipmentTag[]>([]);
  const [locations, setLocations] = useState<EquipmentTag[]>([]);
  const [statuses, setStatuses] = useState<EquipmentTag[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Inline tag creation in detail edit mode
  const [newInlineTag, setNewInlineTag] = useState<{ category: string; value: string } | null>(null);
  const [creatingInlineTag, setCreatingInlineTag] = useState(false);

  // Toggle mask for Windows Key
  const [showWindowsKey, setShowWindowsKey] = useState(false);

  // Batch Editing Mode State (RN-EQ-08 / RN-7.3)
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    serial_number: '',
    patrimony_number: '',
    hostname: '',
    description: '',
    brand: '',
    product_number: '',
    equipment_type: '',
    location: '',
    status: '',
    windows_key: '',
    last_maintenance_at: '',
    notes: '',
  });

  // Modals state
  const [isMovementModalOpen, setIsMovementModalOpen] = useState(false);
  const [isMaintenanceModalOpen, setIsMaintenanceModalOpen] = useState(false);
  const [editingMaintenance, setEditingMaintenance] = useState<EquipmentMaintenance | null>(null);

  useEffect(() => {
    if (id) {
      fetchEquipmentDetail(parseInt(id, 10));
      fetchTags();
    }
  }, [id]);

  const fetchTags = async () => {
    try {
      const tags = await equipmentApi.getTags();
      setTypes(tags.filter((t) => t.category === 'tipo'));
      setLocations(tags.filter((t) => t.category === 'localizacao'));
      setStatuses(tags.filter((t) => t.category === 'situacao'));
    } catch (err) {
      console.error('Erro ao buscar tags:', err);
    }
  };

  const fetchEquipmentDetail = async (eqId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await equipmentApi.getEquipmentDetail(eqId);
      setEquipment(data);
      initEditForm(data);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao carregar detalhes do equipamento'));
    } finally {
      setLoading(false);
    }
  };

  const initEditForm = (data: Equipment) => {
    const rawType = typeof data.equipment_type === 'object' && data.equipment_type !== null ? (data.equipment_type as any).name : data.equipment_type;
    const rawLocation = typeof (data as any).sector === 'object' && (data as any).sector !== null
      ? (data as any).sector.name
      : typeof data.location === 'object' && data.location !== null
      ? (data.location as any).name
      : data.location || (data as any).sector;
    const rawStatus = typeof data.status === 'object' && data.status !== null ? (data.status as any).name : data.status;

    setEditForm({
      serial_number: data.serial_number || '',
      patrimony_number: data.patrimony_number || '',
      hostname: data.hostname || '',
      description: data.description || '',
      brand: data.brand || '',
      product_number: data.product_number || '',
      equipment_type: rawType || '',
      location: rawLocation || '',
      status: rawStatus || '',
      windows_key: data.windows_key || '',
      last_maintenance_at: data.last_maintenance_at
        ? new Date(data.last_maintenance_at).toISOString().substring(0, 10)
        : '',
      notes: data.notes || '',
    });
  };

  const handleCreateInlineTag = async (category: string) => {
    if (!newInlineTag || !newInlineTag.value.trim()) return;
    setError(null);
    setCreatingInlineTag(true);
    try {
      const created = await equipmentApi.createTag(category, newInlineTag.value.trim());
      await fetchTags();
      if (category === 'tipo') {
        setEditForm((prev) => ({ ...prev, equipment_type: created.name }));
      } else if (category === 'localizacao') {
        setEditForm((prev) => ({ ...prev, location: created.name }));
      } else if (category === 'situacao') {
        setEditForm((prev) => ({ ...prev, status: created.name }));
      }
      setNewInlineTag(null);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao criar nova tag.'));
    } finally {
      setCreatingInlineTag(false);
    }
  };

  const handleStartEdit = () => {
    if (equipment) {
      initEditForm(equipment);
      setIsEditing(true);
      setError(null);
      setNewInlineTag(null);
    }
  };

  const handleCancelEdit = () => {
    if (equipment) {
      initEditForm(equipment);
    }
    setIsEditing(false);
    setError(null);
    setNewInlineTag(null);
  };

  const handleSaveEdit = async () => {
    if (!equipment) return;
    setError(null);
    setSaving(true);

    try {
      const typeMatch = types.find(
        (t) => t.name.trim().toLowerCase() === editForm.equipment_type.trim().toLowerCase()
      );
      const locMatch = locations.find(
        (l) => l.name.trim().toLowerCase() === editForm.location.trim().toLowerCase()
      );
      const statusMatch = statuses.find(
        (s) => s.name.trim().toLowerCase() === editForm.status.trim().toLowerCase()
      );

      const updated = await equipmentApi.updateEquipment(equipment.id, {
        serial_number: editForm.serial_number.trim() || null,
        patrimony_number: editForm.patrimony_number.trim() || null,
        hostname: editForm.hostname.trim() || null,
        description: editForm.description.trim() || null,
        brand: editForm.brand.trim() || null,
        model: editForm.product_number.trim() || null,
        product_number: editForm.product_number.trim() || null,
        equipment_type: editForm.equipment_type,
        equipment_type_id: typeMatch?.id,
        location: editForm.location,
        sector_id: locMatch?.id,
        status: editForm.status,
        status_id: statusMatch?.id,
        windows_product_key: editForm.windows_key.trim() || null,
        windows_key: editForm.windows_key.trim() || null,
        notes: editForm.notes.trim() || null,
      });

      setEquipment(updated);
      setIsEditing(false);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao salvar alterações do equipamento'));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteMaintenance = async (maintId: number) => {
    if (!equipment) return;
    if (!window.confirm('Deseja realmente excluir este registro de manutenção?')) return;

    try {
      await equipmentApi.deleteMaintenance(equipment.id, maintId);
      fetchEquipmentDetail(equipment.id);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao excluir manutenção'));
    }
  };

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return 'Não registrada';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  // Unified chronological activity log (Movements + Maintenances)
  const activityLog = useMemo<ActivityItem[]>(() => {
    if (!equipment) return [];
    const items: ActivityItem[] = [];

    (equipment.movements || []).forEach((mov) => {
      items.push({
        id: `mov-${mov.id}`,
        itemType: 'movement',
        date: (mov as any).movement_date || mov.created_at,
        movement: mov,
      });
    });

    (equipment.maintenances || []).forEach((maint) => {
      items.push({
        id: `maint-${maint.id}`,
        itemType: 'maintenance',
        date: (maint as any).started_at || maint.maintenance_date || maint.created_at,
        maintenance: maint,
      });
    });

    // Sort descending by date
    items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
    return items;
  }, [equipment]);

  const renderStatusPill = (status?: any) => {
    const raw = typeof status === 'object' && status !== null ? status.name : status;
    const safeStatus = String(raw || 'Não definido');
    const s = safeStatus.toLowerCase();
    if (s.includes('uso') || s.includes('ativo')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
          {safeStatus}
        </span>
      );
    }
    if (s.includes('manuten') || s.includes('repar') || s.includes('recolhimento')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          {safeStatus}
        </span>
      );
    }
    if (s.includes('ocioso') || s.includes('estoque') || s.includes('dispon')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          {safeStatus}
        </span>
      );
    }
    if (s.includes('baixado') || s.includes('descarte') || s.includes('inativ')) {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-600/20 text-zinc-400 font-medium text-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
          {safeStatus}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-800 text-zinc-300 font-medium text-xs">
        <span className="w-1.5 h-1.5 rounded-full bg-zinc-400" />
        {safeStatus}
      </span>
    );
  };

  const getEquipmentTypeIcon = (type?: any) => {
    const raw = typeof type === 'object' && type !== null ? type.name : type;
    const t = String(raw || '').toLowerCase();
    if (t.includes('notebook') || t.includes('laptop')) return <Laptop className="w-4 h-4 text-[#9E9E9E]" />;
    if (t.includes('monitor') || t.includes('tela')) return <Monitor className="w-4 h-4 text-[#9E9E9E]" />;
    if (t.includes('impressora')) return <Printer className="w-4 h-4 text-[#9E9E9E]" />;
    if (t.includes('celular') || t.includes('tablet')) return <Smartphone className="w-4 h-4 text-[#9E9E9E]" />;
    return <HardDrive className="w-4 h-4 text-[#9E9E9E]" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#121212] flex flex-col items-center justify-center text-[#9E9E9E]">
        <div className="w-6 h-6 border-2 border-[#333333] border-t-white rounded-full animate-spin mb-2" />
        <p className="text-xs font-mono">Carregando prontuário técnico...</p>
      </div>
    );
  }

  if (error && !equipment) {
    return (
      <div className="min-h-screen bg-[#121212] flex flex-col items-center justify-center p-6 text-center">
        <div className="p-6 bg-[#1E1E1E] border border-[#333333] rounded-lg max-w-md space-y-4">
          <p className="text-sm font-semibold text-red-400">{error || 'Equipamento não encontrado'}</p>
          <button
            onClick={() => navigate('/equipamentos')}
            className="px-4 py-2 bg-[#333333] hover:bg-[#444444] text-[#E0E0E0] rounded-md text-xs font-semibold cursor-pointer"
          >
            Voltar para Equipamentos
          </button>
        </div>
      </div>
    );
  }

  if (!equipment) return null;

  return (
    <div className="min-h-screen bg-[#121212] text-[#E0E0E0] font-sans antialiased flex flex-col selection:bg-zinc-800 selection:text-white">
      {/* Header Section */}
      <header className="border-b border-[#333333] bg-[#1E1E1E] px-6 py-4 flex flex-col md:flex-row md:items-center justify-between sticky top-0 z-30 gap-4">
        <div className="flex items-center gap-4">
          {/* Back Button */}
          <button
            onClick={() => navigate('/equipamentos')}
            data-testid="back-to-equipments-btn"
            className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[#333333] hover:bg-[#333333] transition-colors text-sm font-medium text-[#E0E0E0] cursor-pointer"
            title="Voltar para a listagem de Equipamentos"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Voltar para equipamentos</span>
          </button>

          {/* Title & Subtitle */}
          <div className="ml-2 flex flex-col">
            <h1 className="text-lg md:text-xl font-semibold text-white tracking-tight">
              {equipment.description}
            </h1>
            <p className="text-[10px] font-semibold tracking-widest text-[#9E9E9E] uppercase font-mono mt-0.5">
              Prontuário Técnico
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          {!isEditing ? (
            <>
              <button
                onClick={handleStartEdit}
                data-testid="edit-equipment-btn"
                className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[#333333] hover:bg-[#333333] text-sm font-medium text-[#E0E0E0] transition-colors cursor-pointer"
              >
                <Edit className="w-4 h-4 text-[#9E9E9E]" />
                <span>Editar</span>
              </button>

              <button
                onClick={() => setIsMovementModalOpen(true)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-[#333333] hover:bg-[#333333] text-sm font-medium text-[#E0E0E0] transition-colors cursor-pointer"
              >
                <ArrowRightLeft className="w-4 h-4 text-[#9E9E9E]" />
                <span>Movimentar</span>
              </button>

              <button
                onClick={() => setIsMaintenanceModalOpen(true)}
                className="flex items-center gap-2 px-4 py-2 rounded-md bg-white hover:bg-gray-200 text-sm font-semibold text-[#121212] transition-colors shadow-sm cursor-pointer active:scale-[0.99]"
              >
                <Wrench className="w-4 h-4" />
                <span>Manutenção</span>
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleCancelEdit}
                disabled={saving}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-[#333333] hover:bg-[#333333] text-sm font-medium text-[#E0E0E0] transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
                <span>Cancelar</span>
              </button>

              <button
                onClick={handleSaveEdit}
                disabled={saving}
                className="flex items-center gap-1.5 px-4 py-2 rounded-md bg-white hover:bg-gray-200 text-sm font-semibold text-[#121212] transition-colors shadow-sm cursor-pointer disabled:opacity-50"
              >
                {saving ? (
                  <div className="w-4 h-4 border-2 border-[#121212] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    <span>Salvar alterações</span>
                  </>
                )}
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="w-full max-w-7xl mx-auto p-6 md:p-8 flex flex-col gap-6">
        {error && (
          <div className="p-3.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 3 Technical Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Card 1: Identificação */}
          <section className="bg-[#1E1E1E] rounded-lg border border-[#333333] p-6 flex flex-col gap-5 shadow-sm">
            <div className="flex items-center gap-2 text-[#9E9E9E] font-semibold text-xs uppercase tracking-wider border-b border-[#333333] pb-3">
              {getEquipmentTypeIcon(equipment.equipment_type)}
              <h2>Identificação</h2>
            </div>

            <div className="grid grid-cols-2 gap-y-4 gap-x-4 text-xs">
              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1 font-mono">
                  Nº Patrimônio
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.patrimony_number}
                    onChange={(e) => setEditForm({ ...editForm, patrimony_number: e.target.value })}
                    className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono focus:border-[#9E9E9E]"
                  />
                ) : (
                  <span className="text-sm font-semibold text-white font-mono">{equipment.patrimony_number || 'N/A'}</span>
                )}
              </div>

              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1 font-mono">
                  Nº Série (SN)
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    required
                    value={editForm.serial_number}
                    onChange={(e) => setEditForm({ ...editForm, serial_number: e.target.value })}
                    className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono focus:border-[#9E9E9E]"
                  />
                ) : (
                  <span className="text-sm font-medium text-white font-mono">{equipment.serial_number}</span>
                )}
              </div>

              <div className="col-span-2">
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1">
                  Descrição
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    required
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none focus:border-[#9E9E9E]"
                  />
                ) : (
                  <span className="text-sm font-medium text-[#E0E0E0]">{equipment.description}</span>
                )}
              </div>

              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1">
                  Tipo
                </span>
                {isEditing ? (
                  newInlineTag?.category === 'tipo' ? (
                    <div className="flex gap-1.5 mt-1">
                      <input
                        type="text"
                        value={newInlineTag.value}
                        onChange={(e) => setNewInlineTag({ category: 'tipo', value: e.target.value })}
                        placeholder="Novo tipo..."
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleCreateInlineTag('tipo');
                          }
                          if (e.key === 'Escape') setNewInlineTag(null);
                        }}
                        className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1 text-xs text-white outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => handleCreateInlineTag('tipo')}
                        disabled={creatingInlineTag || !newInlineTag.value.trim()}
                        className="px-2 bg-zinc-100 text-zinc-950 rounded-md text-xs font-semibold cursor-pointer"
                        title="Salvar"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setNewInlineTag(null)}
                        className="px-2 bg-zinc-800 text-zinc-300 rounded-md text-xs cursor-pointer"
                        title="Cancelar"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      <select
                        value={editForm.equipment_type}
                        onChange={(e) => setEditForm({ ...editForm, equipment_type: e.target.value })}
                        className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none focus:border-[#9E9E9E]"
                      >
                        {types.map((t) => (
                          <option key={t.id} value={t.name}>{t.name}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => setNewInlineTag({ category: 'tipo', value: '' })}
                        data-testid="inline-create-tipo-btn"
                        className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-[#1a1a1a] hover:bg-[#262626] border border-[#333333] hover:border-[#444444] rounded-md transition-all cursor-pointer shadow-sm"
                      >
                        <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                        <span>Criar tipo</span>
                      </button>
                    </div>
                  )
                ) : (
                  <span className="text-xs font-mono text-[#E0E0E0] px-2 py-0.5 bg-[#121212] border border-[#333333] rounded inline-block">
                    {typeof equipment.equipment_type === 'object' && equipment.equipment_type !== null
                      ? (equipment.equipment_type as any).name
                      : equipment.equipment_type}
                  </span>
                )}
              </div>

              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1">
                  Marca &amp; Produto
                </span>
                {isEditing ? (
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder="Marca"
                      value={editForm.brand}
                      onChange={(e) => setEditForm({ ...editForm, brand: e.target.value })}
                      className="w-full bg-[#121212] border border-[#333333] rounded-md px-2 py-1.5 text-xs text-white outline-none focus:border-[#9E9E9E]"
                    />
                    <input
                      type="text"
                      placeholder="Produto"
                      value={editForm.product_number}
                      onChange={(e) => setEditForm({ ...editForm, product_number: e.target.value })}
                      className="w-full bg-[#121212] border border-[#333333] rounded-md px-2 py-1.5 text-xs text-white outline-none font-mono focus:border-[#9E9E9E]"
                    />
                  </div>
                ) : (
                  <span className="text-xs text-[#E0E0E0]">
                    {equipment.brand || 'N/A'} {equipment.product_number ? `(${equipment.product_number})` : ''}
                  </span>
                )}
              </div>
            </div>
          </section>

          {/* Card 2: Localização & Estado */}
          <section className="bg-[#1E1E1E] rounded-lg border border-[#333333] p-6 flex flex-col gap-4 shadow-sm">
            <div className="flex items-center gap-2 text-[#9E9E9E] font-semibold text-xs uppercase tracking-wider border-b border-[#333333] pb-3">
              <MapPin className="w-4 h-4 text-[#9E9E9E]" />
              <h2>Localização &amp; Estado</h2>
            </div>

            <div className="flex flex-col gap-3.5">
              {/* Current Location Block */}
              <div className="bg-[#121212] rounded-lg border border-[#333333] p-3.5 flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-[#9E9E9E]">
                  <MapPin className="w-3.5 h-3.5" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Localização Atual</span>
                </div>
                {isEditing ? (
                  newInlineTag?.category === 'localizacao' ? (
                    <div className="flex gap-1.5 mt-1">
                      <input
                        type="text"
                        value={newInlineTag.value}
                        onChange={(e) => setNewInlineTag({ category: 'localizacao', value: e.target.value })}
                        placeholder="Nova localização..."
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleCreateInlineTag('localizacao');
                          }
                          if (e.key === 'Escape') setNewInlineTag(null);
                        }}
                        className="w-full bg-[#1E1E1E] border border-[#333333] rounded-md px-2.5 py-1 text-xs text-white outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => handleCreateInlineTag('localizacao')}
                        disabled={creatingInlineTag || !newInlineTag.value.trim()}
                        className="px-2 bg-zinc-100 text-zinc-950 rounded-md text-xs font-semibold cursor-pointer"
                        title="Salvar"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setNewInlineTag(null)}
                        className="px-2 bg-zinc-800 text-zinc-300 rounded-md text-xs cursor-pointer"
                        title="Cancelar"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      <select
                        value={editForm.location}
                        onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                        className="w-full bg-[#1E1E1E] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none mt-1 focus:border-[#9E9E9E]"
                      >
                        {locations.map((l) => (
                          <option key={l.id} value={l.name}>{l.name}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => setNewInlineTag({ category: 'localizacao', value: '' })}
                        data-testid="inline-create-localizacao-btn"
                        className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-[#1a1a1a] hover:bg-[#262626] border border-[#333333] hover:border-[#444444] rounded-md transition-all cursor-pointer shadow-sm"
                      >
                        <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                        <span>Criar local</span>
                      </button>
                    </div>
                  )
                ) : (
                  <span className="text-sm font-semibold text-white mt-0.5">
                    {typeof (equipment as any).sector === 'object' && (equipment as any).sector !== null
                      ? (equipment as any).sector.name
                      : typeof equipment.location === 'object' && equipment.location !== null
                      ? (equipment.location as any).name
                      : equipment.location || (equipment as any).sector || 'Não definido'}
                  </span>
                )}
              </div>

              {/* Status Block */}
              <div className="bg-[#121212] rounded-lg border border-[#333333] p-3.5 flex flex-col gap-1">
                <div className="flex items-center gap-1.5 text-[#9E9E9E]">
                  <TagIcon className="w-3.5 h-3.5" />
                  <span className="text-[10px] font-bold uppercase tracking-wider">Situação do Patrimônio</span>
                </div>
                {isEditing ? (
                  newInlineTag?.category === 'situacao' ? (
                    <div className="flex gap-1.5 mt-1">
                      <input
                        type="text"
                        value={newInlineTag.value}
                        onChange={(e) => setNewInlineTag({ category: 'situacao', value: e.target.value })}
                        placeholder="Nova situação..."
                        autoFocus
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleCreateInlineTag('situacao');
                          }
                          if (e.key === 'Escape') setNewInlineTag(null);
                        }}
                        className="w-full bg-[#1E1E1E] border border-[#333333] rounded-md px-2.5 py-1 text-xs text-white outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => handleCreateInlineTag('situacao')}
                        disabled={creatingInlineTag || !newInlineTag.value.trim()}
                        className="px-2 bg-zinc-100 text-zinc-950 rounded-md text-xs font-semibold cursor-pointer"
                        title="Salvar"
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setNewInlineTag(null)}
                        className="px-2 bg-zinc-800 text-zinc-300 rounded-md text-xs cursor-pointer"
                        title="Cancelar"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      <select
                        value={editForm.status}
                        onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                        className="w-full bg-[#1E1E1E] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none mt-1 focus:border-[#9E9E9E]"
                      >
                        {statuses.map((s) => (
                          <option key={s.id} value={s.name}>{s.name}</option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => setNewInlineTag({ category: 'situacao', value: '' })}
                        data-testid="inline-create-situacao-btn"
                        className="group inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-zinc-300 hover:text-white bg-[#1a1a1a] hover:bg-[#262626] border border-[#333333] hover:border-[#444444] rounded-md transition-all cursor-pointer shadow-sm"
                      >
                        <Plus className="w-3.5 h-3.5 text-zinc-400 group-hover:text-zinc-100 transition-colors" />
                        <span>Criar situação</span>
                      </button>
                    </div>
                  )
                ) : (
                  <div className="mt-1">
                    {renderStatusPill(equipment.status)}
                  </div>
                )}
              </div>

              {/* Hostname */}
              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1 font-mono">
                  Hostname
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.hostname}
                    onChange={(e) => setEditForm({ ...editForm, hostname: e.target.value })}
                    className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono focus:border-[#9E9E9E]"
                  />
                ) : (
                  <span className="text-xs font-mono text-[#E0E0E0] bg-[#121212] px-2.5 py-1 rounded border border-[#333333] inline-block">
                    {equipment.hostname || 'Não informado'}
                  </span>
                )}
              </div>
            </div>
          </section>

          {/* Card 3: Técnica & Licença */}
          <section className="bg-[#1E1E1E] rounded-lg border border-[#333333] p-6 flex flex-col gap-4 shadow-sm">
            <div className="flex items-center gap-2 text-[#9E9E9E] font-semibold text-xs uppercase tracking-wider border-b border-[#333333] pb-3">
              <Key className="w-4 h-4 text-[#9E9E9E]" />
              <h2>Técnica &amp; Licença</h2>
            </div>

            <div className="flex flex-col gap-4">
              {/* Last Maintenance */}
              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1 font-mono">
                  Última Manutenção
                </span>
                {isEditing ? (
                  <input
                    type="date"
                    value={editForm.last_maintenance_at}
                    onChange={(e) => setEditForm({ ...editForm, last_maintenance_at: e.target.value })}
                    className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono focus:border-[#9E9E9E]"
                  />
                ) : (
                  <div className="flex items-center gap-2 mt-1 text-[#E0E0E0]">
                    <Calendar className="w-4 h-4 text-[#9E9E9E]" />
                    <span className="font-mono text-sm">{formatDate(equipment.last_maintenance_at)}</span>
                  </div>
                )}
              </div>

              {/* Windows Key (Masked with Eye button) */}
              <div>
                <span className="text-[10px] font-bold text-[#9E9E9E] uppercase tracking-wider block mb-1 font-mono">
                  Chave Windows
                </span>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.windows_key}
                    onChange={(e) => setEditForm({ ...editForm, windows_key: e.target.value })}
                    placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
                    className="w-full bg-[#121212] border border-[#333333] rounded-md px-2.5 py-1.5 text-xs text-white outline-none font-mono focus:border-[#9E9E9E]"
                  />
                ) : (
                  <div className="mt-1 flex items-center justify-between bg-[#121212] border border-[#333333] rounded-md px-3 py-2">
                    <span className="font-mono text-xs text-[#E0E0E0] truncate">
                      {equipment.windows_key
                        ? showWindowsKey
                          ? equipment.windows_key
                          : '•••••••••••••••••••••••••'
                        : 'Nenhuma chave registrada'}
                    </span>
                    {equipment.windows_key && (
                      <button
                        onClick={() => setShowWindowsKey(!showWindowsKey)}
                        className="p-1 text-[#9E9E9E] hover:text-white transition-colors cursor-pointer"
                        title={showWindowsKey ? 'Ocultar Chave' : 'Mostrar Chave'}
                      >
                        {showWindowsKey ? <EyeOff className="w-4 h-4 text-white" /> : <Eye className="w-4 h-4" />}
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>

        {/* Section: Observações Técnicas & Detalhes (Campo Ampliado conforme solicitado) */}
        <section className="bg-[#1E1E1E] rounded-lg border border-[#333333] p-6 flex flex-col gap-3 shadow-sm">
          <div className="flex items-center gap-2 text-[#9E9E9E] font-semibold text-xs uppercase tracking-wider border-b border-[#333333] pb-3">
            <FileText className="w-4 h-4 text-[#9E9E9E]" />
            <h2>Observações Gerais &amp; Notas do Ativo</h2>
          </div>

          <div>
            {isEditing ? (
              <textarea
                value={editForm.notes}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                rows={5}
                placeholder="Insira detalhes técnicos, alterações de hardware, histórico de peças ou notas relevantes sobre o equipamento..."
                className="w-full bg-[#121212] border border-[#333333] text-[#E0E0E0] rounded-lg p-3 text-sm focus:outline-none focus:ring-1 focus:ring-[#9E9E9E] resize-y placeholder-[#9E9E9E]/50"
              />
            ) : (
              <div className="bg-[#121212] border border-[#333333] rounded-lg p-4 min-h-[90px]">
                <p className="text-sm text-[#E0E0E0] leading-relaxed whitespace-pre-wrap">
                  {equipment.notes || 'Nenhuma observação técnica registrada para este equipamento.'}
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Section: Log de Atividades Unificado (Timeline de Movimentações + Manutenções) */}
        <section className="bg-[#1E1E1E] rounded-lg border border-[#333333] p-6 flex flex-col gap-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-[#333333] pb-3">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-[#9E9E9E]" />
              <h2 className="text-sm font-semibold text-white">
                Log de Atividades ({activityLog.length})
              </h2>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsMovementModalOpen(true)}
                className="flex items-center gap-1 text-xs font-medium text-[#9E9E9E] hover:text-white transition-colors cursor-pointer px-2.5 py-1 rounded bg-[#121212] border border-[#333333]"
              >
                <Plus className="w-3.5 h-3.5" /> Movimentação
              </button>
              <button
                onClick={() => setIsMaintenanceModalOpen(true)}
                className="flex items-center gap-1 text-xs font-medium text-[#9E9E9E] hover:text-white transition-colors cursor-pointer px-2.5 py-1 rounded bg-[#121212] border border-[#333333]"
              >
                <Plus className="w-3.5 h-3.5" /> Manutenção
              </button>
            </div>
          </div>

          {activityLog.length === 0 ? (
            <p className="text-xs text-[#9E9E9E] py-8 text-center font-mono">
              Nenhuma atividade de movimentação ou manutenção registrada.
            </p>
          ) : (
            <div className="flex flex-col gap-3">
              {activityLog.map((act) => {
                if (act.itemType === 'movement') {
                  const mov = act.movement;
                  return (
                    <article
                      key={act.id}
                      className="bg-[#121212] border border-[#333333] rounded-lg p-4 flex items-start gap-4 hover:border-gray-600 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-lg bg-[#1E1E1E] border border-[#333333] flex items-center justify-center shrink-0 text-[#9E9E9E]">
                        <ArrowRightLeft className="w-4 h-4" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-white">Movimentação</span>
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-500/10 text-blue-400 font-mono">
                              Transferência
                            </span>
                          </div>

                          <div className="flex items-center gap-1 text-xs text-[#9E9E9E] font-mono">
                            <Calendar className="w-3.5 h-3.5 text-[#9E9E9E]" />
                            <span>{formatDate(mov.movement_date)}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-[#9E9E9E] mt-2 flex-wrap">
                          <span className="inline-flex items-center px-2 py-0.5 rounded font-medium bg-[#1E1E1E] border border-[#333333] text-[#E0E0E0]">
                            {typeof (mov as any).origin_sector === 'object' && (mov as any).origin_sector !== null
                              ? (mov as any).origin_sector.name
                              : typeof mov.origin_location === 'object' && mov.origin_location !== null
                              ? (mov.origin_location as any).name
                              : mov.origin_location || 'Origem não informada'}
                          </span>
                          <ArrowRight className="w-3.5 h-3.5 text-[#9E9E9E]" />
                          <span className="inline-flex items-center px-2 py-0.5 rounded font-medium bg-[#1E1E1E] border border-[#333333] text-white font-semibold">
                            {typeof (mov as any).destination_sector === 'object' && (mov as any).destination_sector !== null
                              ? (mov as any).destination_sector.name
                              : typeof mov.destination_location === 'object' && mov.destination_location !== null
                              ? (mov.destination_location as any).name
                              : mov.destination_location || 'Destino não informado'}
                          </span>
                        </div>

                        {mov.notes && (
                          <p className="text-xs text-[#9E9E9E] mt-2.5 bg-[#1E1E1E]/60 p-2.5 rounded border border-[#333333]">
                            {mov.notes}
                          </p>
                        )}
                      </div>
                    </article>
                  );
                }

                // Maintenance item
                const maint = act.maintenance;
                const maintTypeName =
                  typeof maint.maintenance_type === 'object' && maint.maintenance_type !== null
                    ? (maint.maintenance_type as any).name
                    : maint.maintenance_type || 'Intervenção';
                const maintDate = (maint as any).started_at || maint.maintenance_date || maint.created_at;

                return (
                  <article
                    key={act.id}
                    className="bg-[#121212] border border-[#333333] rounded-lg p-4 flex items-start gap-4 hover:border-gray-600 transition-colors"
                  >
                    <div className="w-10 h-10 rounded-lg bg-[#1E1E1E] border border-[#333333] flex items-center justify-center shrink-0 text-[#9E9E9E]">
                      <Wrench className="w-4 h-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium text-white">Manutenção Técnica</span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 font-mono">
                            {maintTypeName}
                          </span>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="flex items-center gap-1 text-xs text-[#9E9E9E] font-mono">
                            <Calendar className="w-3.5 h-3.5 text-[#9E9E9E]" />
                            <span>{formatDate(maintDate)}</span>
                          </div>

                          {/* Action Buttons: Edit / Delete */}
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => setEditingMaintenance(maint)}
                              className="p-1 text-[#9E9E9E] hover:text-white transition-colors cursor-pointer"
                              title="Editar manutenção"
                            >
                              <Edit className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDeleteMaintenance(maint.id)}
                              className="p-1 text-[#9E9E9E] hover:text-red-400 transition-colors cursor-pointer"
                              title="Excluir manutenção"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>

                      <p className="text-sm text-white font-medium whitespace-pre-wrap mt-1 leading-relaxed">
                        {maint.description}
                      </p>

                      {maint.notes && (
                        <p className="text-xs text-[#9E9E9E] mt-2 bg-[#1E1E1E]/60 p-2.5 rounded border border-[#333333]">
                          Obs: {maint.notes}
                        </p>
                      )}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </main>

      {/* Modais */}
      <MovementModal
        isOpen={isMovementModalOpen}
        equipmentId={equipment.id}
        currentLocation={
          typeof (equipment as any).sector === 'object' && (equipment as any).sector !== null
            ? (equipment as any).sector.name
            : typeof equipment.location === 'object' && equipment.location !== null
            ? (equipment.location as any).name
            : equipment.location || (equipment as any).sector || 'Não definido'
        }
        locations={locations}
        onClose={() => setIsMovementModalOpen(false)}
        onSuccess={() => fetchEquipmentDetail(equipment.id)}
      />

      <MaintenanceModal
        isOpen={isMaintenanceModalOpen}
        equipmentId={equipment.id}
        onClose={() => setIsMaintenanceModalOpen(false)}
        onSuccess={() => fetchEquipmentDetail(equipment.id)}
      />

      <EditMaintenanceModal
        isOpen={Boolean(editingMaintenance)}
        equipmentId={equipment.id}
        maintenance={editingMaintenance}
        onClose={() => setEditingMaintenance(null)}
        onSuccess={() => fetchEquipmentDetail(equipment.id)}
      />
    </div>
  );
};
