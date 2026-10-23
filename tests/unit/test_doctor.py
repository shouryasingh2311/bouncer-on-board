"""Unit tests for BOB CLI doctor and version commands."""

from typer.testing import CliRunner

from bob import __version__
from bob.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"bob version {__version__}" in result.stdout


def test_cli_doctor_runs() -> None:
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "BOB System Diagnostics" in result.stdout
    assert "Python" in result.stdout
    assert "Ollama Service" in result.stdout
