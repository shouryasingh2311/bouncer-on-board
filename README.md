<p align="center">
  <img src="docs/assets/banner.png" alt="BOB Banner" width="100%">
</p>

# BOB (bouncer-on-board)

<p align="center">
  <strong>Zero-trust agent firewall and pre-deploy security gatekeeper.</strong><br>
  Intercepts hallucinated packages, malicious install scripts, prompt injections, and leaked secrets before anything executes.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="package.json"><img src="https://img.shields.io/badge/npm-zero--dependency-brightgreen.svg" alt="Zero npm dependencies"></a>
  <a href="tests"><img src="https://img.shields.io/badge/Tests-116%20passed-success.svg" alt="116 tests passed"></a>
  <a href="skills/bob/SKILL.md"><img src="https://img.shields.io/badge/IDE%20Skill-Claude%20%7C%20Antigravity%20%7C%20Cursor-orange.svg" alt="IDE Skills"></a>
  <a href="#benchmarks"><img src="https://img.shields.io/badge/Latency-%3C400ms-purple.svg" alt="Sub-400ms Interception"></a>
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> &bull;
  <a href="#why-bob-exists">Why BOB</a> &bull;
  <a href="#what-bob-does">Capabilities</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#ide-slash-commands">IDE Commands</a> &bull;
  <a href="#command-reference">CLI Reference</a> &bull;
  <a href="#benchmarks">Benchmarks</a>
</p>

---

## Why BOB exists

AI coding agents run terminal commands autonomously. While they write code quickly, they introduce a distinct set of supply-chain risks:

1. **Slopsquatting & Model Hallucinations**: LLMs frequently hallucinate package names that do not exist on PyPI or npm. Attackers monitor these hallucinations, register the names with malicious payloads, and compromise autonomous agents.
2. **Install-Time Code Execution**: `npm` lifecycle scripts (`preinstall`, `install`, `postinstall`) and Python `setup.py` files execute arbitrary code *during download and unpacking*. 
3. **Sensitive Path Exfiltration**: Agents prompted by untrusted text or hostile dependencies can read `.env`, `~/.ssh/id_rsa`, or cloud keys and pipe them to external URLs.

### The timing problem: Why traditional audit tools miss agent attacks

| Lifecycle Point | Traditional Tools (`npm audit`, `pip-audit`, Dependabot) | BOB (`bouncer-on-board`) |
|:---|:---|:---|
| **Before Download** | Does nothing. Does not monitor the terminal or IDE actions. | **Pre-Execution Gate**: Inspects package age, typosquat distance, and archive AST statically over HTTPS. |
| **During Download** | Does nothing. `preinstall` or `setup.py` shell scripts execute freely. | **Execution Prevented**: Unverified or hallucinated packages never hit the disk; execution is halted with exit code `2`. |
| **After Install** | Scans lockfiles for known CVEs. Attackers have already stolen credentials. | **Pre-Deploy Gate**: Runs parallel secret scanners, AST rules, and local AI triage before code is committed. |

---

## What BOB does

- **Package Interception Gate**: Intercepts `pip`, `npm`, `yarn`, `pnpm`, and `uv` commands in real time. Blocks unregistered packages, typosquats, and packages under 14 days old before they download.
- **Static Archive Inspection**: Inspects archive bytes (`.tar.gz`, `.whl`) statically over HTTPS using Python's `ast.parse` and JSON parsers without running candidate scripts or using `eval`.
- **Sensitive Path Protection**: Prevents coding agents from reading or modifying `.env`, `.ssh/`, `.aws/credentials`, or `.git/config`.
- **Prompt Injection Defense**: Evaluates markdown instructions, PR descriptions, and issue text for instruction-override phrases and credential-harvesting patterns before an agent reads them into context.
- **Pre-Deploy Security Scanner**: Aggregates parallel static tripwires for hardcoded API keys (Anthropic, OpenAI, AWS, GCP, Stripe, Slack, JWT, DB URLs), SQL injection, dynamic eval, and unverified TLS.
- **Zero-Token IDE-Native AI Triage**: When running inside Claude Code, Google Antigravity, or Cursor, BOB uses your active IDE model to explain findings and propose fix diffs in chat. External API keys or local Ollama instances are completely optional.

