# Testing Architecture & Verification

## Test Framework & Execution
- **Framework**: `pytest>=7.4.0`
- **Suite Size**: 113 unit tests across 25 files.
- **Run Command**:
  ```bash
  pytest
  # Or on Windows virtual environment:
  .venv\Scripts\pytest
  ```

## Test Directory Structure
All unit tests reside in `tests/unit/`:
- `test_allow.py`: Human package allowlist verification (`bob allow <pkg>`).
- `test_builtin_scan.py`: Built-in rule matcher for secrets, eval, and unverified TLS.
- `test_cloud_client.py`: Multi-platform Cloud AI client (Gemini and OpenAI-compatible endpoints).
- `test_cmdparse.py`: Command tokenization, package extraction, flags, and compound commands.
- `test_config.py`: Configuration loading, merging, and `~/.bob/config.yaml` fallback.
- `test_dedupe.py`: Finding deduplication engine using SHA-256 fingerprinting.
- `test_doctor.py`: Diagnostics, binary discovery, Ollama status, and cloud connectivity.
- `test_fallback.py`: Deterministic fallback advice when AI models are offline.
- `test_gate.py`: Pre-install package gate (PyPI, npm, heuristics, OSV advisories).
- `test_guard_text.py`: Prompt injection detection on text and markdown files.
- `test_heuristics.py`: Typosquatting distance calculations, package age, and tropes.
- `test_ide_protection.py`: IDE hook configuration and verification.
- `test_injection.py`: Prompt-injection rule matching and evasion resistance.
- `test_intercept.py`: Pre-action command interception and exit code enforcement.
- `test_prompts.py`: AI triage system prompt construction and JSON schema formatting.
- `test_sarif.py`: SARIF v2.1.0 generation and ingestion compliance.
- `test_scan.py`: End-to-end repository scanner execution.
- `test_scan_safety.py`: User home directory protection and root directory rejection.
- `test_sensitive_paths.py`: Sensitive file blocking (`.env`, `.ssh/`, `.git/`, AWS keys).
- `test_setup_and_banner.py`: Banner column width (<71 chars) and ASCII cp1252 character validation.
- `test_shims.py`: PATH shim generation and execution wrappers.
- `test_static_inspect.py`: AST inspection of setup scripts for obfuscation and network calls.
- `test_triage.py`: Security Axiom 2 enforcement (verifying AI cannot downgrade severity).
- `test_verify.py`: Finding remediation verification via fingerprint prefixes.

## Demo Harness Verification
- `demo/vulnerable_app/tests/test_mock_data.py`:
  - Validates that mock tokens and vulnerable endpoints in `demo/` are inert and safe for testing.

## Quality Gates
- 100% test passing required before PR merge.
- CI pipeline in `.github/workflows/bob.yml` automatically executes the entire test suite on every push.
