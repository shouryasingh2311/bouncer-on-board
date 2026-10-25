"""Unit tests for PATH shims and Antigravity hook adapter."""

from pathlib import Path
from typer.testing import CliRunner

from bob.adapters.ide import configure_antigravity_hook, get_hooks_config
from bob.adapters.shim import install_shims, uninstall_shims
from bob.cli import app

runner = CliRunner()


def test_install_and_uninstall_shims(tmp_path: Path) -> None:
    created = install_shims(tmp_path)
    assert len(created) >= 5
    cmd_files = list(tmp_path.glob("*.cmd"))
    assert len(cmd_files) >= 5

    pip_cmd = tmp_path / "pip.cmd"
    assert pip_cmd.is_file()
    content = pip_cmd.read_text(encoding="utf-8")
    assert "bob intercept --adapter generic --cmd" in content

    removed = uninstall_shims(tmp_path)
    assert removed >= 5
    assert not pip_cmd.is_file()


def test_shim_cli_commands(tmp_path: Path) -> None:
    result_install = runner.invoke(app, ["shim", "install", "--dest", str(tmp_path)])
    assert result_install.exit_code == 0
    assert "Installed" in result_install.output

    result_uninstall = runner.invoke(app, ["shim", "uninstall", "--dest", str(tmp_path)])
    assert result_uninstall.exit_code == 0
    assert "Uninstalled" in result_uninstall.output


def test_antigravity_hooks_config(tmp_path: Path) -> None:
    cfg = get_hooks_config()
    assert "PreToolUse" in cfg
    hook_entry = cfg["PreToolUse"][0]
    assert hook_entry["command"] == "bob"
    assert hook_entry["args"] == ["intercept", "--adapter", "antigravity"]

    hook_file = configure_antigravity_hook(tmp_path)
    assert hook_file.is_file()
    assert ".agents" in str(hook_file)
