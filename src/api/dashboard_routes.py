"""Rotas da API de Dashboard."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user
from src.core.database import get_db
from src.domain.models import User
from src.domain.schemas import DashboardMetricsResponse
from src.use_cases.get_dashboard_metrics import GetDashboardMetricsUseCase

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get(
    "/metrics",
    response_model=DashboardMetricsResponse,
    status_code=status.HTTP_200_OK,
)
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Endpoint HTTP para recuperar os dados e indicadores do Dashboard."""
    use_case = GetDashboardMetricsUseCase(db)
    return use_case.execute(user_id=current_user.id, role=current_user.role)
