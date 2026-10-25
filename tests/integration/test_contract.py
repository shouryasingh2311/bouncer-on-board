"""
BOB Integration Test Suite — Acceptance Matrix Verification.

Asserts strictly against the Contract Addendum v1 in TEAM_PLAN.md Section 5.
Uses subprocess to execute BOB CLI against the local mock registry.
Tagged with markers: m1 (package gate), m2 (guards), m3 (scan), m4 (verify/ai), m5 (injection).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest
import urllib.request

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def run_bob(args: list[str], config_path: Path, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Execute bob CLI using either installed binary or python -m bob.cli."""
    env = dict(os.environ)
    env["BOB_CONFIG"] = str(config_path)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    bob_bin = shutil.which("bob")
    if bob_bin:
        cmd = [bob_bin] + args
    else:
        cmd = [sys.executable, "-m", "bob.cli"] + args

    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
        check=False,
    )


# =====================================================================
# Milestone 1: Package Gate (Acceptance Matrix Rows 1–8)
# =====================================================================

@pytest.mark.m1
def test_row_1_check_install_pypi_good(bob_config_path: Path) -> None:
    """Row 1: check-install pypi demo-good-lib -> exit 0, allow"""
    proc = run_bob(["check-install", "pypi", "demo-good-lib"], bob_config_path)
    assert proc.returncode == 0, f"Expected 0, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "BOB BLOCKED" not in proc.stderr


