import axios from 'axios';
import {
  Category,
  Equipment,
  EquipmentCreatePayload,
  EquipmentFilterParams,
  EquipmentListResponse,
  EquipmentMaintenance,
  EquipmentMovement,
  EquipmentTag,
  Location,
  PatrimonyHistory,
  UserSummary,
} from '../types/equipment';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const equipmentHttpClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const formatLocationLabel = (loc?: Location | { id?: number; name?: string } | string | null): string => {
  if (!loc) return 'Não definido';
  if (typeof loc === 'string') return loc;
  if ('name' in loc && loc.name) return loc.name;
  if ('sector' in loc && loc.sector) {
    const parts = [loc.building, loc.floor, loc.sector, loc.room_number ? `Sala ${loc.room_number}` : null].filter(Boolean);
    return parts.length > 1 ? `${loc.sector} (${loc.building})` : loc.sector;
  }
  return 'Não definido';
};

export const normalizeStatusToEnum = (status?: any): 'disponivel' | 'em_uso' | 'em_manutencao' | 'baixado' => {
  const raw = typeof status === 'object' && status !== null ? status.name : status;
  const s = String(raw || '').trim().toLowerCase();
  if (s === 'disponivel' || s === 'em_uso' || s === 'em_manutencao' || s === 'baixado') {
    return s;
  }
  if (s.includes('manuten') || s.includes('repar') || s.includes('conserto')) return 'em_manutencao';
  if (s.includes('baixa') || s.includes('descart') || s.includes('inativ')) return 'baixado';
  if (s.includes('dispon') || s.includes('estoque') || s.includes('ocioso') || s.includes('reserva')) return 'disponivel';
  return 'em_uso';
};

export const normalizeMaintenanceTypeToEnum = (
  type?: any,
  typeId?: number
): 'preventiva' | 'corretiva' => {
  const raw = typeof type === 'object' && type !== null ? type.name : type;
  const s = String(raw || '').trim().toLowerCase();
  if (s.includes('corret')) return 'corretiva';
  if (s.includes('prevent')) return 'preventiva';
  if (typeId === 2) return 'corretiva';
  return 'preventiva';
};

export const normalizeAssetResponse = (item: any): Equipment => {
  if (!item) return item;
  const specs = item.specs && typeof item.specs === 'object' ? item.specs : {};
  const categoryName =
    item.equipment_type ??
    (item.category && typeof item.category === 'object' ? item.category.name : undefined) ??
    'Geral';
  const locationValue =
    item.location && typeof item.location === 'object' && 'sector' in item.location && !('name' in item.location)
      ? formatLocationLabel(item.location)
      : item.location ?? 'Não definido';

  const movements = Array.isArray(item.movements)
    ? item.movements.map((m: any) => ({
        ...m,
        equipment_id: m.equipment_id ?? m.asset_id ?? item.id,
        movement_date: m.movement_date ?? m.moved_at ?? m.created_at,
        origin_location: m.origin_location ?? (m.origin_location_id ? `Local #${m.origin_location_id}` : 'Origem'),
        destination_location:
          m.destination_location ??
          (m.dest_location_id === null
            ? 'Baixa Patrimonial'
            : m.dest_location_id
            ? `Local #${m.dest_location_id}`
            : 'Destino'),
      }))
    : [];

  const maintenances = Array.isArray(item.maintenances)
    ? item.maintenances.map((mt: any) => ({
        ...mt,
        equipment_id: mt.equipment_id ?? mt.asset_id ?? item.id,
        maintenance_date: mt.maintenance_date ?? mt.started_at ?? mt.created_at,
        notes: mt.notes ?? mt.service_provider ?? null,
      }))
    : [];

  return {
    ...item,
    serial_number: item.serial_number ?? '',
    equipment_type: categoryName,
    equipment_type_id: item.equipment_type_id ?? item.category_id,
    location: locationValue,
    sector_id: item.sector_id ?? item.location_id,
    hostname: item.hostname ?? specs.hostname ?? null,
    windows_key: item.windows_key ?? specs.windows_key ?? null,
    notes: item.notes ?? specs.notes ?? null,
    product_number: item.product_number ?? item.model ?? null,
    movements,
    maintenances,
    patrimony_history: Array.isArray(item.patrimony_history) ? item.patrimony_history : [],
  };
};

