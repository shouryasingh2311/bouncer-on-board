# External Services & Integrations

## 1. Supply Chain & Vulnerability Registries
- **Open Source Vulnerabilities (OSV) API**:
  - Endpoint: `https://api.osv.dev/v1/query`
  - Purpose: Real-time query for known malicious package advisories (`MAL-*`, `GHSA-*`, `CVE-*`) across PyPI and npm ecosystems.
  - Fail-safe: Non-blocking timeout with local heuristics fallback when network is unavailable.
- **PyPI Warehouse API**:
  - Endpoint: `https://pypi.org/pypi/{package}/json`
  - Purpose: Metadata inspection (release timestamps, author provenance, project age, recent updates).
- **npm Registry API**:
  - Endpoint: `https://registry.npmjs.org/{package}`
  - Purpose: Package inspection, release age checking, and install script (`preinstall`, `postinstall`) detection in package manifests.
- **Embedded Popular Package Databases**:
  - Files: `src/bob/data/top_pypi.json` and `src/bob/data/top_npm.json` (top 5,000 packages each).
  - Purpose: Zero-latency, zero-network allowlist resolution for popular verified packages (`requests`, `react`, etc.) to stay under the 400ms interception latency target.

## 2. Artificial Intelligence Providers
- **Local Small Language Models (Ollama)**:
  - Default Endpoint: `http://localhost:11434/api/generate`
  - Supported Models: `gemma4:e2b`, `gemma:2b`, `llama3.2`, etc.
  - Role: Offline, private triage of scan findings, explaining root cause and proposing fixes.
  - Fallback: Pre-baked deterministic rule-based explanations when Ollama is offline (`src/bob/ai/fallback.py`).
- **Cloud AI Client (`src/bob/ai/cloud_client.py`)**:
  - Google Gemini API: Native REST endpoint (`https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`) supporting Gemini 1.5/2.0 Flash.
  - OpenAI-Compatible REST API: Universal JSON endpoint (`https://api.openai.com/v1/chat/completions`) supporting OpenAI, Groq, OpenRouter, and self-hosted vLLM/Ollama OpenAI shims.
  - Verification: Automated live credentials test via `bob doctor` and `bob setup`.

## 3. IDE Process Boundary & Interceptor Integrations
- **Antigravity IDE Hook**:
  - File: `.agents/hooks.json`
  - Hook event: `PreToolUse` targeting terminal/bash execution tools.
  - Interceptor Adapter: `src/bob/adapters/antigravity.py` parsing IDE tool invocations before execution.
- **Terminal PATH Shims (`~/.bob/shims`)**:
  - Wrappers for `pip`, `pip3`, `npm`, `npx` (Windows `.cmd` batch wrappers and POSIX shell scripts).
  - Intercepts package installation commands invoked in Cursor, VSCode, Claude Code, Cline, Roo Code, and direct terminal sessions.

## 4. CI/CD & Automated Governance
- **GitHub Actions (`.github/workflows/bob.yml`)**:
  - Triggers on push and pull request to `main`.
  - Runs full test suite via pytest, executes dependency security audit, runs `bob doctor`, and runs `bob scan src --no-ai`.
