"""Unit tests for bob verify command (Acceptance Matrix Row 16)."""

import json
from pathlib import Path
from typer.testing import CliRunner

from bob.cli import app
from bob.models import Finding

runner = CliRunner()


def test_verify_missing_report(tmp_path: Path) -> None:
    result = runner.invoke(app, ["verify", "BOB-0001", "--report", str(tmp_path / "missing.json")])
    assert result.exit_code == 1
    assert "not found" in result.output.lower()


def test_verify_finding_not_in_report(tmp_path: Path) -> None:
    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps({"findings": []}), encoding="utf-8")

    result = runner.invoke(app, ["verify", "BOB-9999", "--report", str(report_file)])
    assert result.exit_code == 1
    assert "not found in report" in result.output.lower()


def test_verify_finding_still_present(tmp_path: Path) -> None:
    app_file = tmp_path / "config.py"
    app_file.write_text("API_KEY = 'sk-1234567890abcdef1234567890'\n", encoding="utf-8")

    f = Finding(
        id="BOB-0001",
        rule_id="BUILTIN-SECRET-API-KEY",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="OpenAI key hardcoded",
        file=str(app_file),
        line=1,
        evidence="sk-1234****",
    )

    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps({"findings": [f.to_dict()]}), encoding="utf-8")

    # Verify by ID
    result = runner.invoke(app, ["verify", "BOB-0001", "--report", str(report_file)])
    assert result.exit_code == 1
    assert "BOB VERIFY FAILED" in result.output


def test_verify_finding_fixed_acceptance_row_16(tmp_path: Path) -> None:
    """Acceptance Matrix Row 16: Apply a fix, then verify <fingerprint> returns exit 0."""
    app_file = tmp_path / "config.py"
    # The file has been patched to load key from environment!
    app_file.write_text("import os\nAPI_KEY = os.environ.get('OPENAI_API_KEY')\n", encoding="utf-8")

    f = Finding(
        id="BOB-0001",
        rule_id="BUILTIN-SECRET-API-KEY",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="OpenAI key hardcoded",
        file=str(app_file),
        line=1,
        evidence="sk-1234****",
    )

    report_file = tmp_path / "report.json"
    report_file.write_text(json.dumps({"findings": [f.to_dict()]}), encoding="utf-8")

    # Verify by 10-char fingerprint prefix
    prefix = f.fingerprint[:10]
    result = runner.invoke(app, ["verify", prefix, "--report", str(report_file)])
    assert result.exit_code == 0
    assert "BOB VERIFY PASSED" in result.output
