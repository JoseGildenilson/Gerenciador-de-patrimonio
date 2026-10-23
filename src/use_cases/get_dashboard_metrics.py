"""Caso de uso para consulta das métricas patrimoniais do Dashboard."""

from sqlalchemy.orm import Session
from src.domain.schemas import DashboardMetricsResponse
from src.infrastructure.repositories import DashboardRepository


class GetDashboardMetricsUseCase:
    """Caso de uso para obter indicadores consolidados do patrimônio para o Dashboard."""

    def __init__(self, db: Session):
        self.db = db
        self.dashboard_repo = DashboardRepository(db)

    def execute(
        self, user_id: int | None = None, role: str = "tecnico"
    ) -> DashboardMetricsResponse:
        """Executa a consulta de métricas patrimoniais consolidadas."""
        metrics = self.dashboard_repo.get_metrics()
        return DashboardMetricsResponse(
            equipments_total=metrics["equipments_total"],
            equipments_in_maintenance=metrics["equipments_in_maintenance"],
            equipments_in_use=metrics["equipments_in_use"],
            equipments_idle=metrics["equipments_idle"],
            by_status=metrics["by_status"],
            by_type=metrics["by_type"],
            by_sector=metrics["by_sector"],
        )
