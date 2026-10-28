"""Script para popular o banco de dados com massa de testes visuais do SisPatrimonio."""

from src.infrastructure.seed import seed_database


def seed_rich_equipments():
    """Popula banco com dados para testes visuais."""
    seed_database()


seed_rich_assets = seed_rich_equipments


if __name__ == "__main__":  # pragma: no cover
    seed_rich_equipments()
