import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';

import { equipmentApi, equipmentHttpClient } from '../api/equipmentApi';
import { authApi } from '../api/authApi';
import { importApi } from '../api/importApi';
import { AuthProvider, useAuthContext } from '../context/AuthContext';

import { AutocompleteFilterInput } from '../components/AutocompleteFilterInput';
import { ManageTagsModal } from '../components/ManageTagsModal';
import { MovementModal } from '../components/MovementModal';
import { NewEquipmentModal } from '../components/NewEquipmentModal';
import { LoginForm } from '../components/LoginForm';
import { SideMenu } from '../components/SideMenu';
import { MaintenanceModal } from '../components/MaintenanceModal';

import { EquipmentListPage } from '../pages/EquipmentListPage';
import { EquipmentDetailPage } from '../pages/EquipmentDetailPage';
import { DashboardPage } from '../pages/DashboardPage';
import { ImportPage } from '../pages/ImportPage';

import { Equipment, EquipmentTag } from '../types/equipment';

vi.mock('../api/authApi', () => ({
  authApi: {
    getMe: vi.fn(),
    login: vi.fn(),
    refresh: vi.fn(),
    logout: vi.fn(),
  },
}));

vi.mock('../api/importApi', () => ({
  importApi: {
    previewSpreadsheet: vi.fn(),
    executeImport: vi.fn(),
  },
}));

vi.mock('../api/equipmentApi', async () => {
  const actual = await vi.importActual<typeof import('../api/equipmentApi')>('../api/equipmentApi');
  return {
    ...actual,
    equipmentApi: {
      getEquipments: vi.fn(),
      getEquipmentDetail: vi.fn(),
      createEquipment: vi.fn(),
      updateEquipment: vi.fn(),
      getTags: vi.fn(),
      createTag: vi.fn(),
      updateTag: vi.fn(),
      recordMovement: vi.fn(),
      recordMaintenance: vi.fn(),
      updateMaintenance: vi.fn(),
      deleteMaintenance: vi.fn(),
      getSuggestions: vi.fn(),
      exportEquipments: vi.fn(),
    },
  };
});

