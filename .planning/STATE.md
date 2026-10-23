# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 7 (M6: CI Workflow, Dependency Audit, and Final Verification)
- **Branch**: `core/m5-shims` (ready to merge / branch `core/m6-ci`)
- **Status**: Milestone M5 verified and complete. Ready to begin Phase 7 (M6).

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | PR #1 merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | PR #2 merged into `main` |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **DONE** | PR #3 merged into `main` |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | **DONE** | PR #5 merged into `main` |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | **DONE** | PR #6 merged into `main` |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | **DONE** | 93 unit tests pass, matrix rows 14 & 17 verified |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | **READY** | Blocked on M5 merge |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestone M0; squash merged PR #1 to `main`.
- **2026-10-23**: Completed Milestone M1 package gate; squash merged PR #2 to `main`.
- **2026-10-23**: Completed Milestone M2; squash merged PR #3 to `main`.
- **2026-10-23**: Completed Milestone M3; squash merged PR #5 to `main`.
- **2026-10-23**: Completed Milestone M4; squash merged PR #6 to `main`.
- **2026-10-23**: Completed Milestone M5:
  - Seeded YAML injection rules pack (`src/bob/data/rules/injection.yaml`) with `INJ-001` (instruction override), `INJ-010` (invisible zero-width/unicode tags), `INJ-011` (bidirectional Trojan Source), `INJ-020` (credential exfiltration), `INJ-030` (prompt leak), `INJ-040` (roleplay jailbreak).
  - Implemented injection scanner (`src/bob/guards/injection.py`) and semantic AI second opinion evaluator (`evaluate_injection_semantics`).
  - Added CLI `bob guard-text <path> [--ai]`: exits 0 on clean, exits 2 on high/critical tripwire; adds model advisory line when `--ai` is enabled without changing exit code.
  - Implemented PATH shims manager (`src/bob/adapters/shim.py`) with `bob shim install` and `bob shim uninstall` for Windows `.cmd` and POSIX wrappers.
  - Implemented Antigravity hook adapter (`src/bob/adapters/antigravity.py`) with PreToolUse specification.
  - Implemented `bob audit [--manifest <path>]` and human-only `bob allow <pkg>`.
  - Added unit tests: `test_injection.py`, `test_guard_text.py`, `test_shims.py`, `test_allow.py` (total 93 unit tests passing).
  - Verified Acceptance Matrix Rows 14 and 17.

## Next Step
- Commit M5 work to `core/m5-shims`, push to GitHub, open PR #7, merge into `main`, and begin Phase 7 (M6: CI workflow & final audit).
