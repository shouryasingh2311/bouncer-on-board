"""Unit tests for human allowlist command."""

from pathlib import Path
from typer.testing import CliRunner

from bob.cli import app

runner = CliRunner()


def test_bob_allow_adds_package(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["allow", "trusted-internal-lib"])
    assert result.exit_code == 0
    assert "Allowlisted package" in result.output

    allowlist_file = tmp_path / ".bob" / "allowlist.yaml"
    assert allowlist_file.is_file()
    content = allowlist_file.read_text(encoding="utf-8")
    assert "trusted-internal-lib" in content

    # Running again should acknowledge existing
    result_dup = runner.invoke(app, ["allow", "trusted-internal-lib"])
    assert result_dup.exit_code == 0
    assert "already allowlisted" in result_dup.output
