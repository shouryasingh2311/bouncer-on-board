# BOB (`bouncer-on-board`) Enhancement Plan

This document outlines proposed enhancements for BOB (Zero-Trust IDE Agent Firewall & Pre-Deploy Security Gatekeeper) to improve detection accuracy, supply chain security, AI triage quality, and developer experience.

---

## 1. Detection & Scanners
- **Native Tool Integration (`gitleaks` & `semgrep`)**:
  - Automatically discover local binaries of `gitleaks` and `semgrep` on PATH.
  - Run them alongside `bob-builtin` and merge their SARIF outputs through BOB's unified deduplication engine (`scan/dedupe.py`).
- **Expanded Prompt-Injection & Smuggling Rules (`data/rules/injection.yaml`)**:
  - Add rules for indirect prompt injection vectors:
    - Markdown image / webhook exfiltration links disguised as assets.
    - HTML comment payloads (`<!-- ... -->`) containing instruction overrides.
    - Zero-width character obfuscation and homoglyph attacks in external READMEs/issues.

## 2. Supply Chain & Interception
- **Transitive Dependency Lockfile Audit (`bob audit`)**:
  - Expand `bob audit` to parse major lockfiles (`poetry.lock`, `pnpm-lock.yaml`, `package-lock.json`, `Cargo.lock`) and batch-query OSV (`https://api.osv.dev`) for transitive vulnerabilities.
- **Canary Credential Substitution**:
  - Implement canary credential swapping for sensitive paths (returning believable fake credentials or dummy keys instead of blocking) to poison credential harvesters.
- **Advanced Install-Script AST Analysis**:
  - Enhance `pkg/static_inspect.py` using Python's `ast` module to detect obfuscated string decoders (`exec(base64...)`, `codecs`, `zlib`) in Python build hooks.

## 3. AI Triage & Local Model Integration
- **Structured JSON Mode with Ollama**:
  - Leverage Ollama's structured output / JSON schema capabilities to ensure local Gemma models return strictly validated JSON for triage verdicts.
- **Multi-Model Support & Auto-Fallback**:
  - Extend configuration to allow fallback across local models in Ollama (e.g., falling back to available models if `gemma4:e2b` is not pulled).

## 4. Developer Experience & CI/CD
- **Interactive Terminal TUI (`rich`)**:
  - Add an interactive review mode to `bob scan` allowing developers to inspect findings, view masked code snippets, and interactively manage allowlists or fixes.
- **GitHub Actions & PR Inline Annotations**:
  - Enhance the GitHub Action workflow (`.github/workflows/bob.yml`) to post automated PR comments and upload SARIF reports to GitHub Security.
