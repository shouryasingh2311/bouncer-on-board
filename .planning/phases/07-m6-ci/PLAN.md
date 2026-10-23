# PLAN.md — Phase 7: M6 CI Workflow, Dependency Audit & Final Verification

## Goal
Implement GitHub Actions CI workflow (`.github/workflows/bob.yml`), verify packaging data in `pyproject.toml`, execute dependency security audit, ensure zero secret leakage across codebase, and run full end-to-end regression test suite.

## Tasks
1. **Task 1: GitHub Actions CI Gate (`.github/workflows/bob.yml`)**
   - Run tests across Ubuntu on Python 3.10.
   - Run `bob doctor`.
   - Run `bob scan src --no-ai`.

2. **Task 2: Package Data Hygiene (`pyproject.toml`)**
   - Configure `package-data` for `data/*.json` and `data/rules/*.yaml`.

3. **Task 3: Security & Dependency Audit**
   - Audit installed dependencies against OSV.
   - Run `bob scan src --no-ai` to ensure clean pre-deploy gate.

4. **Task 4: Regression Test Verification**
   - Run 100% test suite in `.venv`.
