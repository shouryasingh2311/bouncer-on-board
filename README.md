<p align="center">
  <img src="docs/assets/banner.png" alt="BOB — Bouncer-on-Board Banner" width="100%">
</p>

# BOB (bouncer-on-board)

> **Zero-Trust IDE Agent Firewall & Pre-Deploy Security Gatekeeper**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Model: Gemma 4 / Gemini / OpenAI](https://img.shields.io/badge/AI%20Triage-Local%20%7C%20Cloud-orange.svg)](https://ollama.com/)

Vibe-coding agents ship fast, but they blindly install hallucinated packages, trigger malicious install-time scripts (`preinstall` / `setup.py`), leak credentials via prompt injection, and commit unreviewed vulnerabilities. **BOB is a local-first bouncer that enforces a two-checkpoint zero-trust boundary around coding agents.**

---

## ✨ Key Capabilities

- **Live Pre-Action Interception (<400ms target)**: Intercepts `pip`, `npm`, and terminal actions via IDE hooks or PATH shims before malicious install-time scripts can execute.
- **Supply Chain & Package Gate**: Statically verifies packages against embedded top-5,000 caches, human allowlists, release age, typosquatting heuristics, and live OSV advisories.
- **Sensitive-Path Protection**: Blocks unauthorized agent read/write operations targeting `.env`, `.ssh/`, `.git/`, and cloud credential files.
- **Prompt Injection Defense**: Scans text and markdown inputs for instruction-override phrases and credential-harvesting prompts.
- **Pre-Deploy Security Scanner**: Aggregates parallel AST checks, secret finders, and external SARIF tools (`gitleaks`, `semgrep`).
- **AI Triage & Patch Generation**: Integrates local open-weight SLMs (Gemma via Ollama) or Cloud AI (Google Gemini, OpenAI, Groq) for false-positive triage with strict **Security Axiom 2** enforcement (AI never downgrades Critical or High findings).

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
2. **Path 2 — `bob scan` (Pre-deploy security gate):** Runs deterministic scanners (`gitleaks`, `semgrep`, OSV, built-ins) in parallel, then uses **local Gemma 4 or Cloud AI** to triage false positives, explain risks in plain English, and generate verified patches.

*For full sequence diagrams and defense-in-depth layers, see [docs/architecture.md](docs/architecture.md).*

---

## ⚡ 60-Second Quickstart

### Quick Install (One-Liner)
```bash
pip install git+https://github.com/shouryasingh2311/bouncer-on-board.git
bob doctor
```

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com/) running locally: `ollama run gemma4:e2b` (Optional, for local SLM triage) or Google Gemini / OpenAI API key.

### Windows (PowerShell)
```powershell
# (Run once if script execution is restricted: Set-ExecutionPolicy -Scope Process Bypass)
git clone https://github.com/shouryasingh2311/bouncer-on-board.git; cd bouncer-on-board
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -e .
bob doctor
bob check-install pypi requests
bob scan src --no-ai
```

### macOS / Linux (Bash)
```bash
git clone https://github.com/shouryasingh2311/bouncer-on-board.git && cd bouncer-on-board
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
bob doctor
bob check-install pypi requests
bob scan src --no-ai
```

> **Deterministic Fallback by Design:** If Ollama or Cloud AI is offline, BOB automatically falls back to static rule explanation templates. BOB **never** crashes or fails closed into silence.

---

## 🧪 Interactive Examples & Walkthrough

You can test BOB capabilities interactively in seconds:

### Example 1: Package Gate Attack Defense (Blocks Typosquats & Hallucinations)
Simulate an AI agent attempting to download a hallucinated or typosquatted package:
```bash
bob check-install pypi reqeusts
```
**Expected Outcome**: Instant exit code `2` block:
```
BOB BLOCKED [BOB-0001] rule=PKG-NOT-FOUND package=reqeusts
Reason: Package 'reqeusts' does not exist on PYPI (likely hallucinated).
Do: remove it, ask the user, or pick a verified package. Do not retry this install.
```

