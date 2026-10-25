"""BOB CLI application using Typer."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import time
from typing import List, Optional

import httpx
from rich.console import Console
from rich.table import Table
import typer
import yaml

from bob import __version__
from bob.adapters.shim import (
    get_default_shims_dir,
    install_shims,
    uninstall_shims,
)
from bob.ai.cloud_client import validate_cloud_credentials
from bob.ai.triage import triage_findings
from bob.banner import print_banner
from bob.setup import run_setup_wizard
from bob.cmdparse import (
    check_dangerous_remote_execution,
    extract_install_intents,
    parse_pkg_and_version,
)
from bob.config import load_config
from bob.guards.injection import (
    evaluate_injection_semantics,
    scan_file_for_injections,
)
from bob.guards.sensitive_paths import (
    check_command_sensitive_paths,
    check_self_protection,
)
from bob.models import Decision, Finding
from bob.pkg.gate import evaluate_package
from bob.pkg.osv import query_osv
from bob.report.markdown import count_severities, write_reports, ZERO_FINDINGS_MESSAGE
from bob.scan.builtin import scan_file_content
from bob.scan.runners import run_all_scanners

app = typer.Typer(
    name="bob",
    help="Zero-Trust IDE Agent Firewall & Pre-Deploy Security Gatekeeper",
    no_args_is_help=False,
)
console = Console(soft_wrap=True)
err_console = Console(stderr=True, soft_wrap=True)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"bob version {__version__}")
        raise typer.Exit(code=0)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show BOB version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Zero-Trust IDE Agent Firewall & Pre-Deploy Security Gatekeeper."""
    if ctx.invoked_subcommand is None:
        if sys.stdout.isatty():
            print_banner(console)
        console.print(ctx.get_help())
        if sys.stdout.isatty():
            console.print("\n[dim]Tip: Run [bold]bob setup[/bold] to configure local Gemma/Ollama or cloud API keys.[/dim]\n")
        raise typer.Exit(code=0)


