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
# Stylized 5-layer grayscale gradient banner with wireframe drop-lines
BOB_BANNER_STYLED = """\
  [#e4e4e7]█████████[#71717a]╗    [#e4e4e7]████████[#71717a]╗    [#e4e4e7]█████████[#71717a]╗
  [#a1a1aa]███[#71717a]╔══╗[#a1a1aa]███[#71717a]║   [#a1a1aa]███[#71717a]╔══╗[#a1a1aa]███[#71717a]║   [#a1a1aa]███[#71717a]╔══╗[#a1a1aa]███[#71717a]║
  [#71717a]██████████╣   ███║  ║███║   ██████████╣
  [#52525b]███[#71717a]╔══╗[#52525b]███[#71717a]║   [#52525b]███[#71717a]╚══╝[#52525b]███[#71717a]║   [#52525b]███[#71717a]╔══╗[#52525b]███[#71717a]║
  [#3f3f46]█████████[#71717a]╝    [#3f3f46]████████[#71717a]╝    [#3f3f46]█████████[#71717a]╝
  [#52525b]╚════════╝    ╚══════╝     ╚════════╝
   [bold cyan]-- bouncer-on-board --[/bold cyan]  [dim]"I'm Gate keeping"[/dim]"""


def print_banner(console: Console) -> None:
    """Print stylized block gradient banner if output stream is an interactive terminal."""
    if not sys.stdout.isatty():
        return
    try:
        if sys.platform == "win32":
            sys.stdout.reconfigure(encoding="utf-8")
        console.print(f"\n{BOB_BANNER_STYLED}\n")
    except Exception:
        console.print(f"[bold cyan]{BOB_BANNER_ASCII.strip(chr(10) + chr(13))}[/bold cyan]\n")
