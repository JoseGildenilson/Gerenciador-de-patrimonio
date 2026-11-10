"""Módulo de configurações centrais da aplicação."""

import os
from pydantic import BaseModel

if os.path.exists(".env"):  # pragma: no cover
    with open(".env", "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


class Settings(BaseModel):
    """Configurações da aplicação."""

    PROJECT_NAME: str = "Gerenciador de Patrimônio"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", os.getenv("ENV", "development"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production-1234567890")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/patrimonio_db"
    )
    RATE_LIMIT_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_WINDOW_MINUTES: int = 15
    LOG_SQL_STATEMENTS: bool = False

    def __init__(self, **data):
        super().__init__(**data)
        if "LOG_SQL_STATEMENTS" not in data:
            env_val = os.getenv("LOG_SQL_STATEMENTS")
            if env_val is not None:
                self.LOG_SQL_STATEMENTS = env_val.lower() in ("true", "1", "yes")
            else:
                self.LOG_SQL_STATEMENTS = self.ENVIRONMENT.lower() != "production"

        if self.ENVIRONMENT.lower() == "production":
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == "super-secret-key-change-in-production-1234567890"
            ):
                raise RuntimeError(
                    "A variável de ambiente SECRET_KEY deve ser configurada obrigatoriamente em ambiente de produção."
                )


settings = Settings()