### Example 2: Prompt Injection Defense (`bob guard-text`)
Simulate an AI agent evaluating untrusted instructions or prompt injection attempts:
```bash
bob guard-text prompt.md
```
**Expected Outcome**: Threats flagged before agent execution:
```
BOB BLOCKED [BOB-0001] rule=INJ-001 file=prompt.md
Reason: Instruction override phrase
BOB BLOCKED [BOB-0002] rule=INJ-020 file=prompt.md
Reason: Instruction to send secrets or env data to a URL
```

### Example 3: Pre-Deploy Security Gate (`bob scan`)
Scan any source tree for hardcoded secrets, SQL injection, dynamic eval, and unverified TLS:
```bash
bob scan src --no-ai
```
**Expected Outcome**: Generates `.bob/report.md` and `.bob/report.json`:
```
BOB Pre-Deploy Scan Summary (src)
+------------------+
| Severity | Count |
|----------+-------|
| CRITICAL | 0     |
| HIGH     | 0     |
| MEDIUM   | 0     |
| LOW      | 0     |
| INFO     | 0     |
+------------------+
0 known deterministic tripwires hit.
```

### Example 4: Verify Single-Finding Fix (`bob verify`)
Run `bob verify` against a finding fingerprint prefix (e.g. from `.bob/report.md`):
```bash
bob verify 8a08c677ec
```
**Expected Outcome**: Re-tests originating rule without having to rescan the entire project.

### Test 5: Switch AI Intelligence Modes (`bob setup` & `bob doctor`)
Configure local Gemma via Ollama, Cloud AI (Google Gemini, OpenAI, Groq), or 100% offline Pure Deterministic Mode:
```bash
bob setup
bob doctor
```

---

## 💻 CLI Reference & Complete Command Guide

### Master Command Quick Reference

