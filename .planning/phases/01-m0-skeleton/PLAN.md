# PLAN.md — Phase 1: M0 Skeleton, Data Models, Config & Doctor

## Goal
Establish the foundational Python package, Typer CLI entrypoint, shared dataclasses (`Finding`, `Decision`), config discovery loader, and a working `bob doctor` command probing local Ollama and external scanner availability.

## Tasks
1. **Task 1: Packaging & Project Configuration (`pyproject.toml`)**
   - Define package `bouncer-on-board` (import name `bob`).
   - Specify Python `>=3.10`.
   - Declare runtime dependencies: `typer`, `rich`, `httpx`, `pyyaml`.
   - Declare dev dependencies: `pytest`.
   - Register console script: `bob = bob.cli:app`.

2. **Task 2: Data Models (`src/bob/models.py`)**
   - Define `Finding` dataclass matching `PROJECT.md` Section 6.2 (id, rule_id, source, category, severity, title, file, line, evidence, fingerprint, ai).
   - Define `AITriage` dataclass (verdict, explanation, suggested_fix, model).
   - Define `Decision` dataclass (action, score, reasons, findings).
   - Include serialization helper (`to_dict()`) for JSON output.

3. **Task 3: Configuration Loader (`src/bob/config.py`)**
   - Define `Config` dataclass with defaults:
     - `model: "gemma4:e2b"`
     - `ollama_url: "http://localhost:11434"`
     - `min_package_age_days: 14`
     - `offline_policy: "warn"`
     - `registry_overrides: {}`
     - `sensitive_paths_extra: []`
     - `fail_gate_on: ["critical", "high"]`
   - Read from `./.bob/config.yaml` or path in `BOB_CONFIG` env var.
   - Graceful fallback to default values when file is absent.

4. **Task 4: Typer CLI Skeleton & Doctor Probe (`src/bob/cli.py`)**
   - Initialize Typer app with `rich` console.
   - Implement `bob --version` returning version `0.1.0`.
   - Implement `bob doctor`:
     - Probe `GET {ollama_url}/api/tags` with timeout (1.5s).
     - Check if configured model exists in Ollama tags; measure latency.
     - Check presence of `gitleaks` and `semgrep` executables on PATH.
     - Display clean Rich table summary.
     - Exit code: `0`.
   - Register command stubs for Contract Addendum v1 commands (`check-install`, `intercept`, `guard-text`, `scan`, `verify`, `shim`, `allow`).

5. **Task 5: Unit Tests (`tests/unit/test_config.py`, `tests/unit/test_doctor.py`)**
   - Test default config values and custom YAML loading.
   - Test `Finding` and `Decision` dataclass instantiation and serialization.
   - Test `bob doctor` CLI execution via Typer `CliRunner`.

6. **Task 6: Verification & Commit**
   - Run `pytest` inside `.venv`.
   - Verify `bob doctor` runs cleanly on dev workstation.
   - Commit changes to `core/m0-skeleton`.
