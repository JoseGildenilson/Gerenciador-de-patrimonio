import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search, X, Check } from 'lucide-react';

interface MultiSelectFilterDropdownProps {
  label: string;
  options: string[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  placeholder?: string;
  testId?: string;
}

export const MultiSelectFilterDropdown: React.FC<MultiSelectFilterDropdownProps> = ({
  label,
  options,
  selectedValues,
  onChange,
  placeholder = 'Pesquisar...',
  testId,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const filteredOptions = options.filter((opt) =>
    (opt || '').toLowerCase().includes((search || '').toLowerCase())
  );

  const toggleOption = (option: string) => {
    if (selectedValues.includes(option)) {
      onChange(selectedValues.filter((item) => item !== option));
    } else {
      onChange([...selectedValues, option]);
    }
  };

  const handleClearAll = () => {
    onChange([]);
  };

  // Texto do botão principal do filtro (RN-04 / Seção 3.4)
  const getButtonText = () => {
    if (selectedValues.length === 0) return label;
    if (selectedValues.length === 1) return `${label}: ${selectedValues[0]}`;
    return `${label} (${selectedValues.length})`;
  };

  const isActive = selectedValues.length > 0;

  return (
    <div className="relative inline-block text-left" ref={dropdownRef} data-testid={testId}>
      {/* Botão Gatilho */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center justify-between gap-2 transition-all cursor-pointer ${
          isActive
            ? 'bg-zinc-800 border-zinc-700 text-zinc-100 shadow-sm'
            : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:border-zinc-700 hover:text-zinc-100'
        }`}
      >
        <span className="truncate max-w-[140px]">{getButtonText()}</span>
        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-150 ${isOpen ? 'rotate-180 text-zinc-200' : 'text-zinc-400'}`} />
      </button>

      {/* Painel Dropdown Estilo Linear / Google Sheets */}
      {isOpen && (
        <div className="absolute left-0 mt-1.5 w-60 bg-zinc-900 border border-zinc-800 rounded-xl shadow-dropdown z-50 p-2.5 space-y-2 animate-fade-in">
          {/* Busca Interna */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={placeholder}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-8 pr-2.5 py-1.5 text-xs text-zinc-100 outline-none focus:border-zinc-500 placeholder:text-zinc-500"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-2 top-2 text-zinc-500 hover:text-zinc-200"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Lista de Opções com Checkboxes */}
          <div className="max-h-48 overflow-y-auto space-y-0.5 pr-1 custom-scrollbar">
            {filteredOptions.length === 0 ? (
              <p className="text-[11px] text-zinc-500 py-3 text-center">Nenhuma opção encontrada</p>
            ) : (
              filteredOptions.map((opt) => {
                const isSelected = selectedValues.includes(opt);
                return (
                  <label
                    key={opt}
                    onClick={() => toggleOption(opt)}
                    className="flex items-center gap-2.5 px-2 py-1.5 rounded-md text-xs text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100 cursor-pointer select-none transition-colors"
                  >
                    <div
                      className={`w-3.5 h-3.5 rounded border flex items-center justify-center transition-colors shrink-0 ${
                        isSelected
                          ? 'bg-zinc-100 border-zinc-100 text-zinc-950'
                          : 'bg-zinc-950 border-zinc-700 hover:border-zinc-500'
                      }`}
                    >
                      {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                    </div>
                    <span className="truncate">{opt}</span>
                  </label>
                );
              })
            )}
          </div>

          {/* Rodapé com botão Desmarcar Tudo (RN-11) */}
          <div className="pt-2 border-t border-zinc-800 flex items-center justify-between text-[11px]">
            <span className="text-zinc-500 font-mono text-[10px]">
              {selectedValues.length} {selectedValues.length === 1 ? 'sel.' : 'sel.'}
            </span>
            {selectedValues.length > 0 && (
              <button
                type="button"
                onClick={handleClearAll}
                className="text-zinc-300 hover:text-white font-medium cursor-pointer text-[11px]"
              >
                Desmarcar tudo
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
