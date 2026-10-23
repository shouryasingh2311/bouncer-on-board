# PLAN.md — Phase 3: M2 Sensitive-Path Guard, Self-Protection & Intercept

## Goal
Implement the live action guard (`bob intercept`) that blocks agent reads/writes of sensitive credential paths, protects BOB from self-weakening (`bob allow` and `.bob/` tampering), and routes package install commands to the package gate.

## Tasks
1. **Task 1: Sensitive-Path & Self-Protection Guard (`src/bob/guards/sensitive_paths.py`)**
   - Normalise paths across Windows and POSIX (case-insensitive, forward and backslash, expand `~` and env vars).
   - Flag sensitive targets: `.env`, `.env.*`, `.ssh/`, `id_rsa`, `id_ed25519`, `.aws/credentials`, `.npmrc`, `.pypirc`, `.git-credentials`, `*.pem`, `*.key`, `.kube/config`, `.docker/config.json`, `service-account*.json`, plus `sensitive_paths_extra`.
   - Rule ID: `GUARD-SENSITIVE-PATH`.
   - Flag self-protection violations: any command calling `bob allow` or writing/editing `.bob/`.
   - Rule ID: `GUARD-BOB-SELF-PROTECT`.

2. **Task 2: Live Intercept Engine & CLI (`src/bob/cli.py`)**
   - Command: `bob intercept --adapter <generic|antigravity> [--cmd "<cmd>"]`.
   - Read from `--cmd` or stdin (for pipeline/hook integration).
   - Sequence:
     1. Evaluate self-protection. If hit -> block (exit 2).
     2. Evaluate sensitive paths. If hit -> block (exit 2).
     3. Extract install intents via `cmdparse.py`. If found -> evaluate package gate. If any package blocked -> block (exit 2).
     4. If clean -> allow (exit 0).
   - Stderr output: Fixed template strings.
   - Audit log: Append JSON record to `.bob/log.jsonl`.

3. **Task 3: Unit Tests**
   - `tests/unit/test_sensitive_paths.py`: path normalization, pattern matches, benign path allowance.
   - `tests/unit/test_intercept.py`: Acceptance Matrix rows 9–13:
     - Row 9: `intercept ... --cmd "pip install demo-missing-lib"` -> exit 2
     - Row 10: `intercept ... --cmd "python -m pip install reqeusts"` -> exit 2
     - Row 11: `intercept ... --cmd "cat .env"` -> exit 2, `GUARD-SENSITIVE-PATH`
     - Row 12: `intercept ... --cmd "cat README.md"` -> exit 0
     - Row 13: `intercept ... --cmd "bob allow demo-evil-lib"` -> exit 2, `GUARD-BOB-SELF-PROTECT`
