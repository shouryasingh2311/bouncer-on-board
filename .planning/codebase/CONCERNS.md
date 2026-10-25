# Technical Concerns, Risks & Mitigations

## 1. Security Axiom 2 (AI Downgrade Risk)
- **Risk**: An LLM could hallucinate, be jailbroken by an adversary, or mistakenly deem a real secret or backdoor to be benign, downgrading a Critical or High finding.
- **Mitigation**: Strict code-level enforcement in `src/bob/ai/triage.py`. Even if the AI outputs `severity: low` or `severity: info`, the engine enforces a floor: if the deterministic tripwire flagged Critical or High, the final verdict CANNOT be lowered.

## 2. Windows PATH Shim Bypasses
- **Risk**: If an IDE agent runs `python -m pip install <pkg>` instead of `pip install <pkg>`, it bypasses the `pip.cmd` shim located on the system PATH.
- **Mitigation**: Dual-layer defense:
  - Layer 1: Antigravity IDE lifecycle hook (`.agents/hooks.json`) catches commands directly at the IDE process boundary before shell dispatch.
  - Layer 2: `bob intercept` called from IDE tool adapters parses full compound commands and catches `python -m pip`.

## 3. Offline Resilience & Network Flakiness
- **Risk**: IDE agents running in air-gapped environments or behind strict corporate proxies could cause `bob intercept` to hang or fail if external APIs (OSV, PyPI, npm) timeout.
- **Mitigation**:
  - Embedded offline top-5,000 package caches (`top_pypi.json`, `top_npm.json`) resolve known good packages in <15ms without touching the network.
  - Strict 2-second timeout on external requests.
  - Deterministic fallback triage templates (`src/bob/ai/fallback.py`) provide actionable advice when Ollama or Cloud AI is unavailable.

## 4. Directory Scan Hangs on Large Systems
- **Risk**: Running `bob scan` without arguments from user root (`C:\Users\<user>`) would attempt to traverse huge system directories (`AppData`, `node_modules`, virtualenvs), freezing the terminal.
- **Mitigation**:
  - Implemented `test_scan_safety.py` and safety guards in `src/bob/scan/engine.py` refusing to scan user home directories or drive roots directly, returning clear guidance to point BOB at specific project folders.
  - Comprehensive ignore patterns for `.venv`, `node_modules`, `.git`, `.bob`, `__pycache__`.

## 5. Stale Remote Branches on GitHub
- **Risk**: 15 remote feature and documentation branches remain on `origin` after being merged into `main` via earlier PRs, creating noise in git client branch listings.
- **Remediation**: Remote branches can be safely pruned (`git push origin --delete <branches>`) without impacting history, as all commits are preserved in `main`.
