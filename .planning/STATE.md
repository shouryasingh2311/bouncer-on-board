# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: COMPLETE (All Milestones M0 through M6 implemented, tested, and verified)
- **Branch**: `core/m6-ci` (ready to merge into `main`)
- **Status**: Milestone M6 verified and complete. Ready for submission and teammate handoff.

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | PR #1 merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | PR #2 merged into `main` |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **DONE** | PR #3 merged into `main` |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | **DONE** | PR #5 merged into `main` |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | **DONE** | PR #6 merged into `main` |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | **DONE** | PR #7 merged into `main` |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | **DONE** | 93 unit tests pass, zero vulnerabilities |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestone M0; squash merged PR #1 to `main`.
- **2026-10-23**: Completed Milestone M1 package gate; squash merged PR #2 to `main`.
- **2026-10-23**: Completed Milestone M2; squash merged PR #3 to `main`.
- **2026-10-23**: Completed Milestone M3; squash merged PR #5 to `main`.
- **2026-10-23**: Completed Milestone M4; squash merged PR #6 to `main`.
- **2026-10-23**: Completed Milestone M5; squash merged PR #7 to `main`.
- **2026-10-23**: Completed Milestone M6:
  - Added GitHub Actions CI workflow (`.github/workflows/bob.yml`) running pytest, `bob doctor`, and `bob scan` on Python 3.10.
  - Added `package-data` configuration in `pyproject.toml` ensuring `top_pypi.json`, `top_npm.json`, and `data/rules/*.yaml` are properly packaged.
  - Executed dependency security audit against OSV with zero known vulnerabilities across all runtime and dev dependencies.
  - Executed pre-deploy security scan with `bob scan src --no-ai` (100% clean gate pass).
  - All 93 unit tests passing.

## Next Step
- Commit M6 work to `core/m6-ci`, push to GitHub, open PR #8, and squash merge into `main`.
