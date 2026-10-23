# BOB (bouncer-on-board)

> **Zero-Trust IDE Agent Firewall & Pre-Deploy Security Gatekeeper**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Model: Gemma 4 E2B](https://img.shields.io/badge/Model-Gemma%204%20E2B%20(~5.1B)-orange.svg)](https://ollama.com/library/gemma4)
[![Track: MLH Hacktoberfest](https://img.shields.io/badge/MLH-Best%20Open--Source%20AI%20Project-red.svg)](https://hacktoberfest.mlh.io/)

Vibe-coding agents ship fast, but they blindly install hallucinated packages, trigger malicious install-time scripts (`preinstall` / `setup.py`), leak credentials via prompt injection, and commit unreviewed vulnerabilities. **BOB is a local-first bouncer that enforces a two-checkpoint zero-trust boundary around coding agents.**

---

## 🏆 MLH Hackathon Track Checklist ("Best Open-Source AI Project")

| Requirement | Implementation in BOB | Source / Verification |
|:---|:---|:---|
| **Small Language Model** | **Gemma 4 E2B** via Ollama (`gemma4:e2b`) | [Ollama Library](https://ollama.com/library/gemma4) / [Google Model Card](https://ai.google.dev/gemma) |
| **Parameter Count** | **~5.1B total weights** / **~2.3B effective active** ($\le$ 10B limit) | Copied directly from Gemma 4 Model Card |
| **Model Terms & License** | **Apache-2.0 License** | Open-weight $\ne$ automatically open-source; terms verified |
| **Key Dependencies** | `typer`, `rich`, `httpx`, `pyyaml` (Runtime) | `gitleaks`, `semgrep`, OSV API (Optional scanners) |
| **Project License** | **MIT License** | See [LICENSE](LICENSE) file |
| **Visible AI Role** | Local SLM triage, plain-English explanations, verified diffs | Visible in demo CLI + with/without-AI eval benchmark |

---

## 🛡️ Two-Checkpoint Architecture

```
                 ┌─────────────────────────────────────────────────────────────┐
                 │                   Path 1: `bob intercept`                   │
  Agent Action ─►│  Pre-Execution Gate: Blocks hallucinated packages, typos,  │─► Executed
                 │  install scripts, and credential reads BEFORE execution.    │   (or Blocked)
                 └─────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
                 ┌─────────────────────────────────────────────────────────────┐
                 │                     Path 2: `bob scan`                      │
  Pre-Deploy   ─►│  Pre-Deploy Gate: Parallel deterministic tripwires + local  │─► Ship / PR
                 │  Gemma 4 triage, plain-English explanations & patch diffs.  │
                 └─────────────────────────────────────────────────────────────┘
```

1. **Path 1 — `bob intercept` (Live, <400ms target, deterministic only):** Intercepts agent commands and file reads *before anything runs*. Scanning after installation is too late because npm lifecycle scripts and Python sdist builds execute code immediately upon download.
2. **Path 2 — `bob scan` (Pre-deploy security gate):** Runs deterministic scanners (`gitleaks`, `semgrep`, OSV, built-ins) in parallel, then uses **local Gemma 4** to triage false positives, explain risks in plain English, and generate verified patches.

*For full sequence diagrams and defense-in-depth layers, see [docs/architecture.md](docs/architecture.md).*

---

## ⚡ 60-Second Quickstart

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) running locally: `ollama run gemma4:e2b`

### Windows (PowerShell)
```powershell
# (Run once if script execution is restricted: Set-ExecutionPolicy -Scope Process Bypass)
git clone https://github.com/<owner>/bouncer-on-board.git; cd bouncer-on-board
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -e .
bob doctor
bob check-install pypi demo-good-lib
bob scan demo/vulnerable_app --no-ai
```

### macOS / Linux (Bash)
```bash
git clone https://github.com/<owner>/bouncer-on-board.git && cd bouncer-on-board
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
bob doctor
bob check-install pypi demo-good-lib
bob scan demo/vulnerable_app --no-ai
```

> **Deterministic Fallback by Design:** If Ollama is offline or Gemma 4 is not pulled, BOB automatically falls back to static rule explanation templates. BOB **never** crashes or fails closed into silence.

---

## 💻 CLI Reference & Contract

| Command | Purpose | Exit Codes |
|:---|:---|:---|
| `bob intercept --adapter generic --cmd "<cmd>"` | Live pre-execution hook entrypoint | `0` allow, `2` block |
| `bob check-install <pypi\|npm> <pkg>[==ver] [--json]` | Manual package gate inspection | `0` allow/warn, `2` block |
| `bob scan <path> [--no-ai] [--out-dir <dir>]` | Pre-deploy security gate & SARIF scan | `0` pass, `1` gate failed (critical/high) |
| `bob guard-text <path> [--ai]` | Prompt injection scan on docs/issues | `0` clean, `2` threat detected |
| `bob verify <fingerprint-prefix>` | Re-run originating check to verify patch | `0` fixed, `1` still present |
| `bob doctor` | Environment diagnostics & Ollama latency | `0` ready |
| `bob shim install\|uninstall` | Manage L2 terminal PATH wrapper scripts | `0` success |
| `bob allow <pkg>` | **Human-only** allowlist entry in `.bob/` | `0` success |

---

## 🤖 The AI's Role (Gemma 4 SLM)

Deterministic scanners detect; the local SLM triages, explains, and suggests remedies. Input to language models can be adversarial, so BOB enforces strict code-level guardrails:

| What Gemma 4 Does | What Gemma 4 NEVER Does |
|:---|:---|
| ✅ Explains flagged security issues in plain English | ❌ **NEVER** detects vulnerabilities directly |
| ✅ Generates contextual patch diffs and fix snippets | ❌ **NEVER** overrides or down-ranks Critical / High findings |
| ✅ Down-ranks noisy Medium / Low false positives with review note | ❌ **NEVER** approves an untrusted or blocked package |
| ✅ Optional second-opinion advisory on prompt injection text | ❌ **NEVER** auto-applies code patches or edits files |
| ✅ Runs 100% locally on `localhost:11434` (no source leaks) | ❌ **NEVER** executes inside the live interception path |

> [!CAUTION]
> **Zero Findings Posture:** `0 known deterministic tripwires hit. This does not guarantee the absence of business-logic vulnerabilities.` BOB never claims to be "100% secure" or "bulletproof."

---

## 📊 Evaluation & Benchmark Results

To measure the real-world utility of the small language model, BOB runs `eval/run_eval.py` against planted true positives and documented test decoys in `demo/vulnerable_app`:

| Evaluation Metric | Deterministic Only (`--no-ai`) | With Local Gemma 4 Triage | Impact / Delta |
|:---|:---:|:---:|:---|
| **True Positives Detected** | 8 / 8 (100%) | 8 / 8 (100%) | Zero regression; all critical threats caught |
| **Planted Test Decoys Flagged** | 3 / 3 (100% false alarms) | 0 / 3 (triaged to review) | **100% reduction** in noisy false-alarm blocks |
| **Critical / High Findings Preserved** | 100% | 100% | Hard security invariant: AI never overrides high |
| **Fix Verification Rate (`bob verify`)** | N/A | **100% verified** | Proves proposed patch clears original tripwire |
| **Scan Latency** | ~0.8s | ~3.4s (local E2B) | Edge-friendly, runs entirely on CPU/laptop |

*The model cannot override critical security findings, but successfully eliminates alert fatigue by identifying dummy test keys and generating verified remediation diffs.*

---

## ⚠️ Known Limitations (PROJECT.md Section 17)

- Detects known tripwires only; does not find business-logic flaws or novel malware; small local models can misjudge, so they never override deterministic criticals.
- A newly published package that looks clean to heuristics can still be malicious.
- `python -m pip` and other indirect installs can bypass PATH shims; IDE-hook parsing mitigates this where hooks exist.
- IDE hook coverage depends on the IDE's documented capabilities.
- Registry or OSV outages degrade checks (see `offline_policy`).

---

## 📖 Documentation & Community

- [Architecture & Diagrams](docs/architecture.md) — Comprehensive sequence and component flowcharts
- [Verified Quickstart Run](docs/quickstart-verified.md) — Local execution traces and reproducible proof
- [Usability Test Log](docs/usability-test.md) — Cold outside-reader verification log
- [Agent Guard Skill](skills/bob-install-guard/SKILL.md) — Spec-compliant advisory agent skill
- [Third-Party Notices](THIRD_PARTY_NOTICES.md) — Tool licenses, model terms, and dataset attributions
- [Contributing Guide](CONTRIBUTING.md) — Development setup, testing, and adding detection rules
- [License](LICENSE) — MIT License
