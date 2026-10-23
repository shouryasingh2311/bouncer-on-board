"""ASCII Art banner and visual identity for BOB."""

from __future__ import annotations

import sys
from rich.console import Console

BOB_BANNER_ASCII = r"""
  ____   ____  ____         .-.   .-.                 _...._       
 | __ ) / __ \| __ )       /  /  /  /               /`  __  `\     
 |  _ \| |  | |  _ \     .-'--'--'--.              |  (||||)  |    
 | |_) | |__| | |_) |   /   _.-  -._ \              \  '--'  /     
 |____/ \____/|____/   |   ( -o) (-o )|              \ '---' |     
                       |      (__)    |     _..._     |      |     
  BOUNCER ON BOARD     /   .----------. \  /` .-. `\   |      |     
 ===================   |   /  .::..::.  \ ||  (   )  |  |      |     
 Zero-Trust IDE        |  (    .----.    )| \  '-'  /   |      |     
 Agent Firewall        |   \   `----'   / |  '-----'   /      /      
                        \   '--.____.--' /            /      /       
 (*) Package Gate      /`\==============/`\          /      /        
 (*) Terminal Guard    /  \_/\_/\_/\_/\_   \        /      /         
 (*) Gemma/Ollama AI   /   /              \   \      /      /          
 (*) Multi-IDE Lock    |  /   .-.    .-.   \   \    /      /           
                       | |   /   \  /   \   |   '--'      /            
 (v0.1.0 - Active)     | |  |     ||     |  |        '---'             
 -------------------   '--'  '---'  '---'   '------'                   
"""

SUBTITLE = "Bouncer On Board - Zero-Trust IDE Agent Firewall"


def print_banner(console: Console, include_subtitle: bool = True) -> None:
    """Print ASCII art banner if output stream is an interactive terminal."""
    if not sys.stdout.isatty():
        return
    console.print(f"[bold cyan]{BOB_BANNER_ASCII.strip(chr(10) + chr(13))}[/bold cyan]")
    if include_subtitle:
        console.print(f"[bold white]{SUBTITLE}[/bold white]\n")
