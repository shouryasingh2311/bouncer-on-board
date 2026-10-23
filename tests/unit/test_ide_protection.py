"""Unit tests for IDE and agent workspace protection."""

import json
from pathlib import Path
from typer.testing import CliRunner

from bob.adapters.ide import (
    configure_antigravity,
    configure_claude_code,
    configure_vscode_cursor,
    protect_workspace,
)
from bob.cli import app

runner = CliRunner()


def test_configure_antigravity(tmp_path: Path) -> None:
    hook_file = configure_antigravity(tmp_path)
    assert hook_file.is_file()
    data = json.loads(hook_file.read_text(encoding="utf-8"))
    assert "PreToolUse" in data
    assert data["PreToolUse"][0]["command"] == "bob"


def test_configure_vscode_cursor(tmp_path: Path) -> None:
    shims_dir = tmp_path / "shims"
    settings_file, shims = configure_vscode_cursor(tmp_path, shims_dir=shims_dir)
    assert settings_file.is_file()
    assert len(shims) >= 4

    data = json.loads(settings_file.read_text(encoding="utf-8"))
    assert "terminal.integrated.env.windows" in data
    assert "terminal.integrated.env.linux" in data
    assert str(shims_dir) in data["terminal.integrated.env.windows"]["PATH"] or str(shims_dir.as_posix()) in data["terminal.integrated.env.windows"]["PATH"]


def test_protect_workspace_all(tmp_path: Path) -> None:
    res = protect_workspace(tmp_path, "all")
    assert res["workspace"] == str(tmp_path.resolve())
    assert (tmp_path / ".agents" / "hooks.json").is_file()
    assert (tmp_path / ".vscode" / "settings.json").is_file()
    assert (tmp_path / ".bob" / "allowlist.yaml").is_file()


def test_cli_protect_command(tmp_path: Path) -> None:
    res = runner.invoke(app, ["protect", str(tmp_path), "--ide", "all"])
    assert res.exit_code == 0
    assert "Protected workspace" in res.output
    assert (tmp_path / ".agents" / "hooks.json").is_file()
