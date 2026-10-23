# Third-Party Software and Model Notices

BOB (`bouncer-on-board`) incorporates, interfaces with, or borrows concepts and detection rules from the third-party open-source projects, datasets, and open-weight models listed below.

---

## 1. Open-Weight AI Model

### Google Gemma 4 (`gemma4:e2b`)
- **Author / Provider**: Google DeepMind
- **Repository / Distribution**: Available via Ollama (`ollama pull gemma4:e2b`) and Hugging Face (`google/gemma-4`)
- **Parameter Count**:
  - **Total Parameters**: ~5.1 Billion
  - **Effective Parameters**: ~2.3 Billion (using Per-Layer Embeddings / PLE for edge optimization)
  - **Compliance Note**: Satisfies the MLH "Best Open-Source AI Project" track definition of a Small Language Model (SLM) strictly requiring **10B parameters or fewer**.
- **Licence & Terms**: [Gemma Terms of Use](https://ai.google.dev/gemma/terms)
- **Legal Characterization**: Open-weight model distributed under custom Google Gemma terms. *Note: Open-weight does not automatically mean OSI-approved open source. The Gemma Terms permit commercial and non-commercial use subject to responsible use guidelines.*

---

## 2. Local AI Serving Infrastructure

### Ollama
- **Author / Organization**: Ollama Inc.
- **Repository**: [https://github.com/ollama/ollama](https://github.com/ollama/ollama)
- **License**: [MIT License](https://github.com/ollama/ollama/blob/main/LICENSE)
- **Role in BOB**: Local HTTP inference server on `localhost:11434` providing structured JSON output for offline scan finding triage and plain-English explanations.

---

## 3. Vulnerability Feeds and External Scanners

### Open Source Vulnerabilities (OSV) API & Database
- **Author / Organization**: Google Open Source Security Team
- **Repository / Documentation**: [https://github.com/google/osv.dev](https://github.com/google/osv.dev) | [https://osv.dev](https://osv.dev)
- **API License / Terms**: Apache License 2.0 (Service code) | CC-BY 4.0 (Advisory data feed)
- **Role in BOB**: Direct HTTP API lookups (`https://api.osv.dev/v1/query`) in `pkg/osv.py` for known package advisories and `MAL-` (malicious package) ecosystem reports.

### Gitleaks
- **Author**: Zachary Rice
- **Repository**: [https://github.com/gitleaks/gitleaks](https://github.com/gitleaks/gitleaks)
- **License**: [MIT License](https://github.com/gitleaks/gitleaks/blob/master/LICENSE)
- **Role in BOB**: Optional external secret-detection scanner invoked in `bob scan` with SARIF report output.

### Semgrep
- **Author**: Semgrep, Inc.
- **Repository**: [https://github.com/semgrep/semgrep](https://github.com/semgrep/semgrep)
- **CLI Engine License**: LGPL-2.1 License (`https://github.com/semgrep/semgrep/blob/main/LICENSE`)
- **Licensing Distinction**: Proprietary Semgrep Registry rules are not vendored into this repository. BOB executes Semgrep only with local custom rule files (`data/rules/semgrep-vibe.yaml`) under MIT licensing.

---

## 4. Python Runtime Dependencies

All runtime dependencies are verified against official PyPI distributions and licensed permissively:

| Package | Version / Specification | License | Upstream Link |
|---|---|---|---|
| `typer` | `>=0.12.0` | MIT License | [https://github.com/fastapi/typer](https://github.com/fastapi/typer) |
| `rich` | `>=13.7.0` | MIT License | [https://github.com/Textualize/rich](https://github.com/Textualize/rich) |
| `httpx` | `>=0.27.0` | BSD-3-Clause | [https://github.com/encode/httpx](https://github.com/encode/httpx) |
| `pyyaml` | `>=6.0.1` | MIT License | [https://github.com/yaml/pyyaml](https://github.com/yaml/pyyaml) |

### Development Dependencies
| Package | Version / Specification | License | Upstream Link |
|---|---|---|---|
| `pytest` | `>=8.0.0` | MIT License | [https://github.com/pytest-dev/pytest](https://github.com/pytest-dev/pytest) |

---

## 5. Curated Top-Package Datasets

### PyPI Top Packages Reference List (`data/top_pypi.json`)
- **Source**: Aggregated from the public PyPI BigQuery download dataset (`bigquery-public-data.pypi.file_downloads`).
- **License**: Public domain / US Government & Open Data Commons Public Domain Dedication and License (PDDL).
- **Usage**: Offline Levenshtein distance typosquat detection (`pkg/heuristics.py`).

### npm Top Packages Reference List (`data/top_npm.json`)
- **Source**: Public registry download metrics via npm API (`https://api.npmjs.org/downloads/point/last-month`).
- **License**: Open registry metadata.

---

## 6. Prompt Injection & Heuristic Research References

Detection patterns in `data/rules/injection.yaml` and heuristic signals in `pkg/heuristics.py` draw inspiration from public defensive security research:
- **OWASP Top 10 for LLM Applications** (LLM01: Prompt Injection) - Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA 4.0).
- **Garak (Generative AI Red-teaming & Assessment Kit)** - Apache License 2.0.
- **Promptfoo Security Test Suites** - MIT License.
- **Trojan Source (CVE-2021-42574)** Unicode bidirectional override research (Boucher & Anderson, Cambridge University).
