# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 4 (M3: Pre-Deploy Scanner, SARIF normalizer, builtin rules, report)
- **Branch**: `core/m2-guards` (ready to merge / branch `core/m3-scan`)
- **Status**: Milestone M2 verified and complete. Ready to begin Phase 4 (M3).

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | PR #1 merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | PR #2 merged into `main` |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **DONE** | 47 unit tests pass, matrix rows 9-13 verified |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | **READY** | Blocked on M2 merge |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | PENDING | Blocked on M3 |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | PENDING | Blocked on M4 |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | PENDING | Blocked on M5 |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestone M0; squash merged PR #1 to `main`.
- **2026-10-23**: Completed Milestone M1 package gate; squash merged PR #2 to `main`.
- **2026-10-23**: Completed Milestone M2:
  - Sensitive paths: case-insensitive cross-platform pattern matching for `.env*`, `.ssh/`, `id_rsa`, AWS, kube, docker credentials.
  - BOB self-protection: hard-blocks agent execution of `bob allow` (human-only) and any file writes targeting `.bob/`.
  - CLI `bob intercept`: supports generic shell command inspection and native Antigravity JSON toolCall payload on stdin.
  - Audit log: records all interception actions to `.bob/log.jsonl`.
  - Verified matrix rows 9, 10, 11, 12, 13 pass.

## Next Step
- Commit M2 work to `core/m2-guards`, open PR #3, merge to `main`, and begin Phase 4 (M3: Pre-deploy scan).
