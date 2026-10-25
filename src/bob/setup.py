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

from bob.adapters.ide import protect_workspace
from bob.ai.cloud_client import validate_cloud_credentials
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
            "and hallucinated packages (slopsquatting). It inspects code and packages using\n"
            "deterministic rules, with optional AI triage for remediation advice.\n\n"
            "[bold cyan]Select an intelligence mode:[/bold cyan]\n"
            "  [bold cyan]1[/bold cyan] IDE-Native AI ([green]Recommended for IDE Skills[/green] - Zero Config, uses active IDE agent)\n"
            "  [bold cyan]2[/bold cyan] Local AI via Ollama (Private, Free, Gemma)\n"
            "  [bold cyan]3[/bold cyan] Cloud AI via API Key (Gemini, OpenAI, Groq, OpenRouter)\n"
            "  [bold cyan]4[/bold cyan] Pure Deterministic Mode (Zero setup - 100% built-in local AST/regex rules)",
            title="[bold cyan]BOB Setup[/bold cyan]",
            border_style="cyan",
        )
    )

    choice = Prompt.ask(
        "Choose an option",
        choices=["1", "2", "3", "4"],
        default="1",
        console=console,
    )

    cfg = load_config()

    if choice == "1":
        console.print("\n[bold cyan]Configuring IDE-Native AI Mode...[/bold cyan]")
        cfg.ai_provider = "ide_native"
        cfg.model = "ide_native"
        cfg_path = save_config(cfg)
        console.print(f"[bold green]Configuration saved to {cfg_path}[/bold green]")
        console.print("[green]BOB configured for IDE-native AI! Zero external API keys or background services needed.[/green]")
        console.print("[dim]Your host IDE agent (Claude Code, Google Antigravity, Cursor) will interpret BOB's structured findings directly in chat.[/dim]")

    elif choice == "2":
        console.print("\n[bold cyan]Configuring Local AI (Ollama + Gemma)...[/bold cyan]")
        if not is_ollama_installed():
            console.print("[yellow]Ollama was not detected on your system PATH.[/yellow]")
            console.print("To use local Gemma:")
            console.print("  1. Download and install Ollama from: [bold underline]https://ollama.com[/bold underline]")
            console.print("  2. Run [bold]bob setup[/bold] again after installation.")
            console.print("\n[green]Configuring BOB in IDE-native mode for now.[/green]")
            cfg.ai_provider = "ide_native"
            cfg.model = "ide_native"
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

    elif choice == "3":
        console.print(
            Panel(
                "[bold cyan]Select Cloud AI Platform:[/bold cyan]\n\n"
                "  [bold cyan]1[/bold cyan] Google Gemini ([green]Recommended[/green] - Fast, Free Tier available)\n"
                "  [bold cyan]2[/bold cyan] OpenAI (GPT-4o mini, GPT-4o)\n"
                "  [bold cyan]3[/bold cyan] Groq (High-speed Gemma 2 / Llama 3 API)\n"
                "  [bold cyan]4[/bold cyan] OpenRouter (Multi-provider API)\n"
                "  [bold cyan]5[/bold cyan] Custom OpenAI-compatible Endpoint (vLLM, LM Studio, etc.)",
                title="[bold cyan]Cloud AI Provider[/bold cyan]",
                border_style="cyan",
            )
        )
        cloud_choice = Prompt.ask(
            "Choose a platform",
            choices=["1", "2", "3", "4", "5", "gemini", "openai", "groq", "openrouter", "custom"],
            default="1",
            console=console,
        )

        provider_map = {
            "1": ("gemini", "Google Gemini", "gemini-1.5-flash"),
            "gemini": ("gemini", "Google Gemini", "gemini-1.5-flash"),
            "2": ("openai", "OpenAI", "gpt-4o-mini"),
            "openai": ("openai", "OpenAI", "gpt-4o-mini"),
            "3": ("groq", "Groq", "gemma2-9b-it"),
            "groq": ("groq", "Groq", "gemma2-9b-it"),
            "4": ("openrouter", "OpenRouter", "google/gemma-2-9b-it:free"),
            "openrouter": ("openrouter", "OpenRouter", "google/gemma-2-9b-it:free"),
            "5": ("custom", "Custom Endpoint", "default"),
            "custom": ("custom", "Custom Endpoint", "default"),
        }
        provider_code, provider_name, default_model = provider_map[str(cloud_choice).lower()]

        api_key = Prompt.ask(
            f"Enter your {provider_name} API key (input hidden)",
            password=True,
            console=console,
        )

        custom_base = None
        if provider_code == "custom":
            custom_base = Prompt.ask(
                "Enter API base URL",
                default="http://localhost:8000/v1",
                console=console,
            )

        model_name = Prompt.ask(
            f"Enter model identifier for {provider_name}",
            default=default_model,
            console=console,
        )

        with console.status(f"[bold cyan]Verifying API key with {provider_name}...[/bold cyan]"):
            is_valid, status_msg = validate_cloud_credentials(
                provider_code, api_key, model_name, base_url=custom_base
            )

        if is_valid:
            console.print(f"[bold green][OK] {status_msg}[/bold green]")
        else:
            console.print(f"[bold yellow][!] Live verification note: {status_msg}[/bold yellow]")
            console.print("[dim]Key saved. (Fallback templates will be active until credentials verify)[/dim]")

        cfg.ai_provider = provider_code
        cfg.api_key = api_key.strip()
        cfg.model = model_name
        cfg_path = save_config(cfg)
        console.print(f"\n[bold green]Configuration successfully saved to {cfg_path}[/bold green]")
        console.print(f"Provider: [bold cyan]{provider_name}[/bold cyan] | Model: [bold cyan]{model_name}[/bold cyan]")

    else:
        # Choice 4: Deterministic
        console.print("\n[bold cyan]Configuring Pure Deterministic Mode...[/bold cyan]")
        cfg.ai_provider = "deterministic"
        cfg.model = "deterministic"
        cfg_path = save_config(cfg)
        console.print(f"[bold green]Configuration saved to {cfg_path}[/bold green]")
        console.print("[green]BOB will run in zero-token deterministic mode using built-in AST & tripwire rules.[/green]")

    # Step 2: IDE & Coding Agent Protection
    console.print(
        Panel(
            "[bold white]Step 2: IDE & Coding Agent Protection[/bold white]\n\n"
            "BOB can automatically configure your IDE or coding agent so tool commands\n"
            "and package downloads are intercepted in real-time before execution.\n\n"
            "[bold cyan]Select your IDE / Agent environment to protect:[/bold cyan]\n"
            "  [bold cyan]1[/bold cyan] Cursor / VS Code / Windsurf ([green]Auto-configures terminal interceptor & shims[/green])\n"
            "  [bold cyan]2[/bold cyan] Google Antigravity IDE ([green]Registers native PreToolUse lifecycle hook[/green])\n"
            "  [bold cyan]3[/bold cyan] Claude Code / Terminal Agents ([green]Installs global PATH shims for pip, npm, uv[/green])\n"
            "  [bold cyan]4[/bold cyan] All of the Above ([green]Complete Protection - Recommended[/green])\n"
            "  [bold cyan]5[/bold cyan] Skip IDE setup (CLI commands only)",
            title="[bold cyan]IDE Integration[/bold cyan]",
            border_style="cyan",
        )
    )

    ide_choice = Prompt.ask(
        "Choose IDE protection option",
        choices=["1", "2", "3", "4", "5"],
        default="4",
        console=console,
    )

    target_path = Path.cwd().resolve()
    if ide_choice != "5":
        target_path_str = Prompt.ask(
            "Enter workspace/project directory to protect",
            default=".",
            console=console,
        )
        target_path = Path(target_path_str).resolve()
        user_home = Path.home().resolve()
        if target_path == user_home:
            console.print(
                f"[yellow]Notice: You selected your user home folder ('{target_path}').\n"
                f"For full project protection, you can also re-run 'bob protect' inside your project repository.[/yellow]"
            )

        mapping = {
            "1": "cursor",
            "2": "antigravity",
            "3": "claude",
            "4": "all",
        }
        chosen_ide = mapping.get(ide_choice, "all")
        result = protect_workspace(target_path, chosen_ide)
        console.print(f"\n[bold green][OK] Protected workspace: {result['workspace']}[/bold green]")
        for action in result["actions"]:
            console.print(f"  [green]*[/green] {action}")

    # Crystal clear next steps banner
    console.print(
        Panel(
            f"[bold green]BOB is Ready to Guard Your Agent![/bold green]\n\n"
            f"[bold white]Next Steps:[/bold white]\n"
            f"1. Open your project folder in terminal:\n"
            f"   [cyan]cd \"{target_path}\"[/cyan]\n\n"
            f"2. Verify system & AI status:\n"
            f"   [cyan]bob doctor[/cyan]\n\n"
            f"3. Run a security audit:\n"
            f"   [cyan]bob scan .[/cyan]\n\n"
            f"4. Test package interception gate:\n"
            f"   [cyan]bob check-install pypi demo-good-lib[/cyan]",
            title="[bold green]Ready[/bold green]",
            border_style="green",
        )
    )