---

## Architecture

BOB enforces a two-checkpoint defense boundary:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               Path 1: `bob intercept`                                  │
│   Agent Action ──► [ Pre-Execution Gate: Intercepts commands & sensitive paths ] ──►   │ Executed
│                    Target latency < 400ms (deterministic AST & cached registry checks) │ (or Blocked)
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Path 2: `bob scan`                                     │
│   Pre-Deploy   ──► [ Pre-Deploy Gate: Parallel deterministic tripwires + AI triage ] ──► Ship / PR
│                    Plain-English explanations, false-positive downranking & diffs      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Pre-execution gate (`bob intercept`)**: Runs synchronously before an agent command touches the OS. Target latency is under 400ms using deterministic cache and AST heuristics. No LLM calls occur on this path.
2. **Pre-deploy gate (`bob scan`)**: Runs before code is committed or deployed. Orchestrates parallel scanners, normalizes outputs into SARIF, and triages findings using your configured AI provider.

For full sequence diagrams and defense layers, see [docs/architecture.md](docs/architecture.md).

---

## Quickstart

### Option A: Install via npx (Zero dependencies)
Run interactive onboarding and configure IDE skills and terminal shims in one command:

```bash
# Interactive setup assistant
npx bouncer-on-board install

# Or install globally via npm
npm install -g bouncer-on-board
bob doctor
```

### Option B: Install via Python
```bash
pip install git+https://github.com/shouryasingh2311/bouncer-on-board.git
bob doctor
```

### Option C: Clone and run locally
```bash
git clone https://github.com/shouryasingh2311/bouncer-on-board.git
cd bouncer-on-board
python -m venv .venv

# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

pip install -e .
bob doctor
```

---

## IDE slash commands

BOB integrates natively with modern coding agent environments via `/bob` slash commands:

| IDE / Environment | Integration Mechanism | Key Slash Commands |
|:---|:---|:---|
| **Claude Code** | Global Skill (`~/.claude/skills/bob/SKILL.md`) + PATH shims | `/bob scan`, `/bob check <pypi\|npm> <pkg>`, `/bob doctor` |
| **Google Antigravity** | Workspace Skill (`~/.gemini/config/skills/bob/SKILL.md`) + PreToolUse Hook | `/bob scan`, `/bob check <pypi\|npm> <pkg>`, `/bob protect` |
| **Cursor / VS Code** | Cursor Rules (`.cursor/rules/bob.mdc`) + Terminal shims | `/bob scan`, `/bob guard <file>`, `/bob doctor` |

> **Zero-token IDE AI:** When used as an IDE skill, external AI endpoints (Ollama, Gemini, OpenAI) are optional (`ai_provider: "ide_native"`). The host IDE agent (Claude, Gemini, Cursor) reviews BOB's structured findings and generates patches directly in your conversation.

---

## Examples

### 1. Blocking typosquats and hallucinated packages
Simulate an agent attempting to download a hallucinated or typosquatted package:

```bash
bob check-install pypi reqeusts
```

```text
BOB BLOCKED [BOB-0001] rule=PKG-NOT-FOUND package=reqeusts
Reason: Package 'reqeusts' does not exist on PYPI (likely AI hallucinated / slopsquatting vector).
Do: remove it, ask the user, or pick a verified package. Do not retry this install.
```
*Exit code: `2` (Command execution halted)*

### 2. Guarding against prompt injection
Audit untrusted markdown files, issue descriptions, or external prompts before ingesting them into an agent's context window:

```bash
bob guard-text docs/untrusted_issue.md
```