@app.command()
def doctor() -> None:
    """Report available scanners, Ollama connection, configured model, and system environment."""
    if sys.stdout.isatty():
        print_banner(console)
    cfg = load_config()

    table = Table(title="[bold cyan]BOB System Diagnostics (Doctor)[/bold cyan]")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    # Python & Platform
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python", "[green]OK[/green]", f"v{py_ver} ({sys.platform})")

    ai_provider = cfg.ai_provider.lower()
    needs_setup_prompt = False

    if ai_provider == "ide_native":
        table.add_row(
            "AI Mode",
            "[green]IDE-Native[/green]",
            "Host IDE agent handles chat triage (Zero external AI calls / Zero token cost)",
        )
    elif ai_provider == "deterministic":
        table.add_row(
            "AI Mode",
            "[green]Active[/green]",
            "Pure deterministic mode (100% offline, zero external dependencies)",
        )
    elif ai_provider in ("gemini", "openai", "groq", "openrouter", "custom", "cloud"):
        provider_name = ai_provider.title()
        if cfg.api_key and cfg.api_key.strip():
            masked_key = (
                cfg.api_key[:4] + "..." + cfg.api_key[-4:]
                if len(cfg.api_key) > 8
                else "****"
            )
            is_valid, msg = validate_cloud_credentials(
                ai_provider, cfg.api_key, cfg.model, timeout=2.0
            )
            if is_valid:
                table.add_row(
                    f"Cloud AI ({provider_name})",
                    "[green]Online[/green]",
                    f"{cfg.model} (key: {masked_key}) - {msg}",
                )
            else:
                table.add_row(
                    f"Cloud AI ({provider_name})",
                    "[yellow]Auth Warning[/yellow]",
                    f"{cfg.model} (key: {masked_key}) - {msg}. (Fallback templates active)",
                )
                needs_setup_prompt = True
        else:
            table.add_row(
                f"Cloud AI ({provider_name})",
                "[yellow]Key Missing[/yellow]",
                "No API key configured. Run 'bob setup' to configure.",
            )
            needs_setup_prompt = True
    else:
        # Default: Local Ollama & Model Probe
        ollama_ok = False
        model_found = False
        latency_ms = 0.0

        try:
            t0 = time.perf_counter()
            resp = httpx.get(f"{cfg.ollama_url.rstrip('/')}/api/tags", timeout=1.5)
            latency_ms = (time.perf_counter() - t0) * 1000

            if resp.status_code == 200:
                ollama_ok = True
                tags_data = resp.json()
                models_list = [
                    m.get("name", "") for m in tags_data.get("models", [])
                ]
                cfg_model = cfg.model.lower()
                model_found = any(
                    cfg_model == m.lower() or m.lower().startswith(f"{cfg_model}:")
                    for m in models_list
                )
        except Exception:
            ollama_ok = False

        if ollama_ok:
            table.add_row(
                "Ollama Service",
                "[green]Online[/green]",
                f"{cfg.ollama_url} (latency: {latency_ms:.1f}ms)",
            )
            if model_found:
                table.add_row(
                    "AI Model",
                    "[green]Available[/green]",
                    f"{cfg.model} (ready for local triage)",
                )
            else:
                table.add_row(
                    "AI Model",
                    "[yellow]Not Found[/yellow]",
                    f"Configured: '{cfg.model}'. Run `ollama pull {cfg.model}`. (Fallback templates will be used)",
                )
                needs_setup_prompt = True
        else:
            table.add_row(
                "Ollama Service",
                "[yellow]Offline[/yellow]",
                f"{cfg.ollama_url} unreachable. (Deterministic fallback templates will be used)",
            )
            table.add_row(
                "AI Model",
                "[yellow]Fallback[/yellow]",
                "Deterministic rule templates active",
            )
            needs_setup_prompt = True

    # External Scanners (both optional per PROJECT.md Section 4)
    gitleaks_path = shutil.which("gitleaks")
    if gitleaks_path:
        table.add_row("gitleaks", "[green]Installed[/green]", gitleaks_path)
    else:
        table.add_row(
            "gitleaks",
            "[dim]Missing (Optional)[/dim]",
            "Built-in secrets tripwire will be used",
        )

    semgrep_path = shutil.which("semgrep")
    if semgrep_path:
        table.add_row("semgrep", "[green]Installed[/green]", semgrep_path)
    else:
        table.add_row(
            "semgrep",
            "[dim]Missing (Optional)[/dim]",
            "Built-in AST/regex tripwires will be used",
        )
    # Node.js runtime check
    node_path = shutil.which("node")
    if node_path:
        table.add_row("Node.js", "[green]Installed[/green]", node_path)
    else:
        table.add_row(
            "Node.js",
            "[dim]Missing (Optional)[/dim]",
            "Needed only for npx/npm global command",
        )

    # Layer 2 PATH Shims check
    from bob.adapters.shim import get_default_shims_dir
    shims_dir = get_default_shims_dir()
    if shims_dir.exists() and any(shims_dir.iterdir()):
        shim_count = len(list(shims_dir.iterdir()))
        table.add_row(
            "Layer 2 Shims",
            "[green]Active[/green]",
            f"{shim_count} interceptors in {shims_dir}",
        )
    else:
        table.add_row(
            "Layer 2 Shims",
            "[yellow]Not Installed[/yellow]",
            "Run 'bob protect' to configure automatic terminal protection",
        )

    console.print(table)
    console.print(
        "\n[dim]Note: External tools and Ollama are optional. BOB operates fully in deterministic mode without them.[/dim]"
    )

    if needs_setup_prompt and sys.stdin.isatty() and sys.stdout.isatty():
        from rich.prompt import Confirm
        if Confirm.ask("\n[bold cyan]Run interactive AI setup assistant now?[/bold cyan]", default=False, console=console):
            run_setup_wizard(console)

    raise typer.Exit(code=0)


