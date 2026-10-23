# PLAN.md — Phase 5: M4 Local Gemma 4 AI Triage, Fallback Templates & Verify

## Goal
Implement the local AI triage layer using small language models (Gemma 4 via Ollama on localhost), deterministic fallback templates when Ollama is unavailable, strict enforcement of Security Axiom 2 (AI can never suppress or downgrade Critical/High findings), and the `bob verify <fingerprint>` command.

## Tasks
1. **Task 1: Fallback Explanations (`src/bob/ai/fallback.py`)**
   - Provide static, beginner-friendly explanations (<= 80 words) and suggested fixes for all standard rule IDs.
   - Used when Ollama is offline or model is missing.

2. **Task 2: AI Prompts & Formatting (`src/bob/ai/prompts.py`)**
   - Wrap untrusted code context in `<untrusted>...</untrusted>`.
   - Never include unmasked secrets.
   - Enforce JSON format output with schema: `verdict`, `explanation`, `suggested_fix`.

3. **Task 3: Ollama Client (`src/bob/ai/ollama_client.py`)**
   - Probe `/api/tags` with short timeout (1.5s).
   - Post to `/api/chat` with `format="json"`, `temperature=0`, `keep_alive="5m"`.
   - Graceful fallback on network timeout, 404, or malformed JSON response.

4. **Task 4: Triage Engine & Policy Enforcement (`src/bob/ai/triage.py`)**
   - Process top findings (capped at 10 for CPU efficiency).
   - Strict enforcement of Axiom 2: AI can never override or lower Critical/High findings; only Medium/Low test/example tokens may be downranked.
   - Return structured triage result and summary stats.

5. **Task 5: CLI Integration (`src/bob/cli.py`)**
   - In `bob scan`: execute triage when `--no-ai` is not passed; display model name and plain-English explanations live; print the required AI summary line.
   - In `bob verify <fingerprint-prefix>`: look up finding from `.bob/report.json`, re-evaluate originating check on current file, exit 0 if resolved, exit 1 if still present.

6. **Task 6: Unit Tests & Verification**
   - `tests/unit/test_fallback.py`
   - `tests/unit/test_prompts.py`
   - `tests/unit/test_triage.py`
   - `tests/unit/test_verify.py`
   - Verify Acceptance Matrix Row 16.
