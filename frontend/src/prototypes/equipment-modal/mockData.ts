export interface PrototypeTag {
  id: number;
  category: 'tipo' | 'localizacao' | 'situacao';
  name: string;
  count?: number;
}

export const INITIAL_TAGS: PrototypeTag[] = [
  // Tipos
  { id: 1, category: 'tipo', name: 'Notebook' },
  { id: 2, category: 'tipo', name: 'Desktop' },
  { id: 3, category: 'tipo', name: 'Monitor' },
  { id: 4, category: 'tipo', name: 'Servidor' },
  { id: 5, category: 'tipo', name: 'Switch de Rede' },
  { id: 6, category: 'tipo', name: 'Nobreak' },
  { id: 7, category: 'tipo', name: 'Impressora' },

  // Localizações
  { id: 8, category: 'localizacao', name: 'TI - Suporte' },
  { id: 9, category: 'localizacao', name: 'Almoxarifado' },
  { id: 10, category: 'localizacao', name: 'Financeiro' },
  { id: 11, category: 'localizacao', name: 'Diretoria' },
  { id: 12, category: 'localizacao', name: 'Engenharia' },
  { id: 13, category: 'localizacao', name: 'Recepção' },
  { id: 14, category: 'localizacao', name: 'Data Center' },

  // Situações
  { id: 15, category: 'situacao', name: 'Em uso' },
  { id: 16, category: 'situacao', name: 'Em estoque' },
  { id: 17, category: 'situacao', name: 'Em manutenção' },
  { id: 18, category: 'situacao', name: 'Reservado' },
  { id: 19, category: 'situacao', name: 'Descarte' },
];

export const BACKGROUND_MOCK_EQUIPMENTS = [
  {
    id: 1,
    patrimony_number: 'PAT-0892',
    serial_number: '5CG21890X4',
    description: 'Dell Latitude 5420 i7 16GB 512GB SSD',
    equipment_type: 'Notebook',
    location: 'TI - Suporte',
    status: 'Em uso',
    brand: 'Dell',
    hostname: 'TI-NOTE-04',
  },
  {
    id: 2,
    patrimony_number: 'PAT-0741',
    serial_number: 'MXL89012KA',
    description: 'HP EliteDesk 800 G6 Mini i5 16GB',
    equipment_type: 'Desktop',
    location: 'Financeiro',
    status: 'Em uso',
    brand: 'HP',
    hostname: 'FIN-DESK-01',
  },
  {
    id: 3,
    patrimony_number: 'PAT-0623',
    serial_number: 'CN4091873L',
    description: 'Monitor Dell UltraSharp 27" 4K U2723QE',
    equipment_type: 'Monitor',
    location: 'Diretoria',
    status: 'Em uso',
    brand: 'Dell',
    hostname: null,
  },
  {
    id: 4,
    patrimony_number: 'PAT-0912',
    serial_number: 'FOC2408W09X',
    description: 'Cisco Catalyst 2960-X 48 Ports PoE',
    equipment_type: 'Switch de Rede',
    location: 'Data Center',
    status: 'Em estoque',
    brand: 'Cisco',
    hostname: 'SW-CORE-01',
  },
];
