# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 1 (M0: Skeleton, Data Models, Config & Doctor)
- **Status**: Initialization complete; ready to plan and execute Phase 1.

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **READY** | Pre-flight verifications complete |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | PENDING | Blocked on M0 |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | PENDING | Blocked on M1 |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | PENDING | Blocked on M2 |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | PENDING | Blocked on M3 |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | PENDING | Blocked on M4 |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | PENDING | Blocked on M5 |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Enforced strict role boundary: CORE exclusively owns `src/**`, `tests/unit/**`, `pyproject.toml`, `.github/workflows/bob.yml`, and `PROJECT.md`.

## Next Step
- Plan Phase 1 (M0) via `/gsd-plan-phase 1` or proceed directly with Phase 1 execution.
