"""Aplicação principal do FastAPI - SisPatrimonio."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.routes import router as auth_router
from src.api.dashboard_routes import router as dashboard_router
from src.api.import_routes import router as import_router
from src.api.category_routes import router as category_router
from src.api.location_routes import router as location_router
from src.api.asset_routes import router as asset_router
from src.api.movement_routes import router as movement_router
from src.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de ciclo de vida da aplicação (migrações gerenciadas exclusivamente pelo Alembic)."""
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sistema de Gestão de Patrimônio e Suporte - SisPatrimonio",
    version="0.2.0",
    lifespan=lifespan,
)

# Inclui os roteadores canônicos da aplicação
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(import_router)
app.include_router(category_router)
app.include_router(location_router)
app.include_router(asset_router)
app.include_router(movement_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de verificação de saúde da aplicação."""
    return {"status": "ok", "app": settings.PROJECT_NAME}
