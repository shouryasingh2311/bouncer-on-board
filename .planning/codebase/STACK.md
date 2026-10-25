# Technology Stack & Environment

## Core Runtime & Language
- **Language**: Python 3.10+ (tested on Python 3.10.6, win32 and Linux)
- **Packaging System**: `pyproject.toml` using `setuptools` build backend
- **Entrypoint**: `bob = "bob.cli:app"` defined under `[project.scripts]`

## Runtime Dependencies
Strictly controlled minimal dependency set:
- **`typer>=0.9.0`**: CLI framework providing subcommands, argument parsing, autocompletion, and help menus.
- **`rich>=13.0.0`**: Terminal rendering engine for tables, status spinners, colored alert panels, and progress indicators.
- **`httpx>=0.25.0`**: High-performance HTTP client used synchronously and asynchronously for API calls to OSV, PyPI, npm, Ollama, and Cloud AI services.
- **`pyyaml>=6.0.0`**: Parsing YAML configuration (`~/.bob/config.yaml`) and security rule definitions (`src/bob/data/rules/*.yaml`).

## Development & Testing Dependencies
- **`pytest>=7.4.0`**: Unit and integration test suite runner (113 test cases currently passing).
- **`pytest-cov`**: Test coverage reporting (optional).

## Key Standard Library Modules
Per our strict dependency minimization policy ("Ponytail lazy senior dev mode"), we rely directly on Python standard library modules:
- **`ast`**: Static analysis of Python code and setup scripts without dynamic execution.
- **`hashlib`**: SHA-256 fingerprinting for findings deduplication (`RULE:FILE:LINE:SNIPPET`).
- **`json`**: Parsing JSON-formatted registry responses, SARIF reports, and IDE hook event payloads.
- **`pathlib`**: OS-agnostic path normalization (handles Windows backslashes `\` and POSIX forward slashes `/`).
- **`re`**: Regex pattern matching for secret patterns, malicious import detection, and prompt-injection signatures.
- **`shutil` & `subprocess`**: Path lookup (`shutil.which`), process execution for doctor checks (`ollama list`, etc.).
- **`urllib`**: Safe URL parsing, encoding, and validation.

## Platform Constraints & Invariants
- **Operating Systems**: Windows 10/11 (native PowerShell, CMD, Git Bash), Linux, macOS.
- **Terminal Encoding**: Strict ASCII character range (character codes 32–126). Unicode box-drawing characters and fancy emojis are prohibited in CLI outputs to prevent encoding crashes (`UnicodeEncodeError`) in Windows `cp1252` console sessions.
