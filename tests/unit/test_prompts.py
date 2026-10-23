"""Unit tests for AI prompt construction and untrusted context wrapping."""

from pathlib import Path
from bob.ai.prompts import (
    AI_OUTPUT_SCHEMA,
    SYSTEM_PROMPT,
    build_triage_prompt,
    extract_file_context,
)
from bob.models import Finding


def test_schema_validity() -> None:
    assert AI_OUTPUT_SCHEMA["type"] == "object"
    assert "verdict" in AI_OUTPUT_SCHEMA["properties"]
    assert "explanation" in AI_OUTPUT_SCHEMA["properties"]
    assert "suggested_fix" in AI_OUTPUT_SCHEMA["properties"]
    assert set(AI_OUTPUT_SCHEMA["required"]) == {"verdict", "explanation", "suggested_fix"}


def test_extract_file_context(tmp_path: Path) -> None:
    test_file = tmp_path / "app.py"
    lines = [f"line_{i} = {i}" for i in range(1, 50)]
    test_file.write_text("\n".join(lines), encoding="utf-8")

    snippet = extract_file_context(tmp_path, "app.py", 25, max_lines=10)
    assert "<untrusted>" not in snippet  # wrapper added by prompt builder
    assert "line_25" in snippet
    assert len(snippet.splitlines()) <= 10


def test_extract_file_context_masks_secrets(tmp_path: Path) -> None:
    test_file = tmp_path / "secret.py"
    test_file.write_text("API_KEY = 'sk-1234567890abcdef1234567890'\n", encoding="utf-8")

    snippet = extract_file_context(tmp_path, "secret.py", 1, max_lines=10)
    assert "sk-1234567890abcdef1234567890" not in snippet
    assert "****" in snippet


def test_build_triage_prompt_untrusted_tagging() -> None:
    f = Finding(
        id="BOB-0001",
        rule_id="BUILTIN-CODE-SQL-INJECTION",
        source="bob-builtin",
        category="code",
        severity="critical",
        title="SQL injection risk",
        file="db.py",
        line=15,
        evidence="cursor.execute(query)",
    )
    context = "15 | cursor.execute(query)"
    prompt = build_triage_prompt(f, context)

    assert "<untrusted>" in prompt
    assert "</untrusted>" in prompt
    assert context in prompt
    assert "BOB-0001" in prompt
    assert "BUILTIN-CODE-SQL-INJECTION" in prompt
