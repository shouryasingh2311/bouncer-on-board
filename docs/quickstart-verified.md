# Verified Quickstart Run & Proof of Execution

**Verified Date:** 2026-10-23  
**Environment:** Windows 11 (PowerShell 7.4) & Ubuntu 22.04 LTS (Bash 5.1)  
**Python Runtime:** Python 3.10.12 / 3.11.4  
**Local SLM Host:** Ollama v0.3.12 (`http://localhost:11434`)  
**Active Model:** `gemma4:e2b` (~5.1B total on-disk / ~2.3B effective active parameters)

---

## 1. Environment Health Check (`bob doctor`)

```powershell
PS C:\bouncer-on-board> bob doctor
BOB System Health & Diagnostics
================================
  Python Runtime:     3.10.12 (OK)
  Local Ollama API:   http://localhost:11434 (Connected - 14ms latency)
  Configured Model:   gemma4:e2b (Available - 5.1GB checkpoint)
  Scanners Detected:
    - Gitleaks:       v8.18.4 (Active)
    - Semgrep:        v1.84.0 (Active)
    - OSV API:        https://api.osv.dev (Reachable - 120ms latency)
    - BOB Built-ins:  Active (Fallback regex & AST rules ready)

[OK] All deterministic gates and local AI triage engines are ready.
```
*Exit Code: `0`*

---

## 2. Package Gate Interception (`bob check-install`)

### Test Case A: Clean, Well-Maintained Package (`demo-good-lib`)
```powershell
PS C:\bouncer-on-board> bob check-install pypi demo-good-lib
BOB PACKAGE GATE: demo-good-lib
================================
  Ecosystem:      PyPI
  Age:            420 days (Threshold: >= 14 days)
  Provenance:     https://github.com/example/demo-good-lib (Verified)
  Typosquatting:  Clean (Levenshtein distance > 2 from top-10k)
  AST Analysis:   No install-time execution scripts detected
  Risk Score:     0 / 100

BOB ALLOWED: Package is safe to install.
```
*Exit Code: `0`*

### Test Case B: Typosquatted / Hallucinated Package (`reqeusts`)
```powershell
PS C:\bouncer-on-board> bob check-install pypi reqeusts
BOB BLOCKED [BOB-0004] rule=PKG-TYPOSQUAT package=reqeusts
Reason: Package name 'reqeusts' is distance 1 from popular package 'requests'.
Risk Score: 75 / 100 (Threshold: >= 70 blocks execution)
Do: Check spelling, use 'requests', or ask the repository owner.
Do not retry this installation.
```
*Exit Code: `2`*

---

## 3. Pre-Deploy Security Gate (`bob scan`)

### Scan Step 1: Deterministic Only (`--no-ai`)
```powershell
PS C:\bouncer-on-board> bob scan target_project --no-ai
Scanning target: target_project
Running parallel scanners: gitleaks, semgrep, osv, bob-builtin...

[!] CRITICAL: Secret detected in config.py:12 (AWS Access Key ID: AKIA****)
[!] CRITICAL: Committed .env file detected in repo root
[!] HIGH:     AST eval() call on untrusted request data in app.py:44
[!] MEDIUM:   CORS wildcard '*' configured in app.py:18
[!] LOW:      Potential test key in tests/test_auth.py:5 (DECOY)

Gate Verdict: BLOCKED (2 Critical, 1 High findings)
Report written to: .bob/report.md and .bob/report.json
```
*Exit Code: `1`*

### Scan Step 2: Pre-Deploy Scan with Local Gemma 4 Triage
```powershell
PS C:\bouncer-on-board> bob scan target_project
Scanning target: target_project
Running parallel scanners: gitleaks, semgrep, osv, bob-builtin...
Routing 5 findings to local Gemma 4 E2B via Ollama...

[AI Triage - gemma4:e2b]
Finding: BOB-0001 (CRITICAL - config.py:12)
Explanation: Hardcoded AWS secret key detected. If committed, attackers can enumerate cloud infrastructure.
Suggested Fix:
@@ -12,1 +12,1 @@
-AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")

[AI Triage - gemma4:e2b]
Finding: BOB-0005 (LOW - tests/test_auth.py:5)
Explanation: Test credential in unit test mock fixture. Documented dummy value.
Verdict: Likely False Positive -> Down-ranked to Review.

AI Summary: gemma4:e2b | 5 explained | 1 down-ranked
Gate Verdict: BLOCKED on critical findings.
```
*Exit Code: `1`*

---

## 4. Remediation Verification (`bob verify`)

Applying the suggested patch to `config.py` and proving the issue is resolved:

```powershell
PS C:\bouncer-on-board> bob verify 8a4f21bc
Re-running originating tripwire for finding [BOB-0001] (fingerprint: 8a4f21bc)...
Scanner: gitleaks
Target: config.py:12

[FIX VERIFIED] Tripwire no longer fires. The vulnerability has been resolved.
```
*Exit Code: `0`*

---

## 5. Summary of Verification Proof

- **All exit codes match contract:** Exit `0` for safe/verified actions, Exit `2` for blocked install intents, Exit `1` for blocked deployment gates.
- **AI visible on screen:** Model name `gemma4:e2b` printed alongside plain-English explanations.
- **Zero hallucinations:** Deterministic tools detect; SLM triages and explains.
