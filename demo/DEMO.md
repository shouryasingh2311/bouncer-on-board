# BOB Demo Script & Rehearsal Checklist (60–90 Seconds)

> **Track**: MLH Hacktoberfest Hack Day — Best Open-Source AI Project  
> **Core Theme**: Zero-Trust IDE Agent Firewall & Pre-Deploy Gatekeeper with Local SLM (Gemma 4 via Ollama)

---

## Pre-Demo Rehearsal Checklist

- [ ] **Local mock registry ready**: Port 8765 free.
- [ ] **Ollama service running**: `ollama list` shows `gemma4:e2b` (or active tag).
- [ ] **Warm-up query executed**: Run a throwaway prompt through Ollama so the model is pre-loaded in memory.
- [ ] **Terminal configuration**: High-contrast theme, large font (>= 18pt), clean prompt.
- [ ] **Backup screen recording**: Always have a pre-recorded walkthrough in `docs/assets/demo.mp4` / GIF as contingency.

---

## Three-Act Demo Flow

### Act 1 — Pre-Install Package Gate (Deterministic, 0–25s)
*Narration*: "When vibe-coding agents build apps, hallucinated or typosquatted packages can execute malicious install scripts before anyone reviews the code. BOB blocks risky packages **before** installation."

1. **Hallucinated Package (Instant 404 block)**:
   ```powershell
   bob check-install pypi demo-missing-lib
   ```
   *Expected*: `exit 2`, `BOB BLOCKED [...] rule=PKG-NOT-FOUND package=demo-missing-lib` (<400ms).

2. **Typosquatted Package (Levenshtein distance <= 2)**:
   ```powershell
   bob check-install pypi reqeusts
   ```
   *Expected*: `exit 2`, `BOB BLOCKED [...] rule=PKG-TYPOSQUAT package=reqeusts`.

3. **Inert Malicious sdist (Static AST Inspection)**:
   ```powershell
   bob check-install pypi demo-evil-lib
   ```
   *Expected*: `exit 2`, `BOB BLOCKED [...] rule=PKG-INSTALL-SCRIPT`. Catches base64 decode+exec without executing a single byte of code.

---

### Act 2 — Agent Action & Injection Guard (Deterministic + Advisory AI, 25–45s)
*Narration*: "What if an agent is tricked by indirect prompt injection in a README into reading credentials?"

1. **Prompt Injection Tripwire**:
   ```powershell
   bob guard-text demo/injection_fixture/README.md
   ```
   *Expected*: `exit 2`, flags zero-width Unicode characters (`INJ-010`) and instruction override (`INJ-020`).

2. **Sensitive Path Interception**:
   ```powershell
   bob intercept --adapter generic --cmd "cat .env"
   ```
   *Expected*: `exit 2`, `BOB BLOCKED [...] rule=GUARD-SENSITIVE-PATH`. Blocks the command from executing.

3. **Agent Self-Protection**:
   ```powershell
   bob intercept --adapter generic --cmd "bob allow demo-evil-lib"
   ```
   *Expected*: `exit 2`, `BOB BLOCKED [...] rule=GUARD-BOB-SELF-PROTECT`. The AI agent cannot weaken BOB.

---

### Act 3 — Pre-Deploy Gate with Local SLM Triage (The Main AI Moment, 45–90s)
*Narration*: "Now the code is written. Before shipping, `bob scan` combines deterministic tripwires with local Gemma 4 to triage noise and explain fixes."

1. **Raw Deterministic Scan (Without AI)**:
   ```powershell
   bob scan demo/vulnerable_app --no-ai
   ```
   *Notice*: Gate fails (exit 1). Catches raw secrets, eval, open CORS, and SQL injection, but flags test decoys as noisy false positives.

2. **SLM-Triaged Scan (With Local Gemma 4 on Screen)**:
   ```powershell
   bob scan demo/vulnerable_app
   ```
   *Highlight on screen*:
   - Model name visibly displayed: `AI: gemma4:e2b`
   - Live plain-English explanation of why `eval()` is critical and how to fix it
   - Test decoy keys marked `likely_false_positive` and safely downranked under *"AI-downgraded, please review"*.
   - Zero-findings posture: Never says "100% secure".

3. **Fix and Verification**:
   ```powershell
   # Apply fix to config.py, then:
   bob verify <fingerprint-prefix>
   ```
   *Expected*: `exit 0` (Remediation confirmed; tripwire no longer triggers).

4. **Measured Evaluation Scorecard**:
   ```powershell
   python eval/run_eval.py
   ```
   *Closing punchline*: "Deterministic tripwires detect; the open-weight model triages and explains. Real numbers on screen, zero cloud dependencies, fully local-first."
