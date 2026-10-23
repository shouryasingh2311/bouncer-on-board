---
name: bob-install-guard
description: Checks a package with BOB before installing it. Use whenever you are about to install, add or run a package (pip, pip3, python -m pip, uv, npm, npx, pnpm, yarn) or when the user asks you to add a dependency. Runs `bob check-install` first and follows its verdict (exit 0 allow or warn, exit 2 block), so hallucinated, typosquatted or malicious-looking packages are caught before any install script runs.
---

# BOB install guard

BOB (bouncer-on-board) is a local-first tool that checks a package **before** it is installed. Install scripts run during installation, so checking afterwards is too late.

## When to use this skill

Before any command that installs or runs a package: `pip install`, `python -m pip install`, `uv pip install`, `uv add`, `npm install`, `npx`, `pnpm add`, `yarn add`, or an install from a requirements file.

## Steps

1. For each package you are about to install, run the check first:

   ```bash
   bob check-install pypi <name>
   bob check-install npm <name>
   ```

   - Use `pypi` for pip, pip3, `python -m pip`, `py -m pip` and uv. Use `npm` for npm, npx, pnpm and yarn.
   - To check a specific version, write `<name>==<version>`.
   - Add `--json` if you need the machine-readable decision.

2. Read the exit code:
   - **0**: allowed, or allowed with a warning (a line starting `BOB WARN` on stderr). Tell the user about any warning, then continue.
   - **2**: blocked (the first line starts `BOB BLOCKED`). Do not install the package. Do not retry. Do not look for a workaround such as another install tool or another spelling. Tell the user which package was blocked and which rule id the message gives, and ask what they want to do.
   - **Any other exit code**: BOB hit an internal error. Stop and tell the user. Do not install anything.

3. For a requirements file or lockfile, check every package named in it. For local paths, VCS URLs and direct archive URLs, BOB cannot verify the package: tell the user before installing.

## Rules

- Never run `bob allow` and never edit anything under `.bob/`. Allowlisting is a human-only decision.
- Never weaken, bypass or disable BOB (shims, hooks or config).
- If the `bob` command is not found, stop and tell the user. Do not try to install it yourself.

## Limits

This skill is advisory: an agent can ignore it. BOB's PATH shims and IDE hooks are the real enforcement; this skill is a fallback for environments without hooks. BOB checks known tripwires only, so a clean result is not a guarantee.
