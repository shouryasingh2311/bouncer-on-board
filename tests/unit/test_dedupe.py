"""Unit tests for deduplication and .bobignore filtering."""

from pathlib import Path
from bob.models import Finding
from bob.scan.dedupe import (
    deduplicate_findings,
    is_ignored,
    load_bobignore_patterns,
)


def test_is_ignored() -> None:
    patterns = ["tests/*", "*.tmp", "vendor"]
    assert is_ignored("tests/unit/test_scan.py", patterns) is True
    assert is_ignored("scratch/test.tmp", patterns) is True
    assert is_ignored("src/vendor/lib.py", patterns) is True
    assert is_ignored("src/bob/scan.py", patterns) is False
    assert is_ignored(None, patterns) is False


def test_load_bobignore_patterns(tmp_path: Path) -> None:
    ignore_file = tmp_path / ".bobignore"
    ignore_file.write_text("# Comment\nnode_modules\n*.log\n\n", encoding="utf-8")
    patterns = load_bobignore_patterns(tmp_path)
    assert patterns == ["node_modules", "*.log"]


def test_deduplicate_findings_same_fingerprint() -> None:
    f1 = Finding(
        id="BOB-0001",
        rule_id="RULE-1",
        source="bob-builtin",
        category="secret",
        severity="medium",
        title="Secret found",
        file="config.py",
        line=10,
        evidence="masked-key",
    )
    f2 = Finding(
        id="BOB-0002",
        rule_id="RULE-1",
        source="gitleaks",
        category="secret",
        severity="critical",  # higher severity
        title="Secret found",
        file="config.py",
        line=10,
        evidence="masked-key",
    )

    # Both have the same fingerprint because rule_id, file, line, and evidence are identical
    assert f1.fingerprint == f2.fingerprint

    deduped = deduplicate_findings([f1, f2])
    assert len(deduped) == 1
    assert deduped[0].severity == "critical"
    assert deduped[0].id == "BOB-0001"


def test_deduplicate_findings_with_ignore() -> None:
    f1 = Finding(
        id="BOB-0001",
        rule_id="RULE-1",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="Secret in test file",
        file="tests/test_key.py",
        line=5,
        evidence="masked-key-1",
    )
    f2 = Finding(
        id="BOB-0002",
        rule_id="RULE-2",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="Secret in prod config",
        file="src/config.py",
        line=10,
        evidence="masked-key-2",
    )

    deduped = deduplicate_findings([f1, f2], ignore_patterns=["tests/*"])
    assert len(deduped) == 1
    assert deduped[0].file == "src/config.py"
