"""Roteador HTTP do FastAPI para Importação de Planilhas de Ativos."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from src.api.dependencies import require_tecnico_role
from src.core.database import get_db
from src.domain.models import User
from src.domain.schemas import (
    SpreadsheetImportPreviewResponse,
    SpreadsheetImportResultResponse,
)
from src.use_cases.import_spreadsheet_use_cases import (
    PreviewSpreadsheetUseCase,
    ExecuteSpreadsheetImportUseCase,
)

router = APIRouter(tags=["Importação de Ativos"])


@router.post("/api/v1/assets/import/preview", response_model=SpreadsheetImportPreviewResponse)
@router.post("/api/v1/equipments/import/preview", response_model=SpreadsheetImportPreviewResponse)
async def preview_spreadsheet(
    file: UploadFile = File(..., description="Arquivo de planilha (.xlsx ou .csv)"),
    current_user: User = Depends(require_tecnico_role),
):
    """
    Gera uma pré-visualização dos dados contidos na planilha enviada (Role: Técnico).
    Não realiza persistência no banco de dados.
    """
    try:
        content = await file.read()
        use_case = PreviewSpreadsheetUseCase()
        return use_case.execute(content, file.filename or "")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar a planilha: {str(exc)}",
        )


@router.post("/api/v1/assets/import/execute", response_model=SpreadsheetImportResultResponse)
@router.post("/api/v1/equipments/import/execute", response_model=SpreadsheetImportResultResponse)
async def execute_spreadsheet_import(
    file: UploadFile = File(..., description="Arquivo de planilha (.xlsx ou .csv)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tecnico_role),
):
    """
    Executa a importação transacional dos dados da planilha no banco de dados (Role: Técnico).
    Cria novos ativos, atualiza existentes (upsert), categorias e localizações.
    """
    try:
        content = await file.read()
        use_case = ExecuteSpreadsheetImportUseCase(db)
        return use_case.execute(content, file.filename or "")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao importar a planilha: {str(exc)}",
        )