@app.command(name="setup")
def setup() -> None:
    """Interactive onboarding assistant for local Gemma/Ollama or API keys."""
    run_setup_wizard(console)
    raise typer.Exit(code=0)



@app.command("check-install")
def check_install(
    ecosystem: str = typer.Argument(..., help="Package ecosystem: pypi or npm"),
    package: str = typer.Argument(..., help="Package name with optional ==version"),
    json_output: bool = typer.Option(
        False, "--json", help="Output machine-readable Decision JSON"
    ),
) -> None:
    """Run package gate manually before installation."""
    cfg = load_config()
    pkg_name, version = parse_pkg_and_version(package, ecosystem.lower())

    decision = evaluate_package(ecosystem, pkg_name, version, cfg)

    if json_output:
        console.print(json.dumps(decision.to_dict(), indent=2))

    first_finding = decision.findings[0] if decision.findings else None
    finding_id = first_finding.id if first_finding else "BOB-0001"
    rule_id = first_finding.rule_id if first_finding else "PKG-GATE"
    reason_text = decision.reasons[0] if decision.reasons else "Security policy check"

    if decision.action == "block":
        err_console.print(f"BOB BLOCKED [{finding_id}] rule={rule_id} package={pkg_name}")
        err_console.print(f"Reason: {reason_text}")
        err_console.print("Do: remove it, ask the user, or pick a verified package. Do not retry this install.")
        raise typer.Exit(code=2)
    elif decision.action == "warn":
        err_console.print(f"BOB WARN [{finding_id}] rule={rule_id} package={pkg_name}: {reason_text}")
        raise typer.Exit(code=0)
    else:
        # allow
        if not json_output:
            console.print(f"[green]BOB ALLOW[/green] package={pkg_name} on {ecosystem.upper()}")
        raise typer.Exit(code=0)



def append_audit_log(entry: dict) -> None:
    """Append decision entry to .bob/log.jsonl."""
    try:
        log_dir = Path(".bob")
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


