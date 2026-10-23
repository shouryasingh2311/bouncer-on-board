"""Antigravity IDE lifecycle hook adapter (.agents/hooks.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


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


def configure_antigravity_hook(repo_root: Path) -> Path:
    """Ensure .agents/hooks.json exists and registers BOB pre-execution hook."""
    agents_dir = repo_root / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    hooks_file = agents_dir / "hooks.json"

    data = get_hooks_config()
    with open(hooks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return hooks_file
