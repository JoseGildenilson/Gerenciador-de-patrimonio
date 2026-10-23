import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ManageTagsModal } from '../components/ManageTagsModal';
import { equipmentApi } from '../api/equipmentApi';
import { EquipmentTag } from '../types/equipment';

vi.mock('../api/equipmentApi', () => ({
  equipmentApi: {
    getTags: vi.fn(),
    createTag: vi.fn(),
    updateTag: vi.fn(),
    deleteTag: vi.fn(),
  },
}));

const mockTags: EquipmentTag[] = [
  { id: 1, category: 'tipo', name: 'Notebook', created_at: '2026-08-01T00:00:00Z' },
  { id: 2, category: 'tipo', name: 'Desktop', created_at: '2026-08-01T00:00:00Z' },
  { id: 3, category: 'localizacao', name: 'TI', created_at: '2026-08-01T00:00:00Z' },
  { id: 4, category: 'situacao', name: 'Em uso', created_at: '2026-08-01T00:00:00Z' },
];

describe('Componente ManageTagsModal', () => {
  const onClose = vi.fn();
  const onTagsUpdated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(equipmentApi.getTags).mockResolvedValue([...mockTags]);
  });

  it('Não renderiza quando isOpen é false', () => {
    const { container } = render(
      <ManageTagsModal isOpen={false} onClose={onClose} onTagsUpdated={onTagsUpdated} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('Renderiza categorias e lista tags da categoria ativa', async () => {
    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    expect(screen.getByText('Gerenciador de Tags')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
      expect(screen.getByText('Desktop')).toBeInTheDocument();
    });

    // Troca de aba para Localizações
    const locTab = screen.getByTestId('tab-localizacao');
    fireEvent.click(locTab);

    await waitFor(() => {
      expect(screen.getByText('TI')).toBeInTheDocument();
      expect(screen.queryByText('Notebook')).not.toBeInTheDocument();
    });
  });

  it('Cadastra uma nova tag com sucesso', async () => {
    const user = userEvent.setup();
    vi.mocked(equipmentApi.createTag).mockResolvedValue({
      id: 5,
      category: 'tipo',
      name: 'Tablet',
      created_at: '2026-08-23T00:00:00Z',
    });

    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Adicionar novo tipo de equipamento/i);
    await user.type(input, 'Tablet');

    const addBtn = screen.getByTestId('add-tag-btn');
    await user.click(addBtn);

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('tipo', 'Tablet');
      expect(onTagsUpdated).toHaveBeenCalled();
      expect(screen.getByText('Tag cadastrada com sucesso.')).toBeInTheDocument();
    });
  });

  it('Permite abrir o seletor de ícones, buscar e selecionar um ícone customizado', async () => {
    const user = userEvent.setup();
    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
    });

    // Abre o popover do seletor de ícone
    const pickerBtn = screen.getByTestId('icon-picker-btn');
    await user.click(pickerBtn);

    expect(screen.getByTestId('icon-picker-popover')).toBeInTheDocument();
    expect(screen.getByTestId('icon-picker-popover')).toHaveClass('top-full');
    expect(screen.getByTestId('icon-picker-popover')).toHaveClass('mt-2');

    // Filtra pelo campo de busca
    const searchInput = screen.getByTestId('icon-search-input');
    await user.type(searchInput, 'printer');

    const selectPrinterBtn = screen.getByTestId('select-icon-printer');
    await user.click(selectPrinterBtn);

    // Popover deve fechar após selecionar
    expect(screen.queryByTestId('icon-picker-popover')).not.toBeInTheDocument();
  });

  it('Edita/renomeia uma tag com sucesso', async () => {
    const user = userEvent.setup();
    vi.mocked(equipmentApi.updateTag).mockResolvedValue({
      id: 1,
      category: 'tipo',
      name: 'Laptop',
      created_at: '2026-08-01T00:00:00Z',
    });

    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
    });

    const editBtn = screen.getByTestId('edit-tag-btn-1');
    await user.click(editBtn);

    const editInput = screen.getByDisplayValue('Notebook');
    await user.clear(editInput);
    await user.type(editInput, 'Laptop');

    const saveBtn = screen.getByTestId('save-tag-btn-1');
    await user.click(saveBtn);

    await waitFor(() => {
      expect(equipmentApi.updateTag).toHaveBeenCalledWith(1, 'Laptop');
      expect(onTagsUpdated).toHaveBeenCalled();
      expect(screen.getByText('Tag renomeada com sucesso.')).toBeInTheDocument();
    });
  });

  it('Exclui uma tag com confirmação', async () => {
    const user = userEvent.setup();
    vi.mocked(equipmentApi.deleteTag).mockResolvedValue({ message: 'Tag excluída com sucesso.' });

    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
    });

    const delBtn = screen.getByTestId('delete-tag-btn-1');
    await user.click(delBtn);

    expect(screen.getByText(/Excluir "Notebook"\?/i)).toBeInTheDocument();

    const confirmBtn = screen.getByTestId('confirm-delete-tag-btn-1');
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(equipmentApi.deleteTag).toHaveBeenCalledWith(1);
      expect(onTagsUpdated).toHaveBeenCalled();
      expect(screen.getByText('Tag excluída com sucesso.')).toBeInTheDocument();
    });
  });

  it('Trata erro ao cadastrar tag duplicada ou inválida', async () => {
    const user = userEvent.setup();
    vi.mocked(equipmentApi.createTag).mockRejectedValue({
      response: { data: { detail: 'Tag já cadastrada nesta categoria.' } },
    });

    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/Adicionar novo tipo de equipamento/i);
    await user.type(input, 'Notebook');

    const addBtn = screen.getByTestId('add-tag-btn');
    await user.click(addBtn);

    await waitFor(() => {
      expect(screen.getByText('Tag já cadastrada nesta categoria.')).toBeInTheDocument();
    });
  });

  it('Chama onClose ao clicar no botão de fechar', async () => {
    const user = userEvent.setup();
    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    const closeBtn = screen.getByTestId('close-tags-modal-btn');
    await user.click(closeBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it('Exibe erro ao falhar renomeação ou exclusão de tag e seleciona aba situação', async () => {
    const user = userEvent.setup();
    vi.mocked(equipmentApi.updateTag).mockRejectedValueOnce({
      response: { data: { detail: 'Erro ao renomear tag no catálogo.' } },
    });
    vi.mocked(equipmentApi.deleteTag).mockRejectedValueOnce({
      response: { data: { detail: 'Não é possível excluir tag em uso.' } },
    });

    render(<ManageTagsModal isOpen={true} onClose={onClose} onTagsUpdated={onTagsUpdated} />);

    await waitFor(() => {
      expect(screen.getByText('Notebook')).toBeInTheDocument();
    });

    // 1. Erro ao salvar edição
    const editBtn = screen.getByTestId('edit-tag-btn-1');
    await user.click(editBtn);
    const saveBtn = screen.getByTestId('save-tag-btn-1');
    await user.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText('Erro ao renomear tag no catálogo.')).toBeInTheDocument();
    });

    // Cancelar edição antes de excluir
    const cancelEditBtn = screen.getByTestId('cancel-tag-btn-1');
    await user.click(cancelEditBtn);

    // 2. Erro ao confirmar exclusão
    const delBtn = screen.getByTestId('delete-tag-btn-1');
    await user.click(delBtn);
    const confirmBtn = screen.getByTestId('confirm-delete-tag-btn-1');
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText('Não é possível excluir tag em uso.')).toBeInTheDocument();
    });

    // 3. Seleciona aba situação (cobre linha 241 placeholder 'status')
    const sitTab = screen.getByTestId('tab-situacao');
    await user.click(sitTab);
    expect(screen.getByPlaceholderText(/Adicionar novo status/i)).toBeInTheDocument();
  });
});

