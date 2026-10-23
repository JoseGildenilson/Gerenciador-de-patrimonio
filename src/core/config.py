"""Módulo de configurações centrais da aplicação."""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Configurações da aplicação."""

    PROJECT_NAME: str = "Gestão de Patrimônio e Suporte"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-1234567890")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres@localhost:5432/comunica_patrimonio"
    )
    RATE_LIMIT_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_WINDOW_MINUTES: int = 15

    def __init__(self, **data):
        super().__init__(**data)
        if self.ENVIRONMENT.lower() == "production":
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == "super-secret-key-change-in-production-1234567890"
            ):
                raise RuntimeError(
                    "A variável de ambiente SECRET_KEY deve ser configurada obrigatoriamente em ambiente de produção."
                )


settings = Settings()
