# STATE.md — BOB Project State

## Current Position
- **Project**: `bouncer-on-board` (BOB)
- **Role**: `CORE` (WYTE)
- **Active Phase**: Phase 6 (M5: Injection Tripwire Pack, Antigravity Hook Adapter, PATH Shims)
- **Branch**: `core/m4-ai` (ready to merge / branch `core/m5-shims`)
- **Status**: Milestone M4 verified and complete. Ready to begin Phase 6 (M5).

## Progress Overview
| Phase | Milestone | Scope | Status | Notes |
|---|---|---|---|---|
| Phase 1 | M0 | Skeleton, CLI entrypoint, models, config, doctor | **DONE** | PR #1 merged into `main` |
| Phase 2 | M1 | Pre-install gate (PyPI, npm), cmdparse, heuristics, static inspection | **DONE** | PR #2 merged into `main` |
| Phase 3 | M2 | Sensitive-path guard, self-protection, intercept | **DONE** | PR #3 merged into `main` |
| Phase 4 | M3 | Pre-deploy scanner, SARIF normalizer, builtin rules, report | **DONE** | PR #5 merged into `main` |
| Phase 5 | M4 | Local Gemma 4 AI triage, fallback templates, verify command | **DONE** | 77 unit tests pass, matrix row 16 verified |
| Phase 6 | M5 | Injection tripwire pack, Antigravity hook adapter, PATH shims | **READY** | Blocked on M4 merge |
| Phase 7 | M6 | CI workflow, dependency audit, final hygiene | PENDING | Blocked on M5 |

## Decisions Log
- **2026-10-23**: Confirmed Antigravity lifecycle hook support via `.agents/hooks.json` (`PreToolUse`), verifying our ability to build a dedicated Antigravity adapter in addition to L2 PATH shims.
- **2026-10-23**: Verified PyPI `upload_time_iso_8601` field on release items, npm `time['created']` and `versions[v]['scripts']`, and OSV `MAL-` identifier format over live HTTPS.
- **2026-10-23**: Completed Milestone M0; squash merged PR #1 to `main`.
- **2026-10-23**: Completed Milestone M1 package gate; squash merged PR #2 to `main`.
- **2026-10-23**: Completed Milestone M2; squash merged PR #3 to `main`.
- **2026-10-23**: Completed Milestone M3; squash merged PR #5 to `main`.
- **2026-10-23**: Completed Milestone M4:
  - Implemented deterministic fallback triage templates (`src/bob/ai/fallback.py`) for all standard rules (<= 80 words, beginner-friendly explanations and concrete fixes).
  - Implemented AI prompt builder (`src/bob/ai/prompts.py`) wrapping code context in `<untrusted>` tags and masking secrets.
  - Implemented Ollama HTTP client (`src/bob/ai/ollama_client.py`) with tags health-check, JSON structured output schema, and graceful fallback.
  - Implemented triage engine (`src/bob/ai/triage.py`) enforcing Security Axiom 2: AI cannot downgrade critical or high findings.
  - Integrated live AI explanation display and summary line in `bob scan`.
  - Implemented `bob verify <fingerprint-prefix>` verifying resolution of findings; exit 0 if resolved, exit 1 if still present.
  - Added unit tests: `test_fallback.py`, `test_prompts.py`, `test_triage.py`, `test_verify.py` (total 77 unit tests passing).
  - Verified Acceptance Matrix Row 16.

## Next Step
- Commit M4 work to `core/m4-ai`, push to GitHub, open PR #6, merge into `main`, and begin Phase 6 (M5: Injection tripwires & PATH shims).
