"""Report generator for .bob/report.md and .bob/report.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from bob.models import Finding

ZERO_FINDINGS_MESSAGE = "0 known deterministic tripwires hit. This does not guarantee the absence of business-logic vulnerabilities."


def calculate_risk_points(counts: Dict[str, int]) -> int:
    """Calculate simple risk score: min(100, 40*critical + 15*high + 5*medium + 1*low)."""
    raw = (
        40 * counts.get("critical", 0)
        + 15 * counts.get("high", 0)
        + 5 * counts.get("medium", 0)
        + 1 * counts.get("low", 0)
    )
    return min(100, raw)


def count_severities(findings: List[Finding]) -> Dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        counts[f.severity.lower() if f.severity.lower() in counts else "info"] += 1
    return counts


def generate_report_json(
    findings: List[Finding],
    tools_run: List[str],
    tools_skipped: List[str],
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate structured dictionary matching report.json contract."""
    counts = count_severities(findings)
    risk_pts = calculate_risk_points(counts)

    return {
        "summary": {
            "counts_by_severity": counts,
            "tools_run": tools_run,
            "tools_skipped": tools_skipped,
            "model": model_name or "none",
            "risk_points": risk_pts,
        },
        "findings": [f.to_dict() for f in findings],
    }


def generate_report_markdown(
    findings: List[Finding],
    tools_run: List[str],
    tools_skipped: List[str],
    model_name: Optional[str] = None,
) -> str:
    """Generate human-readable Markdown report matching PROJECT.md Section 9."""
    counts = count_severities(findings)
    risk_pts = calculate_risk_points(counts)
    model_display = model_name if model_name else "deterministic templates"

    lines: List[str] = []
    lines.append("# BOB Security & Pre-Deploy Scan Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- **Risk Points**: {risk_pts}/100 *(heuristic score, not a safety guarantee)*")
    lines.append(f"- **Scanners Run**: {', '.join(tools_run) if tools_run else 'None'}")
    lines.append(f"- **Scanners Skipped (Optional)**: {', '.join(tools_skipped) if tools_skipped else 'None'}")
    lines.append(f"- **AI Triage Model**: {model_display}")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---|")
    for sev in ("critical", "high", "medium", "low", "info"):
        lines.append(f"| **{sev.upper()}** | {counts[sev]} |")
    lines.append("")

    if not findings:
        lines.append("## Findings")
        lines.append(f"> **{ZERO_FINDINGS_MESSAGE}**")
        lines.append("")
    else:
        lines.append("## Findings Details")
        lines.append("")
        for f in findings:
            lines.append(f"### [{f.id}] {f.title} ({f.severity.upper()})")
            lines.append(f"- **Rule ID**: `{f.rule_id}`")
            lines.append(f"- **Source**: `{f.source}` | **Category**: `{f.category}`")
            loc_str = f"`{f.file}`" if f.file else "N/A"
            if f.line:
                loc_str += f" (Line {f.line})"
            lines.append(f"- **Location**: {loc_str}")
            lines.append(f"- **Evidence**: `{f.evidence}`")
            lines.append(f"- **Fingerprint**: `{f.fingerprint[:16]}...`")

            if f.ai:
                lines.append(f"- **AI Verdict ({f.ai.model})**: `{f.ai.verdict}`")
                lines.append(f"- **Explanation**: {f.ai.explanation}")
                if f.ai.suggested_fix:
                    lines.append(f"- **Suggested Fix**:\n  ```\n  {f.ai.suggested_fix}\n  ```")

            lines.append(f"- **Verify Command**: `bob verify {f.fingerprint[:10]}`")
            lines.append("")

    lines.append("## AI-Downgraded Findings (Review These)")
    downgraded = [f for f in findings if f.ai and f.ai.verdict == "likely_false_positive"]
    if downgraded:
        for d in downgraded:
            lines.append(f"- `{d.id}` ({d.title}) downranked by AI: {d.ai.explanation if d.ai else ''}")
    else:
        lines.append("None. (No findings were downranked by AI)")
    lines.append("")

    lines.append("## Limitations")
    lines.append("- Detects known tripwires only; does not find business-logic flaws or novel malware.")
    lines.append("- Small local models can misjudge, so they never override deterministic Critical or High findings.")
    lines.append("- Static analysis without code execution may produce false positives on intentional test decoys.")
    lines.append("")

    return "\n".join(lines)


def write_reports(
    findings: List[Finding],
    tools_run: List[str],
    tools_skipped: List[str],
    out_dir: Path,
    model_name: Optional[str] = None,
) -> Tuple[Path, Path]:
    """Write report.md and report.json into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"

    json_data = generate_report_json(findings, tools_run, tools_skipped, model_name)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)

    md_content = generate_report_markdown(
        findings, tools_run, tools_skipped, model_name
    )
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return md_path, json_path
