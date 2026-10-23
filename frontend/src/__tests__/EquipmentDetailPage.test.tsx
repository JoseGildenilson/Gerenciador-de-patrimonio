import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { EquipmentDetailPage } from '../pages/EquipmentDetailPage';
import { equipmentApi } from '../api/equipmentApi';
import { authApi } from '../api/authApi';
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

const mockTags = [
  { id: 1, category: 'tipo', name: 'Notebook' },
  { id: 2, category: 'tipo', name: 'Desktop' },
  { id: 3, category: 'localizacao', name: 'TI' },
  { id: 4, category: 'localizacao', name: 'Almoxarifado' },
  { id: 5, category: 'situacao', name: 'Em uso' },
  { id: 6, category: 'situacao', name: 'Disponível' },
];

const mockEquipment: Equipment = {
  id: 1,
  serial_number: 'SN-THINKPAD-01',
  patrimony_number: 'PAT-2026-001',
  hostname: 'NB-TI-01',
  description: 'ThinkPad T14 Gen 3',
  brand: 'Lenovo',
  product_number: '21AH000EBR',
  equipment_type: 'Notebook',
  location: 'TI',
  status: 'Em uso',
  windows_key: 'W269N-WFGWX-YVC9B-4J6C9-T83GX',
  last_maintenance_at: '2026-08-10T14:30:00Z',
  notes: 'Equipamento entregue configurado para desenvolvimento.',
  created_at: '2026-01-10T10:00:00Z',
  movements: [
    {
      id: 101,
      equipment_id: 1,
      origin_location: 'Almoxarifado',
      destination_location: 'TI',
      movement_date: '2026-02-01T09:00:00Z',
      notes: 'Alocação inicial',
      created_at: '2026-02-01T09:00:00Z',
    },
  ],
  maintenances: [
    {
      id: 201,
      equipment_id: 1,
      maintenance_date: '2026-08-10T14:30:00Z',
      maintenance_type: 'Manutenção',
      description: 'Limpeza e troca de pasta térmica',
      notes: 'Pasta térmica de prata utilizada',
      created_at: '2026-08-10T14:30:00Z',
    },
  ],
};

