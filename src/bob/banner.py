"""ASCII Art banner and visual identity for BOB."""

from __future__ import annotations

import sys
from rich.console import Console

BOB_BANNER_ASCII = r"""
+----------------------------------------------------------------+
|                      ____   ___  ____                          |
|                     | __ ) / _ \| __ )                         |
|                     |  _ \| | | |  _ \                         |
|                     | |_) | |_| | |_) |                        |
|                     |____/ \___/|____/                         |
|                                                                |
|                    -- bouncer-on-board --                      |
|                      "I'm Gate keeping"                        |
+----------------------------------------------------------------+
"""

SUBTITLE = "bouncer-on-board"
TAGLINE = "I'm Gate keeping"


def print_banner(console: Console, include_subtitle: bool = True) -> None:
    """Print ASCII art banner if output stream is an interactive terminal."""
    if not sys.stdout.isatty():
        return
    console.print(f"[bold cyan]{BOB_BANNER_ASCII.strip(chr(10) + chr(13))}[/bold cyan]\n")
