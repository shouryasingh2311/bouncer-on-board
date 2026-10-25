"""Shell command parsing for package installation intents and guards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
import re
import shlex
from typing import List, Optional, Tuple

from bob.models import Finding


@dataclass
class InstallIntent:
    """Represents an intercepted package installation target."""

    ecosystem: str  # "pypi" | "npm"
    package: str
    version: Optional[str] = None
    is_unverifiable: bool = False
    raw_target: str = ""


SHELL_WRAPPERS = {
    "bash", "sh", "zsh", "dash", "ash", "ksh", "csh", "tcsh", "cmd", "powershell", "pwsh"
}

REMOTE_EXEC_PATTERN = re.compile(
    r"\b(curl|wget|fetch|http|irm|iwr|invoke-webrequest|invoke-restmethod)\b"
    r"[^|;&\n]*"
    r"\|"
    r"\s*(sudo\s+)?"
    r"([a-zA-Z0-9_\-\./\\]*[/\\])?"
    r"\b(sh|bash|zsh|dash|ksh|python|python3|perl|ruby|node|iex|invoke-expression|pwsh|powershell)\b",
    re.IGNORECASE,
)


def get_executable_name(token: str) -> str:
    """Extract clean base executable name from token (e.g. /usr/bin/pip -> pip)."""
    clean = token.strip("\"'")
    norm = clean.replace("\\", "/")
    base = PurePath(norm).name.lower()
    for ext in (".exe", ".cmd", ".bat", ".sh"):
        if base.endswith(ext):
            base = base[:-len(ext)]
            break
    return base


def unwrap_command(tokens: List[str], depth: int = 0) -> List[str]:
    """Recursively strip sudo, nohup, env prefixes, variable assignments, and unwrap shell wrappers."""
    if depth > 5 or not tokens:
        return tokens

    clean_tokens = [t.strip("\"'") for t in tokens if t.strip("\"'")]

    while clean_tokens:
        first_exe = get_executable_name(clean_tokens[0])
        if first_exe in ("sudo", "nohup"):
            clean_tokens = clean_tokens[1:]
            while clean_tokens and clean_tokens[0].startswith("-"):
                if clean_tokens[0] in ("-u", "-g", "-p", "-a", "-c", "-r", "-t") and len(clean_tokens) > 1:
                    clean_tokens = clean_tokens[2:]
                else:
                    clean_tokens = clean_tokens[1:]
            continue

        if first_exe == "env":
            clean_tokens = clean_tokens[1:]
            while clean_tokens and clean_tokens[0].startswith("-"):
                if clean_tokens[0] in ("-u", "-C", "-S") and len(clean_tokens) > 1:
                    clean_tokens = clean_tokens[2:]
                else:
                    clean_tokens = clean_tokens[1:]
            continue

        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", clean_tokens[0]):
            clean_tokens = clean_tokens[1:]
            continue

        break

    if not clean_tokens:
        return []

    exe = get_executable_name(clean_tokens[0])
    if exe in SHELL_WRAPPERS and len(clean_tokens) >= 2:
        wrapper_flag_idx = -1
        for idx, tok in enumerate(clean_tokens[1:], start=1):
            if tok.lower() in ("-c", "/c", "-command", "/command"):
                wrapper_flag_idx = idx
                break
        if wrapper_flag_idx != -1 and wrapper_flag_idx + 1 < len(clean_tokens):
            inner_str = " ".join(clean_tokens[wrapper_flag_idx + 1:])
            try:
                inner_tokens = shlex.split(inner_str, posix=False)
            except Exception:
                inner_tokens = inner_str.split()
            return unwrap_command(inner_tokens, depth=depth + 1)

    return clean_tokens


def check_dangerous_remote_execution(cmd_string: str) -> Optional[Finding]:
    """Detect unverified remote scripts piped directly into a shell interpreter."""
    m = REMOTE_EXEC_PATTERN.search(cmd_string)
    if m:
        snippet = m.group(0).strip()
        return Finding(
            id="BOB-0000",
            rule_id="GUARD-REMOTE-EXEC",
            source="bob-guard",
            category="execution",
            severity="critical",
            title="Unverified remote script piped directly to shell interpreter",
            file=None,
            line=None,
            evidence=snippet,
        )
    return None


def split_pipeline(cmd_string: str) -> List[str]:
    """Split compound shell commands on &&, ;, ||, and | while respecting quotes."""
    pattern = r'(?:[^&;|"\']+|"[^"]*"|\'[^\']*\')+'
    chunks = re.findall(pattern, cmd_string)
    result = []
    for c in chunks:
        stripped = c.strip()
        if stripped and stripped not in ("&&", ";", "||", "|"):
            result.append(stripped)
    return result if result else [cmd_string.strip()]


def parse_pkg_and_version(raw_spec: str, ecosystem: str) -> Tuple[str, Optional[str]]:
    """Parse name and optional version from a package specifier."""
    if ecosystem == "npm":
        # Handle @scope/package@version or package@version
        if raw_spec.startswith("@"):
            parts = raw_spec.split("@")
            # ['' , 'scope/name', 'version?']
            if len(parts) >= 3:
                return f"@{parts[1]}", parts[2]
            return raw_spec, None
        else:
            if "@" in raw_spec:
                name, ver = raw_spec.split("@", 1)
                return name, ver
            return raw_spec, None
    else:
        # PyPI: handle ==, >=, <=, ~=, and strip extras [security]
        m = re.split(r"(==|>=|<=|~=|<|>)", raw_spec, maxsplit=1)
        if len(m) == 3:
            name = re.sub(r"\[.*?\]", "", m[0]).strip()
            return name, m[2].strip()
        name = re.sub(r"\[.*?\]", "", raw_spec).strip()
        return name, None


def is_unverifiable_target(target: str) -> bool:
    """Check if target is a local path, VCS URL, or direct archive URL."""
    lower = target.lower()
    return (
        lower.startswith((".", "/", "\\", "git+", "http://", "https://", "ssh://"))
        or lower.endswith((".whl", ".tar.gz", ".zip", ".tgz"))
        or lower in ("-e", "--editable")
    )


def extract_install_intents(cmd_str: str, depth: int = 0) -> List[InstallIntent]:
    """Extract install targets across Python (pip/uv/poetry/pipx/conda) and Node (npm/npx/yarn/pnpm/bun/bunx)."""
    if depth > 5:
        return []

    intents: List[InstallIntent] = []
    commands = split_pipeline(cmd_str)

    for cmd in commands:
        try:
            tokens = shlex.split(cmd, posix=False)
        except Exception:
            tokens = cmd.split()

        if not tokens:
            continue

        clean_tokens = [t.strip("\"'") for t in tokens if t.strip("\"'")]
        if not clean_tokens:
            continue

        # 1. Strip wrappers and normalize
        clean_tokens = unwrap_command(clean_tokens)
        if not clean_tokens:
            continue

        exe = get_executable_name(clean_tokens[0])

        # 2. Check for shell wrappers that were not unwrapped (e.g. bash -c "complex command")
        if exe in SHELL_WRAPPERS and len(clean_tokens) >= 2:
            wrapper_flag_idx = -1
            for idx, tok in enumerate(clean_tokens[1:], start=1):
                if tok.lower() in ("-c", "/c", "-command", "/command"):
                    wrapper_flag_idx = idx
                    break
            if wrapper_flag_idx != -1 and wrapper_flag_idx + 1 < len(clean_tokens):
                inner_cmd = " ".join(clean_tokens[wrapper_flag_idx + 1:])
                inner_intents = extract_install_intents(inner_cmd, depth=depth + 1)
                intents.extend(inner_intents)
                continue

        # 3. Python: python -m pip/poetry/pipx/conda ...
        if exe in ("python", "python3", "py") and len(clean_tokens) >= 3:
            if clean_tokens[1] == "-m":
                mod = clean_tokens[2].lower()
                if mod in ("pip", "pip3", "pipx", "conda"):
                    sub_idx = -1
                    for idx, tok in enumerate(clean_tokens[3:], start=3):
                        if tok.lower() == "install":
                            sub_idx = idx
                            break
                    if sub_idx != -1:
                        _parse_pip_args(clean_tokens[sub_idx + 1:], intents)
                        continue
                if mod == "poetry":
                    sub_idx = -1
                    for idx, tok in enumerate(clean_tokens[3:], start=3):
                        if tok.lower() == "add":
                            sub_idx = idx
                            break
                    if sub_idx != -1:
                        _parse_pip_args(clean_tokens[sub_idx + 1:], intents)
                        continue

        # 4. Python: pip / pip3 install ...
        if exe in ("pip", "pip3"):
            sub_idx = -1
            for idx, tok in enumerate(clean_tokens[1:], start=1):
                if tok.lower() == "install":
                    sub_idx = idx
                    break
            if sub_idx != -1:
                _parse_pip_args(clean_tokens[sub_idx + 1:], intents)
                continue

        # 5. Python: uv pip install ... or uv add ...
        if exe == "uv":
            lower_tokens = [t.lower() for t in clean_tokens]
            if "add" in lower_tokens:
                add_idx = lower_tokens.index("add")
                _parse_pip_args(clean_tokens[add_idx + 1:], intents)
                continue
            if "pip" in lower_tokens and "install" in lower_tokens:
                inst_idx = lower_tokens.index("install")
                _parse_pip_args(clean_tokens[inst_idx + 1:], intents)
                continue

        # 6. Python: poetry add ...
        if exe == "poetry":
            lower_tokens = [t.lower() for t in clean_tokens]
            if "add" in lower_tokens:
                add_idx = lower_tokens.index("add")
                _parse_pip_args(clean_tokens[add_idx + 1:], intents)
                continue

        # 7. Python: pipx install ...
        if exe == "pipx":
            lower_tokens = [t.lower() for t in clean_tokens]
            if "install" in lower_tokens:
                inst_idx = lower_tokens.index("install")
                _parse_pip_args(clean_tokens[inst_idx + 1:], intents)
                continue

        # 8. Python / Conda: conda install ...
        if exe == "conda":
            lower_tokens = [t.lower() for t in clean_tokens]
            if "install" in lower_tokens:
                inst_idx = lower_tokens.index("install")
                _parse_pip_args(clean_tokens[inst_idx + 1:], intents)
                continue

        # 9. Node: npm install / i / add ...
        if exe == "npm":
            for idx, tok in enumerate(clean_tokens[1:], start=1):
                if tok.lower() in ("install", "i", "add"):
                    _parse_npm_args(clean_tokens[idx + 1:], intents)
                    break
            continue

        # 10. Node: pnpm / yarn add / install / dlx
        if exe in ("pnpm", "yarn"):
            lower_tokens = [t.lower() for t in clean_tokens]
            if "dlx" in lower_tokens:
                dlx_idx = lower_tokens.index("dlx")
                _parse_npx_args(clean_tokens[dlx_idx + 1:], intents)
                continue
            for idx, tok in enumerate(clean_tokens[1:], start=1):
                if tok.lower() in ("add", "install", "i"):
                    _parse_npm_args(clean_tokens[idx + 1:], intents)
                    break
            continue

        # 11. Node: bun add / install / i
        if exe == "bun":
            for idx, tok in enumerate(clean_tokens[1:], start=1):
                if tok.lower() in ("add", "install", "i"):
                    _parse_npm_args(clean_tokens[idx + 1:], intents)
                    break
            continue

        # 12. Node: bunx / npx <pkg> ...
        if exe in ("npx", "bunx") and len(clean_tokens) >= 2:
            _parse_npx_args(clean_tokens[1:], intents)
            continue

    return intents


def _parse_pip_args(args: List[str], intents: List[InstallIntent]) -> None:
    skip_next = False
    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue
        if arg in ("-r", "--requirement", "-c", "--constraint", "-t", "--target", "--index-url", "--extra-index-url"):
            skip_next = True
            intents.append(
                InstallIntent(
                    ecosystem="pypi",
                    package=arg,
                    is_unverifiable=True,
                    raw_target=arg,
                )
            )
            continue
        if arg.startswith("-"):
            continue
        if is_unverifiable_target(arg):
            intents.append(
                InstallIntent(
                    ecosystem="pypi",
                    package=arg,
                    is_unverifiable=True,
                    raw_target=arg,
                )
            )
        else:
            name, ver = parse_pkg_and_version(arg, "pypi")
            intents.append(
                InstallIntent(
                    ecosystem="pypi",
                    package=name,
                    version=ver,
                    is_unverifiable=False,
                    raw_target=arg,
                )
            )


def _parse_npm_args(args: List[str], intents: List[InstallIntent]) -> None:
    for arg in args:
        if arg.startswith("-"):
            continue
        if is_unverifiable_target(arg):
            intents.append(
                InstallIntent(
                    ecosystem="npm",
                    package=arg,
                    is_unverifiable=True,
                    raw_target=arg,
                )
            )
        else:
            name, ver = parse_pkg_and_version(arg, "npm")
            intents.append(
                InstallIntent(
                    ecosystem="npm",
                    package=name,
                    version=ver,
                    is_unverifiable=False,
                    raw_target=arg,
                )
            )


def _parse_npx_args(args: List[str], intents: List[InstallIntent]) -> None:
    # First non-flag token is the package to download and execute
    for arg in args:
        if arg.startswith("-"):
            continue
        if is_unverifiable_target(arg):
            intents.append(
                InstallIntent(
                    ecosystem="npm",
                    package=arg,
                    is_unverifiable=True,
                    raw_target=arg,
                )
            )
        else:
            name, ver = parse_pkg_and_version(arg, "npm")
            intents.append(
                InstallIntent(
                    ecosystem="npm",
                    package=name,
                    version=ver,
                    is_unverifiable=False,
                    raw_target=arg,
                )
            )
        break

