export interface DashboardMetrics {
  assets_total?: number;
  assets_in_use?: number;
  assets_in_maintenance?: number;
  assets_available?: number;
  assets_decommissioned?: number;
  tickets_pending?: number;
  tickets_in_progress?: number;
  equipments_total?: number | null;
}