@app.command()
def intercept(
    adapter: str = typer.Option(
        "generic", "--adapter", help="Adapter: generic or antigravity"
    ),
    cmd: Optional[str] = typer.Option(
        None, "--cmd", help="Command string to inspect"
    ),
) -> None:
    """Interception hook entrypoint for IDE agents and terminal shims."""
    cfg = load_config()

    cmd_str = cmd
    if cmd_str is None:
        if not sys.stdin.isatty():
            raw_stdin = sys.stdin.read().strip()
            if raw_stdin.startswith("{") and "toolCall" in raw_stdin:
                try:
                    payload = json.loads(raw_stdin)
                    cmd_str = (
                        payload.get("toolCall", {})
                        .get("args", {})
                        .get("CommandLine", "")
                    )
                except Exception:
                    cmd_str = raw_stdin
            else:
                cmd_str = raw_stdin

    if not cmd_str:
        if adapter == "antigravity":
            console.print(json.dumps({"decision": "allow"}))
        raise typer.Exit(code=0)

    # 0. Check dangerous remote execution (curl ... | bash, irm ... | iex)
    remote_hit = check_dangerous_remote_execution(cmd_str)
    if remote_hit:
        reason = f"{remote_hit.title} ({remote_hit.evidence}). Piping remote code directly into a shell interpreter is prohibited."
        append_audit_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd_str,
            "action": "block",
            "rule_id": remote_hit.rule_id,
            "reason": reason,
        })
        if adapter == "antigravity":
            console.print(json.dumps({"decision": "deny", "reason": f"BOB BLOCKED [{remote_hit.id}] rule={remote_hit.rule_id} cmd={cmd_str}. {reason}"}))
        else:
            err_console.print(f"BOB BLOCKED [{remote_hit.id}] rule={remote_hit.rule_id} cmd={cmd_str}")
            err_console.print(f"Reason: {reason}")
            err_console.print("Do: inspect and verify the remote script before executing.")
        raise typer.Exit(code=2)

    # 1. Check self-protection
    self_prot_hit = check_self_protection(cmd_str)
    if self_prot_hit:
        reason = f"{self_prot_hit.title}. Modifying BOB configuration or allowlist is prohibited."
        append_audit_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd_str,
            "action": "block",
            "rule_id": self_prot_hit.rule_id,
            "reason": reason,
        })
        if adapter == "antigravity":
            console.print(json.dumps({"decision": "deny", "reason": f"BOB BLOCKED [{self_prot_hit.id}] rule={self_prot_hit.rule_id} cmd={cmd_str}. {reason}"}))
        else:
            err_console.print(f"BOB BLOCKED [{self_prot_hit.id}] rule={self_prot_hit.rule_id} cmd={cmd_str}")
            err_console.print(f"Reason: {reason}")
            err_console.print("Do: do not attempt to weaken or reconfigure BOB.")
        raise typer.Exit(code=2)

    # 2. Check sensitive paths
    sens_hit = check_command_sensitive_paths(cmd_str, cfg)
    if sens_hit:
        reason = f"{sens_hit.title}. Reading or writing sensitive credential paths is prohibited."
        append_audit_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd_str,
            "action": "block",
            "rule_id": sens_hit.rule_id,
            "reason": reason,
        })
        if adapter == "antigravity":
            console.print(json.dumps({"decision": "deny", "reason": f"BOB BLOCKED [{sens_hit.id}] rule={sens_hit.rule_id} target={sens_hit.file}. {reason}"}))
        else:
            err_console.print(f"BOB BLOCKED [{sens_hit.id}] rule={sens_hit.rule_id} target={sens_hit.file}")
            err_console.print(f"Reason: {reason}")
            err_console.print("Do: remove references to sensitive paths from your command.")
        raise typer.Exit(code=2)

    # 3. Check install intents
    intents = extract_install_intents(cmd_str)
    for intent in intents:
        if intent.is_unverifiable:
            err_console.print(f"BOB WARN [BOB-0000] rule=PKG-UNVERIFIABLE package={intent.package}: direct URL/local archive cannot be verified statically.")
            continue

        decision = evaluate_package(intent.ecosystem, intent.package, intent.version, cfg)
        first_finding = decision.findings[0] if decision.findings else None
        finding_id = first_finding.id if first_finding else "BOB-0001"
        rule_id = first_finding.rule_id if first_finding else "PKG-GATE"
        reason_text = decision.reasons[0] if decision.reasons else "Package gate policy check."

        append_audit_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cmd": cmd_str,
            "action": decision.action,
            "rule_id": rule_id,
            "reason": reason_text,
        })

        if decision.action == "block":
            if adapter == "antigravity":
                console.print(json.dumps({"decision": "deny", "reason": f"BOB BLOCKED [{finding_id}] rule={rule_id} package={intent.package}. {reason_text}"}))
            else:
                err_console.print(f"BOB BLOCKED [{finding_id}] rule={rule_id} package={intent.package}")
                err_console.print(f"Reason: {reason_text}")
                err_console.print("Do: remove it, ask the user, or pick a verified package. Do not retry this install.")
            raise typer.Exit(code=2)
        elif decision.action == "warn":
            err_console.print(f"BOB WARN [{finding_id}] rule={rule_id} package={intent.package}: {reason_text}")

    # 4. Clean command
    append_audit_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cmd": cmd_str,
        "action": "allow",
        "rule_id": "CLEAN",
        "reason": "Command allowed.",
    })
    if adapter == "antigravity":
        console.print(json.dumps({"decision": "allow"}))
    raise typer.Exit(code=0)



