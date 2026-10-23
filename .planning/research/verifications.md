# Section 18 Pre-Flight Verifications (Verified on Environment)

Ground-truth verification results performed prior to coding, fulfilling PROJECT.md Section 18:

## 1. Antigravity Pre-Execution Hook & Customization Contract
- **Source**: Official Antigravity documentation in `agy-customizations/docs/hooks.md`.
- **Finding**: Antigravity supports a native pre-execution lifecycle hook via `.agents/hooks.json` (or `~/.gemini/config/hooks.json`).
- **Hook Type**: `PreToolUse` with matcher `run_command` (and file tools).
- **Protocol**:
  - Input (stdin): JSON with `toolCall: { name: "run_command", args: { CommandLine: "..." } }`, `stepIdx`, etc.
  - Output (stdout): JSON with `decision: "deny" | "allow" | "ask"`, `reason: "BOB BLOCKED [...]"`, optional `overwrite`.
- **Impact**: We can provide a first-class Antigravity adapter (`bob intercept --adapter antigravity`) in addition to generic CLI shims.

## 2. Real PyPI and npm JSON Schemas
- **PyPI (`https://pypi.org/pypi/<name>/json`)**:
  - Keys: `['info', 'last_serial', 'ownership', 'releases', 'urls', 'vulnerabilities']`.
  - Project URLs: in `info.project_urls` (dict mapping names like `'Homepage'`, `'Source'` to URLs).
  - Release upload dates: in `releases[version][0]['upload_time_iso_8601']` (e.g. `2012-01-22T05:08:17.091441Z`).
  - No download count in this API (do not invent).
- **npm (`https://registry.npmjs.org/<name>`)**:
  - Keys: `['_id', 'name', 'dist-tags', 'versions', 'time', 'repository', 'homepage', ...]`.
  - Creation time: `time['created']` (e.g. `2010-12-29T19:38:25.450Z`).
  - Scripts: `versions[version]['scripts']` (contains `preinstall`, `install`, `postinstall`).
  - Tarball URL: `versions[version]['dist']['tarball']`.

## 3. OSV API Request/Response Shapes
- **Endpoint**: `POST https://api.osv.dev/v1/query` with body `{"package": {"name": "...", "ecosystem": "PyPI"}, "version": "..."}`.
- **Response**: `{"vulns": [{"id": "...", "summary": "...", ...}]}`.
- **Malicious Packages**: Identified by IDs starting with `MAL-` (e.g., `MAL-2024-5835` from ReversingLabs / OSV).

## 4. Local External Scanners
- `gitleaks` and `semgrep`: Not currently on PATH on this Windows host.
- **Strategy**: Follow `PROJECT.md` Section 8. `bob doctor` reports them as missing/skipped, and `bob scan` relies on built-in rules (`scan/builtin.py`) as primary zero-dependency fallback, gracefully skipping external binaries.

## 5. Local Ollama & Gemma 4
- **Host**: `http://localhost:11434`.
- **Status**: Ollama service is not currently running on localhost (connection refused).
- **Strategy**: `ai/fallback.py` provides deterministic template explanations when Ollama is offline or model is missing.
- **Model Card & Parameter Count**: Gemma models are available in small variants (e.g. 2B, E2B, E4B) well under the 10B parameter ceiling of the hackathon track.
- **License**: Governed by the Gemma Terms of Use / Apache 2.0 depending on exact release.