const CANONICAL_STATUS_TAGS: EquipmentTag[] = [
  { id: 1001, category: 'situacao', name: 'disponivel', created_at: '2026-01-01T00:00:00Z' },
  { id: 1002, category: 'situacao', name: 'em_uso', created_at: '2026-01-01T00:00:00Z' },
  { id: 1003, category: 'situacao', name: 'em_manutencao', created_at: '2026-01-01T00:00:00Z' },
  { id: 1004, category: 'situacao', name: 'baixado', created_at: '2026-01-01T00:00:00Z' },
];

const CANONICAL_MAINTENANCE_TAGS: EquipmentTag[] = [
  { id: 1, category: 'tipo_manutencao', name: 'preventiva', created_at: '2026-01-01T00:00:00Z' },
  { id: 2, category: 'tipo_manutencao', name: 'corretiva', created_at: '2026-01-01T00:00:00Z' },
];

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const REFERENCE_CACHE_TTL = 5 * 60 * 1000; // 5 minutos de TTL

let categoriesCache: CacheEntry<Category[]> | null = null;
let locationsCache: CacheEntry<Location[]> | null = null;
let categoriesInFlight: Promise<Category[]> | null = null;
let locationsInFlight: Promise<Location[]> | null = null;

export const invalidateReferenceCache = (type?: 'categories' | 'locations'): void => {
  if (!type || type === 'categories') {
    categoriesCache = null;
    categoriesInFlight = null;
  }
  if (!type || type === 'locations') {
    locationsCache = null;
    locationsInFlight = null;
  }
};

