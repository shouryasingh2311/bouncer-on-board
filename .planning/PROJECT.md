# PROJECT.md — BOB (`bouncer-on-board`) Context & CORE Scope

## 1. Project Overview
- **Name**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE, repo owner)
- **Scope Boundary**:
  - Owns: `src/**`, `tests/unit/**`, `pyproject.toml`, `.github/workflows/bob.yml`, `PROJECT.md`
  - Does NOT touch: `demo/**`, `eval/**`, `tests/fixtures/**`, `tests/integration/**`, `README.md`, `docs/**`, `skills/**`, `LICENSE`, `THIRD_PARTY_NOTICES.md`, `CONTRIBUTING.md`, etc.
- **Mission**: Zero-trust IDE agent firewall and pre-deploy security gatekeeper:
  - **Path 1 (`bob intercept`)**: Live, deterministic pre-action blocking (<400ms target). Blocks hallucinated, typosquatted, or malicious package installs and sensitive-file reads/writes before execution.
  - **Path 2 (`bob scan`)**: Pre-deploy scanner combining deterministic tripwires (built-in + SARIF) with local open-weight SLM (Gemma 4 via Ollama) for false-positive triage and plain-English explanation.

## 2. Core Working Agreement (Strict Invariants)
1. **Never invent**: No phantom flags, endpoints, fields, or config keys. All external interfaces verified.
2. **Minimal allowed dependencies**: Runtime: `typer`, `rich`, `httpx`, `pyyaml`. Dev: `pytest`. Stdlib for everything else.
3. **Never execute untrusted code**: Purely static inspection. No `pip install`, `exec`, `eval`, or `shell=True`.
4. **Deterministic tripwires detect**: The LLM only explains, annotates, and proposes patches. LLM never overrides Critical/High or approves packages.
5. **Fixed templates for agent messages**: Stderr to agent uses static templates to avoid prompt injection reflections.
6. **Mask secrets everywhere**: First 4 characters + `****`.
7. **Windows-first compatibility**: Python 3.10+, `pathlib`, forward and backslash support, `.cmd` shims.

## 3. Contract Addendum v1 (Shared with QA-DEMO)
- **Commands**:
  - `bob intercept --adapter <generic|antigravity> --cmd "<cmd>"`
  - `bob check-install <pypi|npm> <pkg>[==ver] [--json]`
  - `bob guard-text <path> [--ai]`
  - `bob scan <path> [--no-ai] [--out-dir <dir>]`
  - `bob verify <fingerprint-prefix>`
  - `bob doctor`
  - `bob shim install|uninstall`
  - `bob allow <pkg>` (human only)
- **Exit codes**:
  - `0`: Allow / Clean / Pass / Fixed
  - `1`: Gate failed / finding present / internal warning
  - `2`: Blocked / High or Critical hit
  - `3`: Tool error
- **Rule IDs**:
  - Packages: `PKG-NOT-FOUND`, `PKG-MALICIOUS-ADVISORY`, `PKG-TOO-NEW`, `PKG-TYPOSQUAT`, `PKG-LLM-TROPE`, `PKG-NO-PROVENANCE`, `PKG-INSTALL-SCRIPT`
  - Guards: `GUARD-SENSITIVE-PATH`, `GUARD-BOB-SELF-PROTECT`
  - Injection: `INJ-001`, `INJ-010`, `INJ-011`, `INJ-020`
