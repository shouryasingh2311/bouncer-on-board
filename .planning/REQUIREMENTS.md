# REQUIREMENTS.md — BOB Requirements Specification

## 1. Functional Requirements (CORE Scope)

### M0: Skeleton & Doctor
- [ ] **REQ-M0-1 (Packaging)**: `pyproject.toml` configuration with console script entrypoint `bob = bob.cli:app` using Typer. Allowed runtime deps: `typer`, `rich`, `httpx`, `pyyaml`. Dev: `pytest`.
- [ ] **REQ-M0-2 (Data Models)**: `Finding` and `Decision` dataclasses in `src/bob/models.py`.
- [ ] **REQ-M0-3 (Configuration)**: Default configuration loader in `src/bob/config.py` reading `.bob/config.yaml` or `BOB_CONFIG` env var.
- [ ] **REQ-M0-4 (Doctor)**: `bob doctor` command probing Ollama endpoint (`/api/tags`), checking installed Gemma model, and detecting available external scanners (`gitleaks`, `semgrep`).

### M1: Pre-Install Package Gate & Intercept Parsing
- [ ] **REQ-M1-1 (Command Parser)**: `src/bob/cmdparse.py` extracting install intents from shell command strings (handling `pip`, `pip3`, `python -m pip`, `uv`, `npm`, `npx`, `pnpm`, `yarn`).
- [ ] **REQ-M1-2 (PyPI & npm Clients)**: `src/bob/pkg/pypi.py` and `npm.py` fetching package metadata over HTTPS (with `registry_overrides` support for offline mock registry).
- [ ] **REQ-M1-3 (Heuristics & Typosquatting)**: Age calculation, bundled top-N Levenshtein distance (<=2), trope detection, missing provenance.
- [ ] **REQ-M1-4 (Static Archive Inspection)**: `src/bob/pkg/static_inspect.py` analyzing `setup.py` via `ast` without executing it (flagging base64 decode+exec, env dumps, exfiltration, suspicious subproc calls) and inspecting npm packument scripts.
- [ ] **REQ-M1-5 (OSV Malicious Advisories)**: Direct query to OSV API flagging `MAL-` records.
- [ ] **REQ-M1-6 (Gate Logic & CLI)**: `src/bob/pkg/gate.py` combining signals into a `Decision` score (hard signal or >=70: block [exit 2], 30-69: warn [exit 0], <30: allow [exit 0]). Exposed via `bob check-install`.

### M2: Sensitive-Path Guard & Self-Protection
- [ ] **REQ-M2-1 (Sensitive Paths)**: `src/bob/guards/sensitive_paths.py` blocking commands/file paths targeting `.env*`, `.ssh/`, AWS/GCP/kube/npm/pypirc credentials.
- [ ] **REQ-M2-2 (Self Protection)**: Block agent writes targeting `.bob/` and block agent invocation of `bob allow`.
- [ ] **REQ-M2-3 (Intercept Command)**: `bob intercept --adapter generic --cmd "..."` checking both package install intents and path guards.

### M3: Scanner & Reporting
- [ ] **REQ-M3-1 (Scanner Runners & SARIF)**: Parallel execution of `gitleaks` and `semgrep` with graceful fallback when missing; SARIF normalization into `Finding` objects.
- [ ] **REQ-M3-2 (Built-in Fallback Scanner)**: High-entropy secrets, committed `.env`, CORS `*`, `eval`/`exec`, string-built SQL, `debug=True`.
- [ ] **REQ-M3-3 (Deduplication & Ignore)**: Fingerprinting (sha256 of rule_id+file+line+masked_evidence) and `.bobignore` / `.gitignore` support.
- [ ] **REQ-M3-4 (Report Generation)**: Outputs `.bob/report.md` and `.bob/report.json` with risk score and zero-finding exact sentence.

### M4: Local AI Triage (Gemma 4 via Ollama) & Verification
- [ ] **REQ-M4-1 (Ollama Client & Prompts)**: Structured JSON output via Ollama `/api/chat` with evidence enclosed in `<untrusted>` tags.
- [ ] **REQ-M4-2 (Triage Policy)**: Only down-rank medium/low findings in strict allowlist; never override critical/high.
- [ ] **REQ-M4-3 (Deterministic Fallback)**: `src/bob/ai/fallback.py` when Ollama is offline or model unavailable.
- [ ] **REQ-M4-4 (Verification)**: `bob verify <fingerprint-prefix>` re-running targeted check to confirm fixes.

### M5: Injection Tripwire & Shims
- [ ] **REQ-M5-1 (Injection Rule Pack)**: `src/bob/guards/injection.py` executing YAML rules (`INJ-001`, `INJ-010`, `INJ-011`, `INJ-020`).
- [ ] **REQ-M5-2 (Guard Text CLI)**: `bob guard-text <path> [--ai]`.
- [ ] **REQ-M5-3 (Antigravity & Shim Adapters)**: Windows `.cmd` PATH shims and Antigravity `PreToolUse` hook adapter.

### M6: Polish & CI Workflow
- [ ] **REQ-M6-1 (CI Gate)**: `.github/workflows/bob.yml` running unit tests and pre-deploy `bob scan`.

---

## 2. Acceptance Matrix (Contract Verification)

| # | Command | Expectation |
|---|---|---|
| 1 | `check-install pypi demo-good-lib` | exit 0, allow |
| 2 | `check-install pypi demo-missing-lib` | exit 2, `PKG-NOT-FOUND` |
| 3 | `check-install pypi demo-fresh-lib` | exit 0, `BOB WARN` `PKG-TOO-NEW` |
| 4 | `check-install pypi reqeusts` | exit 2, `PKG-TYPOSQUAT` |
| 5 | `check-install pypi requests-utils` | exit 2, `PKG-LLM-TROPE` |
| 6 | `check-install pypi demo-evil-lib` | exit 2, `PKG-INSTALL-SCRIPT` |
| 7 | `check-install npm demo-npm-evil` | exit 2, `PKG-INSTALL-SCRIPT` |
| 8 | `check-install npm demo-npm-good` | exit 0, allow |
| 9 | `intercept --adapter generic --cmd "pip install demo-missing-lib"` | exit 2 |
| 10 | `intercept ... --cmd "python -m pip install reqeusts"` | exit 2 |
| 11 | `intercept ... --cmd "cat .env"` | exit 2, `GUARD-SENSITIVE-PATH` |
| 12 | `intercept ... --cmd "cat README.md"` | exit 0 |
| 13 | `intercept ... --cmd "bob allow demo-evil-lib"` | exit 2, `GUARD-BOB-SELF-PROTECT` |
| 14 | `guard-text demo/injection_fixture/README.md` | exit 2, `INJ-010`, `INJ-020` |
| 15 | `scan demo/vulnerable_app --no-ai --out-dir <tmp>` | exit 1; finding categories `secret`, `code` |
| 16 | Apply fix -> `verify <fingerprint>` | exit 0 |
| 17 | `guard-text demo/injection_fixture/README.md --ai` (optional with Ollama) | exit 2 + model advisory line |
