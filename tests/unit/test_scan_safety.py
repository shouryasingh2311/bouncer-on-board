"""Unit tests for scan home directory guard and system dir skips."""

from __future__ import annotations

from pathlib import Path
from typer.testing import CliRunner

from bob.cli import app

runner = CliRunner()


def test_scan_refuses_home_directory():
    home_dir = str(Path.home())
    result = runner.invoke(app, ["scan", home_dir])
    assert result.exit_code == 2
    assert "refusing to scan user home or root directory" in result.output.lower()
    assert "please run bob inside your project directory" in result.output.lower()
