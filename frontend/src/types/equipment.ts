export interface EquipmentMovement {
  id: number;
  equipment_id: number;
  origin_sector_id?: number;
  origin_sector?: { id: number; name: string } | null;
  origin_location?: string;
  destination_sector_id?: number;
  destination_sector?: { id: number; name: string } | null;
  destination_location?: string;
  movement_date: string;
  performed_by_user_id?: number;
  notes?: string | null;
  created_at: string;
}

export interface EquipmentMaintenance {
  id: number;
  equipment_id: number;
  maintenance_type_id?: number;
  maintenance_type?: string | { id: number; name: string };
  started_at?: string;
  completed_at?: string | null;
  maintenance_date?: string;
  description: string;
  notes?: string | null;
  created_at: string;
}

export interface EquipmentTag {
  id: number;
  category: 'tipo' | 'localizacao' | 'situacao' | string;
  name: string;
  created_at: string;
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
  equipment_type_id?: number;
  equipment_type: string | { id: number; name: string };
  sector_id?: number;
  sector?: { id: number; name: string };
  location?: string | { id: number; name: string };
  status_id?: number;
  status: string | { id: number; name: string };
  ip_address?: string | null;
  mac_address?: string | null;
  printer_identifier?: string | null;
  windows_key?: string | null;
  windows_product_key?: string | null;
  last_maintenance_at?: string | null;
  notes?: string | null;
  created_at: string;
  movements: EquipmentMovement[];
  maintenances: EquipmentMaintenance[];
}

export interface EquipmentCreatePayload {
  serial_number?: string | null;
  patrimony_number?: string | null;
  hostname?: string | null;
  description?: string | null;
  brand?: string | null;
  model?: string | null;
  product_number?: string | null;
  equipment_type?: string;
  equipment_type_id?: number;
  location?: string;
  sector_id?: number;
  status?: string;
  status_id?: number;
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
