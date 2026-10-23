"""Unit tests for deterministic fallback explanations."""

from bob.ai.fallback import FALLBACK_TEMPLATES, get_fallback_triage
from bob.models import Finding


def test_fallback_templates_word_count() -> None:
    """Verify that all fallback explanation templates are concise (<= 80 words)."""
    for rule_id, (explanation, suggested_fix) in FALLBACK_TEMPLATES.items():
        words = explanation.split()
        assert len(words) <= 80, f"Explanation for {rule_id} exceeds 80 words ({len(words)} words)"
        assert len(suggested_fix) > 0


def test_get_fallback_triage_known_rule() -> None:
    f = Finding(
        id="BOB-0001",
        rule_id="BUILTIN-SECRET-API-KEY",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="OpenAI key hardcoded",
        file="src/config.py",
        line=12,
        evidence="sk-1234****",
    )
    triage = get_fallback_triage(f)
    assert triage.model == "deterministic-templates"
    assert triage.verdict == "likely_true_positive"
    assert "API key" in triage.explanation
    assert "os.environ" in triage.suggested_fix


def test_get_fallback_triage_generic_rule() -> None:
    f = Finding(
        id="BOB-0002",
        rule_id="CUSTOM-RULE",
        source="custom",
        category="secret",
        severity="high",
        title="Custom secret detected",
        file="auth.py",
        line=4,
        evidence="secret****",
    )
    triage = get_fallback_triage(f)
    assert triage.model == "deterministic-templates"
    assert triage.verdict == "likely_true_positive"
    assert "secret" in triage.explanation.lower()
