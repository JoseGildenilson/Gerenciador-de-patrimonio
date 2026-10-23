import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MultiSelectFilterDropdown } from '../components/MultiSelectFilterDropdown';

describe('MultiSelectFilterDropdown', () => {
  const options = ['Notebook', 'Desktop', 'Monitor', 'Impressora'];

  it('renderiza o componente fechado com o rótulo inicial', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
        testId="filter-tipo"
      />
    );

    const button = screen.getByRole('button', { name: /tipo/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Tipo');
    expect(screen.queryByPlaceholderText('Pesquisar...')).not.toBeInTheDocument();
  });

  it('exibe formato "Label: Valor" quando há exatamente 1 item selecionado', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={['Notebook']}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByRole('button')).toHaveTextContent('Tipo: Notebook');
  });

  it('exibe formato "Label (N)" quando há mais de 1 item selecionado', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={['Notebook', 'Monitor']}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByRole('button')).toHaveTextContent('Tipo (2)');
  });

  it('abre e fecha o dropdown ao clicar no botão gatilho', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
      />
    );

    const triggerBtn = screen.getByRole('button');
    fireEvent.click(triggerBtn);

    expect(screen.getByPlaceholderText('Pesquisar...')).toBeInTheDocument();
    expect(screen.getByText('Notebook')).toBeInTheDocument();
    expect(screen.getByText('Desktop')).toBeInTheDocument();

    // Clica novamente para fechar
    fireEvent.click(triggerBtn);
    expect(screen.queryByPlaceholderText('Pesquisar...')).not.toBeInTheDocument();
  });

  it('filtra opções conforme busca interna e permite limpar busca com botão X', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
        placeholder="Buscar tipos..."
      />
    );

    fireEvent.click(screen.getByRole('button'));

    const searchInput = screen.getByPlaceholderText('Buscar tipos...');
    fireEvent.change(searchInput, { target: { value: 'note' } });

    expect(screen.getByText('Notebook')).toBeInTheDocument();
    expect(screen.queryByText('Desktop')).not.toBeInTheDocument();
    expect(screen.queryByText('Monitor')).not.toBeInTheDocument();

    // Botão X de limpar busca aparece
    const clearSearchBtn = searchInput.parentElement?.querySelector('button');
    expect(clearSearchBtn).toBeInTheDocument();
    fireEvent.click(clearSearchBtn!);

    expect(searchInput).toHaveValue('');
    expect(screen.getByText('Notebook')).toBeInTheDocument();
    expect(screen.getByText('Desktop')).toBeInTheDocument();
  });

  it('exibe mensagem quando nenhuma opção corresponde à busca', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    const searchInput = screen.getByPlaceholderText('Pesquisar...');
    fireEvent.change(searchInput, { target: { value: 'Inexistente' } });

    expect(screen.getByText('Nenhuma opção encontrada')).toBeInTheDocument();
  });

  it('chama onChange com novo array ao marcar e ao desmarcar uma opção', () => {
    const handleChange = vi.fn();
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={['Notebook']}
        onChange={handleChange}
      />
    );

    fireEvent.click(screen.getByRole('button'));

    // Clicar em opção não selecionada -> adiciona
    const desktopOption = screen.getByText('Desktop');
    fireEvent.click(desktopOption);
    expect(handleChange).toHaveBeenCalledWith(['Notebook', 'Desktop']);

    // Clicar em opção já selecionada -> remove
    const notebookOption = screen.getByText('Notebook');
    fireEvent.click(notebookOption);
    expect(handleChange).toHaveBeenCalledWith([]);
  });

  it('limpa todas as seleções ao clicar no botão "Desmarcar tudo"', () => {
    const handleChange = vi.fn();
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={['Notebook', 'Monitor']}
        onChange={handleChange}
      />
    );

    fireEvent.click(screen.getByRole('button'));

    const clearAllBtn = screen.getByText('Desmarcar tudo');
    expect(clearAllBtn).toBeInTheDocument();

    fireEvent.click(clearAllBtn);
    expect(handleChange).toHaveBeenCalledWith([]);
  });

  it('não exibe botão "Desmarcar tudo" quando selectedValues está vazio', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(screen.queryByText('Desmarcar tudo')).not.toBeInTheDocument();
    expect(screen.getByText('0 sel.')).toBeInTheDocument();
  });

  it('fecha o dropdown ao clicar fora do componente', () => {
    render(
      <div>
        <div data-testid="outside-element">Fora</div>
        <MultiSelectFilterDropdown
          label="Tipo"
          options={options}
          selectedValues={[]}
          onChange={vi.fn()}
        />
      </div>
    );

    fireEvent.click(screen.getByRole('button', { name: /tipo/i }));
    expect(screen.getByPlaceholderText('Pesquisar...')).toBeInTheDocument();

    // Dispara clique fora
    fireEvent.mouseDown(screen.getByTestId('outside-element'));
    expect(screen.queryByPlaceholderText('Pesquisar...')).not.toBeInTheDocument();
  });

  it('não fecha o dropdown ao clicar dentro dele', () => {
    render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    const searchInput = screen.getByPlaceholderText('Pesquisar...');
    fireEvent.mouseDown(searchInput);
    expect(screen.getByPlaceholderText('Pesquisar...')).toBeInTheDocument();
  });

  it('remove o listener de clique fora ao desmontar', () => {
    const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');
    const { unmount } = render(
      <MultiSelectFilterDropdown
        label="Tipo"
        options={options}
        selectedValues={[]}
        onChange={vi.fn()}
      />
    );

    unmount();
    expect(removeEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function));
    removeEventListenerSpy.mockRestore();
  });
});