```text
BOB BLOCKED [BOB-0001] rule=INJ-001 file=docs/untrusted_issue.md
Reason: Instruction override phrase ("ignore all previous instructions")
BOB BLOCKED [BOB-0002] rule=INJ-020 file=docs/untrusted_issue.md
Reason: Instruction to exfiltrate environment secrets to an external URL
```
*Exit code: `2` (Threat detected)*

### 3. Pre-deploy security gate
Scan source code for hardcoded secrets, SQL injection, dynamic code evaluation, and unverified TLS:

```bash
bob scan src --no-ai
```

```text
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
*Outputs: `.bob/report.md` (human summary), `.bob/report.json` (machine data), and standard SARIF report.*

### 4. Verifying a fix without rescanning
Verify that a specific patch resolved an issue without rescanning the entire repository:

```bash
bob verify 8a08c677ec
```
*Exit code: `0` (Fixed) or `1` (Still failing)*

### 5. Running diagnostics
Check the health of runtime dependencies, active shims, and configured AI provider:

```bash
bob doctor
```

```text
BOB System Diagnostics (Doctor)
+-----------------------------------------------------------------------------+
| Component     | Status             | Details                                |
|---------------+--------------------+----------------------------------------|
| Python        | OK                 | v3.10.6 (win32)                        |
| AI Mode       | IDE-Native         | Host IDE agent handles chat triage     |
| gitleaks      | Missing (Optional) | Built-in secrets tripwire will be used |
| semgrep       | Missing (Optional) | Built-in AST/regex tripwires used      |
| Node.js       | Installed          | C:\Program Files\nodejs\node.EXE       |
| Layer 2 Shims | Active             | 10 interceptors in ~/.bob/shims        |
+-----------------------------------------------------------------------------+
```

---

## Command reference

| Command | Purpose | Key Flags | Exit Codes |
|:---|:---|:---|:---|
| [`bob setup`](#bob-setup) | Interactive onboarding assistant for AI models and IDE protection | *None (interactive wizard)* | `0` success |
| [`bob protect`](#bob-protect) | Configure automated interception hooks and shims in workspace | `[path]`, `--ide` | `0` success |
| [`bob check-install`](#bob-check-install) | Inspect a package before installation (typos, age, scripts, CVEs) | `<ecosystem>`, `<pkg>`, `--json` | `0` allow, `2` block |
| [`bob intercept`](#bob-intercept) | Synchronous gatekeeper for agent commands and sensitive paths | `--cmd`, `--adapter`, `--path` | `0` allow, `2` block |
| [`bob scan`](#bob-scan) | Pre-deploy security gate and SARIF scanner with AI triage | `[path]`, `--no-ai`, `--out-dir` | `0` pass, `1` blocked |
| [`bob verify`](#bob-verify) | Re-test the exact check that flagged a vulnerability | `<fingerprint-prefix>` | `0` fixed, `1` failing |
| [`bob guard-text`](#bob-guard-text) | Audit text for prompt injection and instruction overrides | `<path>`, `--ai` | `0` clean, `2` threat |
| [`bob audit`](#bob-audit) | Scan project lockfiles against the OSV vulnerability database | `[--path]` | `0` clean, `1` vulnerable |
| [`bob shim`](#bob-shim) | Install or remove terminal PATH wrapper scripts | `install`, `uninstall` | `0` success |
| [`bob allow`](#bob-allow) | Human-only override to allowlist a package | `<pkg>`, `--ecosystem` | `0` success |
| [`bob doctor`](#bob-doctor) | System diagnostics for scanners, shims, and model status | *None* | `0` ready |

---

### Command details

#### `bob setup`
Interactive setup assistant. Configures your AI provider and sets up IDE workspace protection.

```bash
bob setup
```
- **Step 1 (AI Provider)**: Choose IDE-Native AI (recommended for IDE skills), local Ollama (Gemma), cloud APIs (Gemini, OpenAI, Groq), or pure deterministic mode.
- **Step 2 (IDE Protection)**: Choose your editor (VS Code, Google Antigravity, Cursor, Claude Code, or all) to configure hooks and shims.

#### `bob protect`
Configures pre-execution interception hooks, rule instructions, and PATH shims in the current or target workspace.

```bash
bob protect
bob protect /path/to/project --ide vscode
bob protect . --ide antigravity
```

#### `bob check-install`
Inspects a package before installation. Evaluates name similarity against top packages, release age, download metrics, install-time scripts (`preinstall`, `setup.py`), and OSV advisories.

```bash
bob check-install pypi requests
bob check-install npm express==4.18.2
bob check-install pypi reqeusts
bob check-install pypi demo-malicious-pkg --json
```

#### `bob intercept`
Synchronous pre-execution hook entrypoint. Called automatically by IDE hooks and PATH shims before commands touch the operating system.

```bash
bob intercept --adapter generic --cmd "pip install reqeusts"
bob intercept --adapter generic --cmd "cat ~/.ssh/id_rsa"
bob intercept --adapter generic --path ".env"
```

#### `bob scan`
Pre-deploy security gate. Runs parallel scanners (`gitleaks`, `semgrep`, OSV, and built-in AST checks), then invokes your configured AI provider to triage false positives, explain root causes, and produce fix diffs.

```bash
bob scan .
bob scan ./src --no-ai
bob scan . --out-dir ./audit-reports
```

#### `bob verify`
Re-runs the exact check that flagged a vulnerability to confirm whether your code patch resolved it.

```bash
bob verify sec-001
```

#### `bob guard-text`
Scans markdown files, issue templates, PR descriptions, or documentation for prompt injection payloads and data exfiltration markers before an agent reads them.

```bash
bob guard-text docs/untrusted_issue.md
```

#### `bob audit`
Scans dependency lockfiles against the OSV vulnerability database. Supports `requirements.txt`, `package-lock.json`, `pnpm-lock.yaml`, `Pipfile.lock`, and `poetry.lock`.

```bash
bob audit
bob audit --path ./backend
```

#### `bob shim`
Manages PATH wrapper shims for `pip`, `npm`, `yarn`, `pnpm`, and `uv`. Shims route terminal package installs through BOB before packages can run lifecycle scripts.

```bash
bob shim install
bob shim uninstall
```

#### `bob allow`
Human-only override. Allows a developer to permit a flagged package by recording their name, reason, and timestamp in `.bob/allowlist.yaml`. AI agents are blocked from running this command.

```bash
bob allow my-private-company-pkg
bob allow @internal/custom-lib --ecosystem npm
```

#### `bob doctor`
Health check for system environment, installed scanners (`gitleaks`, `semgrep`), Node.js bridge, active shims, and configured AI provider.

```bash
bob doctor
```

---

## How AI triage works

Deterministic scanners detect findings; the AI triages, explains, and suggests fixes. Because input can be adversarial, BOB enforces strict code-level guardrails:

| What the AI does | What the AI cannot do |
|:---|:---|
| Explains flagged security issues in plain English | Detect vulnerabilities from scratch |
| Generates fix diffs for developer review | Override or downgrade Critical or High findings |
| Annotates test decoys with review notes | Approve an untrusted or blocked package |
| Provides second opinions on prompt text | Apply code changes automatically without review |
| Runs locally on your machine or inside your IDE | Run inside the live interception path |

> Clean scan message: `0 known deterministic tripwires hit. This does not guarantee the absence of business-logic vulnerabilities.` BOB reports deterministic results plainly without claiming to be unbreakable.

---

## Benchmarks

Benchmark results comparing deterministic checks alone versus deterministic checks with local Gemma triage:

| Metric | Deterministic only (`--no-ai`) | With local Gemma triage | Result |
|:---|:---:|:---:|:---|
| True Positives Detected | 8 / 8 (100%) | 8 / 8 (100%) | All critical threats caught |
| Planted Test Decoys Flagged | 3 / 3 (false alarms) | 0 / 3 (triaged to review) | Eliminates alert fatigue from test files |
| Critical / High Findings Preserved | 100% | 100% | Invariant: AI never overrides high severity |
| Fix Verification (`bob verify`) | N/A | 100% verified | Confirms proposed patch clears the tripwire |
| Scan Latency | ~0.8s | ~3.4s (local E2B) | Runs on CPU without specialized hardware |

---

<details>
<summary><strong>Rule ID Registry</strong></summary>

<br>

| Rule ID | Category | Default Action | Description |
|:---|:---|:---|:---|
| `PKG-NOT-FOUND` | package | Block (Exit 2) | Package does not exist on PyPI/npm (slopsquatting vector) |
| `PKG-MALICIOUS-ADVISORY` | package | Block (Exit 2) | Listed in OSV malicious package advisories |
| `PKG-TOO-NEW` | package | Warn (Exit 0) | Package published under 14 days ago |
| `PKG-TYPOSQUAT` | package | Block (Exit 2) | Distance <= 2 to popular ecosystem packages |
| `PKG-LLM-TROPE` | package | Block (Exit 2) | Hallucinated trope suffix (`-utils`, `-helper`, `-ai`) |
| `PKG-NO-PROVENANCE` | package | Warn (Exit 0) | Missing repository or homepage metadata |
| `PKG-INSTALL-SCRIPT` | package | Block (Exit 2) | Suspicious script execution or credential reads in setup |
| `GUARD-SENSITIVE-PATH` | guard | Block (Exit 2) | Direct agent read/write of `.env`, `.ssh/`, `*.pem` |
| `GUARD-BOB-SELF-PROTECT` | guard | Block (Exit 2) | Agent attempts to modify `.bob/` or call `bob allow` |
| `BUILTIN-SECRET-*` | secret | Gate Block (Exit 1) | Hardcoded API keys (Anthropic, OpenAI, AWS, GCP, Stripe, Slack, JWT, DB URLs) |
| `BUILTIN-CODE-*` | code | Gate Block (Exit 1) | SQL injection, dynamic eval, unverified TLS, shell=True |
| `INJ-001` to `INJ-020` | injection | Block (Exit 2) | Instruction overrides or secret exfiltration phrases |

</details>

<details>
<summary><strong>The 5 Security Axioms</strong></summary>

<br>

1. **Deterministic tools detect; AI triages and explains.** The model never detects vulnerabilities from scratch and cannot hallucinate a pass.
2. **The AI can be adversarial.** The AI model can never suppress or lower Critical or High findings, and cannot approve packages. Any down-ranking of Medium or Low findings is logged for human review.
3. **Messages to agents use fixed templates.** BOB never echoes raw untrusted input or freeform model output back to the terminal, preventing secondary prompt injection.
4. **BOB protects itself.** Agent actions attempting to write to `.bob/` or run `bob allow` are blocked with rule `GUARD-BOB-SELF-PROTECT`. Allowlisting is strictly a human decision.
5. **Honest reporting.** If zero tripwires fire, BOB outputs: `0 known deterministic tripwires hit. This does not guarantee the absence of business-logic vulnerabilities.`

</details>

---

## Limitations

- Detects known patterns only; does not find business logic flaws or novel zero-day malware.
- A newly published package that looks clean to heuristics can still be malicious.
- `python -m pip` and other indirect invocations can bypass PATH shims; IDE hooks catch these where supported.
- Registry or OSV network outages degrade online lookups (see `offline_policy`).

---

## Documentation

- [Architecture](docs/architecture.md): Sequence diagrams, heuristic weights, and defense layers
- [Verified run](docs/quickstart-verified.md): Execution traces and reproducible proof
- [Universal skill](skills/bob/SKILL.md): Slash commands for Claude Code, Cursor, and Antigravity
- [Third-party notices](THIRD_PARTY_NOTICES.md): Tool licenses and model terms
- [Contributing guide](CONTRIBUTING.md): Setup, testing, and adding rules
- [Security policy](SECURITY.md): Vulnerability reporting instructions
- [License](LICENSE): MIT License
