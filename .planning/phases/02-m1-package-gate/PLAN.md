# PLAN.md — Phase 2: M1 Pre-Install Package Gate & Offline Mock Registry Compatibility

## Goal
Implement the pre-install package gate that inspects packages *statically before execution* (pure HTTPS/AST, never running code). It flags nonexistent packages, OSV malicious packages, young packages, typosquats, naming tropes, missing provenance, and suspicious install scripts in PyPI sdist / npm packages.

## Tasks
1. **Task 1: Top-N Packages Bundles (`src/bob/data/`)**
   - Create `src/bob/data/top_pypi.json` (top ~100 PyPI package names for typosquat detection).
   - Create `src/bob/data/top_npm.json` (top ~100 npm package names for typosquat detection).

2. **Task 2: Command Parser (`src/bob/cmdparse.py`)**
   - Parse shell command strings (handling `&&`, `;`, `|`, quotes, and Windows formatting).
   - Detect install intents: `pip install`, `pip3 install`, `python -m pip install`, `py -m pip install`, `uv pip install`, `uv add`, `npm install`, `npm i`, `npm add`, `npx <pkg>`, `pnpm add`, `yarn add`.
   - Extract package name and version (`name[==ver]`).
   - Flag unverifiable inputs (git URLs, file paths, tarball URLs).

3. **Task 3: Registry Clients (`src/bob/pkg/pypi.py`, `src/bob/pkg/npm.py`)**
   - Implement `fetch_pypi_metadata(name, cfg)` -> returns `(status_code, data_dict)`.
   - Implement `fetch_npm_metadata(name, cfg)` -> returns `(status_code, data_dict)`.
   - Support `registry_overrides` from `Config` for offline mock registry.
   - Cache results in memory / `.bob/cache/`.

4. **Task 4: OSV Client (`src/bob/pkg/osv.py`)**
   - Query OSV API `POST https://api.osv.dev/v1/query`.
   - Extract any advisory with ID starting with `MAL-` as malicious-package report.

5. **Task 5: Heuristics & Typosquat Engine (`src/bob/pkg/heuristics.py`)**
   - Self-contained Levenshtein distance function (~15 lines stdlib).
   - Distance <= 2 against top-N list -> `PKG-TYPOSQUAT` (+40).
   - Package age: first upload date < 7d (+50), < 14d (+35), < 30d (+15) -> `PKG-TOO-NEW`.
   - LLM naming tropes (`-utils`, `-helper`, `-ai`, `-gpt`, `-v2`, `-pro`) -> `PKG-LLM-TROPE` (+20).
   - Missing provenance (no repo / homepage URL) -> `PKG-NO-PROVENANCE` (+15).

6. **Task 6: Static Inspection (`src/bob/pkg/static_inspect.py`)**
   - Safe archive extraction (tarball/zip) enforcing path traversal checks and size limits.
   - Python sdist: parse `setup.py` using `ast` without executing it.
     - Flag base64/codecs decode feeding exec/eval/compile.
     - Flag os.environ mass access, ~/.ssh, ~/.aws, .env access.
     - Flag subprocess/os.system calling curl, wget, powershell, or raw sockets.
   - npm packument/tarball: parse `scripts.preinstall`, `scripts.postinstall`.
     - Flag curl|sh, node -e with decoded strings, base64 eval, ~/.ssh access.
   - Signal: `PKG-INSTALL-SCRIPT` (+60 per category, cap +100).

7. **Task 7: Package Gate Coordinator (`src/bob/pkg/gate.py`)**
   - Combine signals into `Decision` score.
   - Hard signals: 404 (nonexistent) -> block; OSV `MAL-` -> block.
   - Score >= 70 -> block (`action="block"`).
   - Score 30-69 -> warn (`action="warn"`).
   - Score < 30 -> allow (`action="allow"`).
   - Error formatting: Fixed template strings for stderr.

8. **Task 8: CLI Integration & Unit Tests**
   - Wire `bob check-install <ecosystem> <package> [--json]` in `src/bob/cli.py`.
   - Write comprehensive unit tests in `tests/unit/test_cmdparse.py`, `test_heuristics.py`, `test_static_inspect.py`, `test_gate.py`.
   - Verify `pytest` passes 100%.