export const equipmentApi = {
  invalidateCache: invalidateReferenceCache,
  getEquipments: async (params?: EquipmentFilterParams): Promise<EquipmentListResponse> => {
    const queryParams: Record<string, any> = { ...params };
    if (Array.isArray(queryParams.status) && queryParams.status.length > 0) {
      queryParams.status = normalizeStatusToEnum(queryParams.status[0]);
    } else if (typeof queryParams.status === 'string' && queryParams.status) {
      queryParams.status = normalizeStatusToEnum(queryParams.status);
    }

    const response = await equipmentHttpClient.get<EquipmentListResponse>('/assets', {
      params: queryParams,
      paramsSerializer: {
        indexes: null,
      },
    });
    const data = response.data;
    return {
      ...data,
      items: Array.isArray(data?.items) ? data.items.map(normalizeAssetResponse) : [],
    };
  },

  getEquipmentDetail: async (id: number): Promise<Equipment> => {
    const response = await equipmentHttpClient.get<Equipment>(`/assets/${id}`);
    return normalizeAssetResponse(response.data);
  },

  createEquipment: async (payload: EquipmentCreatePayload): Promise<Equipment> => {
    const specs: Record<string, any> = { ...(payload.specs || {}) };
    if (payload.hostname) specs.hostname = payload.hostname;
    if (payload.windows_key || payload.windows_product_key) {
      specs.windows_key = payload.windows_key || payload.windows_product_key;
    }
    if (payload.notes) specs.notes = payload.notes;
    if (payload.ip_address) specs.ip_address = payload.ip_address;
    if (payload.mac_address) specs.mac_address = payload.mac_address;

    const canonicalPayload = {
      patrimony_number: payload.patrimony_number || payload.serial_number || `PAT-${Date.now()}`,
      serial_number: payload.serial_number || null,
      description: payload.description || 'Equipamento',
      category_id: payload.category_id ?? payload.equipment_type_id ?? 1,
      location_id: payload.location_id ?? payload.sector_id ?? 1,
      assigned_user_id: payload.assigned_user_id ?? null,
      brand: payload.brand || 'Genérico',
      model: payload.model ?? payload.product_number ?? null,
      purchase_cost: payload.purchase_cost ?? null,
      purchase_date: payload.purchase_date ?? null,
      status: normalizeStatusToEnum(payload.status),
      specs,
    };

    const response = await equipmentHttpClient.post<Equipment>('/assets', canonicalPayload);
    return normalizeAssetResponse(response.data);
  },

  updateEquipment: async (id: number, payload: Partial<EquipmentCreatePayload>): Promise<Equipment> => {
    const updateBody: Record<string, any> = {};
    if (payload.description !== undefined) updateBody.description = payload.description;
    if (payload.serial_number !== undefined) updateBody.serial_number = payload.serial_number;
    if (payload.brand !== undefined) updateBody.brand = payload.brand || 'Genérico';
    if (payload.model !== undefined || payload.product_number !== undefined) {
      updateBody.model = payload.model ?? payload.product_number ?? null;
    }
    if (payload.category_id !== undefined || payload.equipment_type_id !== undefined) {
      updateBody.category_id = payload.category_id ?? payload.equipment_type_id;
    }
    if (payload.location_id !== undefined || payload.sector_id !== undefined) {
      updateBody.location_id = payload.location_id ?? payload.sector_id;
    }
    if (payload.assigned_user_id !== undefined) {
      updateBody.assigned_user_id = payload.assigned_user_id;
    }
    if (payload.purchase_cost !== undefined) updateBody.purchase_cost = payload.purchase_cost;
    if (payload.purchase_date !== undefined) updateBody.purchase_date = payload.purchase_date;
    if (payload.status !== undefined) updateBody.status = normalizeStatusToEnum(payload.status);

    if (
      payload.specs !== undefined ||
      payload.hostname !== undefined ||
      payload.windows_key !== undefined ||
      payload.notes !== undefined
    ) {
      const specs: Record<string, any> = { ...(payload.specs || {}) };
      if (payload.hostname !== undefined) specs.hostname = payload.hostname;
      if (payload.windows_key !== undefined) specs.windows_key = payload.windows_key;
      if (payload.notes !== undefined) specs.notes = payload.notes;
      updateBody.specs = specs;
    }

    const response = await equipmentHttpClient.put<Equipment>(`/assets/${id}`, updateBody);
    return normalizeAssetResponse(response.data);
  },

  renumberPatrimony: async (
    id: number,
    payload: { new_patrimony_number: string; reason: string }
  ): Promise<PatrimonyHistory> => {
    const response = await equipmentHttpClient.post<PatrimonyHistory>(
      `/assets/${id}/renumber`,
      payload
    );
    return response.data;
  },

  acceptCustodyTerm: async (movementId: number): Promise<EquipmentMovement> => {
    const response = await equipmentHttpClient.post<EquipmentMovement>(
      `/movements/${movementId}/accept-term`
    );
    return response.data;
  },

  getUsers: async (): Promise<UserSummary[]> => {
    const response = await equipmentHttpClient.get<UserSummary[]>('/users');
    return response.data;
  },

  getCategories: async (options?: { forceRefresh?: boolean }): Promise<Category[]> => {
    const now = Date.now();
    if (!options?.forceRefresh && categoriesCache && now - categoriesCache.timestamp < REFERENCE_CACHE_TTL) {
      return categoriesCache.data;
    }
    if (!options?.forceRefresh && categoriesInFlight) {
      return categoriesInFlight;
    }

    categoriesInFlight = equipmentHttpClient
      .get<Category[]>('/categories')
      .then((response) => {
        categoriesCache = { data: response.data, timestamp: Date.now() };
        categoriesInFlight = null;
        return response.data;
      })
      .catch((err) => {
        categoriesInFlight = null;
        throw err;
      });

    return categoriesInFlight;
  },

  getLocations: async (options?: { forceRefresh?: boolean }): Promise<Location[]> => {
    const now = Date.now();
    if (!options?.forceRefresh && locationsCache && now - locationsCache.timestamp < REFERENCE_CACHE_TTL) {
      return locationsCache.data;
    }
    if (!options?.forceRefresh && locationsInFlight) {
      return locationsInFlight;
    }

    locationsInFlight = equipmentHttpClient
      .get<Location[]>('/locations')
      .then((response) => {
        locationsCache = { data: response.data, timestamp: Date.now() };
        locationsInFlight = null;
        return response.data;
      })
      .catch((err) => {
        locationsInFlight = null;
        throw err;
      });

    return locationsInFlight;
  },

  getTags: async (category?: string, options?: { forceRefresh?: boolean }): Promise<EquipmentTag[]> => {
    if (category === 'tipo_manutencao') {
      return CANONICAL_MAINTENANCE_TAGS;
    }
    if (category === 'situacao') {
      return CANONICAL_STATUS_TAGS;
    }

    const results: EquipmentTag[] = [];
    if (!category || category === 'tipo') {
      const catData = await equipmentApi.getCategories(options);
      const cats = Array.isArray(catData) ? catData : [];
      cats.forEach((c: any) => {
        results.push({
          id: c.id,
          category: c.category || 'tipo',
          name: c.name,
          requires_serial_number: c.requires_serial_number,
          useful_life_months: c.useful_life_months,
          residual_value_rate: c.residual_value_rate,
          created_at: c.created_at || '2026-01-01T00:00:00Z',
        });
      });
    }

    if (!category || category === 'localizacao') {
      const locData = await equipmentApi.getLocations(options);
      const locs = Array.isArray(locData) ? locData : [];
      locs.forEach((l: any) => {
        results.push({
          id: l.id,
          category: l.category || 'localizacao',
          name: l.name || l.sector || formatLocationLabel(l),
          building: l.building,
          floor: l.floor,
          sector: l.sector,
          room_number: l.room_number,
          created_at: l.created_at || '2026-01-01T00:00:00Z',
        });
      });
    }

    if (!category) {
      results.push(...CANONICAL_STATUS_TAGS);
    }

    return results;
  },

  createTag: async (
    category: string,
    name: string,
    extra?: {
      requires_serial_number?: boolean;
      useful_life_months?: number | null;
      residual_value_rate?: number;
      building?: string;
      floor?: string;
      room_number?: string | null;
    }
  ): Promise<EquipmentTag> => {
    if (category === 'localizacao') {
      const response = await equipmentHttpClient.post<Location>('/locations', {
        building: extra?.building || 'Prédio Principal',
        floor: extra?.floor || 'Térreo',
        sector: name,
        room_number: extra?.room_number ?? null,
      });
      invalidateReferenceCache('locations');
      const loc = response.data;
      return {
        id: loc.id,
        category: 'localizacao',
        name: loc.name || loc.sector || name,
        building: loc.building,
        floor: loc.floor,
        sector: loc.sector,
        room_number: loc.room_number,
        created_at: loc.created_at || new Date().toISOString(),
      };
    }

    if (category === 'situacao') {
      return {
        id: Date.now(),
        category: 'situacao',
        name: normalizeStatusToEnum(name),
        created_at: new Date().toISOString(),
      };
    }

    const response = await equipmentHttpClient.post<Category>('/categories', {
      name,
      requires_serial_number: extra?.requires_serial_number ?? false,
      useful_life_months: extra?.useful_life_months ?? 60,
      residual_value_rate: extra?.residual_value_rate ?? 10,
    });
    invalidateReferenceCache('categories');
    const cat = response.data;
    return {
      id: cat.id,
      category: 'tipo',
      name: cat.name || name,
      requires_serial_number: cat.requires_serial_number,
      useful_life_months: cat.useful_life_months,
      residual_value_rate: cat.residual_value_rate,
      created_at: cat.created_at || new Date().toISOString(),
    };
  },

  updateTag: async (id: number, name: string, category: string = 'tipo'): Promise<EquipmentTag> => {
    if (category === 'localizacao') {
      const response = await equipmentHttpClient.put<Location>(`/locations/${id}`, {
        sector: name,
      });
      invalidateReferenceCache('locations');
      const loc = response.data;
      return {
        id: loc.id,
        category: 'localizacao',
        name: loc.name || loc.sector || name,
        created_at: loc.created_at || new Date().toISOString(),
      };
    }

    const response = await equipmentHttpClient.put<Category>(`/categories/${id}`, { name });
    invalidateReferenceCache('categories');
    const cat = response.data;
    return {
      id: cat.id,
      category: 'tipo',
      name: cat.name || name,
      created_at: cat.created_at || new Date().toISOString(),
    };
  },

  deleteTag: async (id: number, category: string = 'tipo'): Promise<{ message: string }> => {
    const endpoint = category === 'localizacao' ? `/locations/${id}` : `/categories/${id}`;
    const response = await equipmentHttpClient.delete<{ message?: string }>(endpoint);
    invalidateReferenceCache(category === 'localizacao' ? 'locations' : 'categories');
    return {
      message: response.data?.message || 'Tag excluída com sucesso.',
    };
  },

  recordMovement: async (
    equipmentId: number,
    payload: {
      origin_location_id?: number;
      dest_location_id?: number | null;
      origin_sector_id?: number;
      destination_sector_id?: number | null;
      origin_location?: string;
      destination_location?: string;
      from_user_id?: number | null;
      to_user_id?: number | null;
      movement_date?: string;
      notes?: string;
    }
  ): Promise<EquipmentMovement> => {
    const originId = payload.origin_location_id ?? payload.origin_sector_id ?? 1;
    const destId =
      payload.dest_location_id !== undefined
        ? payload.dest_location_id
        : payload.destination_sector_id !== undefined
        ? payload.destination_sector_id
        : 1;

    const response = await equipmentHttpClient.post<EquipmentMovement>(
      `/assets/${equipmentId}/movements`,
      {
        origin_location_id: originId,
        dest_location_id: destId,
        from_user_id: payload.from_user_id ?? null,
        to_user_id: payload.to_user_id ?? null,
        notes: payload.notes,
      }
    );
    return response.data;
  },

  recordMaintenance: async (
    equipmentId: number,
    payload: {
      maintenance_type_id?: number;
      started_at?: string;
      maintenance_date?: string;
      maintenance_type?: string;
      service_provider?: string | null;
      cost?: number | string;
      description: string;
      notes?: string;
    }
  ): Promise<EquipmentMaintenance> => {
    const response = await equipmentHttpClient.post<EquipmentMaintenance>(
      `/assets/${equipmentId}/maintenances`,
      {
        maintenance_type: normalizeMaintenanceTypeToEnum(
          payload.maintenance_type,
          payload.maintenance_type_id
        ),
        service_provider: payload.service_provider ?? payload.notes ?? null,
        description: payload.description,
        cost: payload.cost ?? 0,
        maintenance_date: payload.maintenance_date ?? payload.started_at,
      }
    );
    return response.data;
  },

  updateMaintenance: async (
    equipmentId: number,
    maintenanceId: number,
    payload: {
      maintenance_type_id?: number;
      started_at?: string;
      completed_at?: string | null;
      maintenance_date?: string;
      maintenance_type?: string;
      service_provider?: string | null;
      cost?: number | string;
      description?: string;
      notes?: string;
    }
  ): Promise<EquipmentMaintenance> => {
    const body: Record<string, any> = {};
    if (payload.maintenance_type !== undefined || payload.maintenance_type_id !== undefined) {
      body.maintenance_type = normalizeMaintenanceTypeToEnum(
        payload.maintenance_type,
        payload.maintenance_type_id
      );
    }
    if (payload.description !== undefined) body.description = payload.description;
    if (payload.maintenance_date !== undefined || payload.started_at !== undefined) {
      body.maintenance_date = payload.maintenance_date ?? payload.started_at;
    }
    if (payload.service_provider !== undefined || payload.notes !== undefined) {
      body.service_provider = payload.service_provider ?? payload.notes ?? null;
    }
    if (payload.cost !== undefined) body.cost = payload.cost;

    const response = await equipmentHttpClient.put<EquipmentMaintenance>(
      `/assets/${equipmentId}/maintenances/${maintenanceId}`,
      body
    );
    return response.data;
  },

  deleteMaintenance: async (
    equipmentId: number,
    maintenanceId: number
  ): Promise<{ message: string }> => {
    const response = await equipmentHttpClient.delete<{ message?: string }>(
      `/assets/${equipmentId}/maintenances/${maintenanceId}`
    );
    return {
      message: response.data?.message || 'Manutenção excluída com sucesso.',
    };
  },

  getSuggestions: async (
    field: string,
    prefix: string,
    limit: number = 10
  ): Promise<string[]> => {
    const response = await equipmentHttpClient.get<string[]>('/assets/suggestions', {
      params: { field, prefix, limit },
    });
    return response.data;
  },

  exportEquipments: async (
    params?: Omit<EquipmentFilterParams, 'page' | 'limit'>
  ): Promise<{ data: Blob; filename: string }> => {
    const response = await equipmentHttpClient.get('/assets/export', {
      params,
      responseType: 'blob',
      paramsSerializer: {
        indexes: null,
      },
    });

    let filename = 'patrimonio_export.xlsx';
    const disposition = response.headers['content-disposition'];
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }

    return { data: response.data, filename };
  },
};
