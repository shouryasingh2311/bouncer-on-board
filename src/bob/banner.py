"""ASCII Art banner and visual identity for BOB."""

from __future__ import annotations

import sys
from rich.console import Console

BOB_BANNER_ASCII = r"""
  ____   ____  ____  
 | __ ) / __ \| __ ) 
 |  _ \| |  | |  _ \ 
 | |_) | |__| | |_) |
 |____/ \____/|____/ 
"""

SUBTITLE = "Bouncer On Board - Zero-Trust IDE Agent Firewall"


def print_banner(console: Console, include_subtitle: bool = True) -> None:
    """Print ASCII art banner if output stream is an interactive terminal."""
    if not sys.stdout.isatty():
        return
    console.print(f"[bold cyan]{BOB_BANNER_ASCII.strip()}[/bold cyan]")
    if include_subtitle:
        console.print(f"[bold white]{SUBTITLE}[/bold white]\n")
