"""ASCII Art banner and visual identity for BOB."""

from __future__ import annotations

import sys
from rich.console import Console

BOB_BANNER_ASCII = r"""
 [====][====]-.       [====][====][====]       [====][====]-. 
 |[||]   [||]||       |[||]        [||]|       |[||]   [||]|| 
 [====][====]-+       |[||]        [||]|       [====][====]-+ 
 |[||]   [||]||       |[||]        [||]|       |[||]   [||]|| 
 [====][====]-'       [====][====][====]       [====][====]-' 
  |________|              |________|            |________|    
"""

SUBTITLE = "bouncer-on-board"
TAGLINE = "I'm Gate keeping"


def print_banner(console: Console, include_subtitle: bool = True) -> None:
    """Print ASCII art banner if output stream is an interactive terminal."""
    if not sys.stdout.isatty():
        return
    console.print(f"[bold cyan]{BOB_BANNER_ASCII.strip(chr(10) + chr(13))}[/bold cyan]")
    if include_subtitle:
        console.print(f"               [bold white]-- {SUBTITLE} --[/bold white]")
        console.print(f"                 [dim cyan]\"{TAGLINE}\"[/dim cyan]\n")