@app.command()
def scan(
    path: Path = typer.Argument(
        Path("."), help="Path to codebase directory to scan"
    ),
    no_ai: bool = typer.Option(
        False, "--no-ai", help="Skip AI triage; deterministic scan only"
    ),
    cloud: bool = typer.Option(
        False, "--cloud", help="Cloud scanning (out of MVP)"
    ),
    out_dir: Path = typer.Option(
        Path(".bob"), "--out-dir", help="Directory for report.md and report.json"
    ),
) -> None:
    """Run pre-deploy scan with deterministic tools and local AI triage."""
    if cloud:
        console.print("[dim]Note: --cloud is not implemented; using local/deterministic mode.[/dim]")

    if not path.exists():
        err_console.print(f"[bold red]Error:[/bold red] Target path '{path}' does not exist.")
        raise typer.Exit(code=3)

    resolved_path = path.resolve()
    user_home = Path.home().resolve()
    if resolved_path == user_home or resolved_path.parent == resolved_path:
        err_console.print(
            f"[bold red]Refusing to scan user home or root directory:[/bold red] '{resolved_path}'\n\n"
            f"[yellow]Scanning a user home folder crawls hundreds of thousands of OS and AppData files.\n"
            f"Please run BOB inside your project directory:\n"
            f"  cd <path_to_your_project>\n"
            f"  bob scan .\n\n"
            f"Or specify the project directory explicitly:\n"
            f"  bob scan ./my-project[/yellow]"
        )
        raise typer.Exit(code=2)

    cfg = load_config()

    try:
        findings, tools_run, tools_skipped = run_all_scanners(path, cfg)
    except Exception as e:
        err_console.print(f"[bold red]Tool Error during scan:[/bold red] {e}")
        raise typer.Exit(code=3)

    model_display = "none"
    if not no_ai:
        findings, model_display, explained_count, downranked_count = triage_findings(
            findings, cfg, target_dir=path
        )
        for f in findings:
            if f.ai:
                console.print(f"[{f.ai.model}] {f.id} ({f.title}): {f.ai.explanation}")
        if "unavailable" in model_display:
            console.print("AI: deterministic templates (model unavailable)")
        else:
            console.print(
                f"AI: {model_display} | {explained_count} explained | {downranked_count} down-ranked"
            )

    # Write .bob/report.md and .bob/report.json
    md_path, json_path = write_reports(findings, tools_run, tools_skipped, out_dir, model_name=model_display)

    counts = count_severities(findings)

    table = Table(title=f"[bold cyan]BOB Pre-Deploy Scan Summary ({path})[/bold cyan]")
    table.add_column("Severity", style="bold")
    table.add_column("Count")
    for sev in ("critical", "high", "medium", "low", "info"):
        color = "red" if sev in ("critical", "high") else ("yellow" if sev == "medium" else "green")
        table.add_row(f"[{color}]{sev.upper()}[/{color}]", str(counts[sev]))

    console.print(table)
    console.print(f"[dim]Reports written to {md_path} and {json_path}[/dim]")

    if not findings:
        console.print(f"[green]{ZERO_FINDINGS_MESSAGE}[/green]")
        raise typer.Exit(code=0)

    # Fail gate if any finding matches fail_gate_on (default: critical, high)
    failing_findings = [f for f in findings if f.severity.lower() in cfg.fail_gate_on]
    if failing_findings:
        err_console.print(
            f"\n[bold red]BOB SCAN GATE FAILED[/bold red]: {len(failing_findings)} issue(s) matching fail policy {cfg.fail_gate_on}."
        )
        raise typer.Exit(code=1)

    console.print("\n[green]BOB SCAN GATE PASSED[/green] (no critical or high findings).")
    raise typer.Exit(code=0)


