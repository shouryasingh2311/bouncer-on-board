"""Shell command parsing for package installation intents and guards."""

from __future__ import annotations

from dataclasses import dataclass
import re
import shlex
from typing import List, Optional, Tuple


@dataclass
class InstallIntent:
    """Represents an intercepted package installation target."""

    ecosystem: str  # "pypi" | "npm"
    package: str
    version: Optional[str] = None
    is_unverifiable: bool = False
    raw_target: str = ""


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
        # PyPI: handle ==, >=, <=, ~=
        m = re.split(r"(==|>=|<=|~=|<|>)", raw_spec, maxsplit=1)
        if len(m) == 3:
            return m[0].strip(), m[2].strip()
        return raw_spec.strip(), None


def is_unverifiable_target(target: str) -> bool:
    """Check if target is a local path, VCS URL, or direct archive URL."""
    lower = target.lower()
    return (
        lower.startswith((".", "/", "\\", "git+", "http://", "https://", "ssh://"))
        or lower.endswith((".whl", ".tar.gz", ".zip", ".tgz"))
        or lower in ("-e", "--editable")
    )


def extract_install_intents(cmd_str: str) -> List[InstallIntent]:
    """Extract install targets across Python (pip/uv) and Node (npm/npx/yarn/pnpm)."""
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

        # Normalise executable name
        exe = clean_tokens[0].lower().replace(".exe", "")

        # 1. Python: python -m pip install ... or py -m pip install ...
        if exe in ("python", "python3", "py") and len(clean_tokens) >= 4:
            if clean_tokens[1] == "-m" and clean_tokens[2].lower() in ("pip", "pip3"):
                if clean_tokens[3].lower() == "install":
                    _parse_pip_args(clean_tokens[4:], intents)
                    continue

        # 2. Python: pip / pip3 install ...
        if exe in ("pip", "pip3") and len(clean_tokens) >= 2:
            if clean_tokens[1].lower() == "install":
                _parse_pip_args(clean_tokens[2:], intents)
                continue

        # 3. Python: uv pip install ... or uv add ...
        if exe == "uv" and len(clean_tokens) >= 2:
            if clean_tokens[1].lower() == "add":
                _parse_pip_args(clean_tokens[2:], intents)
                continue
            if len(clean_tokens) >= 3 and clean_tokens[1].lower() == "pip" and clean_tokens[2].lower() == "install":
                _parse_pip_args(clean_tokens[3:], intents)
                continue

        # 4. Node: npm install / i / add ...
        if exe == "npm" and len(clean_tokens) >= 2:
            sub = clean_tokens[1].lower()
            if sub in ("install", "i", "add"):
                _parse_npm_args(clean_tokens[2:], intents)
                continue

        # 5. Node: pnpm add / yarn add ...
        if exe in ("pnpm", "yarn") and len(clean_tokens) >= 2:
            sub = clean_tokens[1].lower()
            if sub in ("add", "install"):
                _parse_npm_args(clean_tokens[2:], intents)
                continue

        # 6. Node: npx <pkg> ...
        if exe == "npx" and len(clean_tokens) >= 2:
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
