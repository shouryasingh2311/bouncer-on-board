# PLAN.md — Phase 6: M5 Prompt-Injection Guard, Antigravity Hook & PATH Shims

## Goal
Implement prompt injection detection via YAML rule packs (`src/bob/data/rules/injection.yaml`), the `bob guard-text <path> [--ai]` CLI command (matrix rows 14 & 17), native Antigravity lifecycle hook integration, and PATH shims (`bob shim install|uninstall`).

## Tasks
1. **Task 1: Injection Rule Pack (`src/bob/data/rules/injection.yaml`)**
   - Seed YAML rules matching PROJECT.md Section 7.6: `INJ-001` (instruction override), `INJ-010` (invisible zero-width/Unicode tag characters), `INJ-011` (bidirectional Trojan Source characters), `INJ-020` (exfiltration of secrets to external URL).

2. **Task 2: Injection Scanner Engine (`src/bob/guards/injection.py`)**
   - Load and compile regexes from YAML once.
   - Provide `scan_text_for_injections(text, file_path)` returning normalized `Finding` objects.
   - Provide AI second opinion evaluator (`evaluate_injection_semantics`) that never runs inside live intercept and never overrides deterministic verdict/exit code.

3. **Task 3: CLI `bob guard-text <path> [--ai]`**
   - Exit 0 if clean, exit 2 if High/Critical injection rule fires, exit 1 if file error.
   - Support `--ai`: query Gemma 4 for semantic advisory line; if unavailable, print `AI second opinion: unavailable`.

4. **Task 4: PATH Shims & Adapters (`src/bob/adapters/shim.py`, `src/bob/adapters/antigravity.py`)**
   - Implement `bob shim install` and `bob shim uninstall` for Windows `.cmd` and POSIX shims.
   - Wire Antigravity IDE adapter with `.agents/hooks.json` contract.

5. **Task 5: Unit Tests & Verification**
   - `tests/unit/test_injection.py`
   - `tests/unit/test_guard_text.py`
   - `tests/unit/test_shims.py`
   - Verify Acceptance Matrix Rows 14 & 17.
