---
name: bob-install-guard
description: Checks a package with BOB before installing it. Use whenever you are about to install, add or run a package (pip, pip3, python -m pip, uv, npm, npx, pnpm, yarn) or when the user asks you to add a dependency. Runs `bob check-install` first and follows its verdict (exit 0 allow or warn, exit 2 block), so hallucinated, typosquatted or malicious-looking packages are caught before any install script runs.
---

# BOB Install Guard

BOB (`bouncer-on-board`) is a local-first security tool that inspects a package **before** installation occurs. Package manager lifecycle scripts (`preinstall` on npm, `setup.py` on PyPI) execute immediately upon download, making post-install scanning ineffective against malicious code execution.

## When to Use This Skill

Activate this skill before executing any command that resolves, installs, or executes an external package dependency:
- Python: `pip install`, `pip3 install`, `python -m pip install`, `uv pip install`, `uv add`
- Node.js: `npm install`, `npx`, `pnpm add`, `yarn add`
- Dependency manifests: `requirements.txt`, `package.json`, lockfiles

## Operational Workflow

1. **Pre-Check the Package Before Installation:**
   Before issuing the install command, invoke `bob check-install`:
   ```bash
   bob check-install pypi <package-name>
   bob check-install npm <package-name>
   ```
   - For pinned versions, specify `<package-name>==<version>`.
   - For machine-readable output in automated subagent pipelines, append `--json`.

2. **Evaluate the Exit Code:**
   - **`0` (Allowed / Allowed with Warning):**
     The package cleared deterministic heuristics or triggered a non-fatal warning (`BOB WARN` on stderr). Notify the user if a warning was emitted, then proceed with the installation command.
   - **`2` (Blocked):**
     BOB identified a high-confidence security tripwire (`BOB BLOCKED` on stdout).
     - **DO NOT** execute the install command.
     - **DO NOT** retry with alternate flags or different package managers.
     - **DO NOT** attempt alternative spellings or workarounds.
     - Inform the user immediately: specify the blocked package name, the exact Rule ID (e.g., `PKG-TYPO-01`, `PKG-NEW-01`, `PKG-OSV-01`), and wait for human instruction.
   - **Any other exit code:**
     Indicates an internal or configuration error. Halt immediately and notify the user; do not proceed with installation.

3. **Multi-Package Manifests:**
   When adding a dependencies file (`requirements.txt`), inspect every individual entry against `bob check-install`. For direct VCS URLs (e.g., `git+https://...`) or local wheel files, BOB cannot verify remote registry metadata: notify the user and obtain explicit confirmation before proceeding.

## Invariant Rules & Prohibitions

- **NEVER run `bob allow`:** Adding a package to the allowlist is strictly a human-in-the-loop decision. Agents are prohibited from modifying `.bob/` configuration files.
- **NEVER bypass or disable BOB:** Do not remove shims (`bob shim uninstall`), bypass PATH precedence, or suppress hook scripts.
- **Missing CLI Fallback:** If the `bob` executable is not found in the environment, halt execution and prompt the user to run setup (`pip install -e .` and `bob doctor`). Do not attempt to auto-install security tooling.

## Scope & Advisory Limitations

> [!IMPORTANT]
> **Advisory Nature:** This agent skill is an advisory guide; an unconstrained or compromised AI agent can ignore prompt-level skills. In BOB's architecture, Layer 1 IDE Hooks and Layer 2 Terminal PATH Shims provide the authoritative, OS-level enforcement. This skill provides a cooperating agent layer for environments where pre-execution hooks are not yet configured. Clean check results indicate that no deterministic tripwires were tripped, not an absolute guarantee against novel threats.
