# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: ONBOARDED & OPERATIONAL (All Milestones M0 through M6 implemented, multi-platform cloud AI integrated, 113 tests passing)
- **Branch**: `main` (synced with `origin/main`)
- **Status**: Production-ready. Codebase mapped, remote branches cleaned, test suite fully passing.

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | Merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | Merged into `main` |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **DONE** | Merged into `main` |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | **DONE** | Merged into `main` |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | **DONE** | Merged into `main` |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | **DONE** | Merged into `main` |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | **DONE** | 113 unit tests pass, zero vulnerabilities |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestones M0 through M6 and merged into `main`.
- **2026-10-23**: Added multi-platform Cloud AI client (`src/bob/ai/cloud_client.py`), evaluator demo harness (`demo/`), and home scan safety guards.
- **2026-10-25**: Executed `/gsd-onboard`: audited codebase and remote repository, pruned 15 stale merged remote branches from GitHub, and established `.planning/codebase/` (7 architecture documents) and `.planning/onboarding/SUMMARY.md`.

## Next Step
- Run `/gsd-progress` or `/gsd-plan-phase` to advance planned enhancements.
