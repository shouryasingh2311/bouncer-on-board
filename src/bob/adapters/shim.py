"""L2 PATH shims management for pip, npm, uv, and npx."""

from __future__ import annotations

import os
from pathlib import Path
import stat
from typing import List, Optional

SHIM_COMMANDS = [
    "pip",
    "pip3",
    "npm",
    "npx",
    "uv",
    "pnpm",
    "yarn",
    "bun",
    "bunx",
    "poetry",
]


def get_default_shims_dir() -> Path:
    """Return default directory for BOB PATH shims (~/.bob/shims)."""
    return Path.home() / ".bob" / "shims"


def install_shims(target_dir: Optional[Path] = None) -> List[Path]:
    """Install interception wrapper scripts for pip, npm, npx, uv.
    
    Creates Windows .cmd and POSIX shell scripts that call 'bob intercept'
    before delegating to the underlying system binary.
    """
    dest = target_dir or get_default_shims_dir()
    dest.mkdir(parents=True, exist_ok=True)
    created: List[Path] = []

    for cmd_name in SHIM_COMMANDS:
        # 1. Windows .cmd wrapper
        cmd_script = dest / f"{cmd_name}.cmd"
        cmd_content = f"""@echo off
bob intercept --adapter generic --cmd "{cmd_name} %*"
if %ERRORLEVEL% NEQ 0 (
    exit /b %ERRORLEVEL%
)

REM Find real executable excluding this shims folder
for /f "tokens=*" %%i in ('where.exe {cmd_name} 2^>nul') do (
    if /i not "%%~dpi"=="%~dp0" (
        "%%i" %*
        exit /b %ERRORLEVEL%
    )
)

echo bob: underlying command '{cmd_name}' not found on system PATH. >&2
exit /b 1
"""
        cmd_script.write_text(cmd_content, encoding="utf-8")
        created.append(cmd_script)

        # 2. POSIX shell wrapper (for Linux, macOS, WSL, git-bash)
        sh_script = dest / cmd_name
        sh_content = f"""#!/usr/bin/env bash
bob intercept --adapter generic --cmd "{cmd_name} $*"
RET=$?
if [ $RET -ne 0 ]; then
    exit $RET
fi

# Find next executable in PATH excluding this directory
DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
REAL_BIN=""
IFS=':' read -ra PATHS <<< "$PATH"
for p in "${{PATHS[@]}}"; do
    if [ "$p" != "$DIR" ] && [ -x "$p/{cmd_name}" ]; then
        REAL_BIN="$p/{cmd_name}"
        break
    fi
done

if [ -n "$REAL_BIN" ]; then
    exec "$REAL_BIN" "$@"
else
    echo "bob: underlying command '{cmd_name}' not found on PATH" >&2
    exit 1
fi
"""
        sh_script.write_text(sh_content, encoding="utf-8")
        try:
            # Mark executable on POSIX systems
            sh_script.chmod(sh_script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass
        created.append(sh_script)

    return created


def uninstall_shims(target_dir: Optional[Path] = None) -> int:
    """Remove installed shim wrappers. Returns count of removed files."""
    dest = target_dir or get_default_shims_dir()
    if not dest.is_dir():
        return 0

    removed = 0
    for cmd_name in SHIM_COMMANDS:
        for fname in (cmd_name, f"{cmd_name}.cmd", f"{cmd_name}.ps1"):
            p = dest / fname
            if p.is_file():
                try:
                    p.unlink()
                    removed += 1
                except Exception:
                    pass

    return removed
