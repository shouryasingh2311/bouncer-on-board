"""IDE and agent workspace protection configuration for Antigravity, Cursor, VS Code, and Claude Code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bob.adapters.antigravity import configure_antigravity_hook
from bob.adapters.shim import get_default_shims_dir, install_shims


def configure_antigravity(target_dir: Path) -> Path:
    """Register Antigravity IDE PreToolUse hook (.agents/hooks.json)."""
    return configure_antigravity_hook(target_dir)


def configure_vscode_cursor(
    target_dir: Path, shims_dir: Optional[Path] = None
) -> Tuple[Path, List[Path]]:
    """Configure Cursor, VS Code, and Windsurf terminal interception via settings.json.
    
    Installs L2 PATH shims and configures .vscode/settings.json terminal environment
    overrides so agent shells automatically route tool commands through BOB.
    """
    s_dir = shims_dir or get_default_shims_dir()
    created_shims = install_shims(s_dir)

    vscode_dir = target_dir / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)
    settings_file = vscode_dir / "settings.json"

    data: Dict[str, Any] = {}
    if settings_file.is_file():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
        except Exception:
            data = {}

    shims_posix = str(s_dir.as_posix())
    shims_str = str(s_dir)

    # Windows terminal environment
    win_env = data.setdefault("terminal.integrated.env.windows", {})
    win_env["PATH"] = f"{shims_str};${{env:PATH}}"

    # Linux terminal environment
    linux_env = data.setdefault("terminal.integrated.env.linux", {})
    linux_env["PATH"] = f"{shims_posix}:${{env:PATH}}"

    # macOS terminal environment
    osx_env = data.setdefault("terminal.integrated.env.osx", {})
    osx_env["PATH"] = f"{shims_posix}:${{env:PATH}}"

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return settings_file, created_shims


def configure_claude_code(shims_dir: Optional[Path] = None) -> List[Path]:
    """Install global PATH shims (~/.bob/shims) for Claude Code and terminal agents."""
    s_dir = shims_dir or get_default_shims_dir()
    return install_shims(s_dir)


def protect_workspace(
    target_dir: Path, target_ide: str = "all"
) -> Dict[str, Any]:
    """Apply zero-trust agent firewall protection to target workspace.
    
    target_ide: "all" | "cursor" | "vscode" | "antigravity" | "claude"
    """
    resolved_dir = target_dir.resolve()
    resolved_dir.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Any] = {
        "workspace": str(resolved_dir),
        "actions": [],
    }

    ide_choice = target_ide.lower().strip()

    # 1. Antigravity IDE hook
    if ide_choice in ("all", "antigravity"):
        hook_path = configure_antigravity(resolved_dir)
        results["actions"].append(f"Antigravity PreToolUse hook registered at {hook_path}")

    # 2. Cursor / VS Code / Windsurf
    if ide_choice in ("all", "cursor", "vscode", "windsurf"):
        settings_path, shims = configure_vscode_cursor(resolved_dir)
        results["actions"].append(
            f"Cursor/VSCode terminal protection configured in {settings_path} ({len(shims)} shims in {get_default_shims_dir()})"
        )

    # 3. Claude Code / Terminal agents
    if ide_choice in ("all", "claude"):
        shims = configure_claude_code()
        results["actions"].append(
            f"Global PATH wrapper shims installed in {get_default_shims_dir()}"
        )

    # 4. Initialize workspace .bob directory
    bob_dir = resolved_dir / ".bob"
    bob_dir.mkdir(parents=True, exist_ok=True)
    allowlist_file = bob_dir / "allowlist.yaml"
    if not allowlist_file.exists():
        allowlist_file.write_text("# Human-managed package allowlist\n[]\n", encoding="utf-8")
        results["actions"].append(f"Initialized allowlist at {allowlist_file}")

    return results
