<#
.SYNOPSIS
    Interactive 3-Act Demo Script for BOB (bouncer-on-board) on Windows PowerShell.
.DESCRIPTION
    Runs the full demo suite offline against the local mock registry.
    Pauses between acts for live narration.
#>

$ErrorActionPreference = "Continue"

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "    BOB (bouncer-on-board) — Live Interactive Hackathon Demo    " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# Set environment
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path "$scriptDir\..").Path
$env:PYTHONPATH = "$repoRoot\src"
$env:BOB_CONFIG = "$repoRoot\demo\workdir\.bob\config.yaml"

# Determine python command
$pyCmd = "python"
if (Test-Path "$repoRoot\.venv\Scripts\python.exe") {
    $pyCmd = "$repoRoot\.venv\Scripts\python.exe"
}

# Start mock registry if not running
Write-Host "`n[+] Ensuring local mock registry is running on port 8765..." -ForegroundColor Yellow
$registryRunning = $false
try {
    $check = Invoke-WebRequest -Uri "http://127.0.0.1:8765/healthz" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
    if ($check.StatusCode -eq 200) { $registryRunning = $true }
} catch {
    $registryRunning = $false
}

$regProcess = $null
if (-not $registryRunning) {
    Write-Host "    Launching demo/mock_registry/server.py in background..." -ForegroundColor Gray
    $regProcess = Start-Process -FilePath $pyCmd -ArgumentList "$repoRoot\demo\mock_registry\server.py" -PassThru -WindowStyle Hidden
    Start-Sleep -Milliseconds 800
}
Write-Host "    Mock registry active at http://127.0.0.1:8765" -ForegroundColor Green

function Step-Prompt($title) {
    Write-Host "`n------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ">> $title" -ForegroundColor Magenta
    Read-Host "   Press [Enter] to execute..."
}

# ----------------------------------------------------------------------
# ACT 1: Pre-Install Package Gate
# ----------------------------------------------------------------------
Write-Host "`n==================================================================" -ForegroundColor Yellow
Write-Host "  ACT 1: Pre-Install Package Gate (Deterministic, Fast <400ms)    " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow

Step-Prompt "1.1: Agent tries to install hallucinated package 'demo-missing-lib'"
Write-Host "Running: $pyCmd -m bob.cli check-install pypi demo-missing-lib" -ForegroundColor White
& $pyCmd -m bob.cli check-install pypi demo-missing-lib
Write-Host "Exit Code: $LASTEXITCODE (Expected 2: BLOCKED)" -ForegroundColor Gray

Step-Prompt "1.2: Agent tries to install typosquatted package 'reqeusts'"
Write-Host "Running: $pyCmd -m bob.cli check-install pypi reqeusts" -ForegroundColor White
& $pyCmd -m bob.cli check-install pypi reqeusts
Write-Host "Exit Code: $LASTEXITCODE (Expected 2: BLOCKED)" -ForegroundColor Gray

Step-Prompt "1.3: Agent attempts install of 'demo-evil-lib' with malicious setup.py"
Write-Host "Running: $pyCmd -m bob.cli check-install pypi demo-evil-lib" -ForegroundColor White
& $pyCmd -m bob.cli check-install pypi demo-evil-lib
Write-Host "Exit Code: $LASTEXITCODE (Expected 2: BLOCKED before execution)" -ForegroundColor Gray

# ----------------------------------------------------------------------
# ACT 2: Agent Action & Injection Guard
# ----------------------------------------------------------------------
Write-Host "`n==================================================================" -ForegroundColor Yellow
Write-Host "  ACT 2: Agent Action Guard & Prompt Injection Defense            " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow

Step-Prompt "2.1: Scanner inspects README for hidden/indirect prompt injection"
Write-Host "Running: $pyCmd -m bob.cli guard-text demo/injection_fixture/README.md" -ForegroundColor White
& $pyCmd -m bob.cli guard-text "$repoRoot\demo\injection_fixture\README.md"
Write-Host "Exit Code: $LASTEXITCODE (Expected 2: Flagged INJ-010 & INJ-020)" -ForegroundColor Gray

Step-Prompt "2.2: Intercept agent command attempting to read sensitive .env"
Write-Host "Running: $pyCmd -m bob.cli intercept --adapter generic --cmd 'cat .env'" -ForegroundColor White
& $pyCmd -m bob.cli intercept --adapter generic --cmd "cat .env"
Write-Host "Exit Code: $LASTEXITCODE (Expected 2: GUARD-SENSITIVE-PATH blocked)" -ForegroundColor Gray

Step-Prompt "2.3: Intercept agent command attempting to tamper with BOB (.bob allow)"
Write-Host "Running: $pyCmd -m bob.cli intercept --adapter generic --cmd 'bob allow demo-evil-lib'" -ForegroundColor White
& $pyCmd -m bob.cli intercept --adapter generic --cmd "bob allow demo-evil-lib"
Write-Host "Exit Code: $LASTEXITCODE (Expected 2: GUARD-BOB-SELF-PROTECT blocked)" -ForegroundColor Gray

# ----------------------------------------------------------------------
# ACT 3: Pre-Deploy Scan with Local SLM (Gemma 4 via Ollama)
# ----------------------------------------------------------------------
Write-Host "`n==================================================================" -ForegroundColor Yellow
Write-Host "  ACT 3: Pre-Deploy Gate — Local SLM Triage & Fix Verification    " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Yellow

Step-Prompt "3.1: Raw Deterministic Scan (--no-ai) — High noise, decoys flagged"
Write-Host "Running: $pyCmd -m bob.cli scan demo/vulnerable_app --no-ai" -ForegroundColor White
& $pyCmd -m bob.cli scan "$repoRoot\demo\vulnerable_app" --no-ai
Write-Host "Exit Code: $LASTEXITCODE (Gate failed on Critical/High)" -ForegroundColor Gray

Step-Prompt "3.2: Local SLM Triaged Scan — Gemma 4 visible on screen"
Write-Host "Running: $pyCmd -m bob.cli scan demo/vulnerable_app" -ForegroundColor White
& $pyCmd -m bob.cli scan "$repoRoot\demo\vulnerable_app"
Write-Host "Exit Code: $LASTEXITCODE" -ForegroundColor Gray

Step-Prompt "3.3: Run Formal Benchmark Evaluation (eval/run_eval.py)"
Write-Host "Running: $pyCmd eval/run_eval.py" -ForegroundColor White
& $pyCmd "$repoRoot\eval\run_eval.py"

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "  DEMO COMPLETE — Zero-Trust Security Gatekeeper for AI Agents!  " -ForegroundColor Cyan
Write-Host "==================================================================`n" -ForegroundColor Cyan

# Cleanup mock registry process if spawned
if ($regProcess -ne $null) {
    Stop-Process -Id $regProcess.Id -Force -ErrorAction SilentlyContinue
}
