# ==========================================
# Multi-stage Dockerfile para Backend FastAPI
# ==========================================

# Estágio 1: Builder para compilação e resolução de dependências
FROM python:3.13-slim-bookworm AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Instala compiladores para dependências com extensões C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala o binário oficial do uv
COPY --from=ghcr.io/astral-sh/uv:0.6.5 /uv /uvx /bin/

# Copia arquivos de dependências
COPY pyproject.toml uv.lock ./

# Instala dependências do projeto no ambiente virtual /app/.venv
RUN uv sync --frozen --no-dev --no-cache

# ==========================================
# Estágio de Desenvolvimento (com ferramentas de dev e reload)
# ==========================================
FROM python:3.13-slim-bookworm AS development

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/alembic.ini

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==========================================
# Estágio de Produção (Enxuto, Seguro e Non-Root UID 10001)
# ==========================================
FROM python:3.13-slim-bookworm AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

WORKDIR /app

# Dependências mínimas de runtime (sem gcc, sem libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário e grupo de sistema não-privilegiados
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin --no-create-home appuser

# Copia o virtualenv compilado do builder
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv

# Copia o script de entrypoint e arquivos da aplicação
COPY --chown=appuser:appgroup entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup alembic/ /app/alembic/
COPY --chown=appuser:appgroup alembic.ini /app/alembic.ini

# Alterna para o usuário não-privilegiado
USER 10001

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
