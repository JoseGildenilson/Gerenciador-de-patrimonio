"""Testes unitários para o módulo CLI de criação e povoamento do banco de dados."""

from unittest.mock import patch
from src import cli


def test_cli_create_db(capsys):
    """Testa execução de create_db."""
    exit_code = cli.create_db()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Criando tabelas e tipos do SisPatrimonio" in captured.out
    assert "Sucesso!" in captured.out


def test_cli_seed_db(capsys):
    """Testa execução de seed_db."""
    with patch("src.cli.seed_database") as mock_seed:
        exit_code = cli.seed_db()
        assert exit_code == 0
        mock_seed.assert_called_once()
    captured = capsys.readouterr()
    assert "Populando o banco de dados" in captured.out
    assert "Sucesso! Banco de dados populado com sucesso." in captured.out


def test_cli_main_help_options(capsys):
    """Testa chamada do CLI com flags de ajuda e lista vazia."""
    assert cli.main([]) == 0
    assert "Comandos disponíveis:" in capsys.readouterr().out

    assert cli.main(["-h"]) == 0
    assert "Comandos disponíveis:" in capsys.readouterr().out

    assert cli.main(["--help"]) == 0
    assert "Comandos disponíveis:" in capsys.readouterr().out


def test_cli_main_create_and_seed_commands():
    """Testa execução dos comandos create-db e seed-db via main()."""
    with patch("src.cli.create_db", return_value=0) as mock_create:
        assert cli.main(["create-db"]) == 0
        mock_create.assert_called_once()

    with patch("src.cli.seed_db", return_value=0) as mock_seed:
        assert cli.main(["seed-db"]) == 0
        mock_seed.assert_called_once()


def test_cli_main_unknown_command(capsys):
    """Testa tratamento de comando inválido/desconhecido."""
    exit_code = cli.main(["comando-invalido"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Comando desconhecido: 'comando-invalido'" in captured.out


def test_cli_main_sys_argv_fallback():
    """Testa fallback para sys.argv quando args=None."""
    with patch("sys.argv", ["cli.py", "--help"]):
        assert cli.main(None) == 0
