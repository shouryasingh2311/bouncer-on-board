"""Unit tests for AI triage engine and Axiom 2 policy enforcement."""

from unittest.mock import patch
from bob.ai.triage import can_downrank_severity, triage_findings
from bob.config import Config
from bob.models import Finding


def test_axiom2_cannot_downrank_critical_or_high() -> None:
    assert can_downrank_severity("critical", "ANY-RULE") is False
    assert can_downrank_severity("CRITICAL", "ANY-RULE") is False
    assert can_downrank_severity("high", "ANY-RULE") is False
    assert can_downrank_severity("HIGH", "ANY-RULE") is False

    assert can_downrank_severity("medium", "ANY-RULE") is True
    assert can_downrank_severity("low", "ANY-RULE") is True


def test_triage_findings_ollama_offline() -> None:
    cfg = Config()
    f = Finding(
        id="BOB-0001",
        rule_id="BUILTIN-SECRET-API-KEY",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="OpenAI key hardcoded",
        file="config.py",
        line=1,
        evidence="sk-1234****",
    )

    with patch("bob.ai.triage.check_ollama_status", return_value=(False, "offline")):
        findings, model_display, explained_count, downranked_count = triage_findings([f], cfg)

    assert "model unavailable" in model_display
    assert explained_count == 1
    assert downranked_count == 0
    assert f.ai is not None
    assert f.ai.model == "deterministic-templates"
    assert f.severity == "critical"


def test_triage_findings_axiom2_blocks_critical_downgrade() -> None:
    cfg = Config()
    f = Finding(
        id="BOB-0001",
        rule_id="BUILTIN-CODE-SQL-INJECTION",
        source="bob-builtin",
        category="code",
        severity="critical",
        title="SQL injection risk",
        file="app.py",
        line=10,
        evidence="cursor.execute(f'SELECT...')",
    )

    mock_llm_response = {
        "verdict": "likely_false_positive",
        "explanation": "This seems safe in test code.",
        "suggested_fix": "No fix needed.",
    }

    with patch("bob.ai.triage.check_ollama_status", return_value=(True, "ready")), \
         patch("bob.ai.triage.query_ollama_triage", return_value=mock_llm_response):
        findings, model_display, explained_count, downranked_count = triage_findings([f], cfg)

    assert f.severity == "critical"  # Must NOT be downgraded!
    assert downranked_count == 0
    assert f.ai is not None
    assert f.ai.verdict == "likely_true_positive"
    assert "Axiom 2" in f.ai.explanation


def test_triage_findings_allows_medium_downgrade() -> None:
    cfg = Config()
    f = Finding(
        id="BOB-0002",
        rule_id="BUILTIN-CODE-OPEN-CORS",
        source="bob-builtin",
        category="code",
        severity="medium",
        title="Wildcard CORS",
        file="server.js",
        line=5,
        evidence="cors({origin: '*'})",
    )

    mock_llm_response = {
        "verdict": "likely_false_positive",
        "explanation": "This is a public documentation endpoint intentionally allowing CORS.",
        "suggested_fix": "No change needed if intended for public consumption.",
    }

    with patch("bob.ai.triage.check_ollama_status", return_value=(True, "ready")), \
         patch("bob.ai.triage.query_ollama_triage", return_value=mock_llm_response):
        findings, model_display, explained_count, downranked_count = triage_findings([f], cfg)

    assert f.severity == "info"  # Downgraded!
    assert downranked_count == 1
    assert f.ai is not None
    assert f.ai.verdict == "likely_false_positive"
