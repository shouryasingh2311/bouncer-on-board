"""Parallel runner for built-in tripwires and optional external scanners."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import List, Optional, Tuple

from bob.config import Config
from bob.models import Finding
from bob.pkg.osv import query_osv
from bob.scan.builtin import scan_directory_builtin
from bob.scan.dedupe import deduplicate_findings, load_bobignore_patterns
from bob.scan.sarif import parse_sarif_content, parse_sarif_file


def run_gitleaks_scanner(target_dir: Path) -> Tuple[List[Finding], bool]:
    """Run gitleaks if available, returning (findings, ran_successfully)."""
    if not shutil.which("gitleaks"):
        return [], False

    with tempfile.TemporaryDirectory() as tmp_dir:
        sarif_out = Path(tmp_dir) / "gitleaks.sarif"
        cmd = [
            "gitleaks",
            "dir",
            str(target_dir),
            "--report-format",
            "sarif",
            "--report-path",
            str(sarif_out),
            "--no-git",
        ]
        try:
            subprocess.run(
                cmd,
                capture_output=True,
                timeout=15,
                check=False,
            )
            if sarif_out.is_file():
                return parse_sarif_file(sarif_out, default_source="gitleaks"), True
        except Exception:
            return [], False

    return [], False


def run_semgrep_scanner(target_dir: Path) -> Tuple[List[Finding], bool]:
    """Run semgrep if available, returning (findings, ran_successfully)."""
    if not shutil.which("semgrep"):
        return [], False

    cmd = [
        "semgrep",
        "scan",
        "--sarif",
        "--config",
        "auto",
        str(target_dir),
    ]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            timeout=20,
            check=False,
            text=True,
        )
        if res.stdout:
            sarif_data = json.loads(res.stdout)
            return parse_sarif_content(sarif_data, default_source="semgrep"), True
    except Exception:
        return [], False

    return [], False


def run_all_scanners(
    target_dir: Path, config: Config
) -> Tuple[List[Finding], List[str], List[str]]:
    """Run all available scanners in parallel, deduplicate, and return summary."""
    tools_run: List[str] = []
    tools_skipped: List[str] = []
    raw_findings: List[Finding] = []

    # 1. Built-in tripwire scanner always runs
    tools_run.append("bob-builtin")
    raw_findings.extend(scan_directory_builtin(target_dir))

    # 2. Parallel run for external scanners
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_gitleaks = executor.submit(run_gitleaks_scanner, target_dir)
        future_semgrep = executor.submit(run_semgrep_scanner, target_dir)

        gitleaks_findings, gitleaks_ran = future_gitleaks.result()
        if gitleaks_ran:
            tools_run.append("gitleaks")
            raw_findings.extend(gitleaks_findings)
        else:
            tools_skipped.append("gitleaks")

        semgrep_findings, semgrep_ran = future_semgrep.result()
        if semgrep_ran:
            tools_run.append("semgrep")
            raw_findings.extend(semgrep_findings)
        else:
            tools_skipped.append("semgrep")

    # 3. Deduplicate and apply .bobignore
    ignore_patterns = load_bobignore_patterns(target_dir)
    deduped = deduplicate_findings(raw_findings, ignore_patterns)

    return deduped, tools_run, tools_skipped