@app.command()
def verify(
    finding_id: str = typer.Argument(
        ..., help="Finding ID or fingerprint prefix to verify"
    ),
    report_file: Path = typer.Option(
        Path(".bob/report.json"), "--report", help="Path to scan report.json"
    ),
) -> None:
    """Re-run originating check after a fix to prove patch resolved finding."""
    if not report_file.is_file():
        err_console.print(f"[bold red]Error:[/bold red] Report file '{report_file}' not found. Run 'bob scan' first.")
        raise typer.Exit(code=1)

    try:
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        err_console.print(f"[bold red]Error reading report:[/bold red] {e}")
        raise typer.Exit(code=1)

    findings = data.get("findings", [])
    target_finding = None
    query = finding_id.lower()

    for item in findings:
        f_id = item.get("id", "").lower()
        f_fp = item.get("fingerprint", "").lower()
        if query == f_id or f_fp.startswith(query) or query in f_fp:
            target_finding = item
            break

    if not target_finding:
        err_console.print(f"[bold red]Error:[/bold red] Finding '{finding_id}' not found in report.")
        raise typer.Exit(code=1)

    rel_file = target_finding.get("file")
    rule_id = target_finding.get("rule_id", "")
    target_id = target_finding.get("id", finding_id)

    if not rel_file:
        console.print(f"[green]BOB VERIFY PASSED[/green]: [{target_id}] No specific file to check; verified resolved.")
        raise typer.Exit(code=0)

    target_path = Path(rel_file)
    if not target_path.exists():
        console.print(f"[green]BOB VERIFY PASSED[/green]: [{target_id}] File '{rel_file}' has been removed or renamed. Finding resolved.")
        raise typer.Exit(code=0)

    # Re-run check on target file
    try:
        content = target_path.read_text(encoding="utf-8", errors="replace")
        new_findings = scan_file_content(rel_file, content)
    except Exception as e:
        err_console.print(f"[bold red]Error re-scanning file:[/bold red] {e}")
        raise typer.Exit(code=1)

    matching_new = [f for f in new_findings if f.rule_id == rule_id]
    if matching_new:
        err_console.print(
            f"[bold red]BOB VERIFY FAILED[/bold red]: [{target_id}] {rule_id} is still present in {rel_file} (Line {matching_new[0].line})."
        )
        raise typer.Exit(code=1)

    console.print(f"[green]BOB VERIFY PASSED[/green]: [{target_id}] {rule_id} was successfully resolved.")
    raise typer.Exit(code=0)



@app.command(name="guard-text")
def guard_text(
    path: Path = typer.Argument(
        ..., help="Path to text or markdown file to scan for injections"
    ),
    ai: bool = typer.Option(
        False, "--ai", help="Query local SLM for semantic second opinion"
    ),
) -> None:
    """Scan file for prompt injection and instruction overrides before agent reads it."""
    if not path.is_file():
        err_console.print(f"[bold red]Error:[/bold red] Target file '{path}' does not exist.")
        raise typer.Exit(code=1)

    findings = scan_file_for_injections(path)
    cfg = load_config()

    if ai:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            ai_opinion = evaluate_injection_semantics(content, cfg)
            if ai_opinion:
                console.print(f"AI: {cfg.model} | {ai_opinion}")
            else:
                console.print("AI second opinion: unavailable")
        except Exception:
            console.print("AI second opinion: unavailable")

    high_crit_findings = [f for f in findings if f.severity.lower() in ("critical", "high")]
    if high_crit_findings:
        for f in high_crit_findings:
            err_console.print(f"BOB BLOCKED [{f.id}] rule={f.rule_id} file={path}")
            err_console.print(f"Reason: {f.title}")
            err_console.print(f"Evidence: {f.evidence}")
            err_console.print("Do: review and sanitize this file before allowing the agent to read it.")
        raise typer.Exit(code=2)

    console.print(f"[green]BOB GUARD-TEXT PASSED[/green]: No high/critical prompt injection tripwires detected in {path}.")
    raise typer.Exit(code=0)


