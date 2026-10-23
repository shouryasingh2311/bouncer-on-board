"""Unit tests for bob intercept command and Acceptance Matrix rows 9-13."""

from datetime import datetime, timedelta, timezone
from typer.testing import CliRunner

from bob.cli import app

runner = CliRunner()


def test_matrix_row_9_intercept_missing_package(monkeypatch) -> None:
    # Row 9: intercept --adapter generic --cmd "pip install demo-missing-lib" -> exit 2
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (404, {}))
    result = runner.invoke(app, ["intercept", "--adapter", "generic", "--cmd", "pip install demo-missing-lib"])
    assert result.exit_code == 2
    assert "BOB BLOCKED" in result.stderr
    assert "PKG-NOT-FOUND" in result.stderr


def test_matrix_row_10_intercept_m_pip_typosquat(monkeypatch) -> None:
    # Row 10: intercept ... --cmd "python -m pip install reqeusts" -> exit 2
    date_5d = datetime.now(timezone.utc) - timedelta(days=5)
    data = {
        "info": {},
        "releases": {"0.1.0": [{"upload_time_iso_8601": date_5d.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    result = runner.invoke(app, ["intercept", "--adapter", "generic", "--cmd", "python -m pip install reqeusts"])
    assert result.exit_code == 2
    assert "BOB BLOCKED" in result.stderr
    assert "PKG-TYPOSQUAT" in result.stderr


def test_matrix_row_11_intercept_cat_env() -> None:
    # Row 11: intercept ... --cmd "cat .env" -> exit 2, GUARD-SENSITIVE-PATH
    result = runner.invoke(app, ["intercept", "--adapter", "generic", "--cmd", "cat .env"])
    assert result.exit_code == 2
    assert "BOB BLOCKED" in result.stderr
    assert "GUARD-SENSITIVE-PATH" in result.stderr


def test_matrix_row_12_intercept_cat_readme() -> None:
    # Row 12: intercept ... --cmd "cat README.md" -> exit 0
    result = runner.invoke(app, ["intercept", "--adapter", "generic", "--cmd", "cat README.md"])
    assert result.exit_code == 0


def test_matrix_row_13_intercept_bob_allow() -> None:
    # Row 13: intercept ... --cmd "bob allow demo-evil-lib" -> exit 2, GUARD-BOB-SELF-PROTECT
    result = runner.invoke(app, ["intercept", "--adapter", "generic", "--cmd", "bob allow demo-evil-lib"])
    assert result.exit_code == 2
    assert "BOB BLOCKED" in result.stderr
    assert "GUARD-BOB-SELF-PROTECT" in result.stderr


def test_antigravity_adapter_json_block() -> None:
    # Antigravity adapter denies tool execution when command touches .env
    payload = '{"toolCall": {"name": "run_command", "args": {"CommandLine": "cat .env"}}}'
    result = runner.invoke(app, ["intercept", "--adapter", "antigravity"], input=payload)
    assert result.exit_code == 2
    assert '"decision": "deny"' in result.stdout
    assert "GUARD-SENSITIVE-PATH" in result.stdout


def test_antigravity_adapter_json_allow() -> None:
    # Antigravity adapter allows clean tool execution
    payload = '{"toolCall": {"name": "run_command", "args": {"CommandLine": "git status"}}}'
    result = runner.invoke(app, ["intercept", "--adapter", "antigravity"], input=payload)
    assert result.exit_code == 0
    assert '"decision": "allow"' in result.stdout
