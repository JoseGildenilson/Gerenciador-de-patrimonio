"""Módulo CLI para gerenciamento e povoamento do banco de dados."""

import sys
from sqlalchemy import inspect
from src.core.database import Base, engine
from src.infrastructure.seed import seed_database


def create_db() -> int:
    """Cria todas as tabelas e tipos do modelo de dados no banco de dados configurado."""
    print("Criando tabelas e tipos do SisPatrimonio no banco de dados...")
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Sucesso! {len(tables)} tabelas presentes no banco de dados.")
    return 0


def seed_db() -> int:
    """Popula o banco de dados com massa de dados de teste e entidades do SisPatrimonio."""
    print("Populando o banco de dados com dados iniciais do SisPatrimonio...")
    seed_database()
    print("Sucesso! Banco de dados populado com sucesso.")
    return 0


def main(args: list[str] | None = None) -> int:
    """Ponto de entrada unificado para execução dos comandos CLI."""
    cli_args = args if args is not None else sys.argv[1:]
    if not cli_args or cli_args[0] in ("-h", "--help"):
        print(
            "Uso: python -m src.cli [comando]\n\n"
            "Comandos disponíveis:\n"
            "  create-db    Cria tabelas no banco de dados\n"
            "  seed-db      Popula o banco de dados com dados iniciais\n"
        )
        return 0

    command = cli_args[0]
    if command == "create-db":
        return create_db()
    if command == "seed-db":
        return seed_db()

    print(f"Comando desconhecido: '{command}'. Use 'create-db' ou 'seed-db'.")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
