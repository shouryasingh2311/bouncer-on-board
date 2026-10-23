# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 5 (M4: Local Gemma 4 AI Triage, Fallback Templates & Verify)
- **Branch**: `core/m3-scan` (ready to merge / branch `core/m4-ai`)
- **Status**: Milestone M3 verified and complete. Ready to begin Phase 5 (M4).

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | PR #1 merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | PR #2 merged into `main` |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **DONE** | PR #3 merged into `main` |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | **DONE** | 62 unit tests pass, matrix row 15 verified |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | **READY** | Blocked on M3 merge |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | PENDING | Blocked on M4 |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | PENDING | Blocked on M5 |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestone M0; squash merged PR #1 to `main`.
- **2026-10-23**: Completed Milestone M1 package gate; squash merged PR #2 to `main`.
- **2026-10-23**: Completed Milestone M2; squash merged PR #3 to `main`.
- **2026-10-23**: Completed Milestone M3:
  - Implemented SARIF 2.1.0 normalizer (`src/bob/scan/sarif.py`) for gitleaks and semgrep with secret masking.
  - Implemented zero-dependency built-in scanner (`src/bob/scan/builtin.py`) for secrets, committed `.env`, dynamic eval/exec, SQL injection, open CORS, debug mode, and disabled TLS.
  - Implemented parallel runner (`src/bob/scan/runners.py`) with ThreadPoolExecutor and graceful skip of missing external tools.
  - Implemented deduplication and `.bobignore` filtering (`src/bob/scan/dedupe.py`).
  - Implemented report formatter (`src/bob/report/markdown.py`) generating `.bob/report.md` and `.bob/report.json` with risk points and exact zero-findings sentence.
  - Added CLI `bob scan <path> [--no-ai] [--out-dir <dir>]` in `src/bob/cli.py` with exit code 0 on clean, exit 1 on gate failure, exit 3 on tool error.
  - Added unit tests: `test_sarif.py`, `test_builtin_scan.py`, `test_dedupe.py`, `test_scan.py` (total 62 unit tests passing).
  - Verified Acceptance Matrix Row 15.

## Next Step
- Commit M3 work to `core/m3-scan`, push to GitHub, open PR #4, merge into `main`, and begin Phase 5 (M4: Local Gemma 4 AI Triage).
