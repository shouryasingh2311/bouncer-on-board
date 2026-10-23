"""Unit tests for bob scan CLI and report generation."""

import json
from pathlib import Path
from typer.testing import CliRunner

from bob.cli import app
from bob.report.markdown import (
    calculate_risk_points,
    count_severities,
    generate_report_json,
    generate_report_markdown,
    ZERO_FINDINGS_MESSAGE,
)
from bob.models import Finding

runner = CliRunner()


def test_calculate_risk_points() -> None:
    counts = {"critical": 2, "high": 1, "medium": 1, "low": 2, "info": 5}
    # 2*40 + 1*15 + 1*5 + 2*1 = 80 + 15 + 5 + 2 = 102 -> capped at 100
    assert calculate_risk_points(counts) == 100

    low_counts = {"critical": 0, "high": 1, "medium": 1, "low": 0}
    # 0 + 15 + 5 + 0 = 20
    assert calculate_risk_points(low_counts) == 20


def test_scan_nonexistent_path() -> None:
    result = runner.invoke(app, ["scan", "this/path/does/not/exist/ever"])
    assert result.exit_code == 3


def test_scan_clean_directory(tmp_path: Path) -> None:
    clean_dir = tmp_path / "clean_project"
    clean_dir.mkdir()
    (clean_dir / "main.py").write_text("print('clean application')\n", encoding="utf-8")

    out_dir = tmp_path / "bob_out"
    result = runner.invoke(app, ["scan", str(clean_dir), "--no-ai", "--out-dir", str(out_dir)])
    assert result.exit_code == 0
    out_text = " ".join(result.output.split())
    assert ZERO_FINDINGS_MESSAGE in out_text

    # Verify report files
    md_file = out_dir / "report.md"
    json_file = out_dir / "report.json"
    assert md_file.is_file()
    assert json_file.is_file()

    md_content = md_file.read_text(encoding="utf-8")
    assert ZERO_FINDINGS_MESSAGE in md_content
    assert "## Limitations" in md_content

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["summary"]["risk_points"] == 0
    assert len(data["findings"]) == 0


def test_scan_vulnerable_directory_acceptance_row_15(tmp_path: Path) -> None:
    """Acceptance Matrix Row 15: scan returns exit 1 on critical/high issues.
    Findings include category secret in config.py and .env, category code in app.py.
    """
    app_dir = tmp_path / "vulnerable_app"
    app_dir.mkdir()

    (app_dir / "config.py").write_text("API_KEY = 'sk-1234567890abcdef1234567890'\n", encoding="utf-8")
    (app_dir / ".env").write_text("DB_PASS=supersecret\n", encoding="utf-8")
    (app_dir / "app.py").write_text("def run(req):\n    eval(req.get('code'))\n", encoding="utf-8")

    out_dir = tmp_path / "bob_out"
    result = runner.invoke(app, ["scan", str(app_dir), "--no-ai", "--out-dir", str(out_dir)])
    assert result.exit_code == 1
    assert "BOB SCAN GATE FAILED" in result.output

    json_file = out_dir / "report.json"
    assert json_file.is_file()

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["summary"]["risk_points"] > 0
    findings = data["findings"]
    assert len(findings) >= 3

    # Check categories and files
    secret_findings = [f for f in findings if f["category"] == "secret"]
    code_findings = [f for f in findings if f["category"] == "code"]

    assert any("config.py" in str(f.get("file")) for f in secret_findings)
    assert any(".env" in str(f.get("file")) for f in secret_findings)
    assert any("app.py" in str(f.get("file")) for f in code_findings)
