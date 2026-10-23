"""Finding deduplication and .bobignore filtering."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Set

from bob.models import Finding

SEVERITY_ORDER = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
}


def load_bobignore_patterns(target_dir: Path) -> List[str]:
    """Read ignore patterns from .bobignore if present."""
    patterns: List[str] = []
    ignore_file = target_dir / ".bobignore"
    if ignore_file.is_file():
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s and not s.startswith("#"):
                        patterns.append(s)
        except Exception:
            pass
    return patterns


def is_ignored(file_path: Optional[str], patterns: List[str]) -> bool:
    """Check if file matches any ignore glob pattern."""
    if not file_path or not patterns:
        return False

    norm = file_path.replace("\\", "/")
    for pat in patterns:
        norm_pat = pat.replace("\\", "/")
        if fnmatch.fnmatch(norm, norm_pat) or fnmatch.fnmatch(Path(norm).name, norm_pat):
            return True
        if norm_pat in norm:
            return True

    return False


def deduplicate_findings(
    findings: List[Finding], ignore_patterns: Optional[List[str]] = None
) -> List[Finding]:
    """Deduplicate findings by fingerprint, keeping highest severity and filtering ignores."""
    patterns = ignore_patterns or []
    grouped: Dict[str, Finding] = {}

    for f in findings:
        if is_ignored(f.file, patterns):
            continue

        fp = f.fingerprint
        if fp not in grouped:
            grouped[fp] = f
        else:
            existing = grouped[fp]
            existing_rank = SEVERITY_ORDER.get(existing.severity.lower(), 0)
            new_rank = SEVERITY_ORDER.get(f.severity.lower(), 0)
            if new_rank > existing_rank:
                grouped[fp] = f

    # Stable sequential IDs BOB-0001, BOB-0002...
    result: List[Finding] = []
    for idx, f in enumerate(grouped.values(), start=1):
        f.id = f"BOB-{idx:04d}"
        result.append(f)

    # Sort primarily by severity descending
    result.sort(
        key=lambda item: SEVERITY_ORDER.get(item.severity.lower(), 0), reverse=True
    )
    return result
