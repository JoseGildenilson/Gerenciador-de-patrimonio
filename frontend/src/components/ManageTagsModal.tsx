import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  Plus,
  Tag as TagIcon,
  MapPin,
  Laptop,
  CheckCircle,
  AlertCircle,
  Edit2,
  Trash2,
  Check,
  Search,
  Monitor,
  Printer,
  Smartphone,
  Server,
  HardDrive,
  Cpu,
  Wifi,
  Radio,
  Building,
  Home,
  Briefcase,
  Layers,
  Archive,
  Clock,
  Wrench,
  Shield,
  HelpCircle,
  Folder,
  Sliders,
  ChevronDown,
} from 'lucide-react';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentTag } from '../types/equipment';
import { formatApiError } from '../utils/errorUtils';

interface ManageTagsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTagsUpdated?: () => void;
}

type CategoryType = 'tipo' | 'localizacao' | 'situacao';

export const ICON_OPTIONS: { name: string; label: string; icon: React.FC<{ className?: string }> }[] = [
  { name: 'laptop', label: 'Notebook / Laptop', icon: Laptop },
  { name: 'monitor', label: 'Monitor / Tela', icon: Monitor },
  { name: 'printer', label: 'Impressora', icon: Printer },
  { name: 'smartphone', label: 'Smartphone / Tablet', icon: Smartphone },
  { name: 'server', label: 'Servidor', icon: Server },
  { name: 'harddrive', label: 'Desktop / HD / Storage', icon: HardDrive },
  { name: 'cpu', label: 'Processador / Hardware', icon: Cpu },
  { name: 'wifi', label: 'Rede / Roteador / Wi-Fi', icon: Wifi },
  { name: 'radio', label: 'Rádio / Comunicação', icon: Radio },
  { name: 'building', label: 'Prédio / Sede / Setor', icon: Building },
  { name: 'map-pin', label: 'Local / Sala / Ponto', icon: MapPin },
  { name: 'home', label: 'Home Office / Base', icon: Home },
  { name: 'briefcase', label: 'Diretoria / Administrativo', icon: Briefcase },
  { name: 'layers', label: 'Camada / Estoque', icon: Layers },
  { name: 'archive', label: 'Almoxarifado / Arquivo', icon: Archive },
  { name: 'check', label: 'Em Uso / Ativo / Ok', icon: Check },
  { name: 'wrench', label: 'Manutenção / Reparo', icon: Wrench },
  { name: 'clock', label: 'Aguardando / Pendente', icon: Clock },
  { name: 'shield', label: 'Segurança / TI', icon: Shield },
  { name: 'tag', label: 'Tag Geral / Status', icon: TagIcon },
  { name: 'folder', label: 'Pasta / Projeto', icon: Folder },
  { name: 'sliders', label: 'Configuração / Outro', icon: Sliders },
];

export const getIconComponent = (iconName?: string | null, fallbackIcon?: React.FC<{ className?: string }>) => {
  if (iconName) {
    const found = ICON_OPTIONS.find((item) => item.name.toLowerCase() === iconName.toLowerCase());
    if (found) return found.icon;
  }
  return fallbackIcon || TagIcon;
};

const CATEGORIES: { id: CategoryType; label: string; icon: React.FC<{ className?: string }>; defaultIconName: string }[] = [
  { id: 'tipo', label: 'Tipos de Equipamento', icon: Laptop, defaultIconName: 'laptop' },
  { id: 'localizacao', label: 'Localizações', icon: MapPin, defaultIconName: 'map-pin' },
  { id: 'situacao', label: 'Situações (Status)', icon: TagIcon, defaultIconName: 'tag' },
];

