import React, { useState, useRef, useEffect } from 'react';
import { equipmentApi } from '../api/equipmentApi';

export interface AutocompleteFilterInputProps {
  field: 'patrimony_number' | 'serial_number' | 'product_number';
  placeholder: string;
  selectedValues: string[];
  onAddValue: (value: string) => void;
  testId?: string;
}

export const AutocompleteFilterInput: React.FC<AutocompleteFilterInputProps> = ({
  field,
  placeholder,
  selectedValues,
  onAddValue,
  testId,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fecha o dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Busca sugestões com debounce de 300ms quando prefixo >= 2 caracteres (RN-AC-01, RN-AC-06)
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const clean = inputValue.trim();
    if (clean.length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const results = await equipmentApi.getSuggestions(field, clean, 10);
        // Oculta valores já selecionados nos chips ativos (RN-AC-07)
        const filtered = results.filter((item) => !selectedValues.includes(item));
        setSuggestions(filtered);
        setIsOpen(filtered.length > 0);
      } catch (err) {
        console.error('Erro ao buscar sugestões:', err);
        setSuggestions([]);
        setIsOpen(false);
      }
    }, 300);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [inputValue, field, selectedValues]);

  const handleSelectSuggestion = (val: string) => {
    onAddValue(val);
    setInputValue('');
    setSuggestions([]);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const clean = inputValue.trim();
      if (clean) {
        onAddValue(clean);
        setInputValue('');
        setSuggestions([]);
        setIsOpen(false);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} className="relative inline-block">
      <input
        type="text"
        placeholder={placeholder}
        value={inputValue}
        data-testid={testId}
        onChange={(e) => setInputValue(e.target.value)}
        onFocus={() => {
          if (suggestions.length > 0) {
            setIsOpen(true);
          }
        }}
        onKeyDown={handleKeyDown}
        className="bg-[#121212] border border-[#333333] text-[#E0E0E0] text-sm rounded-md px-3 py-2 focus:ring-1 focus:ring-[#9E9E9E] focus:border-[#9E9E9E] focus:outline-none placeholder-[#9E9E9E]/50 w-32 font-mono"
      />

      {/* Badge com contagem de filtros selecionados */}
      {selectedValues.length > 0 && (
        <span
          data-testid={`${testId || 'autocomplete'}-count-badge`}
          className="absolute right-2 top-2.5 px-1.5 py-0.2 rounded bg-[#333333] text-white font-mono font-bold text-[10px] pointer-events-none"
        >
          {selectedValues.length}
        </span>
      )}

      {/* Dropdown de sugestões (RN-AC-03, RN-AC-04) */}
      {isOpen && suggestions.length > 0 && (
        <div
          data-testid={`${testId || 'autocomplete'}-dropdown`}
          className="absolute left-0 top-full mt-1 z-50 min-w-full w-max max-w-xs bg-[#1E1E1E] border border-[#333333] rounded-md shadow-xl overflow-hidden py-1"
        >
          <div className="px-2.5 py-1 text-[10px] uppercase font-semibold text-[#9E9E9E] tracking-wider border-b border-[#333333]/60 mb-0.5">
            Sugestões
          </div>
          <ul className="max-h-48 overflow-y-auto">
            {suggestions.map((item) => (
              <li
                key={item}
                data-testid={`suggestion-item-${item}`}
                onClick={() => handleSelectSuggestion(item)}
                className="px-3 py-1.5 text-xs text-[#E0E0E0] hover:bg-[#333333] hover:text-white cursor-pointer font-mono flex items-center justify-between transition-colors"
              >
                <span className="truncate">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
