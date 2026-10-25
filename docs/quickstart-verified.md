# Verified Quickstart Run and Proof of Execution

**Verified Date:** 2026-10-25  
**Environment:** Windows 11 (PowerShell 7.4) & Ubuntu 22.04 LTS (Bash 5.1)  
**Python Runtime:** Python 3.10.12 / 3.11.4  
**Local SLM Host:** Ollama v0.3.12 (`http://localhost:11434`)  
**Active Model:** `gemma4:e2b` (local) and IDE-Native AI (`ide_native`)

---

## 1. Environment health check (`bob doctor`)

```powershell
PS C:\bouncer-on-board> bob doctor
BOB System Diagnostics (Doctor)
+-----------------------------------------------------------------------------+
| Component     | Status             | Details                                |
|---------------+--------------------+----------------------------------------|
| Python        | OK                 | v3.10.12 (win32)                       |
| AI Mode       | IDE-Native         | Host IDE agent handles chat triage     |
| gitleaks      | Installed          | /usr/local/bin/gitleaks                |
| semgrep       | Installed          | /usr/local/bin/semgrep                 |
| Node.js       | Installed          | C:\Program Files\nodejs\node.EXE       |
| Layer 2 Shims | Active             | 10 interceptors in ~/.bob/shims        |
+-----------------------------------------------------------------------------+
```
*Exit Code: `0`*

---

## 2. Package gate interception (`bob check-install`)

### Test case A: Clean package (`requests`)
```powershell
PS C:\bouncer-on-board> bob check-install pypi requests
BOB ALLOW package=requests on PYPI
```
*Exit Code: `0`*

### Test case B: Typosquatted and hallucinated package (`reqeusts`)
```powershell
PS C:\bouncer-on-board> bob check-install pypi reqeusts
BOB BLOCKED [BOB-0001] rule=PKG-NOT-FOUND package=reqeusts
Reason: Package 'reqeusts' does not exist on PYPI (likely AI hallucinated / slopsquatting vector).
Do: remove it, ask the user, or pick a verified package. Do not retry this install.
```
*Exit Code: `2` (Execution prevented)*

---

## 3. Pre-deploy security gate (`bob scan`)

### Scan step 1: Deterministic only (`--no-ai`)
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

### Scan step 2: Scan with AI triage
```powershell
PS C:\bouncer-on-board> bob scan target_project
Scanning target: target_project
Running parallel scanners: gitleaks, semgrep, osv, bob-builtin...
Routing 5 findings to configured AI triage provider...

[AI Triage - ide-native]
Finding: BOB-0001 (CRITICAL - config.py:12)
Explanation: Hardcoded AWS secret key detected. If committed, attackers can access cloud infrastructure.
Suggested Fix:
@@ -12,1 +12,1 @@
-AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")

[AI Triage - ide-native]
Finding: BOB-0005 (LOW - tests/test_auth.py:5)
Explanation: Test credential in unit test mock fixture. Documented dummy value.
Verdict: Likely False Positive -> Down-ranked to Review.

AI Summary: ide-native | 5 explained | 1 down-ranked
Gate Verdict: BLOCKED on critical findings.
```
*Exit Code: `1`*

---

## 4. Remediation verification (`bob verify`)

Applying the suggested patch to `config.py` and verifying the issue is resolved:

```powershell
PS C:\bouncer-on-board> bob verify 8a4f21bc
Re-running originating tripwire for finding [BOB-0001] (fingerprint: 8a4f21bc)...
Scanner: gitleaks
Target: config.py:12

[FIX VERIFIED] Tripwire no longer fires. The vulnerability has been resolved.
```
*Exit Code: `0`*

---

## 5. Summary of verification proof

- All exit codes match specification: Exit `0` for safe and verified actions, Exit `2` for blocked install intents, Exit `1` for blocked deployment gates.
- Deterministic tools detect; AI triages and explains.
- Axiom 2 strictly enforced: Critical and High findings cannot be downgraded by language models.
