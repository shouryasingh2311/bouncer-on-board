"""Interactive AI setup wizard and Ollama process manager for BOB."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import List, Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from bob.banner import print_banner
from bob.config import Config, load_config, save_config


def is_ollama_installed() -> bool:
    """Check if 'ollama' executable is available in system PATH."""
    return shutil.which("ollama") is not None


def is_ollama_running(url: str = "http://localhost:11434") -> bool:
    """Check if Ollama HTTP service is responding on the target URL."""
    try:
        with httpx.Client(timeout=1.5) as client:
            resp = client.get(f"{url.rstrip('/')}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


def start_ollama_service(url: str = "http://localhost:11434", max_wait: float = 4.0) -> bool:
    """Start 'ollama serve' in the background and wait until it responds."""
    if is_ollama_running(url):
        return True

    if not is_ollama_installed():
        return False

    creationflags = 0
    if sys.platform == "win32":
        # Create detached background process on Windows
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
            subprocess, "DETACHED_PROCESS", 0
        )
        subprocess.Popen(
            ["ollama", "serve"],
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        # Start in separate process session on POSIX
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    # Poll until ready or timeout
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < max_wait:
        time.sleep(0.5)
        if is_ollama_running(url):
            return True

    return False


def get_ollama_models(url: str = "http://localhost:11434") -> List[str]:
    """Retrieve list of model names currently installed in local Ollama."""
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{url.rstrip('/')}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        pass
    return []


def pull_ollama_model(model_name: str) -> bool:
    """Interactively pull a model via 'ollama pull <model_name>'."""
    if not is_ollama_installed():
        return False
    try:
        res = subprocess.run(["ollama", "pull", model_name])
        return res.returncode == 0
    except Exception:
        return False


def run_setup_wizard(console: Console) -> None:
    """Run interactive onboarding assistant for local Gemma/Ollama or API keys."""
    print_banner(console)

    console.print(
        Panel(
            "[bold white]Welcome to the BOB Security & Intelligence Setup Assistant![/bold white]\n\n"
            "BOB protects your IDE agents against prompt injections, credential exfiltration,\n"
            "and hallucinated packages. It uses AI to triage security findings with remediation\n"
            "advice, with seamless fallback to built-in rules.\n\n"
            "[bold cyan]Select an intelligence mode:[/bold cyan]\n"
            "  [bold cyan]1[/bold cyan] Local AI via Ollama ([green]Recommended[/green] • Private, Free, Gemma)\n"
            "  [bold cyan]2[/bold cyan] Cloud AI via API Key (Gemini, Gemma endpoint, or OpenAI)\n"
            "  [bold cyan]3[/bold cyan] Pure Deterministic Mode (Zero setup • 100% built-in local rules)",
            title="[bold cyan]BOB Setup[/bold cyan]",
            border_style="cyan",
        )
    )

    choice = Prompt.ask(
        "Choose an option",
        choices=["1", "2", "3"],
        default="1",
        console=console,
    )

    cfg = load_config()

    if choice == "1":
        console.print("\n[bold cyan]Configuring Local AI (Ollama + Gemma)...[/bold cyan]")
        if not is_ollama_installed():
            console.print("[yellow]Ollama was not detected on your system PATH.[/yellow]")
            console.print("To use local Gemma:")
            console.print("  1. Download and install Ollama from: [bold underline]https://ollama.com[/bold underline]")
            console.print("  2. Run [bold]bob setup[/bold] again after installation.")
            console.print("\n[green]Configuring BOB in deterministic mode for now (built-in rules active).[/green]")
            cfg.ai_provider = "deterministic"
            save_config(cfg)
            return

        console.print("[green]Ollama executable found![/green]")

        # Check if Ollama service is running
        if not is_ollama_running(cfg.ollama_url):
            console.print("[yellow]Ollama service is currently stopped.[/yellow]")
            start_now = Confirm.ask(
                "Would you like BOB to automatically launch 'ollama serve' in the background?",
                default=True,
                console=console,
            )
            if start_now:
                with console.status("[bold cyan]Starting Ollama service...[/bold cyan]"):
                    started = start_ollama_service(cfg.ollama_url)
                if started:
                    console.print("[green]Ollama service successfully launched in background![/green]")
                else:
                    console.print("[yellow]Could not auto-start Ollama service. Please run 'ollama serve' manually.[/yellow]")
            else:
                console.print("[dim]You can start it later by running 'ollama serve'.[/dim]")

        # Inspect local models
        if is_ollama_running(cfg.ollama_url):
            models = get_ollama_models(cfg.ollama_url)
            if models:
                console.print(f"[green]Found {len(models)} local model(s):[/green] {', '.join(models)}")
                chosen_model = Prompt.ask(
                    "Which model would you like BOB to use for security triage?",
                    default=models[0],
                    console=console,
                )
                cfg.model = chosen_model
            else:
                console.print("[yellow]No AI models are currently pulled in your local Ollama library.[/yellow]")
                pull_now = Confirm.ask(
                    "Would you like to pull Gemma now? (e.g. 'gemma2:2b', ~1.6GB, fast & lightweight)",
                    default=True,
                    console=console,
                )
                if pull_now:
                    console.print("[bold cyan]Downloading Gemma via 'ollama pull gemma2:2b'...[/bold cyan]")
                    ok = pull_ollama_model("gemma2:2b")
                    if ok:
                        cfg.model = "gemma2:2b"
                        console.print("[green]Successfully downloaded and verified gemma2:2b![/green]")
                    else:
                        cfg.model = "gemma2:2b"
                        console.print("[yellow]Download incomplete. You can pull it later via: ollama pull gemma2:2b[/yellow]")
                else:
                    cfg.model = "gemma2:2b"
                    console.print("[dim]Configured default 'gemma2:2b'. Pull it whenever you are ready: ollama pull gemma2:2b[/dim]")

        cfg.ai_provider = "ollama"
        cfg_path = save_config(cfg)
        console.print(f"\n[bold green]Configuration successfully saved to {cfg_path}[/bold green]")
        console.print(f"Model: [bold cyan]{cfg.model}[/bold cyan] via [bold]{cfg.ollama_url}[/bold]")

    elif choice == "2":
        console.print("\n[bold cyan]Configuring Cloud AI Provider...[/bold cyan]")
        provider = Prompt.ask(
            "Select provider",
            choices=["gemini", "openai", "custom"],
            default="gemini",
            console=console,
        )
        api_key = Prompt.ask(
            "Enter your API key (input hidden)",
            password=True,
            console=console,
        )
        model_name = Prompt.ask(
            "Enter model identifier",
            default="gemini-1.5-flash" if provider == "gemini" else "gpt-4o-mini",
            console=console,
        )
        cfg.ai_provider = provider
        cfg.api_key = api_key
        cfg.model = model_name
        cfg_path = save_config(cfg)
        console.print(f"\n[bold green]Configuration successfully saved to {cfg_path}[/bold green]")
        console.print(f"Provider: [bold cyan]{provider}[/bold cyan] | Model: [bold cyan]{model_name}[/bold cyan]")

    else:
        # Choice 3: Deterministic
        console.print("\n[bold cyan]Configuring Pure Deterministic Mode...[/bold cyan]")
        cfg.ai_provider = "deterministic"
        cfg.model = "deterministic"
        cfg_path = save_config(cfg)
        console.print(f"[bold green]Configuration saved to {cfg_path}[/bold green]")
        console.print("[green]BOB will run in zero-token deterministic mode using built-in AST & tripwire rules.[/green]")

    console.print("\n[dim]Run [bold]bob doctor[/bold] to check system status, or [bold]bob scan .[/bold] to run a pre-deploy audit.[/dim]\n")
