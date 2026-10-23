# Hackathon Submission Details

> **Event**: MLH Hacktoberfest Hack Day (Bengaluru x AWS Student Builder Group, Atria Institute of Technology)  
> **Selected Track**: **Best Open-Source AI Project**  
> **Project Name**: BOB (`bouncer-on-board`)

---

## 1. OrganizerHQ Submission Fields (Copy-Paste Ready)

- **Project Title**: BOB (bouncer-on-board) — Zero-Trust IDE Agent Firewall & Pre-Deploy Gatekeeper
- **Track**: `Best Open-Source AI Project`
- **Repository URL**: `https://github.com/<owner>/bouncer-on-board`
- **Demo Video / Recording URL**: `[Insert link to demo recording / docs/assets/demo.mp4]`
- **Technologies Used**:
  - Python 3.10+
  - Google Gemma 4 (`gemma4:e2b` — 5.1B total / 2.3B effective parameters)
  - Ollama (Local inference runtime)
  - Typer & Rich (CLI & terminal formatting)
  - HTTPX (Direct asynchronous registry and OSV REST querying)
  - PyYAML (Rule packs and configuration)
  - Gitleaks (SARIF secret scanning engine)
  - Semgrep (SARIF pattern scanning engine)
  - OSV API (Open Source Vulnerabilities database)
  - Pytest (Automated contract verification)

---

## 2. Project Description (Submission Writeup - ~300 Words)

### Inspiration
The rapid adoption of "vibe coding" and autonomous IDE agents has introduced a dangerous new attack surface: AI agents routinely hallucinate nonexistent packages (which attackers squat with malicious payloads), install dependencies without human review, and fall prey to hidden prompt injections that trick them into exfiltrating local `.env` files or SSH credentials. Standard scanners only look at code after installation—by which time malicious install scripts have already executed.

### What it does
BOB is a local-first bouncer operating at two critical checkpoints:
1. **Path 1 (`bob intercept`):** A pre-execution gatekeeper enforcing our core invariant: **Check BEFORE install**. Running via IDE hooks or PATH shims, it statically intercepts package installation commands (`pip`, `npm`, `uv`), inspects registry metadata, age, typosquats, and sdist install scripts, and blocks attacks before untrusted code ever touches the filesystem. It also guards sensitive files (`.env`, `~/.ssh`) and flags prompt injections.
2. **Path 2 (`bob scan`):** A pre-deploy security scanner that runs deterministic analyzers (Gitleaks, Semgrep, OSV, built-ins), normalizes findings to SARIF, and uses a local open-weight model (Gemma 4 E2B via Ollama) to triage false positives, explain risks in plain English, and propose actionable fixes.

### What the AI does (and does NOT do)
- **Does**: Explains complex security findings beginner-friendly, triages low-severity false positives, and provides semantic second opinions.
- **Does NOT do**: The LLM never overrides critical/high findings, never approves packages, and never auto-applies code patches. Deterministic tripwires detect; the AI triages.

### Challenges we overcame
Handling Python and npm command variations without shell execution, performing in-memory static AST inspection of archive bytes safely, and structuring Ollama prompt boundaries so hostile code context cannot hijack the triage engine.

### What's next
Extending IDE adapters to VS Code extensions and MCP pre-execution hooks, adding crate/cargo support, and benchmarking across larger real-world repositories.

---

## 3. Two-Minute Pitch Outline

1. **The Hook (20s)**: "Agents write code fast, but they blindly install hallucinated packages and fall for prompt injections in READMEs. Once an install script runs, it's game over."
2. **The Innovation (30s)**: "BOB is an IDE agent firewall that checks BEFORE install. Path 1 stops malicious packages and `.env` snooping in under 400ms without calling any cloud."
3. **The Live Demo (50s - Screen showing AI in action)**:
   - *Act 1*: Attempting to install typosquatted or malicious package -> blocked instantly on stderr with rule id.
   - *Act 2*: Prompt injection in README -> blocked before reading `.env`.
   - *Act 3*: Pre-deploy scan with `gemma4:e2b` visible on screen -> live plain-English triage, followed by `bob verify` confirming the fix.
4. **Honest AI Posture & Team (20s)**: "Local Gemma 4 (5.1B params, under the 10B track limit) keeps your code private. Deterministic tools detect; AI explains. Built as a 4-person coordinated team (Core, QA-Demo, Docs-A, Docs-B)."
