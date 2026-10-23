"""Sensitive-path guard and BOB self-protection."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shlex
from typing import List, Optional, Tuple

from bob.config import Config
from bob.models import Finding


# Default sensitive patterns matching PROJECT.md Section 7.4
DEFAULT_SENSITIVE_PATTERNS = [
    r"(^|[/\\])\.env(\.[a-zA-Z0-9_\-]+)?$",  # .env, .env.local, .env.prod
    r"(^|[/\\])\.ssh([/\\]|$)",  # .ssh directory or contents
    r"(^|[/\\])(id_rsa|id_ed25519|id_ecdsa|id_dsa)($|\.)",  # ssh keys
    r"(^|[/\\])\.aws[/\\](credentials|config)$",
    r"(^|[/\\])\.npmrc$",
    r"(^|[/\\])\.pypirc$",
    r"(^|[/\\])\.git-credentials$",
    r"\.(pem|key)$",
    r"(^|[/\\])\.kube[/\\]config$",
    r"(^|[/\\])\.docker[/\\]config\.json$",
    r"(^|[/\\])service-account.*\.json$",
]


def normalise_path(p: str) -> str:
    """Normalise path for consistent cross-platform matching."""
    expanded = os.path.expanduser(os.path.expandvars(p.strip()))
    # Replace backslashes with forward slashes for unified regex matching
    return expanded.replace("\\", "/").lower()


def check_self_protection(cmd_string: str) -> Optional[Finding]:
    """Prevent agent actions from modifying .bob/ or executing 'bob allow'."""
    cmd_clean = cmd_string.strip()

    # 1. Prohibit agent calling 'bob allow' (allowlisting is human-only per Axiom 6)
    if re.search(r"(^|\s|&|;|\|)bob\s+allow(\s|$)", cmd_clean, re.IGNORECASE):
        return Finding(
            id="BOB-0000",
            rule_id="GUARD-BOB-SELF-PROTECT",
            source="bob-guard",
            category="config",
            severity="critical",
            title="Agent prohibited from modifying BOB allowlist",
            file=".bob/allowlist.yaml",
            line=None,
            evidence="bob allow (allowlisting is a human-only action)",
        )

    # 2. Prohibit writes/mutations targeting .bob/
    write_patterns = [
        r">\s*(\./)?\.bob([/\\]|$)",  # redirect > .bob/...
        r">>\s*(\./)?\.bob([/\\]|$)",  # redirect >> .bob/...
        r"(rm|del|remove|rmdir|mv|ren|move|cp|copy)\s+.*(\./)?\.bob([/\\]|$)",  # destructive / copy into .bob
        r"(\./)?\.bob[/\\](config|allowlist)\.yaml",  # direct target of file writes
    ]
    for pat in write_patterns:
        if re.search(pat, cmd_clean, re.IGNORECASE):
            return Finding(
                id="BOB-0000",
                rule_id="GUARD-BOB-SELF-PROTECT",
                source="bob-guard",
                category="config",
                severity="critical",
                title="Agent prohibited from modifying BOB configuration directory",
                file=".bob",
                line=None,
                evidence="write or modification targeting .bob/",
            )

    return None


def is_sensitive_path(path_str: str, config: Optional[Config] = None) -> Optional[str]:
    """Check if a specific path targets sensitive credentials."""
    norm = normalise_path(path_str)

    patterns = list(DEFAULT_SENSITIVE_PATTERNS)
    if config and config.sensitive_paths_extra:
        for extra in config.sensitive_paths_extra:
            norm_extra = normalise_path(extra).replace("/", r"[/\\]")
            patterns.append(rf"(^|[/\\]){re.escape(norm_extra)}($|[/\\])")

    for pat in patterns:
        if re.search(pat, norm, re.IGNORECASE):
            return path_str

    return None


def check_command_sensitive_paths(
    cmd_string: str, config: Optional[Config] = None
) -> Optional[Finding]:
    """Scan tokens and paths in a shell command for sensitive file targets."""
    # Split tokens to examine individual arguments
    try:
        tokens = shlex.split(cmd_string, posix=False)
    except Exception:
        tokens = cmd_string.split()

    for token in tokens:
        clean = token.strip("\"'<>|;&")
        if not clean or clean.startswith("-"):
            continue

        matched = is_sensitive_path(clean, config)
        if matched:
            return Finding(
                id="BOB-0000",
                rule_id="GUARD-SENSITIVE-PATH",
                source="bob-guard",
                category="secret",
                severity="critical",
                title="Access to sensitive credential path blocked",
                file=matched,
                line=None,
                evidence=f"Command touches sensitive target: {matched}",
            )

    # Substring check for paths containing spaces or inline redirections
    norm_cmd = normalise_path(cmd_string)
    inline_targets = [
        r"(^|\s|[<>&|])\.env(\.[a-zA-Z0-9_\-]+)?(\s|$|[<>&|])",
        r"(^|\s|[<>&|])~?/\.ssh(/[^\s]+)?(\s|$|[<>&|])",
        r"(^|\s|[<>&|])id_rsa(\s|$|[<>&|])",
        r"(^|\s|[<>&|])id_ed25519(\s|$|[<>&|])",
        r"(^|\s|[<>&|])\.aws/credentials(\s|$|[<>&|])",
        r"(^|\s|[<>&|])\.npmrc(\s|$|[<>&|])",
    ]
    for pat in inline_targets:
        m = re.search(pat, norm_cmd, re.IGNORECASE)
        if m:
            matched_str = m.group(0).strip("<>&| \t")
            return Finding(
                id="BOB-0000",
                rule_id="GUARD-SENSITIVE-PATH",
                source="bob-guard",
                category="secret",
                severity="critical",
                title="Access to sensitive credential path blocked",
                file=matched_str,
                line=None,
                evidence=f"Command touches sensitive target: {matched_str}",
            )

    return None
