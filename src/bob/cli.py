"""BOB CLI application using Typer."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import time
from typing import Optional
import httpx
from rich.console import Console
from rich.table import Table
import typer

from bob import __version__
from bob.config import load_config
from bob.models import Decision, Finding

app = typer.Typer(
    name="bob",
    help="Zero-Trust IDE Agent Firewall & Pre-Deploy Security Gatekeeper",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"bob version {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main(
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
    pass


@app.command()
def doctor() -> None:
    """Report available scanners, Ollama connection, configured model, and system environment."""
    cfg = load_config()

    table = Table(title="[bold cyan]BOB System Diagnostics (Doctor)[/bold cyan]")
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    # Python & Platform
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python", "[green]OK[/green]", f"v{py_ver} ({sys.platform})")

    # Local Ollama & Model Probe
    ollama_ok = False
    model_found = False
    latency_ms = 0.0

    try:
        t0 = time.perf_counter()
        # Probe Ollama /api/tags with a short timeout (1.5s)
        resp = httpx.get(f"{cfg.ollama_url.rstrip('/')}/api/tags", timeout=1.5)
        latency_ms = (time.perf_counter() - t0) * 1000

        if resp.status_code == 200:
            ollama_ok = True
            tags_data = resp.json()
            models_list = [
                m.get("name", "") for m in tags_data.get("models", [])
            ]
            # Match configured model (e.g. gemma4:e2b or gemma4:e2b:latest)
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

    console.print(table)
    console.print(
        "\n[dim]Note: External tools and Ollama are optional. BOB operates fully in deterministic mode without them.[/dim]"
    )
    raise typer.Exit(code=0)


from bob.cmdparse import parse_pkg_and_version
from bob.pkg.gate import evaluate_package


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
    err_console.print(
        f"[yellow]intercept is under development in M1/M2 (adapter: {adapter})[/yellow]"
    )
    raise typer.Exit(code=0)


@app.command("guard-text")
def guard_text(
    path: Path = typer.Argument(..., help="Path to file/text to scan for prompt injection"),
    ai: bool = typer.Option(
        False, "--ai", help="Request optional AI semantic second opinion"
    ),
) -> None:
    """Scan file content with injection tripwire pack."""
    err_console.print(
        f"[yellow]guard-text is under development in M5: {path}[/yellow]"
    )
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
    err_console.print(
        f"[yellow]scan is under development in M3/M4: {path}[/yellow]"
    )
    raise typer.Exit(code=0)


@app.command()
def verify(
    finding_id: str = typer.Argument(
        ..., help="Finding ID or fingerprint prefix to verify"
    ),
) -> None:
    """Re-run originating check after a fix to prove patch resolved finding."""
    err_console.print(
        f"[yellow]verify is under development in M4: {finding_id}[/yellow]"
    )
    raise typer.Exit(code=0)


@app.command()
def audit() -> None:
    """Check lockfiles and installed dependencies against OSV advisories."""
    err_console.print("[yellow]audit is under development in M1/M3[/yellow]")
    raise typer.Exit(code=0)


@app.command()
def shim(
    action: str = typer.Argument(..., help="Action: install or uninstall"),
) -> None:
    """Manage PATH wrapper shims (pip, npm, uv)."""
    err_console.print(f"[yellow]shim {action} is under development in M5[/yellow]")
    raise typer.Exit(code=0)


@app.command()
def allow(
    package: str = typer.Argument(..., help="Package name to allowlist"),
) -> None:
    """Human-only allowlist entry in .bob/allowlist.yaml."""
    err_console.print(
        f"[yellow]allow is under development in M2: {package}[/yellow]"
    )
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
