#!/usr/bin/env bash
# Interactive 3-Act Demo Script for BOB (bouncer-on-board) on Linux/macOS.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$REPO_ROOT/src:$PYTHONPATH"
export BOB_CONFIG="$REPO_ROOT/demo/workdir/.bob/config.yaml"

PYCMD="python3"
if [ -f "$REPO_ROOT/.venv/bin/python" ]; then
    PYCMD="$REPO_ROOT/.venv/bin/python"
fi

echo -e "\033[1;36m=================================================================="
echo -e "    BOB (bouncer-on-board) — Live Interactive Hackathon Demo"
echo -e "==================================================================\033[0m"

# Ensure mock registry
echo -e "\n\033[1;33m[+] Checking local mock registry on port 8765...\033[0m"
if ! curl -s http://127.0.0.1:8765/healthz > /dev/null 2>&1; then
    echo "    Starting demo/mock_registry/server.py in background..."
    $PYCMD "$REPO_ROOT/demo/mock_registry/server.py" &
    MOCK_PID=$!
    sleep 1
    trap "kill $MOCK_PID 2>/dev/null || true" EXIT
fi
echo -e "\033[1;32m    Mock registry active at http://127.0.0.1:8765\033[0m"

step_prompt() {
    echo -e "\n\033[1;30m------------------------------------------------------------------\033[0m"
    echo -e "\033[1;35m>> $1\033[0m"
    read -rp "   Press [Enter] to execute..."
}

# ACT 1
echo -e "\n\033[1;33m=== ACT 1: Pre-Install Package Gate (Deterministic, Fast <400ms) ===\033[0m"
step_prompt "1.1: Agent tries to install hallucinated package 'demo-missing-lib'"
$PYCMD -m bob.cli check-install pypi demo-missing-lib || echo "(Blocked as expected with exit $?)"

step_prompt "1.2: Agent tries to install typosquatted package 'reqeusts'"
$PYCMD -m bob.cli check-install pypi reqeusts || echo "(Blocked as expected with exit $?)"

step_prompt "1.3: Agent attempts install of 'demo-evil-lib' with malicious setup.py"
$PYCMD -m bob.cli check-install pypi demo-evil-lib || echo "(Blocked as expected with exit $?)"

# ACT 2
echo -e "\n\033[1;33m=== ACT 2: Agent Action Guard & Prompt Injection Defense ===\033[0m"
step_prompt "2.1: Scanner inspects README for hidden/indirect prompt injection"
$PYCMD -m bob.cli guard-text "$REPO_ROOT/demo/injection_fixture/README.md" || echo "(Flagged with exit $?)"

step_prompt "2.2: Intercept agent command attempting to read sensitive .env"
$PYCMD -m bob.cli intercept --adapter generic --cmd "cat .env" || echo "(Blocked with exit $?)"

step_prompt "2.3: Intercept agent command attempting to tamper with BOB (.bob allow)"
$PYCMD -m bob.cli intercept --adapter generic --cmd "bob allow demo-evil-lib" || echo "(Blocked with exit $?)"

# ACT 3
echo -e "\n\033[1;33m=== ACT 3: Pre-Deploy Gate — Local SLM Triage & Fix Verification ===\033[0m"
step_prompt "3.1: Raw Deterministic Scan (--no-ai) — High noise, decoys flagged"
$PYCMD -m bob.cli scan "$REPO_ROOT/demo/vulnerable_app" --no-ai || echo "(Scan gate failed with exit $?)"

step_prompt "3.2: Local SLM Triaged Scan — Gemma 4 visible on screen"
$PYCMD -m bob.cli scan "$REPO_ROOT/demo/vulnerable_app" || echo "(Scan completed with exit $?)"

step_prompt "3.3: Run Formal Benchmark Evaluation (eval/run_eval.py)"
$PYCMD "$REPO_ROOT/eval/run_eval.py"

echo -e "\n\033[1;36m=================================================================="
echo -e "  DEMO COMPLETE — Zero-Trust Security Gatekeeper for AI Agents!"
echo -e "==================================================================\033[0m\n"
