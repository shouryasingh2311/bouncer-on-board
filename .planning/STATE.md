# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 3 (M2: Sensitive-Path Guard & Self-Protection Intercept)
- **Branch**: `core/m1-pkg-gate` (ready to merge / branch `core/m2-guards`)
- **Status**: Milestone M1 verified and complete. Ready to begin Phase 3 (M2).

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | PR #1 merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | 35 unit tests pass, matrix rows 1-8 verified |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **READY** | Blocked on M1 merge |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | PENDING | Blocked on M2 |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | PENDING | Blocked on M3 |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | PENDING | Blocked on M4 |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | PENDING | Blocked on M5 |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestone M0; squash merged PR #1 to `main`.
- **2026-10-23**: Completed Milestone M1 package gate:
  - Command parsing: `pip`, `pip3`, `python -m pip`, `py -m pip`, `uv`, `npm`, `npx`, `pnpm`, `yarn`.
  - Heuristics: 15-line stdlib Levenshtein typosquatting, upload age calculation, LLM naming tropes, provenance checks.
  - Static AST inspection: setup.py parsed safely without execution (flagging base64 decode+exec, env dumps, curl/powershell calls), npm lifecycle script checks.
  - OSV client: checks for `MAL-` malicious package advisories.
  - CLI: `bob check-install <pypi|npm> <pkg>[==ver] [--json]` fully implemented with exit codes 0 (allow/warn) and 2 (block).

## Next Step
- Commit M1 work to `core/m1-pkg-gate`, open PR #2, merge to `main`, and begin Phase 3 (M2).
