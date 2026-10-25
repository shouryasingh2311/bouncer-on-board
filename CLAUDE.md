# BOB (bouncer-on-board)

Zero-trust agent firewall and pre-deploy security gatekeeper for AI coding agents.

## Tech Stack
- **Python**: 3.10+ (Typer, Rich, HTTPX, PyYAML, pytest)
- **Node.js**: Pure standard library CLI bridge (`bin/bob.js`), zero npm dependencies
- **IDE Adapters**: Antigravity (`hooks.json`), Claude Code (`SKILL.md`), Cursor (`.cursor/rules`)

## Commands
- **Run tests**: `pytest` or `.\.venv\Scripts\pytest.exe`
- **Pre-deploy scan**: `python -m bob.cli scan . --no-ai`
- **Run diagnostics**: `python -m bob.cli doctor`
- **Package check**: `python -m bob.cli check-install pypi <pkg>`
- **Node bridge check**: `node bin/bob.js --version`

## Architecture & Code Map
- `src/bob/cmdparse.py`: Recursive command unwrapper (`bash -c`, `sudo`, `env`) & package manager parser
- `src/bob/guards/`: Sensitive path protection (`.env`, `.ssh`), env secret dump guard, prompt injection tripwires
- `src/bob/pkg/`: Real-time package gate, OSV queries, static AST inspection
- `src/bob/scan/`: Pre-deploy scanner tripwires (secrets, SQLi, eval, TLS) & `.bobignore` deduplication
- `src/bob/adapters/`: L1 IDE hooks (`hooks.json`) and L2 terminal PATH shims (`~/.bob/shims`)
- `bin/bob.js`: Zero-dependency npm/npx installer and execution bridge

## Development Conventions
- **Zero-Dependency Core Bridge**: Never add runtime npm dependencies to `package.json`.
- **Minimal Python Footprint**: Use standard library (`ast`, `shlex`, `re`, `pathlib`) before external packages.
- **Security Invariant**: Never downgrade Critical/High findings via AI. Agents cannot modify `.bob/` or run `bob allow`.
- **Testing**: Every evasion vector or guard change must include a runnable unit test in `tests/unit/`.
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`) via feature branch PRs.
