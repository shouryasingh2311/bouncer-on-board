# Security Policy

## 1. Reporting a Vulnerability

If you discover a security issue or bypass in BOB (`bouncer-on-board`), please report it responsibly:

- **Preferred Method**: Use GitHub [Private Vulnerability Reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-communicating-vulnerabilities/privately-reporting-a-security-vulnerability) directly in this repository (Security tab -> "Report a vulnerability").
- **Alternative Method**: If private reporting is unavailable, contact the project maintainers via encrypted email or open an issue marked `[SECURITY-ADVISORY: REQUEST CONTACT]` without disclosing the exploit payload publicly.

Please include:
- A description of the attack vector or bypass technique.
- Inert reproduction steps (do not provide working credential-theft or exfiltration payloads).
- Expected vs. actual bouncer behavior.

We acknowledge receipt within 48 hours and coordinate fixes prior to public disclosure.

---

## 2. Scope

### In Scope
- Bypasses of `bob intercept` command parsing that allow package installation commands to slip past the pre-install gate.
- Path traversal or execution vulnerabilities in archive static inspection (`pkg/static_inspect.py`).
- Flaws in sensitive path normalization allowing unauthorized access to credential files (`.env`, `~/.ssh`).
- Prompt injection vulnerabilities that evade static rule packs without altering semantic meaning.

### Out of Scope
- Direct local compromises where an attacker already possesses full shell execution rights without going through monitored agent interfaces.
- Outages or data tampering upstream on PyPI, npm, or OSV servers.
- Hallucinations in external local LLM models when running in advisory mode.

---

## 3. Honest Posture & No-Guarantee Statement

BOB provides defensive tripwires and heuristic checks designed to elevate developer safety during AI-assisted programming.

**BOB does not guarantee the complete absence of vulnerabilities.** A clean scan result means zero known deterministic rules fired; it is not a certificate of security. Attackers constantly devise novel evasion techniques, and newly published packages may evade heuristics. Always exercise human oversight before running or shipping production software.

---

## 4. Responsible Use

BOB is a defensive security tool intended to protect developer workstations, CI/CD pipelines, and coding agents. You may only scan, monitor, or intercept repositories, systems, and package environments that you own or have explicit authorization to inspect.