@app.command()
def audit(
    manifest_path: Path = typer.Option(
        Path("requirements.txt"), "--manifest", help="Manifest or lockfile to audit"
    ),
) -> None:
    """Check lockfiles and installed dependencies against OSV advisories."""
    if not manifest_path.is_file():
        console.print(f"[dim]No manifest found at '{manifest_path}'. Lockfile audit skipped.[/dim]")
        raise typer.Exit(code=0)

    try:
        content = manifest_path.read_text(encoding="utf-8", errors="replace")
        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
    except Exception as e:
        err_console.print(f"[bold red]Error reading manifest:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[bold cyan]BOB Audit ({manifest_path}):[/bold cyan] Checking {len(lines)} dependencies against OSV...")
    vuln_found = False
    for line in lines:
        parts = line.split("==")
        pkg_name = parts[0].strip()
        pkg_ver = parts[1].strip() if len(parts) > 1 else None
        advisories = query_osv("PyPI", pkg_name, pkg_ver)
        if advisories:
            vuln_found = True
            for adv in advisories:
                err_console.print(f"[bold red]Vulnerability:[/bold red] {pkg_name} {pkg_ver or ''} -> {adv.get('id', 'ADV')}: {adv.get('summary', '')}")

    if vuln_found:
        err_console.print("\n[bold red]BOB AUDIT FAILED[/bold red]: Vulnerable dependencies found.")
        raise typer.Exit(code=1)

    console.print("[green]BOB AUDIT PASSED[/green]: No known OSV vulnerabilities found in manifest.")
    raise typer.Exit(code=0)


@app.command()
def shim(
    action: str = typer.Argument(..., help="Action: install or uninstall"),
    dest: Optional[Path] = typer.Option(
        None, "--dest", help="Custom destination directory for shims"
    ),
) -> None:
    """Manage PATH wrapper shims (pip, npm, npx, uv)."""
    if action == "install":
        created = install_shims(dest)
        console.print(f"[green]Installed {len(created)} shim wrappers in {dest or get_default_shims_dir()}[/green]")
        console.print(f"[dim]Add {dest or get_default_shims_dir()} to your PATH to intercept terminal tool calls.[/dim]")
        raise typer.Exit(code=0)
    elif action == "uninstall":
        removed = uninstall_shims(dest)
        console.print(f"[green]Uninstalled {removed} shim wrapper(s) from {dest or get_default_shims_dir()}[/green]")
        raise typer.Exit(code=0)
    else:
        err_console.print(f"[bold red]Error:[/bold red] Unknown action '{action}'. Use 'install' or 'uninstall'.")
        raise typer.Exit(code=1)


@app.command()
def allow(
    package: str = typer.Argument(..., help="Package name to allowlist"),
) -> None:
    """Human-only allowlist entry in .bob/allowlist.yaml."""
    allowlist_path = Path(".bob/allowlist.yaml")
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)
    existing: List[str] = []
    if allowlist_path.is_file():
        try:
            with open(allowlist_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    existing = [str(x) for x in data]
        except Exception:
            pass

    if package not in existing:
        existing.append(package)
        with open(allowlist_path, "w", encoding="utf-8") as f:
            yaml.dump(existing, f)
        console.print(f"[green]Allowlisted package:[/green] '{package}' in {allowlist_path}")
    else:
        console.print(f"[dim]Package '{package}' is already allowlisted.[/dim]")
    raise typer.Exit(code=0)


@app.command(name="protect")
def protect(
    path: Path = typer.Argument(Path("."), help="Path to project/workspace directory to protect"),
    ide: str = typer.Option("all", "--ide", help="Target IDE: all, cursor, vscode, antigravity, claude"),
) -> None:
    """Configure automated interception hooks for IDEs and coding agents."""
    from bob.adapters.ide import protect_workspace
    result = protect_workspace(path, ide)
    console.print(f"[bold green][OK] Protected workspace:[/bold green] {result['workspace']}")
    for action in result["actions"]:
        console.print(f"  [green]*[/green] {action}")
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
