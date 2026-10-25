"""Unit tests for ASCII banner and interactive setup wizard."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from bob.banner import BOB_BANNER_ASCII, BOB_BANNER_STYLED, print_banner
from bob.cli import app
from bob.config import Config, load_config, save_config
from bob.setup import run_setup_wizard

runner = CliRunner()


def test_ascii_banner_content() -> None:
    assert "____" in BOB_BANNER_ASCII
    assert "bouncer-on-board" in BOB_BANNER_ASCII
    assert "+---" in BOB_BANNER_ASCII  # Box border
    assert "Gate keeping" in BOB_BANNER_ASCII
    for line in BOB_BANNER_ASCII.splitlines():
        assert len(line) <= 80, f"Line too long: {len(line)} chars"
        for ch in line:
            assert ord(ch) <= 126 and (ord(ch) >= 32 or ch in "\r\n\t"), f"Non-ASCII char: {ch}"


def test_styled_banner_content() -> None:
    assert "█████████" in BOB_BANNER_STYLED
    assert "╚════════╝" in BOB_BANNER_STYLED


def test_print_banner_tty(monkeypatch) -> None:
    mock_console = MagicMock()
    # Force isatty to True
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    print_banner(mock_console)
    assert mock_console.print.called


def test_print_banner_non_tty(monkeypatch) -> None:
    mock_console = MagicMock()
    # Force isatty to False
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)
    print_banner(mock_console)
    assert not mock_console.print.called


def test_config_save_and_reload(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg = Config(
        model="gemma2:2b",
        ai_provider="ollama",
        api_key="sk-test-key",
    )
    save_config(cfg, cfg_file)

    loaded = load_config(cfg_file)
    assert loaded.model == "gemma2:2b"
    assert loaded.ai_provider == "ollama"
    assert loaded.api_key == "sk-test-key"


def test_setup_wizard_ide_native_choice(tmp_path: Path, monkeypatch) -> None:
    mock_console = MagicMock()
    cfg_path = tmp_path / "config.yaml"

    responses = iter(["1", "5"])
    monkeypatch.setattr("bob.setup.Prompt.ask", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr("bob.setup.load_config", lambda: Config())
    monkeypatch.setattr("bob.setup.save_config", lambda c: save_config(c, cfg_path))

    run_setup_wizard(mock_console)

    loaded = load_config(cfg_path)
    assert loaded.ai_provider == "ide_native"
    assert loaded.model == "ide_native"


def test_setup_wizard_deterministic_choice(tmp_path: Path, monkeypatch) -> None:
    mock_console = MagicMock()
    cfg_path = tmp_path / "config.yaml"

    responses = iter(["4", "5"])
    monkeypatch.setattr("bob.setup.Prompt.ask", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr("bob.setup.load_config", lambda: Config())
    monkeypatch.setattr("bob.setup.save_config", lambda c: save_config(c, cfg_path))

    run_setup_wizard(mock_console)

    loaded = load_config(cfg_path)
    assert loaded.ai_provider == "deterministic"
    assert loaded.model == "deterministic"


def test_setup_wizard_cloud_choice(tmp_path: Path, monkeypatch) -> None:
    mock_console = MagicMock()
    cfg_path = tmp_path / "config.yaml"

    responses = iter(["3", "gemini", "my-secret-key", "gemini-1.5-flash", "5"])
    monkeypatch.setattr("bob.setup.Prompt.ask", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr("bob.setup.load_config", lambda: Config())
    monkeypatch.setattr("bob.setup.save_config", lambda c: save_config(c, cfg_path))

    run_setup_wizard(mock_console)

    loaded = load_config(cfg_path)
    assert loaded.ai_provider == "gemini"
    assert loaded.api_key == "my-secret-key"
    assert loaded.model == "gemini-1.5-flash"


def test_cli_setup_help() -> None:
    result = runner.invoke(app, ["setup", "--help"])
    assert result.exit_code == 0
    assert "Interactive onboarding assistant" in result.output