const renderPage = (initialRoute = '/equipamentos/1') => {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/equipamentos/:id" element={<EquipmentDetailPage />} />
          <Route path="/equipamentos" element={<div>Listagem de Equipamentos</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
};

describe('EquipmentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (authApi.getMe as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      email: 'tecnico@empresa.com',
      role: 'tecnico',
      is_active: true,
    });
    (equipmentApi.getTags as ReturnType<typeof vi.fn>).mockResolvedValue(mockTags);
    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValue(mockEquipment);
  });

  it('renderiza os detalhes completos do equipamento em tela única', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'ThinkPad T14 Gen 3' })).toBeInTheDocument();
    });

    // Identificação e especificações
    expect(screen.getByText('PAT-2026-001')).toBeInTheDocument();
    expect(screen.getByText('SN-THINKPAD-01')).toBeInTheDocument();
    expect(screen.getByText('NB-TI-01')).toBeInTheDocument();

    // Tags
    expect(screen.getByText('Notebook')).toBeInTheDocument();
    expect(screen.getAllByText('TI')[0]).toBeInTheDocument();
    expect(screen.getByText('Em uso')).toBeInTheDocument();

    // Chave Windows mascarada
    expect(screen.getByText('•••••••••••••••••••••••••')).toBeInTheDocument();

    // Observações
    expect(screen.getByText('Equipamento entregue configurado para desenvolvimento.')).toBeInTheDocument();

    // Histórico unificado
    expect(screen.getByText('Limpeza e troca de pasta térmica')).toBeInTheDocument();
    expect(screen.getByText('Alocação inicial')).toBeInTheDocument();
  });

  it('exibe erro de carregamento quando getEquipmentDetail falha', async () => {
    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: { data: { detail: 'Equipamento não encontrado' } },
    });

    renderPage();

    expect(await screen.findByText('Equipamento não encontrado')).toBeInTheDocument();
  });

  it('navega de volta para /equipamentos ao clicar no botão voltar', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('back-to-equipments-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('back-to-equipments-btn'));

    expect(await screen.findByText('Listagem de Equipamentos')).toBeInTheDocument();
  });

  it('alterna visualização da chave Windows mascarada / revelada', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('•••••••••••••••••••••••••')).toBeInTheDocument();
    });

    const toggleKeyBtn = screen.getByTitle('Mostrar Chave');
    fireEvent.click(toggleKeyBtn);

    // Revela a chave real
    expect(screen.getByText('W269N-WFGWX-YVC9B-4J6C9-T83GX')).toBeInTheDocument();
    expect(screen.getByTitle('Ocultar Chave')).toBeInTheDocument();

    // Oculta novamente
    fireEvent.click(screen.getByTitle('Ocultar Chave'));
    expect(screen.getByText('•••••••••••••••••••••••••')).toBeInTheDocument();
  });

  it('exibe mensagem quando equipamento não possui chave Windows cadastrada', async () => {
    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...mockEquipment,
      windows_key: null,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Nenhuma chave registrada')).toBeInTheDocument();
    });
    expect(screen.queryByTitle('Mostrar Chave')).not.toBeInTheDocument();
  });

  it('entra no modo de edição em lote e permite cancelar restaurando valores', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    });

    // Inicia edição
    fireEvent.click(screen.getByTestId('edit-equipment-btn'));

    expect(screen.getByText('Salvar alterações')).toBeInTheDocument();
    expect(screen.getByText('Cancelar')).toBeInTheDocument();

    // Altera um campo
    const descInput = screen.getByDisplayValue('ThinkPad T14 Gen 3');
    fireEvent.change(descInput, { target: { value: 'ThinkPad Modificado' } });

    // Cancela
    fireEvent.click(screen.getByText('Cancelar'));

    // Modo de edição fechado e valor anterior preservado
    expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    expect(screen.getAllByText('ThinkPad T14 Gen 3')[0]).toBeInTheDocument();
  });

  it('salva alterações no modo de edição em lote com sucesso', async () => {
    const updatedEquipment: Equipment = {
      ...mockEquipment,
      description: 'ThinkPad T14 Gen 3 (Atualizado)',
      hostname: 'NB-TI-01-PROD',
      brand: 'Lenovo Brasil',
    };
    (equipmentApi.updateEquipment as ReturnType<typeof vi.fn>).mockResolvedValueOnce(
      updatedEquipment
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('edit-equipment-btn'));

    const descInput = screen.getByDisplayValue('ThinkPad T14 Gen 3');
    fireEvent.change(descInput, { target: { value: 'ThinkPad T14 Gen 3 (Atualizado)' } });

    const hostInput = screen.getByDisplayValue('NB-TI-01');
    fireEvent.change(hostInput, { target: { value: 'NB-TI-01-PROD' } });

    fireEvent.click(screen.getByText('Salvar alterações'));

    await waitFor(() => {
      expect(equipmentApi.updateEquipment).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          description: 'ThinkPad T14 Gen 3 (Atualizado)',
          hostname: 'NB-TI-01-PROD',
        })
      );
      expect(screen.getAllByText('ThinkPad T14 Gen 3 (Atualizado)')[0]).toBeInTheDocument();
    });
  });

  it('exibe erro retornado pela API caso o salvamento falhe', async () => {
    (equipmentApi.updateEquipment as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: { data: { detail: 'Hostname já cadastrado em outro equipamento' } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('edit-equipment-btn'));
    fireEvent.click(screen.getByText('Salvar alterações'));

    expect(
      await screen.findByText('Hostname já cadastrado em outro equipamento')
    ).toBeInTheDocument();
    // Permanece no formulário de edição
    expect(screen.getByText('Salvar alterações')).toBeInTheDocument();
  });

  it('cria uma nova tag inline durante o modo de edição', async () => {
    (equipmentApi.createTag as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      id: 99,
      category: 'tipo',
      name: 'Workstation',
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('edit-equipment-btn'));

    // Clica no botão inline de criar novo tipo
    const inlineBtn = screen.getByTestId('inline-create-tipo-btn');
    fireEvent.click(inlineBtn);

    const inlineInput = screen.getByPlaceholderText(/novo tipo/i);
    fireEvent.change(inlineInput, { target: { value: 'Workstation' } });

    // Confirma criação
    const confirmInlineBtn = screen.getByTitle('Salvar');
    fireEvent.click(confirmInlineBtn);

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('tipo', 'Workstation');
    });
  });

  it('exibe erro caso a criação de tag inline falhe', async () => {
    (equipmentApi.createTag as ReturnType<typeof vi.fn>).mockRejectedValueOnce({
      response: { data: { detail: 'Tag já existente' } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('edit-equipment-btn'));
    fireEvent.click(screen.getByTestId('inline-create-tipo-btn'));

    const inlineInput = screen.getByPlaceholderText(/novo tipo/i);
    fireEvent.change(inlineInput, { target: { value: 'Notebook' } });

    fireEvent.click(screen.getByTitle('Salvar'));

    expect(await screen.findByText('Tag já existente')).toBeInTheDocument();
  });

  it('solicita confirmação e exclui registro de manutenção ao clicar na lixeira', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm');
    confirmSpy.mockReturnValueOnce(true);
    (equipmentApi.deleteMaintenance as ReturnType<typeof vi.fn>).mockResolvedValueOnce({});

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Limpeza e troca de pasta térmica')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByTitle('Excluir manutenção');
    fireEvent.click(deleteBtn);

    expect(confirmSpy).toHaveBeenCalledWith(
      'Deseja realmente excluir este registro de manutenção?'
    );

    await waitFor(() => {
      expect(equipmentApi.deleteMaintenance).toHaveBeenCalledWith(1, 201);
      expect(equipmentApi.getEquipmentDetail).toHaveBeenCalledTimes(2);
    });

    confirmSpy.mockRestore();
  });

  it('aborta exclusão de manutenção se o usuário cancelar o diálogo de confirmação', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm');
    confirmSpy.mockReturnValueOnce(false);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Limpeza e troca de pasta térmica')).toBeInTheDocument();
    });

    const deleteBtn = screen.getByTitle('Excluir manutenção');
    fireEvent.click(deleteBtn);

    expect(equipmentApi.deleteMaintenance).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('abre os modais de Movimentação, Manutenção e Edição de Manutenção', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /movimentar/i })).toBeInTheDocument();
    });

    // Abrir Modal de Movimentação
    fireEvent.click(screen.getByRole('button', { name: /movimentar/i }));
    expect(screen.getByRole('heading', { name: /registrar movimentação/i })).toBeInTheDocument();
    // Fechar Modal de Movimentação
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }));

    // Abrir Modal de Manutenção
    const maintButtons = screen.getAllByRole('button', { name: /manutenção/i });
    fireEvent.click(maintButtons[0]);
    expect(screen.getByRole('heading', { name: /registrar manutenção/i })).toBeInTheDocument();
    // Fechar Modal de Manutenção
    fireEvent.click(screen.getByRole('button', { name: /cancelar/i }));

    // Abrir Modal de Edição de Manutenção a partir do histórico
    const editMaintBtn = screen.getByTitle('Editar manutenção');
    fireEvent.click(editMaintBtn);
    expect(screen.getByRole('heading', { name: /editar manutenção/i })).toBeInTheDocument();
  });

  it('exibe mensagem apropriada quando equipamento não possui histórico', async () => {
    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      ...mockEquipment,
      movements: [],
      maintenances: [],
    });

    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText('Nenhuma atividade de movimentação ou manutenção registrada.')
      ).toBeInTheDocument();
    });
  });

  it('permite criação inline de localização e situação durante a edição do equipamento', async () => {
    vi.mocked(equipmentApi.createTag).mockResolvedValueOnce({
      id: 10,
      category: 'localizacao',
      name: 'Laboratório Novo',
      created_at: '2026-08-23T00:00:00Z',
    });
    vi.mocked(equipmentApi.createTag).mockResolvedValueOnce({
      id: 11,
      category: 'situacao',
      name: 'Em Teste',
      created_at: '2026-08-23T00:00:00Z',
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('edit-equipment-btn')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('edit-equipment-btn'));

    // 1. Criar localização inline com Enter
    const createLocBtn = screen.getByTestId('inline-create-localizacao-btn');
    fireEvent.click(createLocBtn);
    const locInput = screen.getByPlaceholderText('Nova localização...');
    fireEvent.change(locInput, { target: { value: 'Laboratório Novo' } });
    fireEvent.keyDown(locInput, { key: 'Enter' });

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('localizacao', 'Laboratório Novo');
    });

    // 2. Criar situação inline, cancelar com Escape e criar novamente salvando com Enter
    const createSitBtn = screen.getByTestId('inline-create-situacao-btn');
    fireEvent.click(createSitBtn);
    const sitInput = screen.getByPlaceholderText('Nova situação...');
    fireEvent.keyDown(sitInput, { key: 'Escape' });
    expect(screen.queryByPlaceholderText('Nova situação...')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('inline-create-situacao-btn'));
    const sitInput2 = screen.getByPlaceholderText('Nova situação...');
    fireEvent.change(sitInput2, { target: { value: 'Em Teste' } });
    fireEvent.keyDown(sitInput2, { key: 'Enter' });

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('situacao', 'Em Teste');
    });

    // 3. Criar tipo inline, cancelar com Escape e salvar com Enter
    vi.mocked(equipmentApi.createTag).mockResolvedValueOnce({
      id: 12,
      category: 'tipo',
      name: 'Tablet Corporativo',
      created_at: '2026-08-23T00:00:00Z',
    });
    const createTipoBtn = screen.getByTestId('inline-create-tipo-btn');
    fireEvent.click(createTipoBtn);
    const tipoInput = screen.getByPlaceholderText('Novo tipo...');
    fireEvent.keyDown(tipoInput, { key: 'Escape' });
    expect(screen.queryByPlaceholderText('Novo tipo...')).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId('inline-create-tipo-btn'));
    const tipoInput2 = screen.getByPlaceholderText('Novo tipo...');
    fireEvent.change(tipoInput2, { target: { value: 'Tablet Corporativo' } });
    fireEvent.keyDown(tipoInput2, { key: 'Enter' });

    await waitFor(() => {
      expect(equipmentApi.createTag).toHaveBeenCalledWith('tipo', 'Tablet Corporativo');
    });
  });

  it('covers residual branches for object maintenance_type and object sector in modals', async () => {
    const customEq: any = {
      ...mockEquipment,
      sector: { name: 'Setor Objeto Alpha' },
      location: 'Sala 1',
      maintenances: [
        {
          id: 99,
          maintenance_date: '2026-05-10T10:00:00Z',
          maintenance_type: { name: 'Manutenção Preventiva Especial' },
          description: 'Revisão periódica',
        },
      ],
    };

    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce(customEq);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Manutenção Preventiva Especial')).toBeInTheDocument();
    });

    const moveBtn = screen.getByRole('button', { name: /movimentar/i });
    fireEvent.click(moveBtn);
  });

  it('covers residual branch for object location when sector is absent', async () => {
    const customEqLocationOnly: any = {
      ...mockEquipment,
      sector: null,
      location: { name: 'Sala 404 Objeto' },
    };
    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce(customEqLocationOnly);

    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText('ThinkPad T14 Gen 3')[0]).toBeInTheDocument();
    });

    const moveBtn = screen.getByRole('button', { name: /movimentar/i });
    fireEvent.click(moveBtn);
  });

  it('covers movement origin and destination sector/location object fallbacks (lines 948-961)', async () => {
    const customEqMovements: any = {
      ...mockEquipment,
      movements: [
        {
          id: 301,
          movement_date: '2026-05-10T10:00:00Z',
          origin_sector: { name: 'Setor Origem Objeto' },
          destination_sector: { name: 'Setor Destino Objeto' },
          notes: 'Transferência de setor',
        },
        {
          id: 302,
          movement_date: '2026-05-11T10:00:00Z',
          origin_sector: null,
          origin_location: { name: 'Local Origem Objeto' },
          destination_sector: null,
          destination_location: { name: 'Local Destino Objeto' },
          notes: 'Transferência de local',
        },
      ],
    };

    (equipmentApi.getEquipmentDetail as ReturnType<typeof vi.fn>).mockResolvedValueOnce(customEqMovements);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Setor Origem Objeto')).toBeInTheDocument();
      expect(screen.getByText('Setor Destino Objeto')).toBeInTheDocument();
      expect(screen.getByText('Local Origem Objeto')).toBeInTheDocument();
      expect(screen.getByText('Local Destino Objeto')).toBeInTheDocument();
    });
  });
});


