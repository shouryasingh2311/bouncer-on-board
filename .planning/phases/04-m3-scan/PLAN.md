# PLAN.md — Phase 4: M3 Pre-Deploy Scanner, SARIF Normalizer & Markdown/JSON Report

## Goal
Implement the pre-deploy repository scanner (`bob scan`) with built-in zero-dependency tripwires (secrets, CORS *, eval/exec, string SQL, debug=True, TLS disabled), SARIF parsing for optional external tools (`gitleaks`, `semgrep`), fingerprint deduplication, and structured Markdown/JSON reports (`.bob/report.md`, `.bob/report.json`).

## Tasks
1. **Task 1: SARIF Parser (`src/bob/scan/sarif.py`)**
   - Parse SARIF 2.1.0 output from `gitleaks` and `semgrep`.
   - Normalise findings into `Finding` dataclass with mapped severities and masked evidence.

2. **Task 2: Built-in Tripwire Scanner (`src/bob/scan/builtin.py`)**
   - Zero-dependency rules for secrets (AWS, OpenAI, GitHub, private keys, committed `.env`).
   - Rules for insecure code (dynamic eval/exec, string-built SQL, debug=True, CORS *, TLS disabled, frontend keys).
   - Mark confidence and severity accurately.

3. **Task 3: Parallel Scanner Runner (`src/bob/scan/runners.py`)**
   - Run available scanners in parallel (`concurrent.futures.ThreadPoolExecutor`).
   - Graceful skip of missing external tools; track `tools_run` vs `tools_skipped`.

4. **Task 4: Deduplication & Ignore Engine (`src/bob/scan/dedupe.py`)**
   - Respect `.gitignore`, `.bobignore`, skip binary files and venv/node_modules/.bob.
   - Deduplicate findings by fingerprint (sha256 of rule_id+file+line+masked_evidence).

5. **Task 5: Report Formatter (`src/bob/report/markdown.py`)**
   - Generate `.bob/report.md` with risk points, severity breakdown, finding details, and exact zero-findings sentence.
   - Generate `.bob/report.json` matching Contract Addendum v1 schema.

6. **Task 6: CLI Command & Unit Tests**
   - Update `bob scan <path> [--no-ai] [--out-dir <dir>]` in `src/bob/cli.py`.
   - Exit 1 if any critical/high finding is hit (or severity in `fail_gate_on`).
   - Write comprehensive unit tests in `tests/unit/` and verify Acceptance Matrix row 15.
