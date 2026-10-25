"""IDE and agent workspace protection configuration for Antigravity, Cursor, VS Code, and Claude Code."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bob.adapters.shim import get_default_shims_dir, install_shims


def get_hooks_config() -> Dict[str, Any]:
    """Return standard PreToolUse hook configuration for Antigravity IDE."""
    return {
        "PreToolUse": [
            {
                "command": "bob",
                "args": ["intercept", "--adapter", "antigravity"],
            }
        ]
    }


def configure_antigravity(target_dir: Path) -> Path:
    """Register Antigravity IDE PreToolUse hook (.agents/hooks.json)."""
    agents_dir = target_dir / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = agents_dir / "hooks.json"

    data = get_hooks_config()
    with open(hooks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return hooks_file


configure_antigravity_hook = configure_antigravity


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


def get_skill_content() -> str:
    """Load universal SKILL.md content from disk or fallback template."""
    skill_file = Path(__file__).resolve().parent.parent.parent.parent / "skills" / "bob" / "SKILL.md"
    if skill_file.is_file():
        try:
            return skill_file.read_text(encoding="utf-8")
        except Exception:
            pass

    return """---
name: bob
description: "Zero-trust IDE firewall and security gatekeeper. Inspects packages before download to block slopsquatting and malicious install scripts, scans code for secrets with native IDE AI triage, guards against prompt injection, and manages automatic terminal shims."
argument-hint: "bob scan [path] | bob check <pypi|npm> <package> | bob guard <file> | bob doctor | bob protect"
user-invocable: true
---

# BOB: Zero-Trust IDE Agent Firewall
Use `/bob scan`, `/bob check <pypi|npm> <pkg>`, `/bob guard <file>`, `/bob doctor`, or `/bob protect`.
"""


def install_skill_files(target_dir: Path, target_ide: str = "all") -> List[Path]:
    """Deploy universal bob skill to target IDE skill/rules directories."""
    installed: List[Path] = []
    content = get_skill_content()
    ide_choice = target_ide.lower().strip()

    # 1. Antigravity Skill (~/.gemini/config/skills/bob/SKILL.md)
    if ide_choice in ("all", "antigravity"):
        try:
            ag_skill_dir = Path.home() / ".gemini" / "config" / "skills" / "bob"
            ag_skill_dir.mkdir(parents=True, exist_ok=True)
            ag_file = ag_skill_dir / "SKILL.md"
            ag_file.write_text(content, encoding="utf-8")
            installed.append(ag_file)
        except Exception:
            pass

    # 2. Claude Code Skill (~/.claude/skills/bob/SKILL.md)
    if ide_choice in ("all", "claude"):
        try:
            claude_skill_dir = Path.home() / ".claude" / "skills" / "bob"
            claude_skill_dir.mkdir(parents=True, exist_ok=True)
            claude_file = claude_skill_dir / "SKILL.md"
            claude_file.write_text(content, encoding="utf-8")
            installed.append(claude_file)
        except Exception:
            pass

    # 3. Cursor Rules (.cursor/rules/bob.mdc)
    if ide_choice in ("all", "cursor"):
        try:
            cursor_dir = target_dir / ".cursor" / "rules"
            cursor_dir.mkdir(parents=True, exist_ok=True)
            cursor_file = cursor_dir / "bob.mdc"
            cursor_file.write_text(content, encoding="utf-8")
            installed.append(cursor_file)
        except Exception:
            pass

    return installed


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

    # 4. Deploy universal IDE skills
    skills_installed = install_skill_files(resolved_dir, ide_choice)
    for s in skills_installed:
        results["actions"].append(f"Universal BOB skill installed at {s}")

    # 5. Initialize workspace .bob directory
    bob_dir = resolved_dir / ".bob"
    bob_dir.mkdir(parents=True, exist_ok=True)
    allowlist_file = bob_dir / "allowlist.yaml"
    if not allowlist_file.exists():
        allowlist_file.write_text("# Human-managed package allowlist\n[]\n", encoding="utf-8")
        results["actions"].append(f"Initialized allowlist at {allowlist_file}")

    return results
