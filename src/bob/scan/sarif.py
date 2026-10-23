"""SARIF 2.1.0 parser normalising external scanner outputs into BOB Findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from bob.models import Finding, mask_secret


LEVEL_TO_SEVERITY = {
    "error": "high",
    "warning": "medium",
    "note": "low",
    "none": "info",
}


def parse_sarif_content(
    sarif_data: Dict[str, Any], default_source: str = "sarif"
) -> List[Finding]:
    """Parse SARIF JSON dictionary and convert results into Finding objects."""
    findings: List[Finding] = []
    runs = sarif_data.get("runs", [])
    finding_counter = 1

    for run in runs:
        tool_name = (
            run.get("tool", {}).get("driver", {}).get("name")
            or default_source
        ).lower()

        # Rules map for title/description lookup
        rules_map: Dict[str, Dict[str, Any]] = {}
        for r in run.get("tool", {}).get("driver", {}).get("rules", []):
            if "id" in r:
                rules_map[r["id"]] = r

        results = run.get("results", [])
        for res in results:
            rule_id = str(res.get("ruleId", "UNKNOWN-RULE"))
            level = str(res.get("level", "warning")).lower()
            severity = LEVEL_TO_SEVERITY.get(level, "medium")

            # Gitleaks findings are secrets -> elevate severity
            if "gitleaks" in tool_name:
                category = "secret"
                if severity == "high":
                    severity = "critical"
            else:
                category = "code"

            rule_meta = rules_map.get(rule_id, {})
            title = (
                rule_meta.get("shortDescription", {}).get("text")
                or res.get("message", {}).get("text")
                or f"Issue detected by {tool_name}"
            )

            # Location extraction
            file_path: Optional[str] = None
            line_no: Optional[int] = None
            evidence_str: str = ""

            locations = res.get("locations", [])
            if locations:
                phys = locations[0].get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri")
                if uri:
                    file_path = str(Path(uri).as_posix())

                region = phys.get("region", {})
                line_no = region.get("startLine")
                snippet = region.get("snippet", {}).get("text")
                if snippet:
                    evidence_str = str(snippet).strip()

            if not evidence_str:
                evidence_str = res.get("message", {}).get("text", "")

            # Always mask evidence if category is secret
            if category == "secret":
                evidence_str = mask_secret(evidence_str)

            f = Finding(
                id=f"BOB-{finding_counter:04d}",
                rule_id=rule_id,
                source=tool_name,
                category=category,
                severity=severity,
                title=title,
                file=file_path,
                line=line_no,
                evidence=evidence_str,
            )
            findings.append(f)
            finding_counter += 1

    return findings


def parse_sarif_file(
    file_path: Path, default_source: str = "sarif"
) -> List[Finding]:
    """Read a SARIF JSON file from disk and parse findings."""
    if not file_path.is_file():
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_sarif_content(data, default_source)
    except Exception:
        return []
