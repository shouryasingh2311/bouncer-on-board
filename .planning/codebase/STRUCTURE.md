# Codebase Layout & Directory Structure

## Repository Map

```
bouncer-on-board/
├── .agents/
│   └── hooks.json                 # Antigravity IDE PreToolUse interception hook
├── .github/
│   └── workflows/
│       └── bob.yml                # CI pipeline (Python 3.10, pytest, audit, bob scan)
├── .planning/                     # GSD planning directory
│   ├── codebase/                  # Architecture & engineering codebase map
│   ├── onboarding/                # Onboarding summaries
│   ├── phases/                    # Milestone phase specs (M0 through M6)
│   ├── PROJECT.md                 # Project vision, rules, scope boundary
│   ├── REQUIREMENTS.md            # Traceable functional requirements
│   ├── ROADMAP.md                 # Strategic milestones roadmap
│   ├── STATE.md                   # Current project state & decisions log
│   └── enhancement.md             # Future enhancements roadmap
├── demo/                          # Evaluator / Judge testing harness
│   ├── malicious_prompt.md        # Prompt injection test attack vector
│   └── vulnerable_app/            # App with deliberate mock test vulnerabilities
│       ├── .env                   # Fake mock keys for scanner evaluation
│       ├── app.py                 # Mock vulnerable endpoints (eval, sql, tls)
│       └── tests/
│           └── test_mock_data.py  # Unit test asserting mock fixtures are inert
├── docs/                          # Architecture documentation & diagrams
│   ├── architecture.md            # In-depth architectural writeup
│   ├── quickstart-verified.md     # Verified quickstart instructions
│   ├── usability-test.md          # Usability validation runbook
│   └── assets/                    # Project logos and badges
├── skills/
│   └── bob-install-guard/         # IDE agent skill definition
├── src/bob/                       # Core Python Package (`bob`)
│   ├── adapters/                  # IDE hook adapters
│   │   ├── antigravity.py         # Intercept adapter for Antigravity hooks
│   │   └── generic.py             # Generic IDE command interceptor
│   ├── ai/                        # Small Language Model & Cloud AI triage
│   │   ├── cloud_client.py        # Gemini & OpenAI-compatible HTTP client
│   │   ├── fallback.py            # Offline rule-based triage advice
│   │   ├── ollama.py              # Ollama local REST client
│   │   ├── prompts.py             # System prompts and JSON schema templates
│   │   └── triage.py              # Triage engine enforcing Security Axiom 2
│   ├── data/                      # Embedded offline databases & rules
│   │   ├── rules/                 # Detection rule definitions
│   │   │   ├── code_execution.yaml # Dangerous code execution AST rules
│   │   │   ├── injection.yaml     # Prompt injection signatures
│   │   │   └── secrets.yaml       # API keys, tokens, and credential patterns
│   │   ├── top_npm.json           # Cached top-5000 popular npm packages
│   │   └── top_pypi.json          # Cached top-5000 popular PyPI packages
│   ├── guards/                    # Security tripwire enforcement
│   │   ├── injection.py           # Text guard prompt injection scanner
│   │   └── sensitive_paths.py     # Sensitive paths (.env, .ssh, .git, etc.)
│   ├── pkg/                       # Supply chain package gate
│   │   ├── gate.py                # Package verification orchestrator
│   │   ├── heuristics.py          # Typosquatting, package age, trope checks
│   │   ├── npm.py                 # npm registry metadata fetcher
│   │   ├── pypi.py                # PyPI warehouse metadata fetcher
│   │   └── static_inspect.py      # Python setup.py / wheel AST inspector
│   ├── report/                    # Output formatting engines
│   │   ├── console.py             # Terminal rendering tables and panels
│   │   ├── markdown.py            # GitHub-flavored markdown report writer
│   │   └── sarif.py               # SARIF v2.1.0 report exporter
│   ├── scan/                      # Pre-deploy code scanner
│   │   ├── dedupe.py              # SHA-256 finding deduplication engine
│   │   ├── engine.py              # Directory traverser and tripwire evaluator
│   │   └── sarif.py               # External SARIF report normalizer
│   ├── banner.py                  # Standard ASCII boxed banner & logo
│   ├── cli.py                     # Typer CLI subcommands & option handling
│   ├── cmdparse.py                # Shell command parser & package extractor
│   ├── config.py                  # YAML configuration manager & defaults
│   ├── models.py                  # Core domain models and dataclasses
│   └── setup.py                   # Onboarding wizard & IDE protection installer
├── tests/
│   └── unit/                      # 24 test suites covering 113 unit test cases
├── pyproject.toml                 # Package configuration & dependencies
├── README.md                      # Primary project documentation & quickstart
├── PROJECT.md                     # Comprehensive hackathon project spec
├── TEAM_PLAN.md                   # Multi-agent coordination and roles
└── LICENSE                        # MIT License
```

## Key Module Responsibilities
- **`bob.cli`**: Routes terminal commands to appropriate subsystems; controls exit codes (0, 1, 2, 3).
- **`bob.pkg.gate`**: Verifies packages before installation against top caches, human allowlists, and live OSV advisories.
- **`bob.scan.engine`**: Traverses project files while ignoring system caches and user homes; evaluates tripwire rules.
- **`bob.ai.triage`**: Calls local SLM or cloud endpoints to annotate scan findings while strictly locking severity scores.
