# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 2 (M1: Pre-Install Package Gate & Offline Mock Registry Compatibility)
- **Branch**: `core/m0-skeleton` (ready to merge / branch `core/m1-pkg-gate`)
- **Status**: Milestone M0 verified and complete. Ready to begin Phase 2 (M1).

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | `bob doctor` exit 0, all 9 unit tests pass |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **READY** | Acceptance matrix rows 1-8 |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | PENDING | Blocked on M1 |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | PENDING | Blocked on M2 |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | PENDING | Blocked on M3 |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | PENDING | Blocked on M4 |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | PENDING | Blocked on M5 |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Implemented `Finding`, `AITriage`, `Decision` models with deterministic SHA-256 fingerprinting and secret masking (`mask_secret()`).
- **2026-10-23**: Implemented `load_config()` supporting `.bob/config.yaml`, `BOB_CONFIG` env var, and default fallback.
- **2026-10-23**: Implemented `bob doctor` probing Ollama `/api/tags` and detecting `gitleaks`/`semgrep`. Tested and verified exit code 0.

## Next Step
- Commit M0 work to `core/m0-skeleton`, open PR / merge to `main`, and begin Phase 2 (M1: Pre-install Package Gate).
