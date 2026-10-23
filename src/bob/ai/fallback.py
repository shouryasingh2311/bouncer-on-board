"""Deterministic fallback explanations when local AI model is unavailable."""

from __future__ import annotations

from typing import Dict, Tuple

from bob.models import AITriage, Finding

FALLBACK_TEMPLATES: Dict[str, Tuple[str, str]] = {
    "BUILTIN-SECRET-API-KEY": (
        "An API key was hardcoded in source code. Anyone with access to this file can impersonate your account and incur billing or access data.",
        "Move the API key to an environment variable and load it with `os.environ.get('API_KEY')`.",
    ),
    "BUILTIN-SECRET-AWS-ID": (
        "An AWS Access Key ID was detected in source code. Hardcoded credentials risk exposure in version control.",
        "Use AWS IAM roles, AWS Secrets Manager, or load from `~/.aws/credentials` via `boto3.Session()`.",
    ),
    "BUILTIN-SECRET-AWS-KEY": (
        "An AWS Secret Access Key was detected in code. Hardcoding secret keys allows full account compromise.",
        "Store the secret in an environment variable or use IAM instance profiles instead of hardcoded keys.",
    ),
    "BUILTIN-SECRET-GITHUB-TOKEN": (
        "A GitHub personal access token was found in plaintext. This permits unauthorized repository and organization operations.",
        "Revoke the token immediately on GitHub and read from `GITHUB_TOKEN` environment variable.",
    ),
    "BUILTIN-SECRET-PRIVATE-KEY": (
        "An unencrypted private key is embedded directly in source code.",
        "Load the private key from a secure secrets vault or file path outside the source repository.",
    ),
    "BUILTIN-SECRET-HARDCODED": (
        "A hardcoded secret or token was detected in configuration or source code.",
        "Replace the hardcoded secret with an environment variable lookup or `.env` read via a secret manager.",
    ),
    "BUILTIN-SECRET-COMMITTED-ENV": (
        "A `.env` file containing local environment configuration is committed to the repository.",
        "Add `.env` to `.gitignore` and remove it from git tracking: `git rm --cached .env`.",
    ),
    "BUILTIN-CODE-DYNAMIC-EVAL": (
        "Dynamic code execution (`eval` or `exec`) runs directly on untrusted request input, enabling remote code execution (RCE).",
        "Replace `eval()` with structured parsing like `json.loads()` or a dictionary lookup table.",
    ),
    "BUILTIN-CODE-SQL-INJECTION": (
        "SQL query was constructed using string formatting or concatenation with input data.",
        "Use parameterized queries (e.g., `cursor.execute('SELECT * FROM t WHERE id = ?', (user_id,))`).",
    ),
    "BUILTIN-CODE-TLS-DISABLED": (
        "TLS certificate validation is explicitly disabled, leaving connections vulnerable to man-in-the-middle interception.",
        "Ensure TLS validation is enabled and supply the trusted CA certificate bundle if using a private certificate authority.",
    ),
    "BUILTIN-CODE-OPEN-CORS": (
        "CORS allows wildcard origins (`*`), which allows any third-party domain to make cross-origin requests to this endpoint.",
        "Restrict `Access-Control-Allow-Origin` to specific trusted client domains.",
    ),
    "BUILTIN-CONFIG-DEBUG-MODE": (
        "Application debug mode is enabled in code. Debug mode often exposes interactive shells and detailed stack traces.",
        "Disable debug mode before deploying or control via an environment variable `DEBUG=False`.",
    ),
    "PKG-NOT-FOUND": (
        "Package does not exist on the public registry. This commonly happens when AI agents hallucinate plausible package names.",
        "Remove the package dependency or verify the exact name on PyPI/npm.",
    ),
    "PKG-MALICIOUS-ADVISORY": (
        "The package matches an active malicious advisory report in the OSV database.",
        "Do not install this package. Remove it from requirements and report the incident.",
    ),
    "PKG-TOO-NEW": (
        "The package was uploaded very recently. Brand-new packages have not undergone community scrutiny and have a higher malware rate.",
        "Wait until the package matures, or inspect the repository source and release provenance manually.",
    ),
    "PKG-TYPOSQUAT": (
        "The package name is suspiciously close to a popular library name (Levenshtein distance <= 2).",
        "Check for typographical errors in the dependency name and install the verified original package.",
    ),
    "PKG-LLM-TROPE": (
        "The package name uses generic AI/utility tropes without verifiable source repository links.",
        "Verify the maintainer and repository origin before installing.",
    ),
    "PKG-NO-PROVENANCE": (
        "The package metadata contains no repository or homepage URL, hiding its source provenance.",
        "Verify the package author and verify the source repository before allowing installation.",
    ),
    "PKG-INSTALL-SCRIPT": (
        "The package archive contains suspicious install-time scripts (`setup.py` / `postinstall`) with obfuscation or network calls.",
        "Inspect the package archive statically and avoid running install lifecycle scripts.",
    ),
    "GUARD-SENSITIVE-PATH": (
        "Access to sensitive credential files (.env, SSH keys, cloud configs) was requested by an agent.",
        "Deny access. Do not expose local secret files to AI agents.",
    ),
    "GUARD-BOB-SELF-PROTECT": (
        "An agent command attempted to modify BOB configuration, bypass policies, or invoke `bob allow`.",
        "Self-protection tripped. Only human operators may modify BOB security rules or allowlists.",
    ),
}


def get_fallback_triage(finding: Finding) -> AITriage:
    """Generate a deterministic fallback triage for a finding."""
    # Look up by exact rule_id
    if finding.rule_id in FALLBACK_TEMPLATES:
        exp, fix = FALLBACK_TEMPLATES[finding.rule_id]
        return AITriage(
            verdict="likely_true_positive",
            explanation=exp,
            suggested_fix=fix,
            model="deterministic-templates",
        )

    # General category-based fallbacks
    cat = (finding.category or "").lower()
    if cat == "secret":
        return AITriage(
            verdict="likely_true_positive",
            explanation="A potential secret or credential was detected in this file. Storing credentials in repositories creates risk of unauthorized access.",
            suggested_fix="Store the secret in an environment variable or external secret manager.",
            model="deterministic-templates",
        )
    elif cat == "code":
        return AITriage(
            verdict="likely_true_positive",
            explanation=f"A code pattern flagged as {finding.title} was detected. Untrusted input handling requires strict sanitization and parameterization.",
            suggested_fix="Review input validation and apply secure coding guidelines for this function.",
            model="deterministic-templates",
        )

    return AITriage(
        verdict="uncertain",
        explanation=f"Deterministic scanner '{finding.source}' reported '{finding.title}'.",
        suggested_fix="Inspect the flagged line and verify whether the pattern is intentional.",
        model="deterministic-templates",
    )
