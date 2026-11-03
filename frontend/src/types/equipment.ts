export type AssetStatus = 'disponivel' | 'em_uso' | 'em_manutencao' | 'baixado' | string;
export type MaintenanceType = 'preventiva' | 'corretiva' | string;

export interface Category {
  id: number;
  name: string;
  useful_life_months?: number | null;
  residual_value_rate?: number | string;
  requires_serial_number?: boolean;
  created_at?: string;
}

export interface Location {
  id: number;
  building: string;
  floor: string;
  sector: string;
  room_number?: string | null;
  description?: string | null;
  created_at?: string;
  name?: string;
}

export interface UserSummary {
  id: number;
  name: string;
  email: string;
  role: string;
}

export interface PatrimonyHistory {
  id: number;
  asset_id: number;
  old_patrimony_number: string;
  new_patrimony_number: string;
  reason: string;
  changed_by_id: number;
  changed_at: string;
}

export interface EquipmentMovement {
  id: number;
  asset_id?: number;
  equipment_id?: number;
  origin_location_id?: number;
  origin_sector_id?: number;
  origin_sector?: { id: number; name: string } | null;
  origin_location?: string | Location | { id: number; name: string };
  dest_location_id?: number | null;
  destination_sector_id?: number;
  destination_sector?: { id: number; name: string } | null;
  destination_location?: string | Location | { id: number; name: string };
  from_user_id?: number | null;
  to_user_id?: number | null;
  moved_by_id?: number;
  performed_by_user_id?: number;
  moved_at?: string;
  movement_date: string;
  accepted_at?: string | null;
  notes?: string | null;
  created_at: string;
}

export type AssetMovement = EquipmentMovement;

export interface EquipmentMaintenance {
  id: number;
  asset_id?: number;
  equipment_id?: number;
  registered_by_id?: number;
  maintenance_type_id?: number;
  maintenance_type?: MaintenanceType | { id: number; name: string };
  service_provider?: string | null;
  cost?: number | string;
  started_at?: string;
  completed_at?: string | null;
  maintenance_date?: string;
  description: string;
  notes?: string | null;
  created_at: string;
}

export type AssetMaintenance = EquipmentMaintenance;

export interface EquipmentTag {
  id: number;
  category: 'tipo' | 'localizacao' | 'situacao' | string;
  name: string;
  created_at: string;
  requires_serial_number?: boolean;
  useful_life_months?: number | null;
  residual_value_rate?: number | string;
  building?: string;
  floor?: string;
  sector?: string;
  room_number?: string | null;
}

export interface Equipment {
  id: number;
  serial_number: string;
  patrimony_number?: string | null;
  hostname?: string | null;
  description: string;
  brand?: string | null;
  model?: string | null;
  product_number?: string | null;
  category_id?: number;
  category?: Category | null;
  equipment_type_id?: number;
  equipment_type: string | { id: number; name: string };
  location_id?: number;
  sector_id?: number;
  sector?: { id: number; name: string } | null;
  location?: string | Location | { id: number; name: string };
  assigned_user_id?: number | null;
  assigned_user?: UserSummary | null;
  purchase_cost?: number | string | null;
  purchase_date?: string | null;
  status_id?: number;
  status: AssetStatus | { id: number; name: string };
  specs?: Record<string, any>;
  ip_address?: string | null;
  mac_address?: string | null;
  printer_identifier?: string | null;
  windows_key?: string | null;
  windows_product_key?: string | null;
  last_maintenance_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at?: string;
  movements: EquipmentMovement[];
  maintenances: EquipmentMaintenance[];
  patrimony_history?: PatrimonyHistory[];
}

export type Asset = Equipment;

export interface EquipmentCreatePayload {
  serial_number?: string | null;
  patrimony_number?: string | null;
  hostname?: string | null;
  description?: string | null;
  brand?: string | null;
  model?: string | null;
  product_number?: string | null;
  category_id?: number;
  equipment_type?: string;
  equipment_type_id?: number;
  location_id?: number;
  location?: string;
  sector_id?: number;
  assigned_user_id?: number | null;
  purchase_cost?: number | string | null;
  purchase_date?: string | null;
  status?: AssetStatus;
  status_id?: number;
  specs?: Record<string, any>;
  ip_address?: string | null;
  mac_address?: string | null;
  printer_identifier?: string | null;
  windows_key?: string | null;
  windows_product_key?: string | null;
  last_maintenance_at?: string | null;
  notes?: string | null;
}

export interface EquipmentListResponse {
  items: Equipment[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface EquipmentFilterParams {
  page?: number;
  limit?: number;
  category_id?: number;
  location_id?: number;
  type?: string | string[];
  location?: string | string[];
  status?: string | string[];
  patrimony_number?: string | string[];
  serial_number?: string | string[];
  product_number?: string | string[];
  search?: string;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}
