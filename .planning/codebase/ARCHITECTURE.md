# System Architecture & Design

## Two-Checkpoint Zero-Trust Model

BOB implements a dual-checkpoint architecture designed to protect developers and IDE agents from supply-chain attacks, prompt injection, and credential exfiltration.

```
+-----------------------------------------------------------------------------------+
|                                BOB ZERO-TRUST ENGINE                              |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ CHECKPOINT 1: PRE-ACTION INTERCEPTION ]                                        |
|  Triggered via IDE Hook (`PreToolUse`) or PATH Shim (`pip`, `npm`)                |
|                                                                                   |
|  Agent Command ---> [ Command Tokenizer ]                                         |
|                           |                                                       |
|                           +---> [ Package Gate ]                                  |
|                           |     * Top-5k Cache Hit? -> Allow (<10ms)              |
|                           |     * Human Allowlist Hit? -> Allow                   |
|                           |     * OSV Malicious Advisory? -> BLOCK                |
|                           |     * Age < 72h / Typosquat / Trope? -> BLOCK         |
|                           |                                                       |
|                           +---> [ Sensitive-Path Guard ]                          |
|                                 * Access to .env, .ssh, .git, AWS keys? -> BLOCK  |
|                                 * BOB Self-Protection (.bob/config)? -> BLOCK     |
|                                                                                   |
|                           Verdict: ALLOW (exit 0) or BLOCK (exit 2)               |
|                                                                                   |
|-----------------------------------------------------------------------------------|
|                                                                                   |
|  [ CHECKPOINT 2: PRE-DEPLOY SECURITY SCANNER ]                                    |
|  Triggered via `bob scan <path>` or CI/CD Pipeline                                |
|                                                                                   |
|  Repository Files ---> [ Built-in Tripwire Pack ] (Secrets, Code Exec, Injection) |
|                                   +                                               |
|                        [ SARIF Ingestion ] (Gitleaks, Semgrep normalized)         |
|                                   |                                               |
|                                   v                                               |
|                        [ Findings Deduplication Engine ] (SHA-256 Fingerprint)    |
|                                   |                                               |
|                                   v                                               |
|                        [ AI Triage & Explanation ]                                |
|                        * Local Gemma 4 via Ollama or Cloud Gemini/OpenAI          |
|                        * Offline Fallback Templates                               |
|                        * STRICT SECURITY AXIOM 2: AI NEVER downgrades Critical    |
|                          or High findings!                                        |
|                                   |                                               |
|                                   v                                               |
|                        [ Multi-Format Reporter ]                                  |
|                        * Terminal Tables (Rich ASCII)                             |
|                        * SARIF Output (`.bob/report.sarif`)                       |
|                        * Markdown Report (`.bob/report.md`)                       |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

## Core Security Invariants
1. **Security Axiom 1 (Fail-Closed on High/Critical Risks)**:
   - Malicious package advisories (`MAL-*`) or direct hits on sensitive credentials trigger an immediate exit code `2` (Block).
2. **Security Axiom 2 (AI Authority Ceiling)**:
   - AI models (local SLM or cloud) are advisory-only. The AI can provide context, plain-English explanations, and remediation diffs, but it can NEVER downgrade a Critical or High finding, nor can it approve an untrusted package.
3. **Deterministic Latency Budget**:
   - `bob intercept` targets under 400ms for pre-action checks. Local cache hits resolve in <15ms.
4. **Secret Masking Guarantee**:
   - Discovered secrets in scanner outputs, SARIF reports, and log records are permanently masked: only the first 4 characters are shown, followed by `****`.
5. **Safe Reflection Resistance**:
   - Error messages returned to IDE agents use fixed, pre-defined templates to prevent prompt injection reflection attacks.
