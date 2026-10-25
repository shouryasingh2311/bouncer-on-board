# Contributing to BOB (`bouncer-on-board`)

Thanks for helping make vibe-coding safer for everyone. BOB is a local-first security tool designed to stop malicious package installs and agent hijack attempts before they execute, while using local open-weight AI to triage pre-deploy scan findings.

---

## 1. Development Setup

BOB targets **Python >= 3.10** and works natively across Windows (PowerShell/CMD) and macOS/Linux.

```bash
# Clone the repository
git clone https://github.com/shouryasingh2311/bouncer-on-board.git
cd bouncer-on-board

# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install development dependencies in editable mode
pip install -e .
pip install pytest
```

---

## 2. Running Tests

All unit tests and integration tests run offline against our built-in mock registry:

```bash
# Run all unit tests
pytest tests/unit

# Run contract tests by milestone tag
pytest tests/integration -m m1
pytest tests/integration -m m2
pytest tests/integration -m m3
```

---

## 3. Branching & PR Workflow

We follow trunk-based development with short-lived, single-topic branches and squash merges into `main`:

1. Sync your local `main`:
   ```bash
   git checkout main
   git pull origin main
   ```
2. Create a topic branch using standard prefixes:
   - Features: `feat/<feature-name>`
   - Bug fixes: `fix/<bug-name>`
   - Documentation: `docs/<topic>`
   - Tooling & CI: `chore/<topic>`
3. Follow conventional commit messages: `feat(pkg): ...`, `test(pkg): ...`, `docs: ...`, `fix(guard): ...`.
4. Keep PRs small and focused. Rebase onto `origin/main` before opening PRs.

---

## 4. How to Add a Detection Rule

To add a prompt injection detection rule:

1. Open `src/bob/data/rules/injection.yaml` and add an entry:
   ```yaml
   - id: INJ-025
     title: Human-readable title
     severity: high # or critical, medium, low
     regex: '(?i)your_regex_pattern_here'
   ```
2. Add a corresponding test case in `tests/unit/test_injection.py` validating that harmless text passes (exit 0) and hostile samples trigger the rule id.

---

## 5. What We Do NOT Accept (Axioms)

To maintain trust and security integrity, we will reject PRs that introduce:

- **Auto-applied AI code patches**: AI proposes fixes; human developers and deterministic checks prove them.
- **Cloud-by-default or telemetry**: BOB must function 100% offline and keep code local.
- **Dynamic execution of untrusted code**: We never `eval`, `exec`, or import candidate packages during static analysis or inspection.
- **Overriding Critical/High findings with LLMs**: The AI layer triages and annotates, but cannot downgrade critical or high deterministic findings.
- **Claims of "100% secure" or "bulletproof"**: We report deterministic tripwires honestly without false guarantees.
