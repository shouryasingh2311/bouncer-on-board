# ROADMAP.md — BOB Phased Implementation Roadmap

Each phase corresponds directly to the milestone schedule in `PROJECT.md` Section 15 and `TEAM_PLAN.md`.
As CORE, our branches are named `core/<phase>-<topic>`.

---

## Phase 1: M0 — Skeleton, Data Models, Config & Doctor
- **Goal**: Establish the Python package structure, Typer CLI entrypoint, shared dataclasses, and doctor probe.
- **Deliverables**:
  - `pyproject.toml`
  - `src/bob/__init__.py`, `cli.py`, `models.py`, `config.py`
  - Unit tests for models & config in `tests/unit/test_config.py`
  - Working `bob doctor` command probing localhost:11434 and checking external tools
- **Exit Criteria**: `bob doctor` runs and exits 0 on the host machine.

---

## Phase 2: M1 — Pre-Install Package Gate & Offline Mock Registry Compatibility
- **Goal**: Block hallucinated, young, typosquatted, and malicious packages before installation runs.
- **Deliverables**:
  - `src/bob/cmdparse.py`: Shell command parsing for install intents
  - `src/bob/pkg/pypi.py` & `npm.py`: HTTPS registry clients respecting `registry_overrides`
  - `src/bob/pkg/heuristics.py`: Age, Levenshtein distance (top_pypi.json/top_npm.json), LLM tropes
  - `src/bob/pkg/static_inspect.py`: AST parsing of setup.py and npm scripts (safe archive extraction)
  - `src/bob/pkg/osv.py`: OSV client checking `MAL-` records
  - `src/bob/pkg/gate.py`: Score calculation and `Decision` generation
  - CLI: `bob check-install <ecosystem> <pkg>[==ver] [--json]`
  - Unit tests in `tests/unit/test_cmdparse.py`, `test_heuristics.py`, `test_static_inspect.py`
- **Exit Criteria**: Acceptance Matrix rows 1 to 8 pass against mock registry.

---

## Phase 3: M2 — Sensitive-Path Guard & Self-Protection Intercept
- **Goal**: Prevent agent from accessing credentials or tampering with BOB configuration.
- **Deliverables**:
  - `src/bob/guards/sensitive_paths.py`: Normalised, case-insensitive path blocking (`.env*`, `.ssh/`, AWS keys, etc.)
  - Self-protection logic: Block agent writes to `.bob/` and invocation of `bob allow`
  - CLI: `bob intercept --adapter generic --cmd "<cmd>"`
  - Unit tests in `tests/unit/test_sensitive_paths.py` and `test_intercept.py`
- **Exit Criteria**: Acceptance Matrix rows 9 to 13 pass.

---

## Phase 4: M3 — Pre-Deploy Scanner, SARIF Normalizer & Markdown/JSON Report
- **Goal**: Implement pre-deploy code and secret scanner with zero-dependency fallback rules.
- **Deliverables**:
  - `src/bob/scan/runners.py`: Parallel runner for optional external scanners (`gitleaks`, `semgrep`)
  - `src/bob/scan/sarif.py`: SARIF parser normalising findings
  - `src/bob/scan/builtin.py`: Zero-dependency regex scanner for secrets, open CORS, eval/exec, SQL injection, debug mode
  - `src/bob/scan/dedupe.py`: Fingerprint-based deduplication and `.bobignore` support
  - `src/bob/report/markdown.py`: Markdown and JSON reports (`.bob/report.md`, `.bob/report.json`)
  - CLI: `bob scan <path> --no-ai [--out-dir <dir>]`
  - Unit tests in `tests/unit/test_sarif.py`, `test_builtin_scan.py`, `test_dedupe.py`
- **Exit Criteria**: Acceptance Matrix row 15 passes against vulnerable app fixture.

---

## Phase 5: M4 — Local SLM Triage (Gemma 4 / Ollama), Fallbacks & Verify
- **Goal**: Integrate local Gemma 4 via Ollama for plain-English explanations and false-positive downranking; verify fixes.
- **Deliverables**:
  - `src/bob/ai/ollama_client.py`: Structured JSON chat API with strict timeout & health check
  - `src/bob/ai/prompts.py`: Safe prompts wrapping evidence in `<untrusted>` tags
  - `src/bob/ai/triage.py`: Policy enforcement (critical/high immutable, downrank medium/low only in allowlist)
  - `src/bob/ai/fallback.py`: Deterministic explanation templates when model is unavailable
  - CLI updates: `bob scan` with AI summary lines; `bob verify <fingerprint-prefix>`
  - Unit tests in `tests/unit/test_ai_triage.py` and `test_verify.py`
- **Exit Criteria**: Acceptance Matrix row 16 passes (`bob verify` confirms remediated finding).

---

## Phase 6: M5 — Prompt Injection Tripwire, Antigravity Adapter & PATH Shims
- **Goal**: Scan incoming text/READMEs for prompt injection and intercept commands at OS/IDE level.
- **Deliverables**:
  - `src/bob/guards/injection.py`: YAML rule engine (`INJ-001`, `INJ-010`, `INJ-011`, `INJ-020`)
  - `src/bob/adapters/antigravity.py`: Handler for Antigravity `PreToolUse` lifecycle hook
  - `src/bob/adapters/shim.py`: Installation and removal of Windows `.cmd` wrappers (`bob shim install`)
  - CLI: `bob guard-text <path> [--ai]` (AI advisory line bonus)
  - Unit tests in `tests/unit/test_injection.py`, `test_adapters.py`
- **Exit Criteria**: Acceptance Matrix rows 14 & 17 pass; shim blocks install in terminal.

---

## Phase 7: M6 — CI Workflow, Final Audit & Polish
- **Goal**: Package verification, CI pipeline, and feature freeze.
- **Deliverables**:
  - `.github/workflows/bob.yml`: GitHub Action running test suite and `bob scan`
  - Code review and dependency vulnerability audit (`pip audit` check)
- **Exit Criteria**: Clean test suite passes, zero unresolved lints or unhandled exceptions.