@pytest.mark.m1
def test_row_2_check_install_pypi_missing(bob_config_path: Path) -> None:
    """Row 2: check-install pypi demo-missing-lib -> exit 2, PKG-NOT-FOUND"""
    proc = run_bob(["check-install", "pypi", "demo-missing-lib"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "PKG-NOT-FOUND" in (proc.stderr + proc.stdout)


@pytest.mark.m1
def test_row_3_check_install_pypi_fresh_warn(bob_config_path: Path) -> None:
    """Row 3: check-install pypi demo-fresh-lib -> exit 0, BOB WARN PKG-TOO-NEW"""
    proc = run_bob(["check-install", "pypi", "demo-fresh-lib"], bob_config_path)
    assert proc.returncode == 0, f"Expected 0, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    combined = proc.stderr + proc.stdout
    assert "BOB WARN" in combined or "PKG-TOO-NEW" in combined


@pytest.mark.m1
def test_row_4_check_install_pypi_typosquat(bob_config_path: Path) -> None:
    """Row 4: check-install pypi reqeusts -> exit 2, PKG-TYPOSQUAT"""
    proc = run_bob(["check-install", "pypi", "reqeusts"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "PKG-TYPOSQUAT" in (proc.stderr + proc.stdout)


@pytest.mark.m1
def test_row_5_check_install_pypi_trope(bob_config_path: Path) -> None:
    """Row 5: check-install pypi requests-utils -> exit 2, PKG-LLM-TROPE"""
    proc = run_bob(["check-install", "pypi", "requests-utils"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "PKG-LLM-TROPE" in (proc.stderr + proc.stdout)


@pytest.mark.m1
def test_row_6_check_install_pypi_evil(bob_config_path: Path) -> None:
    """Row 6: check-install pypi demo-evil-lib -> exit 2, PKG-INSTALL-SCRIPT"""
    proc = run_bob(["check-install", "pypi", "demo-evil-lib"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "PKG-INSTALL-SCRIPT" in (proc.stderr + proc.stdout)


@pytest.mark.m1
def test_row_7_check_install_npm_evil(bob_config_path: Path) -> None:
    """Row 7: check-install npm demo-npm-evil -> exit 2, PKG-INSTALL-SCRIPT"""
    proc = run_bob(["check-install", "npm", "demo-npm-evil"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "PKG-INSTALL-SCRIPT" in (proc.stderr + proc.stdout)


@pytest.mark.m1
def test_row_8_check_install_npm_good(bob_config_path: Path) -> None:
    """Row 8: check-install npm demo-npm-good -> exit 0"""
    proc = run_bob(["check-install", "npm", "demo-npm-good"], bob_config_path)
    assert proc.returncode == 0, f"Expected 0, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "BOB BLOCKED" not in proc.stderr


# =====================================================================
# Milestone 2: Intercept & Guards (Acceptance Matrix Rows 9–13)
# =====================================================================

@pytest.mark.m2
def test_row_9_intercept_pip_missing(bob_config_path: Path) -> None:
    """Row 9: intercept --adapter generic --cmd 'pip install demo-missing-lib' -> exit 2"""
    proc = run_bob(["intercept", "--adapter", "generic", "--cmd", "pip install demo-missing-lib"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"


@pytest.mark.m2
def test_row_10_intercept_python_m_pip_typosquat(bob_config_path: Path) -> None:
    """Row 10: intercept ... --cmd 'python -m pip install reqeusts' -> exit 2"""
    proc = run_bob(["intercept", "--adapter", "generic", "--cmd", "python -m pip install reqeusts"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"


@pytest.mark.m2
def test_row_11_intercept_cat_env(bob_config_path: Path) -> None:
    """Row 11: intercept ... --cmd 'cat .env' -> exit 2, GUARD-SENSITIVE-PATH"""
    proc = run_bob(["intercept", "--adapter", "generic", "--cmd", "cat .env"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "GUARD-SENSITIVE-PATH" in (proc.stderr + proc.stdout)


@pytest.mark.m2
def test_row_12_intercept_cat_readme(bob_config_path: Path) -> None:
    """Row 12: intercept ... --cmd 'cat README.md' -> exit 0"""
    proc = run_bob(["intercept", "--adapter", "generic", "--cmd", "cat README.md"], bob_config_path)
    assert proc.returncode == 0, f"Expected 0, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"


@pytest.mark.m2
def test_row_13_intercept_self_protect(bob_config_path: Path) -> None:
    """Row 13: intercept ... --cmd 'bob allow demo-evil-lib' -> exit 2, GUARD-BOB-SELF-PROTECT"""
    proc = run_bob(["intercept", "--adapter", "generic", "--cmd", "bob allow demo-evil-lib"], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    assert "GUARD-BOB-SELF-PROTECT" in (proc.stderr + proc.stdout)


# =====================================================================
# Milestone 3: Pre-Deploy Scan (Acceptance Matrix Row 15)
# =====================================================================

@pytest.mark.m3
def test_row_15_scan_vulnerable_app_no_ai(bob_config_path: Path, tmp_path: Path) -> None:
    """Row 15: scan demo/vulnerable_app --no-ai --out-dir <tmp> -> exit 1, secret & code categories"""
    vuln_app = REPO_ROOT / "demo" / "vulnerable_app"
    proc = run_bob(["scan", str(vuln_app), "--no-ai", "--out-dir", str(tmp_path)], bob_config_path)
    assert proc.returncode == 1, f"Expected 1, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"

    report_json_path = tmp_path / "report.json"
    assert report_json_path.exists(), "report.json was not generated"

    with open(report_json_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    findings = report.get("findings", [])
    categories = {f.get("category") for f in findings}
    files = {str(Path(f.get("file", "")).name) for f in findings if f.get("file")}

    assert "secret" in categories, f"Expected 'secret' category in {categories}"
    assert "code" in categories, f"Expected 'code' category in {categories}"
    assert any("config.py" in fl for fl in files), f"Expected config.py in {files}"
    assert any("app.py" in fl for fl in files), f"Expected app.py in {files}"


# =====================================================================
# Milestone 4: Verify Command (Acceptance Matrix Row 16)
# =====================================================================

@pytest.mark.m4
def test_row_16_verify_after_fix(bob_config_path: Path, tmp_path: Path) -> None:
    """Row 16: Apply a fix to a copy of the app, then verify <fingerprint> -> exit 0"""
    # 1. Copy vulnerable_app to temp dir
    src_app = REPO_ROOT / "demo" / "vulnerable_app"
    test_app = tmp_path / "app_copy"
    shutil.copytree(src_app, test_app)

    # 2. Run scan to get findings & fingerprints
    out_dir = tmp_path / "bob_out"
    scan_proc = run_bob(["scan", str(test_app), "--no-ai", "--out-dir", str(out_dir)], bob_config_path)
    assert scan_proc.returncode == 1

    report_file = out_dir / "report.json"
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    findings = data.get("findings", [])
    assert findings, "No findings detected to verify"

    # Pick a finding in config.py
    target = next((f for f in findings if "config.py" in str(f.get("file", ""))), findings[0])
    fingerprint = target["fingerprint"][:8]

    # 3. Remediate: remove the secret line from the copy
    cfg_file = test_app / "config.py"
    cfg_file.write_text("# Clean config\nDEBUG = False\nDATABASE_NAME = 'demo.db'\n", encoding="utf-8")

    # 4. Run bob verify <fingerprint> in the test_app directory
    verify_proc = run_bob(["verify", fingerprint], bob_config_path, cwd=test_app)
    assert verify_proc.returncode == 0, f"Expected 0 (fixed), got {verify_proc.returncode}. Output: {verify_proc.stdout} {verify_proc.stderr}"


# =====================================================================
# Milestone 5: Injection Tripwire & AI Second Opinion (Rows 14 & 17)
# =====================================================================

@pytest.mark.m5
def test_row_14_guard_text_injection(bob_config_path: Path) -> None:
    """Row 14: guard-text demo/injection_fixture/README.md -> exit 2, INJ-010 and INJ-020"""
    inj_file = REPO_ROOT / "demo" / "injection_fixture" / "README.md"
    proc = run_bob(["guard-text", str(inj_file)], bob_config_path)
    assert proc.returncode == 2, f"Expected 2, got {proc.returncode}. Output: {proc.stdout} {proc.stderr}"
    combined = proc.stderr + proc.stdout
    assert "INJ-010" in combined
    assert "INJ-020" in combined


@pytest.mark.m5
def test_row_17_guard_text_ai_optional(bob_config_path: Path) -> None:
    """Row 17: (optional) guard-text demo/injection_fixture/README.md --ai -> exit 2 + model advisory"""
    # Check if Ollama is accessible
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1) as resp:
            ollama_up = (resp.status == 200)
    except Exception:
        ollama_up = False

    if not ollama_up:
        pytest.skip("Ollama is not responding on localhost:11434; skipping optional row 17")

    inj_file = REPO_ROOT / "demo" / "injection_fixture" / "README.md"
    proc = run_bob(["guard-text", str(inj_file), "--ai"], bob_config_path)
    assert proc.returncode == 2
    assert "AI" in (proc.stdout + proc.stderr)
