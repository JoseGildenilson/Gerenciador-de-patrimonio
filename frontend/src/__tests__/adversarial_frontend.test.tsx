import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { MultiSelectFilterDropdown } from '../components/MultiSelectFilterDropdown';
import { MaintenanceModal } from '../components/MaintenanceModal';
import { EditMaintenanceModal } from '../components/EditMaintenanceModal';
import { EquipmentDetailPage } from '../pages/EquipmentDetailPage';
import { equipmentApi } from '../api/equipmentApi';
import { authApi } from '../api/authApi';
import { AuthProvider } from '../context/AuthContext';
import { Equipment } from '../types/equipment';

vi.mock('../api/authApi', () => ({
  authApi: {
    getMe: vi.fn(),
  },
}));

vi.mock('../api/equipmentApi', () => ({
  equipmentApi: {
    getEquipmentDetail: vi.fn(),
    getTags: vi.fn(),
    createTag: vi.fn(),
    updateEquipment: vi.fn(),
    deleteMaintenance: vi.fn(),
    recordMaintenance: vi.fn(),
    updateMaintenance: vi.fn(),
    recordMovement: vi.fn(),
  },
}));

describe('Adversarial Stress Testing: MultiSelectFilterDropdown', () => {
  it('handles empty options list gracefully without crashing', () => {
    const handleChange = vi.fn();
    render(
      <MultiSelectFilterDropdown
        label="Vazio"
        options={[]}
        selectedValues={[]}
        onChange={handleChange}
        testId="empty-dropdown"
      />
    );

    const trigger = screen.getByRole('button');
    fireEvent.click(trigger);

    expect(screen.getByText('Nenhuma opção encontrada')).toBeInTheDocument();
    expect(screen.getByText('0 sel.')).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText('Pesquisar...');
    fireEvent.change(searchInput, { target: { value: 'teste' } });
    expect(screen.getByText('Nenhuma opção encontrada')).toBeInTheDocument();
  });

  it('handles 1000 items efficiently without freeze, supports searching and selecting item #999', () => {
    const thousandOptions = Array.from({ length: 1000 }, (_, i) => `Equipamento_${String(i).padStart(4, '0')}`);
    const handleChange = vi.fn();

    render(
      <MultiSelectFilterDropdown
        label="Mil Itens"
        options={thousandOptions}
        selectedValues={[]}
        onChange={handleChange}
      />
    );

    const trigger = screen.getByRole('button');
    fireEvent.click(trigger);

    const searchInput = screen.getByPlaceholderText('Pesquisar...');
    // Search for 999
    fireEvent.change(searchInput, { target: { value: '0999' } });

    const item999 = screen.getByText('Equipamento_0999');
    expect(item999).toBeInTheDocument();

    fireEvent.click(item999);
    expect(handleChange).toHaveBeenCalledWith(['Equipamento_0999']);
  });

  it('handles special regex characters in search without throwing SyntaxError or crashing', () => {
    const regexOptions = ['Item (Alpha)', 'Item [Beta]', 'Item.*', 'Item $100', 'Item^start', 'Item+plus', 'Item?mark'];
    const handleChange = vi.fn();

    render(
      <MultiSelectFilterDropdown
        label="Regex Test"
        options={regexOptions}
        selectedValues={[]}
        onChange={handleChange}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    const searchInput = screen.getByPlaceholderText('Pesquisar...');

    const adversarialStrings = ['.*', '[a-z]', '\\', '(', ')', '+', '?', '^', '$', '{', '}', '|', '[', ']'];

    for (const pattern of adversarialStrings) {
      expect(() => {
        fireEvent.change(searchInput, { target: { value: pattern } });
      }).not.toThrow();
    }

    // Exact match on parenthesis
    fireEvent.change(searchInput, { target: { value: '(Alpha)' } });
    expect(screen.getByText('Item (Alpha)')).toBeInTheDocument();
    expect(screen.queryByText('Item [Beta]')).not.toBeInTheDocument();
  });

  it('resists rapid fire clicking on trigger and options without state desync', () => {
    const options = ['Opção A', 'Opção B', 'Opção C'];
    const handleChange = vi.fn();

    render(
      <MultiSelectFilterDropdown
        label="Rapid Click"
        options={options}
        selectedValues={['Opção A']}
        onChange={handleChange}
      />
    );

    const trigger = screen.getByRole('button');

    // 20 rapid clicks on trigger
    for (let i = 0; i < 20; i++) {
      fireEvent.click(trigger);
    }

    // If even number of clicks (20), it should be closed
    expect(screen.queryByPlaceholderText('Pesquisar...')).not.toBeInTheDocument();

    // Open again
    fireEvent.click(trigger);
    expect(screen.getByPlaceholderText('Pesquisar...')).toBeInTheDocument();

    // Rapid clicking on an option
    const optB = screen.getByText('Opção B');
    for (let i = 0; i < 10; i++) {
      fireEvent.click(optB);
    }
    expect(handleChange).toHaveBeenCalledTimes(10);
  });

  it('handles selected values that do not exist in options gracefully', () => {
    const handleChange = vi.fn();
    render(
      <MultiSelectFilterDropdown
        label="Legado"
        options={['Opção 1', 'Opção 2']}
        selectedValues={['ItemExcluido1', 'ItemExcluido2']}
        onChange={handleChange}
      />
    );

    expect(screen.getByRole('button')).toHaveTextContent('Legado (2)');
    fireEvent.click(screen.getByRole('button'));

    expect(screen.getByText('2 sel.')).toBeInTheDocument();
    const clearBtn = screen.getByText('Desmarcar tudo');
    fireEvent.click(clearBtn);
    expect(handleChange).toHaveBeenCalledWith([]);
  });

  it('handles extremely long option strings without breaking layout or crashing', () => {
    const longString = 'X'.repeat(5000);
    render(
      <MultiSelectFilterDropdown
        label="Long String"
        options={[longString]}
        selectedValues={[longString]}
        onChange={vi.fn()}
      />
    );

    expect(screen.getByRole('button')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button'));
    expect(screen.getByText(longString)).toBeInTheDocument();
  });
});

describe('Adversarial Stress Testing: Modals (MaintenanceModal & EditMaintenanceModal)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('MaintenanceModal: prevents concurrent submissions during network delay (button disabled)', async () => {
    let resolveApi: (val: any) => void = () => {};
    const delayedPromise = new Promise((resolve) => {
      resolveApi = resolve;
    });
    (equipmentApi.recordMaintenance as ReturnType<typeof vi.fn>).mockReturnValue(delayedPromise);

    const onSuccess = vi.fn();
    const onClose = vi.fn();

    render(
      <MaintenanceModal
        isOpen={true}
        equipmentId={1}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
    fireEvent.change(descInput, { target: { value: 'Substituição de placa mãe' } });

    const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
    fireEvent.click(submitBtn);

    // Button should now be disabled and show spinner
    expect(submitBtn).toBeDisabled();

    // Repeated rapid clicks while disabled must not fire additional calls
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);

    expect(equipmentApi.recordMaintenance).toHaveBeenCalledTimes(1);

    // Resolve delay
    await act(async () => {
      resolveApi({ id: 100 });
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('MaintenanceModal: handles extreme rejection payloads (network error, null response, 500 error) without crashing', async () => {
    const rejectionScenarios = [
      new Error('Failed to fetch'),
      { response: null },
      { response: { data: null } },
      { response: { data: { detail: '' } } },
      { response: { status: 500, data: '<html>500 Internal Server Error</html>' } },
      'string rejection error',
    ];

    for (const errorPayload of rejectionScenarios) {
      (equipmentApi.recordMaintenance as ReturnType<typeof vi.fn>).mockRejectedValueOnce(errorPayload);

      const { unmount } = render(
        <MaintenanceModal
          isOpen={true}
          equipmentId={1}
          onClose={vi.fn()}
          onSuccess={vi.fn()}
        />
      );

      const descInput = screen.getByPlaceholderText(/Ex: Troca de SSD/i);
      fireEvent.change(descInput, { target: { value: 'Stress test error' } });

      const submitBtn = screen.getByRole('button', { name: /salvar manutenção/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/Erro ao registrar manutenção/i)).toBeInTheDocument();
      });

      unmount();
    }
  });

  it('EditMaintenanceModal: prevents concurrent submissions during slow response and handles network drops gracefully', async () => {
    let resolveUpdate: (val: any) => void = () => {};
    const delayedPromise = new Promise((resolve) => {
      resolveUpdate = resolve;
    });
    (equipmentApi.updateMaintenance as ReturnType<typeof vi.fn>).mockReturnValue(delayedPromise);

    const mockMaint = {
      id: 55,
      equipment_id: 1,
      maintenance_date: '2026-05-10T10:00:00Z',
      maintenance_type: 'Manutenção',
      description: 'Manutenção original',
      notes: 'Notas originais',
      created_at: '2026-05-10T10:00:00Z',
    };

    const onClose = vi.fn();
    const onSuccess = vi.fn();

    render(
      <EditMaintenanceModal
        isOpen={true}
        equipmentId={1}
        maintenance={mockMaint}
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    const submitBtn = screen.getByRole('button', { name: /salvar alterações/i });
    fireEvent.click(submitBtn);

    expect(submitBtn).toBeDisabled();

    // Additional clicks ignored
    fireEvent.click(submitBtn);
    fireEvent.click(submitBtn);
    expect(equipmentApi.updateMaintenance).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveUpdate({ id: 55 });
    });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});

describe('Adversarial Stress Testing: EquipmentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      email: 'tecnico@empresa.com',
      role: 'tecnico',
      is_active: true,
    });
    (equipmentApi.getTags as ReturnType<typeof vi.fn>).mockResolvedValue([]);
  });

  const renderDetailPage = (id = '99') => {
    return render(
      <AuthProvider>
        <MemoryRouter initialEntries={[`/equipamentos/${id}`]}>
          <Routes>
            <Route path="/equipamentos/:id" element={<EquipmentDetailPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
  };

  it('renders gracefully with minimal/null equipment data without throwing TypeError', async () => {
    const minimalEquipment: Equipment = {
      id: 99,
      serial_number: 'SN-MINIMAL-001',
      patrimony_number: null,
      hostname: null,
      description: '',
      brand: null,
      product_number: null,
      equipment_type: 'Outro',
      location: 'Almoxarifado',
      status: 'Ocioso',
      windows_key: null,
      last_maintenance_at: null,
      notes: null,
      created_at: '2026-01-01T00:00:00Z',
      movements: [],
      maintenances: [],
    };

    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce(minimalEquipment);

    renderDetailPage('99');

    expect(await screen.findByText('SN-MINIMAL-001')).toBeInTheDocument();
    expect(screen.getByText('Nenhuma chave registrada')).toBeInTheDocument();
    expect(screen.getByText('Nenhuma atividade de movimentação ou manutenção registrada.')).toBeInTheDocument();
  });

  it('handles extreme long text fields without breaking page render', async () => {
    const hugeDescription = 'D'.repeat(4000);
    const hugeNotes = 'N'.repeat(2000);

    const extremeEquipment: Equipment = {
      id: 100,
      serial_number: 'SN-HUGE-TEXT',
      patrimony_number: 'PAT-HUGE',
      hostname: 'HOST-HUGE',
      description: hugeDescription,
      brand: 'Brand',
      product_number: 'ProdNum',
      equipment_type: 'Desktop',
      location: 'TI',
      status: 'Em uso',
      windows_key: 'AAAAA-BBBBB-CCCCC-DDDDD-EEEEE',
      last_maintenance_at: '2026-05-01T00:00:00Z',
      notes: hugeNotes,
      created_at: '2026-01-01T00:00:00Z',
      movements: [],
      maintenances: [],
    };

    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce(extremeEquipment);

    renderDetailPage('100');

    expect(await screen.findByText('SN-HUGE-TEXT')).toBeInTheDocument();
    expect(screen.getAllByText(hugeDescription)[0]).toBeInTheDocument();
    expect(screen.getByText(hugeNotes)).toBeInTheDocument();
  });

  it('resists rapid edit toggle cycles and resets form fields to original values on cancel', async () => {
    const originalEquipment: Equipment = {
      id: 101,
      serial_number: 'SN-ORIGINAL',
      patrimony_number: 'PAT-ORIGINAL',
      hostname: 'HOST-ORIGINAL',
      description: 'Desc Original',
      brand: 'Dell',
      product_number: 'LAT-5420',
      equipment_type: 'Notebook',
      location: 'TI',
      status: 'Em uso',
      windows_key: 'AAAAA-BBBBB-CCCCC-DDDDD-EEEEE',
      last_maintenance_at: null,
      notes: 'Nota Original',
      created_at: '2026-01-01T00:00:00Z',
      movements: [],
      maintenances: [],
    };

    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValue(originalEquipment);

    renderDetailPage('101');

    expect(await screen.findByText('SN-ORIGINAL')).toBeInTheDocument();

    const editBtn = screen.getByTestId('edit-equipment-btn');

    // Cycle 1: Click edit -> change serial -> Cancel
    fireEvent.click(editBtn);
    expect(screen.getByDisplayValue('SN-ORIGINAL')).toBeInTheDocument();

    const serialInput = screen.getByDisplayValue('SN-ORIGINAL');
    fireEvent.change(serialInput, { target: { value: 'SN-TAMPERED' } });
    expect(screen.getByDisplayValue('SN-TAMPERED')).toBeInTheDocument();

    const cancelBtn = screen.getByRole('button', { name: /cancelar/i });
    fireEvent.click(cancelBtn);

    // Verify back in read mode with original value
    expect(screen.queryByDisplayValue('SN-TAMPERED')).not.toBeInTheDocument();
    expect(screen.getByText('SN-ORIGINAL')).toBeInTheDocument();

    // Cycle 2: Click edit again -> verify original value reloaded
    const reEditBtn = screen.getByTestId('edit-equipment-btn');
    fireEvent.click(reEditBtn);
    expect(screen.getByDisplayValue('SN-ORIGINAL')).toBeInTheDocument();
  });

  it('resists rapid Windows key toggles back and forth', async () => {
    const equipmentWithKey: Equipment = {
      id: 102,
      serial_number: 'SN-KEY-TEST',
      patrimony_number: null,
      hostname: null,
      description: 'Key Test',
      brand: null,
      product_number: null,
      equipment_type: 'Desktop',
      location: 'TI',
      status: 'Em uso',
      windows_key: 'W269N-WFGWX-YVC9B-4J6C9-T83GX',
      last_maintenance_at: null,
      notes: null,
      created_at: '2026-01-01T00:00:00Z',
      movements: [],
      maintenances: [],
    };

    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce(equipmentWithKey);

    renderDetailPage('102');

    expect(await screen.findByText('SN-KEY-TEST')).toBeInTheDocument();

    // Initially masked: •••••••••••••••••••••••••
    expect(screen.getByText('•••••••••••••••••••••••••')).toBeInTheDocument();

    // Toggle 10 times (5 cycles of show/hide)
    for (let i = 0; i < 5; i++) {
      const showBtn = screen.getByTitle('Mostrar Chave');
      fireEvent.click(showBtn);
      expect(screen.getByText('W269N-WFGWX-YVC9B-4J6C9-T83GX')).toBeInTheDocument();

      const hideBtn = screen.getByTitle('Ocultar Chave');
      fireEvent.click(hideBtn);
      expect(screen.getByText('•••••••••••••••••••••••••')).toBeInTheDocument();
    }
  });
});
