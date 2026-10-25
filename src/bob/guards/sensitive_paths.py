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


def check_environment_dump(cmd_string: str) -> Optional[Finding]:
    """Prevent agents from executing bulk environment / secret dumps."""
    norm = cmd_string.strip()

    # 1. printenv (standalone, with args, or in pipeline / subshell)
    if re.search(
        r"(?:^|[;&|`]\s*|\b(?:bash|sh|zsh|dash|cmd|powershell|pwsh)\s+-[cC]\s+['\"])printenv\b",
        norm,
        re.IGNORECASE,
    ):
        return Finding(
            id="BOB-0000",
            rule_id="GUARD-ENV-DUMP",
            source="bob-guard",
            category="secret",
            severity="critical",
            title="Bulk environment secret dumping prohibited",
            file="ENV",
            line=None,
            evidence="Command executes printenv to dump environment secrets",
        )

    # 2. export -p (standalone or in pipeline)
    if re.search(r"(?:^|[;&|`]\s*)export\s+-p\b", norm, re.IGNORECASE):
        return Finding(
            id="BOB-0000",
            rule_id="GUARD-ENV-DUMP",
            source="bob-guard",
            category="secret",
            severity="critical",
            title="Bulk environment secret dumping prohibited",
            file="ENV",
            line=None,
            evidence="Command executes 'export -p' to dump exported environment variables",
        )

    # 3. env without a sub-command (e.g. standalone 'env', 'env | ...', 'env > ...')
    chunks = re.findall(r"(?:[^&;|]+|\"[^\"]*\"|'[^']*')+", norm)
    for c in chunks:
        c_str = c.strip()
        if not c_str:
            continue
        try:
            tokens = shlex.split(c_str, posix=False)
        except Exception:
            tokens = c_str.split()
        if not tokens:
            continue

        clean = []
        for t in tokens:
            if t in (">", ">>", "<"):
                break
            clean.append(t.strip("\"'"))
        if not clean:
            continue

        exe = clean[0].lower().replace(".exe", "").replace("\\", "/").split("/")[-1]
        if exe == "env":
            idx = 1
            while idx < len(clean):
                tok = clean[idx]
                if tok.startswith("-"):
                    if tok in ("-u", "-C", "-S") and idx + 1 < len(clean):
                        idx += 2
                    else:
                        idx += 1
                elif "=" in tok and not tok.startswith("="):
                    idx += 1
                else:
                    break
            if idx >= len(clean):
                return Finding(
                    id="BOB-0000",
                    rule_id="GUARD-ENV-DUMP",
                    source="bob-guard",
                    category="secret",
                    severity="critical",
                    title="Bulk environment secret dumping prohibited",
                    file="ENV",
                    line=None,
                    evidence="Command executes standalone/piped env without target executable",
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
    """Scan tokens and paths in a shell command for sensitive file targets and secret dumps."""
    # 0. Check bulk environment dumps
    dump_hit = check_environment_dump(cmd_string)
    if dump_hit:
        return dump_hit

    # Split tokens to examine individual arguments
    try:
        tokens = shlex.split(cmd_string, posix=False)
    except Exception:
        tokens = cmd_string.split()

    for token in tokens:
        clean = token.strip("\"'<>|;&()")
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

    # Substring check for paths containing spaces, inline redirections, or inline script invocations
    norm_cmd = normalise_path(cmd_string)
    inline_targets = [
        r"(?<![a-zA-Z0-9_\-])\.env(\.[a-zA-Z0-9_\-]+)?(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])(~?/\.ssh|\.ssh)(?:[/\\][^\s'\"`\)]*)?(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])(id_rsa|id_ed25519|id_ecdsa|id_dsa)(\.[a-zA-Z0-9_\-]+)?(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])\.aws[/\\](credentials|config)(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])(\.npmrc|\.pypirc|\.git-credentials)(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])service-account[a-zA-Z0-9_\-]*\.json(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])[a-zA-Z0-9_\-\./\\]+\.(pem|key)(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])\.kube[/\\]config(?![a-zA-Z0-9_\-])",
        r"(?<![a-zA-Z0-9_\-])\.docker[/\\]config\.json(?![a-zA-Z0-9_\-])",
    ]
    for pat in inline_targets:
        m = re.search(pat, norm_cmd, re.IGNORECASE)
        if m:
            matched_str = m.group(0).strip("<>&| \t'\"()")
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