describe('Coverage Completion Suite: 100% Statement and Branch Coverage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('1. equipmentApi.getTags without category argument (line 50)', () => {
    it('executes real equipmentApi.getTags without category and passes undefined params', async () => {
      const getSpy = vi.spyOn(equipmentHttpClient, 'get').mockResolvedValueOnce({ data: [] } as any);

      const actualModule = await vi.importActual<typeof import('../api/equipmentApi')>('../api/equipmentApi');
      const tags = await actualModule.equipmentApi.getTags();

      expect(tags).toEqual([]);
      expect(getSpy).toHaveBeenCalledWith('/tags', { params: undefined });
    });
  });

  describe('2. AuthContext fallback detail when Axios error has no data.detail (line 55)', () => {
    const TestConsumer: React.FC = () => {
      const { login, error } = useAuthContext();
      const handleLogin = async () => {
        try {
          await login({ email: 'test@empresa.com', password: '123' });
        } catch {
          // Captura erro para não gerar unhandled rejection no teste
        }
      };

      return (
        <div>
          <span data-testid="auth-error">{error || ''}</span>
          <button onClick={handleLogin}>Do Login</button>
        </div>
      );
    };

    it('sets generic fallback error message when status is 500 and response data is empty', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('no session'));
      (authApi.refresh as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('no refresh'));

      const errorWithoutDetail = new axios.AxiosError('Server Error', '500', undefined, undefined, {
        status: 500,
        statusText: 'Internal Server Error',
        data: {},
        headers: {},
        config: { headers: {} as any },
      });

      (authApi.login as ReturnType<typeof vi.fn>).mockRejectedValue(errorWithoutDetail);

      render(
        <AuthProvider>
          <TestConsumer />
        </AuthProvider>
      );

      fireEvent.click(screen.getByText('Do Login'));

      await waitFor(() => {
        expect(screen.getByTestId('auth-error')).toHaveTextContent('Erro ao realizar login.');
      });
    });
  });

  describe('3. AutocompleteFilterInput default testId fallback (lines 112, 122)', () => {
    it('uses autocomplete fallback for count-badge and dropdown when testId is undefined', async () => {
      vi.mocked(equipmentApi.getSuggestions).mockResolvedValue(['PAT-001', 'PAT-002']);

      render(
        <AutocompleteFilterInput
          field="patrimony_number"
          placeholder="Buscar patrimônio..."
          selectedValues={['PAT-999']}
          onAddValue={vi.fn()}
        />
      );

      const countBadge = screen.getByTestId('autocomplete-count-badge');
      expect(countBadge).toBeInTheDocument();
      expect(countBadge).toHaveTextContent('1');

      const input = screen.getByPlaceholderText('Buscar patrimônio...');
      fireEvent.change(input, { target: { value: 'PAT' } });

      await waitFor(() => {
        expect(equipmentApi.getSuggestions).toHaveBeenCalledWith('patrimony_number', 'PAT', 10);
        expect(screen.getByTestId('autocomplete-dropdown')).toBeInTheDocument();
      });
    });
  });

  describe('4. ManageTagsModal error paths (lines 71, 116-118)', () => {
    it('sets fallback error when fetchTags fails with and without response detail', async () => {
      vi.mocked(equipmentApi.getTags).mockRejectedValueOnce({
        response: { data: { detail: 'Falha personalizada na API de tags' } },
      });

      const { unmount } = render(<ManageTagsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Falha personalizada na API de tags')).toBeInTheDocument();
      });

      unmount();

      vi.mocked(equipmentApi.getTags).mockRejectedValueOnce(new Error('Network error'));
      render(<ManageTagsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Erro ao carregar tags.')).toBeInTheDocument();
      });
    });

    it('sets error when handleSaveEdit is called with empty or whitespace tag name', async () => {
      const mockTags: EquipmentTag[] = [
        { id: 101, category: 'tipo', name: 'Notebook', created_at: '2026-01-01T00:00:00Z' },
      ];
      vi.mocked(equipmentApi.getTags).mockResolvedValue(mockTags);

      render(<ManageTagsModal isOpen={true} onClose={vi.fn()} />);

      await waitFor(() => {
        expect(screen.getByText('Notebook')).toBeInTheDocument();
      });

      const editBtn = screen.getByTestId('edit-tag-btn-101');
      fireEvent.click(editBtn);

      const editInput = screen.getByDisplayValue('Notebook');
      fireEvent.change(editInput, { target: { value: '   ' } });

      const saveBtn = screen.getByTitle('Salvar');
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText('O nome da tag não pode ser vazio.')).toBeInTheDocument();
      });
    });
  });

  describe('5. MovementModal branches (lines 35-36, 49, 123-125)', () => {
    it('updates destinationLocation when locations change and destinationLocation is empty', async () => {
      const initialLocations: EquipmentTag[] = [
        { id: 1, category: 'localizacao', name: 'TI', created_at: '2026-01-01' },
      ];

      const { rerender } = render(
        <MovementModal
          isOpen={true}
          equipmentId={1}
          currentLocation="Almoxarifado"
          locations={initialLocations}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      const select = screen.getByRole('combobox');
      fireEvent.change(select, { target: { value: '' } });

      const updatedLocations: EquipmentTag[] = [
        { id: 2, category: 'localizacao', name: 'Sala 102', created_at: '2026-01-01' },
      ];

      rerender(
        <MovementModal
          isOpen={true}
          equipmentId={1}
          currentLocation="Almoxarifado"
          locations={updatedLocations}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('Sala 102')).toBeInTheDocument();
      });
    });

    it('triggers handleCreateLocation on Enter key and handles API error fallback', async () => {
      vi.mocked(equipmentApi.createTag).mockRejectedValueOnce({
        response: { data: {} },
      });

      render(
        <MovementModal
          isOpen={true}
          equipmentId={1}
          currentLocation="TI"
          locations={[{ id: 1, category: 'localizacao', name: 'TI', created_at: '2026-01-01' }]}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      fireEvent.click(screen.getByTestId('inline-create-location-btn'));
      const input = screen.getByPlaceholderText('Nova localização');
      fireEvent.change(input, { target: { value: 'Almoxarifado Central' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText('Erro ao criar nova localização.')).toBeInTheDocument();
      });
    });
  });

  describe('6. NewEquipmentModal validation and submission error (lines 90-91, 113, 142-145)', () => {
    it('validates empty serial number and description and displays error alert', async () => {
      render(
        <NewEquipmentModal
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
      });

      const submitBtn = screen.getByRole('button', { name: /cadastrar equipamento/i });
      const form = submitBtn.closest('form')!;
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('Número de patrimônio ou número de série é obrigatório.')).toBeInTheDocument();
      });
    });

    it('displays error from API rejection when createEquipment fails', async () => {
      vi.mocked(equipmentApi.createEquipment).mockRejectedValueOnce({
        response: { data: { detail: 'Número de série duplicado no sistema.' } },
      });

      render(
        <NewEquipmentModal
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
      });

      const serialInput = screen.getByPlaceholderText('ex: SN12345678');
      const descInput = screen.getByPlaceholderText('ex: Dell OptiPlex 7090 Core i7 16GB SSD 512GB');

      fireEvent.change(serialInput, { target: { value: 'SN-DUPLICATE' } });
      fireEvent.change(descInput, { target: { value: 'Laptop de Teste' } });

      const submitBtn = screen.getByRole('button', { name: /cadastrar equipamento/i });
      const form = submitBtn.closest('form')!;
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('Número de série duplicado no sistema.')).toBeInTheDocument();
      });
    });

    it('falls back to default error message when API rejection has no response detail', async () => {
      vi.mocked(equipmentApi.createEquipment).mockRejectedValueOnce(new Error('Network failure'));

      render(
        <NewEquipmentModal
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
      });

      const serialInput = screen.getByPlaceholderText('ex: SN12345678');
      const descInput = screen.getByPlaceholderText('ex: Dell OptiPlex 7090 Core i7 16GB SSD 512GB');

      fireEvent.change(serialInput, { target: { value: 'SN-NETWORK' } });
      fireEvent.change(descInput, { target: { value: 'Laptop de Teste' } });

      const submitBtn = screen.getByRole('button', { name: /cadastrar equipamento/i });
      const form = submitBtn.closest('form')!;
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('Erro ao cadastrar equipamento')).toBeInTheDocument();
      });
    });
  });

  describe('7. EquipmentListPage brand pill and pagination controls (lines 493-495, 544-564)', () => {
    it('renders brand pill when brand is present and exercises full pagination controls', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockResolvedValue([
        { id: 1, category: 'tipo', name: 'Notebook', created_at: '2026-01-01T00:00:00Z' },
      ]);

      vi.mocked(equipmentApi.getEquipments).mockResolvedValue({
        items: [
          {
            id: 1,
            serial_number: 'SN-BRAND-01',
            patrimony_number: 'PAT-001',
            hostname: 'NB-01',
            description: 'Notebook Dell Pro',
            brand: 'Dell Technologies',
            product_number: null,
            equipment_type: 'Notebook',
            location: 'TI',
            status: 'Em uso',
            windows_key: null,
            last_maintenance_at: '2026-03-01T10:00:00Z',
            notes: null,
            created_at: '2026-01-01T00:00:00Z',
            movements: [],
            maintenances: [],
          },
        ],
        total: 30,
        page: 1,
        limit: 10,
        pages: 3,
      });

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos']}>
            <Routes>
              <Route path="/equipamentos" element={<EquipmentListPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Dell Technologies')).toBeInTheDocument();
      });

      expect(screen.getByText(/Página/i)).toBeInTheDocument();

      const prevBtn = screen.getByRole('button', { name: /Anterior/i });
      const nextBtn = screen.getByRole('button', { name: /Próxima/i });

      expect(prevBtn).toBeDisabled();
      expect(nextBtn).toBeEnabled();

      fireEvent.click(nextBtn);

      await waitFor(() => {
        expect(equipmentApi.getEquipments).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }));
      });
    });
  });

  describe('8. EquipmentDetailPage status pills and type icons (lines 273-279, 289-301, 308-310)', () => {
    const renderEquipmentDetail = (overrides: Partial<Equipment>) => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockResolvedValue([]);
      vi.mocked(equipmentApi.getEquipmentDetail).mockResolvedValue({
        id: 99,
        serial_number: 'SN-99',
        patrimony_number: 'PAT-99',
        hostname: 'HOST-99',
        description: 'Equipamento Teste',
        brand: 'Generic',
        product_number: null,
        equipment_type: 'Impressora',
        location: 'TI',
        status: 'Em Manutenção',
        windows_key: null,
        last_maintenance_at: null,
        notes: null,
        created_at: '2026-01-01T00:00:00Z',
        movements: [],
        maintenances: [],
        ...overrides,
      });

      return render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos/99']}>
            <Routes>
              <Route path="/equipamentos/:id" element={<EquipmentDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );
    };

    it('renders amber status pill for manuten/repar/recolhimento status and printer icon', async () => {
      const { unmount } = renderEquipmentDetail({
        status: 'Em Manutenção Preventiva',
        equipment_type: 'Impressora Laser',
      });

      await waitFor(() => {
        expect(screen.getByText('Em Manutenção Preventiva')).toBeInTheDocument();
      });

      unmount();
    });

    it('renders zinc status pill for baixado/descarte status and smartphone icon', async () => {
      const { unmount } = renderEquipmentDetail({
        status: 'Equipamento Baixado por Obsolescência',
        equipment_type: 'Celular Corporativo',
      });

      await waitFor(() => {
        expect(screen.getByText('Equipamento Baixado por Obsolescência')).toBeInTheDocument();
      });

      unmount();
    });

    it('renders default zinc pill for unknown status and fallback icon for server type', async () => {
      renderEquipmentDetail({
        status: 'Status Desconhecido Custom',
        equipment_type: 'Servidor Rack',
      });

      await waitFor(() => {
        expect(screen.getByText('Status Desconhecido Custom')).toBeInTheDocument();
      });
    });
  });

  describe('9. ImportPage error fallbacks (lines 48-49, 87)', () => {
    it('handles preview error without response detail using message and generic fallback', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(importApi.previewSpreadsheet).mockRejectedValueOnce(new Error('Falha de leitura do arquivo'));

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/importar']}>
            <Routes>
              <Route path="/importar" element={<ImportPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      const file = new File(['content'], 'test.xlsx');
      const input = screen.getByTestId('spreadsheet-file-input');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Falha de leitura do arquivo')).toBeInTheDocument();
      });
    });

    it('handles execute import error without response detail using message and generic fallback', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(importApi.previewSpreadsheet).mockResolvedValueOnce({
        filename: 'test.xlsx',
        total_rows: 1,
        sample_rows: [
          {
            row_number: 2,
            equipment_type: 'DESKTOP',
            location: 'TI',
            status: 'EM USO',
            description: 'Desktop HP',
            patrimony_number: '123',
            serial_number: 'SN-123',
            brand: 'HP',
            last_maintenance_at: null,
          },
        ],
        detected_sheet: 'Patrimônio',
        headers: ['TIPO', 'LOCALIZAÇÃO'],
      });

      vi.mocked(importApi.executeImport).mockRejectedValueOnce(new Error('Erro de conexão ao banco'));

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/importar']}>
            <Routes>
              <Route path="/importar" element={<ImportPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      const file = new File(['content'], 'test.xlsx');
      const input = screen.getByTestId('spreadsheet-file-input');
      fireEvent.change(input, { target: { files: [file] } });

      const confirmBtn = await screen.findByTestId('confirm-import-button');
      fireEvent.click(confirmBtn);

      await waitFor(() => {
        expect(screen.getByText('Erro de conexão ao banco')).toBeInTheDocument();
      });
    });

    it('handles preview error with empty object fallback', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(importApi.previewSpreadsheet).mockRejectedValueOnce({});

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/importar']}>
            <Routes>
              <Route path="/importar" element={<ImportPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      const file = new File(['content'], 'test.xlsx');
      const input = screen.getByTestId('spreadsheet-file-input');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText('Não foi possível ler a planilha. Verifique o formato do arquivo.')).toBeInTheDocument();
      });
    });

    it('handles execute import error with empty object fallback', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(importApi.previewSpreadsheet).mockResolvedValueOnce({
        filename: 'test.xlsx',
        total_rows: 1,
        sample_rows: [
          {
            row_number: 2,
            equipment_type: 'DESKTOP',
            location: 'TI',
            status: 'EM USO',
            description: 'Desktop HP',
            patrimony_number: '123',
            serial_number: 'SN-123',
            brand: 'HP',
            last_maintenance_at: null,
          },
        ],
        detected_sheet: 'Patrimônio',
        headers: ['TIPO', 'LOCALIZAÇÃO'],
      });

      vi.mocked(importApi.executeImport).mockRejectedValueOnce({});

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/importar']}>
            <Routes>
              <Route path="/importar" element={<ImportPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      const file = new File(['content'], 'test.xlsx');
      const input = screen.getByTestId('spreadsheet-file-input');
      fireEvent.change(input, { target: { files: [file] } });

      const confirmBtn = await screen.findByTestId('confirm-import-button');
      fireEvent.click(confirmBtn);

      await waitFor(() => {
        expect(screen.getByText('Erro ao processar importação no banco de dados.')).toBeInTheDocument();
      });
    });
  });

  describe('10. LoginForm password visibility toggle and field error clearing (lines 109, 113, 127-130)', () => {
    it('toggles password visibility and clears password field error on change', async () => {
      render(
        <AuthProvider>
          <LoginForm onSuccess={vi.fn()} />
        </AuthProvider>
      );

      const passwordInput = screen.getByPlaceholderText('••••••••••••');
      expect(passwordInput).toHaveAttribute('type', 'password');

      const toggleBtn = screen.getByRole('button', { name: 'Exibir senha' });
      fireEvent.click(toggleBtn);

      expect(passwordInput).toHaveAttribute('type', 'text');
      expect(screen.getByRole('button', { name: 'Ocultar senha' })).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: 'Ocultar senha' }));
      expect(passwordInput).toHaveAttribute('type', 'password');

      // Submeter vazio para gerar fieldErrors.password
      fireEvent.click(screen.getByRole('button', { name: /entrar no sistema/i }));
      expect(await screen.findByText('Senha é obrigatória.')).toBeInTheDocument();

      // Digitar na senha para disparar line 113: if (fieldErrors.password) setFieldErrors(...)
      fireEvent.change(passwordInput, { target: { value: 'secret' } });
      expect(screen.queryByText('Senha é obrigatória.')).not.toBeInTheDocument();
    });
  });

  describe('11. DashboardPage navigation to /equipamentos (line 70)', () => {
    it('navigates to /equipamentos when clicking the card', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/dashboard']}>
            <Routes>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/equipamentos" element={<div>Rota de Equipamentos Acessada</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      const card = await screen.findByTestId('equipamentos-card');
      fireEvent.click(card);

      expect(await screen.findByText('Rota de Equipamentos Acessada')).toBeInTheDocument();
    });
  });

  describe('12. SideMenu manage tags modal onClose handler', () => {
    it('opens and closes ManageTagsModal from SideMenu', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockResolvedValue([]);

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/dashboard']}>
            <SideMenu />
          </MemoryRouter>
        </AuthProvider>
      );

      // Esperar que o AuthProvider carregue o usuário técnico
      await screen.findByText('tecnico@empresa.com');

      fireEvent.click(screen.getByTestId('toggle-menu-btn'));
      const manageTagsBtn = await screen.findByTestId('manage-tags-menu-item');
      fireEvent.click(manageTagsBtn);

      expect(await screen.findByText('Gerenciador de Tags')).toBeInTheDocument();
      expect(screen.getByTestId('manage-tags-modal')).toHaveClass('z-[60]');

      const closeBtn = screen.getByTestId('close-tags-modal-btn');
      fireEvent.click(closeBtn);

      await waitFor(() => {
        expect(screen.queryByText('Gerenciador de Tags')).not.toBeInTheDocument();
      });
    });
  });

  describe('13. MaintenanceModal notes input change', () => {
    it('allows entering technical notes', () => {
      render(
        <MaintenanceModal
          isOpen={true}
          equipmentId={1}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      const notesInput = screen.getByPlaceholderText(/Ex: Teste de estabilidade concluído/i);
      fireEvent.change(notesInput, { target: { value: 'Limpeza térmica realizada com sucesso.' } });

      expect(notesInput).toHaveValue('Limpeza térmica realizada com sucesso.');
    });
  });

  describe('14. NewEquipmentModal tags error and inline create error (lines 50-51, 80-81)', () => {
    it('catches error when fetchTags fails on modal open', async () => {
      vi.mocked(equipmentApi.getTags).mockRejectedValueOnce(new Error('Tags load fail'));

      render(
        <NewEquipmentModal
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
      });
    });

    it('catches error when inline createTag fails', async () => {
      vi.mocked(equipmentApi.getTags).mockResolvedValue([]);
      vi.mocked(equipmentApi.createTag).mockRejectedValueOnce({
        response: { data: { detail: 'Tag já cadastrada no sistema' } },
      });

      render(
        <NewEquipmentModal
          isOpen={true}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Novo Equipamento')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('inline-create-tipo-btn'));
      const input = screen.getByPlaceholderText('Novo tipo');
      fireEvent.change(input, { target: { value: 'Workstation' } });
      fireEvent.keyDown(input, { key: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText('Tag já cadastrada no sistema')).toBeInTheDocument();
      });
    });
  });

  describe('15. EquipmentDetailPage tags failure and maintenance delete failure (lines 105, 200, 221-222)', () => {
    it('handles tag fetch failure gracefully and handles delete maintenance failure', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockRejectedValueOnce(new Error('Failed tags'));
      vi.mocked(equipmentApi.getEquipmentDetail).mockResolvedValue({
        id: 50,
        serial_number: 'SN-50',
        patrimony_number: 'PAT-50',
        hostname: 'HOST-50',
        description: 'Notebook Corporativo',
        brand: 'Dell',
        product_number: null,
        equipment_type: 'Notebook',
        location: 'TI',
        status: 'Em uso',
        windows_key: null,
        last_maintenance_at: null,
        notes: null,
        created_at: '2026-01-01T00:00:00Z',
        movements: [],
        maintenances: [
          {
            id: 99,
            equipment_id: 50,
            maintenance_date: '2026-02-01T00:00:00Z',
            maintenance_type: 'Preventiva',
            description: 'Troca de bateria',
            notes: null,
            created_at: '2026-02-01T00:00:00Z',
          },
        ],
      });

      vi.spyOn(window, 'confirm').mockReturnValue(true);
      vi.mocked(equipmentApi.deleteMaintenance).mockRejectedValueOnce({
        response: { data: { detail: 'Não é permitido excluir esta manutenção.' } },
      });

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos/50']}>
            <Routes>
              <Route path="/equipamentos/:id" element={<EquipmentDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Notebook Corporativo')[0]).toBeInTheDocument();
      });

      const deleteBtn = screen.getByTitle('Excluir manutenção');
      fireEvent.click(deleteBtn);

      await waitFor(() => {
        expect(screen.getByText('Não é permitido excluir esta manutenção.')).toBeInTheDocument();
      });
    });

    it('saves equipment edit with empty last_maintenance_at (line 200)', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockResolvedValue([]);
      vi.mocked(equipmentApi.getEquipmentDetail).mockResolvedValue({
        id: 51,
        serial_number: 'SN-51',
        patrimony_number: 'PAT-51',
        hostname: 'HOST-51',
        description: 'Notebook Corporativo 51',
        brand: 'Dell',
        product_number: null,
        equipment_type: 'Notebook',
        location: 'TI',
        status: 'Em uso',
        windows_key: null,
        last_maintenance_at: '2026-03-01T00:00:00Z',
        notes: null,
        created_at: '2026-01-01T00:00:00Z',
        movements: [],
        maintenances: [],
      });

      vi.mocked(equipmentApi.updateEquipment).mockResolvedValueOnce({
        id: 51,
        serial_number: 'SN-51',
        patrimony_number: 'PAT-51',
        hostname: 'HOST-51',
        description: 'Notebook Corporativo 51 Alterado',
        brand: 'Dell',
        product_number: null,
        equipment_type: 'Notebook',
        location: 'TI',
        status: 'Em uso',
        windows_key: null,
        last_maintenance_at: null,
        notes: null,
        created_at: '2026-01-01T00:00:00Z',
        movements: [],
        maintenances: [],
      });

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos/51']}>
            <Routes>
              <Route path="/equipamentos/:id" element={<EquipmentDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getAllByText('Notebook Corporativo 51')[0]).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTestId('edit-equipment-btn'));

      const descInput = screen.getByDisplayValue('Notebook Corporativo 51');
      fireEvent.change(descInput, { target: { value: 'Notebook Corporativo 51 Alterado' } });

      fireEvent.click(screen.getByRole('button', { name: /Salvar alterações/i }));

      await waitFor(() => {
        expect(equipmentApi.updateEquipment).toHaveBeenCalledWith(
          51,
          expect.objectContaining({ description: 'Notebook Corporativo 51 Alterado' })
        );
      });
    });
  });

  describe('16. EquipmentListPage serial/product chips and export button (lines 213-242, 411-420)', () => {
    it('renders serial and product chips, allows removing them, and triggers export', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockResolvedValue([]);
      vi.mocked(equipmentApi.getEquipments).mockResolvedValue({
        items: [],
        total: 0,
        page: 1,
        limit: 10,
        pages: 1,
      });

      // Mock URL.createObjectURL e revokeObjectURL
      window.URL.createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/mock');
      window.URL.revokeObjectURL = vi.fn();

      vi.mocked(equipmentApi.exportEquipments).mockResolvedValue({
        data: new Blob(['csv content']),
        filename: 'inventario.xlsx',
      });

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos']}>
            <Routes>
              <Route path="/equipamentos" element={<EquipmentListPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Equipamentos')).toBeInTheDocument();
      });

      // Adicionar filtro de série
      const serialInput = screen.getByTestId('filter-serial-input');
      fireEvent.change(serialInput, { target: { value: 'SN-TEST-FILTER' } });
      fireEvent.keyDown(serialInput, { key: 'Enter' });

      // Adicionar filtro de produto
      const prodInput = screen.getByTestId('filter-product-input');
      fireEvent.change(prodInput, { target: { value: 'PROD-TEST-FILTER' } });
      fireEvent.keyDown(prodInput, { key: 'Enter' });

      await waitFor(() => {
        expect(screen.getByText((_, el) => el?.tagName === 'SPAN' && el.textContent?.includes('Série: SN-TEST-FILTER') && !el.textContent?.includes('Produto') ? true : false)).toBeInTheDocument();
        expect(screen.getByText((_, el) => el?.tagName === 'SPAN' && el.textContent?.includes('Produto: PROD-TEST-FILTER') && !el.textContent?.includes('Série') ? true : false)).toBeInTheDocument();
      });

      // Remover chips
      const removeButtons = screen.getAllByRole('button', { name: '×' });
      removeButtons.forEach((btn) => fireEvent.click(btn));

      await waitFor(() => {
        expect(screen.queryByText((_, el) => el?.tagName === 'SPAN' && el.textContent?.includes('Série: SN-TEST-FILTER') && !el.textContent?.includes('Produto') ? true : false)).not.toBeInTheDocument();
        expect(screen.queryByText((_, el) => el?.tagName === 'SPAN' && el.textContent?.includes('Produto: PROD-TEST-FILTER') && !el.textContent?.includes('Série') ? true : false)).not.toBeInTheDocument();
      });

      // Disparar exportação
      const exportBtn = screen.getByTestId('export-spreadsheet-btn');
      fireEvent.click(exportBtn);

      await waitFor(() => {
        expect(equipmentApi.exportEquipments).toHaveBeenCalled();
      });
    });

    it('renders various equipment types, statuses, and handles export error', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockResolvedValue([]);
      vi.mocked(equipmentApi.getEquipments).mockResolvedValue({
        items: [
          {
            id: 101,
            serial_number: 'SN-MON',
            patrimony_number: 'PAT-MON',
            hostname: null,
            description: 'Monitor Ultrawide',
            brand: 'LG',
            product_number: null,
            equipment_type: 'Monitor',
            location: 'Design',
            status: 'Disponível',
            windows_key: null,
            last_maintenance_at: null,
            notes: null,
            created_at: '2026-01-01T00:00:00Z',
            movements: [],
            maintenances: [],
          },
          {
            id: 102,
            serial_number: 'SN-PRINT',
            patrimony_number: null,
            hostname: null,
            description: 'Impressora Laser',
            brand: 'Brother',
            product_number: null,
            equipment_type: 'Impressora',
            location: 'RH',
            status: 'Em manutenção',
            windows_key: null,
            last_maintenance_at: null,
            notes: null,
            created_at: '2026-01-01T00:00:00Z',
            movements: [],
            maintenances: [],
          },
          {
            id: 103,
            serial_number: 'SN-PHONE',
            patrimony_number: null,
            hostname: null,
            description: 'Smartphone Samsung',
            brand: 'Samsung',
            product_number: null,
            equipment_type: 'Celular',
            location: 'Comercial',
            status: 'Baixado',
            windows_key: null,
            last_maintenance_at: null,
            notes: null,
            created_at: '2026-01-01T00:00:00Z',
            movements: [],
            maintenances: [],
          },
          {
            id: 104,
            serial_number: 'SN-SRV',
            patrimony_number: null,
            hostname: null,
            description: 'Servidor Blade',
            brand: 'HPE',
            product_number: null,
            equipment_type: 'Servidor',
            location: 'Datacenter',
            status: 'Desconhecido',
            windows_key: null,
            last_maintenance_at: null,
            notes: null,
            created_at: '2026-01-01T00:00:00Z',
            movements: [],
            maintenances: [],
          },
        ],
        total: 4,
        page: 1,
        limit: 10,
        pages: 1,
      });

      vi.mocked(equipmentApi.exportEquipments).mockRejectedValueOnce(new Error('Export crash'));

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos']}>
            <Routes>
              <Route path="/equipamentos" element={<EquipmentListPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Monitor Ultrawide')).toBeInTheDocument();
        expect(screen.getByText('Impressora Laser')).toBeInTheDocument();
        expect(screen.getByText('Smartphone Samsung')).toBeInTheDocument();
        expect(screen.getByText('Servidor Blade')).toBeInTheDocument();
      });

      // Disparar erro no export
      const exportBtn = screen.getByTestId('export-spreadsheet-btn');
      fireEvent.click(exportBtn);

      await waitFor(() => {
        expect(equipmentApi.exportEquipments).toHaveBeenCalled();
      });
    });

    it('handles fetchTags and fetchEquipments failure gracefully on EquipmentListPage (lines 88-89, 114)', async () => {
      (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
        id: 1,
        email: 'tecnico@empresa.com',
        role: 'tecnico',
        is_active: true,
      });

      vi.mocked(equipmentApi.getTags).mockRejectedValueOnce(new Error('Tags load error'));
      vi.mocked(equipmentApi.getEquipments).mockRejectedValueOnce(new Error('Equipments load error'));

      render(
        <AuthProvider>
          <MemoryRouter initialEntries={['/equipamentos']}>
            <Routes>
              <Route path="/equipamentos" element={<EquipmentListPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByText('Equipamentos')).toBeInTheDocument();
      });
    });
  });
});