export const ManageTagsModal: React.FC<ManageTagsModalProps> = ({
  isOpen,
  onClose,
  onTagsUpdated,
}) => {
  const [activeCategory, setActiveCategory] = useState<CategoryType>('tipo');
  const [tags, setTags] = useState<EquipmentTag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // New tag input & icon state
  const [newTagName, setNewTagName] = useState('');
  const [selectedIconName, setSelectedIconName] = useState<string>('laptop');
  const [isIconPickerOpen, setIsIconPickerOpen] = useState(false);
  const [iconSearch, setIconSearch] = useState('');
  const [addingTag, setAddingTag] = useState(false);
  const iconPickerRef = useRef<HTMLDivElement>(null);

  // Map of local custom icons for tags
  const [tagIcons, setTagIcons] = useState<Record<number, string>>(() => {
    try {
      const saved = localStorage.getItem('equipment_tag_icons');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // Editing state
  const [editingTagId, setEditingTagId] = useState<number | null>(null);
  const [editingTagName, setEditingTagName] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Deleting state
  const [deletingTagId, setDeletingTagId] = useState<number | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchTags();
      setError(null);
      setSuccessMsg(null);
      setNewTagName('');
      setEditingTagId(null);
      setDeletingTagId(null);
    }
  }, [isOpen]);

  const fetchTags = async () => {
    setLoading(true);
    try {
      const data = await equipmentApi.getTags();
      setTags(data);
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao carregar tags.'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const currentCategoryTags = tags.filter((t) => t.category === activeCategory);
  const activeCategoryObj = CATEGORIES.find((c) => c.id === activeCategory);

  const handleAddTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTagName.trim()) return;

    setError(null);
    setSuccessMsg(null);
    setAddingTag(true);

    try {
      const createdTag = await equipmentApi.createTag(activeCategory, newTagName.trim());
      if (createdTag?.id) {
        const nextMap = { ...tagIcons, [createdTag.id]: selectedIconName };
        setTagIcons(nextMap);
        try {
          localStorage.setItem('equipment_tag_icons', JSON.stringify(nextMap));
        } catch {
          // ignore localStorage error
        }
      }
      setNewTagName('');
      setSuccessMsg('Tag cadastrada com sucesso.');
      await fetchTags();
      if (onTagsUpdated) onTagsUpdated();
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao cadastrar tag.'));
    } finally {
      setAddingTag(false);
    }
  };

  const handleStartEdit = (tag: EquipmentTag) => {
    setEditingTagId(tag.id);
    setEditingTagName(tag.name);
    setError(null);
    setSuccessMsg(null);
  };

  const handleCancelEdit = () => {
    setEditingTagId(null);
    setEditingTagName('');
  };

  const handleSaveEdit = async (tagId: number) => {
    if (!editingTagName.trim()) {
      setError('O nome da tag não pode ser vazio.');
      return;
    }

    setError(null);
    setSuccessMsg(null);
    setSavingEdit(true);

    try {
      await equipmentApi.updateTag(tagId, editingTagName.trim());
      setEditingTagId(null);
      setEditingTagName('');
      setSuccessMsg('Tag renomeada com sucesso.');
      await fetchTags();
      if (onTagsUpdated) onTagsUpdated();
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao renomear tag.'));
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteTag = async (tagId: number) => {
    setError(null);
    setSuccessMsg(null);

    try {
      await equipmentApi.deleteTag(tagId);
      setDeletingTagId(null);
      setSuccessMsg('Tag excluída com sucesso.');
      await fetchTags();
      if (onTagsUpdated) onTagsUpdated();
    } catch (err: any) {
      setError(formatApiError(err, 'Erro ao excluir tag.'));
    }
  };

  return createPortal(
    <div
      data-testid="manage-tags-modal"
      className="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6 bg-black/70 backdrop-blur-sm animate-fade-in-overlay overflow-y-auto"
    >
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl shadow-dropdown w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-fade-in my-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800 bg-zinc-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-zinc-900 border border-zinc-800 text-zinc-300 rounded-lg">
              <TagIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-zinc-100 tracking-tight">Gerenciador de Tags</h2>
              <p className="text-[11px] text-zinc-500 font-mono">CADASTRO E MANUTENÇÃO DE CATEGORIAS</p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="close-tags-modal-btn"
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Feedback Banners */}
        {error && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle className="w-4 h-4 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Category Tabs */}
        <div className="flex border-b border-zinc-800 bg-zinc-900/40 px-6 pt-2">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const count = tags.filter((t) => t.category === cat.id).length;
            const isActive = activeCategory === cat.id;

            return (
              <button
                key={cat.id}
                onClick={() => {
                  setActiveCategory(cat.id);
                  setSelectedIconName(cat.defaultIconName);
                  setIsIconPickerOpen(false);
                  setError(null);
                  setSuccessMsg(null);
                  setEditingTagId(null);
                  setDeletingTagId(null);
                }}
                data-testid={`tab-${cat.id}`}
                className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
                  isActive
                    ? 'border-white text-white bg-zinc-900/60'
                    : 'border-transparent text-zinc-400 hover:text-zinc-200'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{cat.label}</span>
                <span className="px-1.5 py-0.2 rounded bg-zinc-800 text-[10px] text-zinc-300 font-mono">
                  {count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Static Add Tag Form Container (com overflow visível para o popover) */}
        <div className="px-6 pt-5 pb-2 relative z-20 overflow-visible">
          <form onSubmit={handleAddTag} className="space-y-2">
            <div className="flex gap-2 relative">
              {/* Seletor de Ícone estilo Iconize */}
              <div className="relative" ref={iconPickerRef}>
                <button
                  type="button"
                  onClick={() => setIsIconPickerOpen(!isIconPickerOpen)}
                  data-testid="icon-picker-btn"
                  className="h-full px-3 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 hover:text-white rounded-xl text-xs flex items-center gap-1.5 transition-colors cursor-pointer"
                  title="Escolher ícone"
                >
                  {React.createElement(getIconComponent(selectedIconName, activeCategoryObj?.icon), {
                    className: 'w-4 h-4 text-zinc-300',
                  })}
                  <ChevronDown className="w-3 h-3 text-zinc-500" />
                </button>

                {isIconPickerOpen && (
                  <div
                    data-testid="icon-picker-popover"
                    className="absolute left-0 top-full mt-2 w-72 bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl p-3 z-50 space-y-2.5 animate-fade-in"
                  >
                    <div className="flex items-center justify-between pb-1.5 border-b border-zinc-800 text-[11px] font-mono text-zinc-400">
                      <span>SELECIONAR ÍCONE</span>
                      <button
                        type="button"
                        onClick={() => setIsIconPickerOpen(false)}
                        className="text-zinc-500 hover:text-zinc-200"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>

                    {/* Campo de Busca de Ícones */}
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                      <input
                        type="text"
                        value={iconSearch}
                        onChange={(e) => setIconSearch(e.target.value)}
                        placeholder="Buscar ícone (ex: printer, server)..."
                        data-testid="icon-search-input"
                        autoFocus
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-zinc-200 placeholder:text-zinc-500 outline-none focus:border-zinc-600"
                      />
                    </div>

                    {/* Grid de Ícones */}
                    <div className="max-h-48 overflow-y-auto grid grid-cols-4 gap-1.5 custom-scrollbar pr-1">
                      {ICON_OPTIONS.filter(
                        (opt) =>
                          opt.name.toLowerCase().includes(iconSearch.toLowerCase()) ||
                          opt.label.toLowerCase().includes(iconSearch.toLowerCase())
                      ).map((opt) => {
                        const IconComponent = opt.icon;
                        const isSelected = selectedIconName === opt.name;
                        return (
                          <button
                            key={opt.name}
                            type="button"
                            onClick={() => {
                              setSelectedIconName(opt.name);
                              setIsIconPickerOpen(false);
                            }}
                            data-testid={`select-icon-${opt.name}`}
                            className={`p-2 rounded-lg flex flex-col items-center justify-center gap-1 transition-all cursor-pointer ${
                              isSelected
                                ? 'bg-white/15 border border-white/40 text-white shadow-sm'
                                : 'bg-zinc-900/60 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 border border-transparent'
                            }`}
                            title={opt.label}
                          >
                            <IconComponent className="w-4 h-4" />
                            <span className="text-[9px] font-mono truncate w-full text-center">
                              {opt.name}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <input
                type="text"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                placeholder={`Adicionar novo ${
                  activeCategory === 'tipo'
                    ? 'tipo de equipamento'
                    : activeCategory === 'localizacao'
                    ? 'local'
                    : 'status'
                }...`}
                className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-3.5 py-2 text-xs text-zinc-100 placeholder:text-zinc-500 focus:border-zinc-500 outline-none"
              />
              <button
                type="submit"
                disabled={addingTag || !newTagName.trim()}
                data-testid="add-tag-btn"
                className="px-4 py-2 bg-zinc-100 hover:bg-white text-zinc-950 rounded-xl text-xs font-semibold transition-all shadow-sm disabled:opacity-50 cursor-pointer flex items-center gap-1.5 active:scale-[0.99]"
              >
                {addingTag ? (
                  <div className="w-3.5 h-3.5 border-2 border-zinc-400 border-t-zinc-950 rounded-full animate-spin" />
                ) : (
                  <>
                    <Plus className="w-3.5 h-3.5" />
                    <span>Adicionar</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Tags List com Rolagem Independente */}
        <div className="flex-1 overflow-y-auto px-6 pb-6 pt-2 space-y-2 custom-scrollbar">
          <h3 className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider font-mono">
              Tags Cadastradas ({currentCategoryTags.length})
            </h3>

            {loading ? (
              <div className="py-10 flex flex-col items-center justify-center gap-2 text-zinc-500 text-xs">
                <div className="w-5 h-5 border-2 border-zinc-800 border-t-white rounded-full animate-spin" />
                <span>Carregando tags...</span>
              </div>
            ) : currentCategoryTags.length === 0 ? (
              <div className="py-8 text-center bg-zinc-900/30 border border-zinc-800/80 rounded-xl">
                <p className="text-xs text-zinc-400">Nenhuma tag cadastrada nesta categoria.</p>
                <p className="text-[11px] text-zinc-500 mt-1">Utilize o campo acima para adicionar.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {currentCategoryTags.map((tag) => {
                  const isEditingThis = editingTagId === tag.id;
                  const isConfirmingDelete = deletingTagId === tag.id;

                  if (isEditingThis) {
                    return (
                      <div
                        key={tag.id}
                        className="flex items-center gap-1.5 p-2 bg-zinc-900 border border-zinc-700 rounded-xl"
                      >
                        <input
                          type="text"
                          value={editingTagName}
                          onChange={(e) => setEditingTagName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveEdit(tag.id);
                            if (e.key === 'Escape') handleCancelEdit();
                          }}
                          autoFocus
                          className="flex-1 bg-zinc-950 border border-zinc-700 rounded-lg px-2.5 py-1 text-xs text-white outline-none focus:border-zinc-400"
                        />
                        <button
                          type="button"
                          onClick={() => handleSaveEdit(tag.id)}
                          disabled={savingEdit}
                          data-testid={`save-tag-btn-${tag.id}`}
                          className="p-1.5 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 rounded-lg transition-colors cursor-pointer"
                          title="Salvar"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={handleCancelEdit}
                          data-testid={`cancel-tag-btn-${tag.id}`}
                          className="p-1.5 bg-zinc-800 text-zinc-400 hover:text-white rounded-lg transition-colors cursor-pointer"
                          title="Cancelar"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  }

                  if (isConfirmingDelete) {
                    return (
                      <div
                        key={tag.id}
                        className="flex items-center justify-between gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400"
                      >
                        <span className="truncate">Excluir &quot;{tag.name}&quot;?</span>
                        <div className="flex items-center gap-1 shrink-0">
                          <button
                            type="button"
                            onClick={() => handleDeleteTag(tag.id)}
                            data-testid={`confirm-delete-tag-btn-${tag.id}`}
                            className="px-2 py-0.5 bg-red-500 text-white text-[11px] font-semibold rounded hover:bg-red-600 transition-colors cursor-pointer"
                          >
                            Sim
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeletingTagId(null)}
                            data-testid={`cancel-delete-tag-btn-${tag.id}`}
                            className="px-2 py-0.5 bg-zinc-800 text-zinc-300 text-[11px] rounded hover:bg-zinc-700 transition-colors cursor-pointer"
                          >
                            Não
                          </button>
                        </div>
                      </div>
                    );
                  }

                  const TagIconComponent = getIconComponent(tagIcons[tag.id], activeCategoryObj?.icon);

                  return (
                    <div
                      key={tag.id}
                      data-testid={`tag-item-${tag.id}`}
                      className="flex items-center justify-between gap-2 p-2.5 bg-zinc-900/60 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <div className="p-1.5 rounded-lg bg-zinc-800/80 border border-zinc-700/50 text-zinc-300 shrink-0">
                          <TagIconComponent className="w-3.5 h-3.5" />
                        </div>
                        <span className="text-xs font-medium text-zinc-200 truncate">{tag.name}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleStartEdit(tag)}
                          data-testid={`edit-tag-btn-${tag.id}`}
                          className="p-1 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-colors cursor-pointer"
                          title="Renomear tag"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeletingTagId(tag.id)}
                          data-testid={`delete-tag-btn-${tag.id}`}
                          className="p-1 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded-lg transition-colors cursor-pointer"
                          title="Excluir tag"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-3.5 border-t border-zinc-800 bg-zinc-900/40 text-[11px] text-zinc-500">
          <span>* A renomeação atualiza automaticamente os equipamentos associados.</span>
          <button
            type="button"
            onClick={onClose}
            className="px-3.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-xl text-xs font-medium transition-colors cursor-pointer"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};