| Command | Purpose | Key Flags | Exit Codes |
|:---|:---|:---|:---|
| [`bob setup`](#1-bob-setup) | Interactive onboarding assistant for AI models & IDE protection | *None (interactive wizard)* | `0` success |
| [`bob protect`](#2-bob-protect) | Configure automated interception hooks for IDE workspaces | `[path]`, `--ide` | `0` success |
| [`bob check-install`](#3-bob-check-install) | Manual package gate inspection (typos, age, scripts, CVEs) | `<ecosystem>`, `<pkg>`, `--json` | `0` allow, `2` block |
| [`bob intercept`](#4-bob-intercept) | Live pre-execution gatekeeper for agent commands & sensitive paths | `--cmd`, `--adapter`, `--path` | `0` allow, `2` block |
| [`bob scan`](#5-bob-scan) | Pre-deploy security gate & SARIF scan with local Gemma triage | `[path]`, `--no-ai`, `--out-dir` | `0` pass, `1` blocked |
| [`bob verify`](#6-bob-verify) | Re-run originating tripwire to verify a patch resolved finding | `<fingerprint-prefix>` | `0` fixed, `1` still failing |
| [`bob guard-text`](#7-bob-guard-text) | Detect prompt injection in docs/issues before agent ingests it | `<path>`, `--ai` | `0` clean, `2` threat |
| [`bob audit`](#8-bob-audit) | Scan project lockfiles against OSV open-source vulnerability database | `[--path]` | `0` clean, `1` vulnerable |
| [`bob shim`](#9-bob-shim) | Manage L2 terminal PATH wrapper scripts for package managers | `install`, `uninstall` | `0` success |
| [`bob allow`](#10-bob-allow) | **Human-only** allowlist entry in `.bob/allowlist.yaml` | `<pkg>`, `--ecosystem` | `0` success |
| [`bob doctor`](#11-bob-doctor) | System environment diagnostics, scanner checks & Ollama latency | *None* | `0` ready |

---

### Detailed Command Guide & Usage

#### 1. `bob setup`
Interactive, beginner-friendly onboarding assistant. Guides developers through configuring their AI model provider and setting up IDE workspace protection in two quick steps.

```bash
# Launch interactive setup
bob setup
```

- **Step 1 (AI Provider)**: Choose between:
  1. *Local Ollama* (auto-detects local Ollama server on `localhost:11434`, pulls or selects Gemma 4 / Gemma 2).
  2. *Cloud AI APIs* (configures Gemini, OpenAI, Anthropic, DeepSeek, OpenRouter, or Groq with an API key).
  3. *Deterministic Rule Engine* (offline, zero external AI dependencies).
- **Step 2 (IDE Protection)**: Choose your editor (VS Code, Google Antigravity, Cursor, Windsurf, or Generic) to automatically scaffold pre-execution interception hooks and agent firewall rules.

---

#### 2. `bob protect`
Scaffolds automated pre-execution interception hooks, IDE tasks, and zero-trust agent firewall guidelines inside a project workspace.

```bash
# Protect current workspace (auto-detects IDE)
bob protect

# Protect a specific project folder for VS Code
bob protect /path/to/project --ide vscode

# Protect for Google Antigravity / Cursor
bob protect . --ide antigravity
```

- **What it configures**:
  - `.agents/rules/bob-agent-firewall.md` — Mandatory instructions instructing AI coding agents to route shell commands through BOB.
  - `.vscode/tasks.json` — Pre-install and pre-commit task triggers.
  - Verifies local `.bob/` configuration state.

---

#### 3. `bob check-install`
Manually inspects a package before installing it. Evaluates typosquatting distance against popular packages, package release age, download metrics, hidden install-time scripts (`preinstall`, `setup.py`), and known vulnerabilities via OSV.

```bash
# Inspect a safe PyPI package
bob check-install pypi requests

# Check a specific version of an npm package
bob check-install npm express==4.18.2

# Check a suspicious typosquatted package (will block with exit code 2)
bob check-install pypi reqeusts

# Output structured JSON result for CI/CD scripting
bob check-install pypi demo-malicious-pkg --json
```

- **Exit Codes**: `0` = Allowed (or Low warning); `2` = Blocked (Quarantined/Critical risk).

---

#### 4. `bob intercept`
The high-speed pre-execution hook entrypoint (<400ms target). Executed automatically by IDE agent hooks, wrapper shims, or terminal wrappers before any command touches the operating system or file system.

```bash
# Intercept an agent command intending to install a package
bob intercept --adapter generic --cmd "pip install reqeusts"

# Intercept a command attempting to read sensitive credential files
bob intercept --adapter generic --cmd "cat ~/.ssh/id_rsa"

# Intercept a direct file read probe
bob intercept --adapter generic --path ".env"
```

- **Protection Scope**:
  - Blocks typosquatted or non-existent hallucinated packages.
  - Blocks execution of packages containing malicious install-time hooks.
  - Blocks unauthorized access to sensitive credential files (`.env`, `.ssh/`, `.aws/`, `.git/config`).
  - Blocks tamper attempts against BOB itself (`rm -rf .bob`).
- **Exit Codes**: `0` = Allow command; `2` = Block command with plain-English explanation.

---

#### 5. `bob scan`
The pre-deploy zero-trust security gatekeeper. Runs parallel deterministic tripwires (`gitleaks`, `semgrep`, OSV dependency scan, and built-in AST checks), then invokes the local Small Language Model (Gemma 4 SLM) to triage false positives, explain root causes, and produce verified remediation diffs.

```bash
# Run full scan with local AI triage and explanations
bob scan .

# Run deterministic scan only (faster, zero AI dependencies)
bob scan ./src --no-ai

# Specify custom output directory for SARIF and Markdown reports
bob scan . --out-dir ./audit-reports
```

- **Outputs**:
  - Formatted terminal report with severity breakdown.
  - `.bob/reports/scan_report.md` — Detailed report with code snippets, CWEs, and suggested diffs.
  - `.bob/reports/scan_report.sarif` — Standard SARIF format for GitHub Security and IDE integration.
- **Exit Codes**: `0` = Passed (zero Critical/High findings); `1` = Gate failed (Critical or High findings detected).

---

#### 6. `bob verify`
Re-runs the exact originating tripwire check that flagged a vulnerability to mathematically prove whether your code patch fixed the issue before committing.

```bash
# Verify a specific finding using its fingerprint prefix from bob scan
bob verify sec-001

# Verify after editing code to ensure secret or bug is eliminated
bob verify vuln-3a7b
```

- **Exit Codes**: `0` = Verified fixed; `1` = Finding still active (patch unsuccessful).

---

#### 7. `bob guard-text`
Scans untrusted markdown files, issue templates, PR descriptions, or documentation for prompt injection payloads, instruction overrides, and data exfiltration markers before an AI coding agent ingests them into its context window.

```bash
# Scan a documentation file for prompt injection
bob guard-text docs/untrusted_issue.md

# Scan with second-opinion SLM semantic evaluation
bob guard-text README.md --ai
```

- **Exit Codes**: `0` = Clean (safe for agent ingestion); `2` = Threat detected (prompt injection or instruction hijack found).

---

#### 8. `bob audit`
Scans all dependency lockfiles in the current workspace against the open-source OSV vulnerability database. Supports `requirements.txt`, `package-lock.json`, `pnpm-lock.yaml`, `Pipfile.lock`, and `poetry.lock`.

```bash
# Audit current repository dependencies
bob audit

# Audit a specific directory or microservice
bob audit --path ./backend
```

- **Exit Codes**: `0` = Clean (no known CVE advisories); `1` = Vulnerable dependencies found.

---

#### 9. `bob shim`
Installs or uninstalls lightweight PATH wrapper shims for standard package managers (`pip`, `npm`, `npx`, `uv`). Shims automatically route command-line package installations through BOB's pre-execution gate before packages can execute lifecycle scripts.

```bash
# Install PATH wrapper shims
bob shim install

# Uninstall PATH wrapper shims
bob shim uninstall
```

- **Exit Codes**: `0` = Success.

---

#### 10. `bob allow`
Human-only override mechanism. Permits a human developer to explicitly allow a flagged or unreleased package by recording their username, reason, and timestamp in `.bob/allowlist.yaml`. AI coding agents are strictly forbidden from executing this command.

```bash
# Allow an internal private or flagged PyPI package
bob allow my-private-company-pkg

# Allow an npm package
bob allow @internal/custom-lib --ecosystem npm
```

- **Exit Codes**: `0` = Package recorded in `.bob/allowlist.yaml`.

---

#### 11. `bob doctor`
Runs a full health check on the local system environment, reporting installed scanner binaries (`gitleaks`, `semgrep`), Ollama connectivity and model response latency, configured provider, active IDE protection, and PATH shim status.

```bash
# Run system diagnostic health check
bob doctor
```

- **Exit Codes**: `0` = System ready.

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

To measure the real-world utility of the small language model, BOB was benchmarked against planted true positives and documented test decoys:

| Evaluation Metric | Deterministic Only (`--no-ai`) | With Local Gemma 4 Triage | Impact / Delta |
|:---|:---:|:---:|:---|
| **True Positives Detected** | 8 / 8 (100%) | 8 / 8 (100%) | Zero regression; all critical threats caught |
| **Planted Test Decoys Flagged** | 3 / 3 (100% false alarms) | 0 / 3 (triaged to review) | **100% reduction** in noisy false-alarm blocks |
| **Critical / High Findings Preserved** | 100% | 100% | Hard security invariant: AI never overrides high |
| **Fix Verification Rate (`bob verify`)** | N/A | **100% verified** | Proves proposed patch clears original tripwire |
| **Scan Latency** | ~0.8s | ~3.4s (local E2B) | Edge-friendly, runs entirely on CPU/laptop |

*The model cannot override critical security findings, but successfully eliminates alert fatigue by identifying dummy test keys and generating verified remediation diffs.*

---

## ⚠️ Known Limitations

- Detects known tripwires only; does not find business-logic flaws or novel malware; small local models can misjudge, so they never override deterministic criticals.
- A newly published package that looks clean to heuristics can still be malicious.
- `python -m pip` and other indirect installs can bypass PATH shims; IDE-hook parsing mitigates this where hooks exist.
- IDE hook coverage depends on the IDE's documented capabilities.
- Registry or OSV outages degrade checks (see `offline_policy`).

---

## 📖 Documentation & Community

- [Architecture & Diagrams](docs/architecture.md) — Comprehensive sequence and component flowcharts
- [Verified Quickstart Run](docs/quickstart-verified.md) — Local execution traces and reproducible proof
- [Agent Guard Skill](skills/bob-install-guard/SKILL.md) — Spec-compliant advisory agent skill
- [Third-Party Notices](THIRD_PARTY_NOTICES.md) — Tool licenses, model terms, and dataset attributions
- [Contributing Guide](CONTRIBUTING.md) — Development setup, testing, and adding detection rules
- [License](LICENSE) — MIT License

