"""AI triage orchestrator and security policy enforcement (Axiom 2)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

from bob.ai.fallback import get_fallback_triage
from bob.ai.ollama_client import check_ollama_status, query_ollama_triage
from bob.ai.prompts import extract_file_context
from bob.config import Config
from bob.models import AITriage, Finding


def can_downrank_severity(severity: str, rule_id: str) -> bool:
    """Axiom 2: AI can NEVER downgrade critical or high findings."""
    sev = severity.lower()
    if sev in ("critical", "high"):
        return False

    # Only medium/low items may be downranked
    return True


def triage_findings(
    findings: List[Finding],
    config: Config,
    target_dir: Optional[Path] = None,
    max_findings_to_triage: int = 10,
) -> Tuple[List[Finding], str, int, int]:
    """Run AI triage across findings, strictly enforcing Security Axiom 2.
    
    Returns:
        (updated_findings, model_display, explained_count, downranked_count)
    """
    if not findings:
        return [], config.model, 0, 0

    is_ollama_ready, _ = check_ollama_status(config.ollama_url, config.model)

    model_display = config.model if is_ollama_ready else "deterministic templates (model unavailable)"
    explained_count = 0
    downranked_count = 0

    for idx, finding in enumerate(findings):
        # Only query LLM for the top N findings by severity to preserve CPU performance
        if is_ollama_ready and idx < max_findings_to_triage:
            context_snippet = extract_file_context(
                target_dir, finding.file, finding.line, max_lines=30
            )
            raw_triage = query_ollama_triage(
                config.ollama_url, config.model, finding, context_snippet
            )
            if raw_triage:
                verdict = raw_triage.get("verdict", "uncertain")
                explanation = str(raw_triage.get("explanation", "")).strip()
                suggested_fix = str(raw_triage.get("suggested_fix", "")).strip()

                # Axiom 2 Policy Enforcement in code:
                # LLM can NEVER suppress or lower critical/high findings
                if verdict == "likely_false_positive":
                    if can_downrank_severity(finding.severity, finding.rule_id):
                        # Allowed to downrank medium or low findings
                        finding.severity = "info"
                        downranked_count += 1
                    else:
                        # Overridden: critical/high cannot be downranked!
                        verdict = "likely_true_positive"
                        explanation += " [Policy Note: AI suggested false-positive, but Security Axiom 2 forbids downgrading critical/high findings.]"

                finding.ai = AITriage(
                    verdict=verdict,
                    explanation=explanation,
                    suggested_fix=suggested_fix,
                    model=config.model,
                )
                explained_count += 1
                continue

        # Fallback to deterministic template
        finding.ai = get_fallback_triage(finding)
        explained_count += 1

    return findings, model_display, explained_count, downranked_count
