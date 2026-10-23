import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { AutocompleteFilterInput } from '../components/AutocompleteFilterInput';
import { equipmentApi } from '../api/equipmentApi';

describe('Componente AutocompleteFilterInput', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('Renderiza input com placeholder e não busca com menos de 2 caracteres', async () => {
    const getSuggestionsSpy = vi.spyOn(equipmentApi, 'getSuggestions').mockResolvedValue([]);
    const onAddValue = vi.fn();

    render(
      <AutocompleteFilterInput
        field="patrimony_number"
        placeholder="Patrimônio..."
        selectedValues={[]}
        onAddValue={onAddValue}
        testId="patrimony-filter-input"
      />
    );

    const input = screen.getByTestId('patrimony-filter-input');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', 'Patrimônio...');

    // Digita 1 caractere
    fireEvent.change(input, { target: { value: 'P' } });

    // Avança o tempo
    await act(async () => {
      await new Promise((r) => setTimeout(r, 400));
    });

    expect(getSuggestionsSpy).not.toHaveBeenCalled();
    expect(screen.queryByTestId('patrimony-filter-input-dropdown')).not.toBeInTheDocument();
  });

  it('Busca sugestões com debounce de 300ms ao digitar 2 ou mais caracteres', async () => {
    const getSuggestionsSpy = vi.spyOn(equipmentApi, 'getSuggestions').mockResolvedValue(['PAT001', 'PAT002', 'PAT003']);
    const onAddValue = vi.fn();

    render(
      <AutocompleteFilterInput
        field="patrimony_number"
        placeholder="Patrimônio..."
        selectedValues={['PAT002']} // PAT002 já está selecionado
        onAddValue={onAddValue}
        testId="patrimony-filter-input"
      />
    );

    const input = screen.getByTestId('patrimony-filter-input');

    // Digita 'PA'
    fireEvent.change(input, { target: { value: 'PA' } });

    // Aguarda o debounce de 300ms
    await act(async () => {
      await new Promise((r) => setTimeout(r, 350));
    });

    expect(getSuggestionsSpy).toHaveBeenCalledWith('patrimony_number', 'PA', 10);

    // Dropdown deve abrir
    await waitFor(() => {
      expect(screen.getByTestId('patrimony-filter-input-dropdown')).toBeInTheDocument();
    });

    // PAT001 e PAT003 devem aparecer, mas PAT002 não (já selecionado)
    expect(screen.getByTestId('suggestion-item-PAT001')).toBeInTheDocument();
    expect(screen.getByTestId('suggestion-item-PAT003')).toBeInTheDocument();
    expect(screen.queryByTestId('suggestion-item-PAT002')).not.toBeInTheDocument();

    // Clica em PAT001
    fireEvent.click(screen.getByTestId('suggestion-item-PAT001'));

    expect(onAddValue).toHaveBeenCalledWith('PAT001');
    expect(input).toHaveValue('');
    expect(screen.queryByTestId('patrimony-filter-input-dropdown')).not.toBeInTheDocument();
  });

  it('Permite adicionar valor livre via tecla Enter', async () => {
    vi.spyOn(equipmentApi, 'getSuggestions').mockResolvedValue([]);
    const onAddValue = vi.fn();

    render(
      <AutocompleteFilterInput
        field="serial_number"
        placeholder="Série..."
        selectedValues={[]}
        onAddValue={onAddValue}
        testId="serial-filter-input"
      />
    );

    const input = screen.getByTestId('serial-filter-input');

    // Digita valor e pressiona Enter
    fireEvent.change(input, { target: { value: 'SN-NOVO-999' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(onAddValue).toHaveBeenCalledWith('SN-NOVO-999');
    expect(input).toHaveValue('');
  });

  it('Fecha o dropdown ao pressionar tecla Escape ou clicar fora', async () => {
    vi.spyOn(equipmentApi, 'getSuggestions').mockResolvedValue(['PROD_A', 'PROD_B']);
    const onAddValue = vi.fn();

    render(
      <div>
        <div data-testid="outside-element">Fora</div>
        <AutocompleteFilterInput
          field="product_number"
          placeholder="Produto..."
          selectedValues={[]}
          onAddValue={onAddValue}
          testId="prod-filter-input"
        />
      </div>
    );

    const input = screen.getByTestId('prod-filter-input');
    fireEvent.change(input, { target: { value: 'PR' } });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 350));
    });

    await waitFor(() => {
      expect(screen.getByTestId('prod-filter-input-dropdown')).toBeInTheDocument();
    });

    // Pressiona Escape
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(screen.queryByTestId('prod-filter-input-dropdown')).not.toBeInTheDocument();

    // Reabre ao focar se houver sugestões
    fireEvent.focus(input);
    expect(screen.getByTestId('prod-filter-input-dropdown')).toBeInTheDocument();

    // Clica fora
    fireEvent.mouseDown(screen.getByTestId('outside-element'));
    expect(screen.queryByTestId('prod-filter-input-dropdown')).not.toBeInTheDocument();
  });

  it('Exibe badge de contagem quando selectedValues não estiver vazio', () => {
    render(
      <AutocompleteFilterInput
        field="patrimony_number"
        placeholder="Patrimônio..."
        selectedValues={['PAT1', 'PAT2']}
        onAddValue={vi.fn()}
        testId="pat-input"
      />
    );

    const badge = screen.getByTestId('pat-input-count-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('2');
  });

  it('Trata erros de API na busca de sugestões silenciosamente', async () => {
    vi.spyOn(equipmentApi, 'getSuggestions').mockRejectedValue(new Error('Network error'));
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <AutocompleteFilterInput
        field="patrimony_number"
        placeholder="Patrimônio..."
        selectedValues={[]}
        onAddValue={vi.fn()}
        testId="pat-err-input"
      />
    );

    const input = screen.getByTestId('pat-err-input');
    fireEvent.change(input, { target: { value: 'PA' } });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 350));
    });

    expect(screen.queryByTestId('pat-err-input-dropdown')).not.toBeInTheDocument();
    expect(consoleSpy).toHaveBeenCalled();
  });
});
