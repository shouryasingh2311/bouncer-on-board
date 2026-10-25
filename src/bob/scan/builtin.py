"""Zero-dependency built-in scanner for secrets and insecure code patterns."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

from bob.models import Finding, mask_secret


SECRET_PATTERNS = [
    (
        r"\b(sk-ant-[a-zA-Z0-9_\-]{32,})\b",
        "BUILTIN-SECRET-ANTHROPIC",
        "Anthropic API key hardcoded",
        "critical",
    ),
    (
        r"\b(sk-[a-zA-Z0-9_\-]{20,})\b",
        "BUILTIN-SECRET-API-KEY",
        "OpenAI / AI provider API key hardcoded",
        "critical",
    ),
    (
        r"\b(AIza[0-9A-Za-z_\-]{35})\b",
        "BUILTIN-SECRET-GCP-API",
        "Google Cloud API key hardcoded",
        "critical",
    ),
    (
        r"\b(AKIA[0-9A-Z]{16})\b",
        "BUILTIN-SECRET-AWS-ID",
        "AWS Access Key ID hardcoded",
        "critical",
    ),
    (
        r"(?i)aws_secret_access_key\s*=\s*['\"]([a-zA-Z0-9/+=]{40})['\"]",
        "BUILTIN-SECRET-AWS-KEY",
        "AWS Secret Access Key hardcoded",
        "critical",
    ),
    (
        r"\b(ghp_[a-zA-Z0-9]{36})\b",
        "BUILTIN-SECRET-GITHUB-TOKEN",
        "GitHub personal access token hardcoded",
        "critical",
    ),
    (
        r"\b(sk_live_[0-9a-zA-Z]{24,})\b",
        "BUILTIN-SECRET-STRIPE",
        "Stripe live secret key hardcoded",
        "critical",
    ),
    (
        r"\b(xox[baprs]-[0-9a-zA-Z]{10,48})\b",
        "BUILTIN-SECRET-SLACK",
        "Slack token hardcoded",
        "critical",
    ),
    (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "BUILTIN-SECRET-PRIVATE-KEY",
        "Embedded unencrypted private key",
        "critical",
    ),
    (
        r"\b(eyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,})\b",
        "BUILTIN-SECRET-JWT",
        "Hardcoded JSON Web Token (JWT)",
        "high",
    ),
    (
        r"(?i)\b(postgres|postgresql|mysql|mongodb|redis)://[^:\s]+:([^@\s]+)@",
        "BUILTIN-SECRET-CONN-STRING",
        "Database connection string with hardcoded password",
        "critical",
    ),
    (
        r"(?i)\b(api_key|apikey|secret_key|auth_token)\s*=\s*['\"]([a-zA-Z0-9_\-\.]{12,})['\"]",
        "BUILTIN-SECRET-HARDCODED",
        "Hardcoded sensitive secret/API key",
        "high",
    ),
]

CODE_PATTERNS = [
    (
        r"(?i)\b(eval|exec)\s*\((request|req|params|data|body|user_input|input|\w+\.get\(|\w+\[)",
        "BUILTIN-CODE-DYNAMIC-EVAL",
        "Dynamic code execution (eval/exec) on untrusted request data",
        "high",
    ),
    (
        r"(?i)(cursor\.)?execute\s*\(\s*(f['\"].*(SELECT|INSERT|UPDATE|DELETE)|['\"].*(SELECT|INSERT|UPDATE|DELETE).*['\"]\s*\+)",
        "BUILTIN-CODE-SQL-INJECTION",
        "String-concatenated SQL query (SQL injection risk)",
        "critical",
    ),
    (
        r"(?i)(verify\s*=\s*false|rejectunauthorized\s*:\s*false)",
        "BUILTIN-CODE-TLS-DISABLED",
        "TLS/SSL certificate verification disabled",
        "high",
    ),
    (
        r"(?i)subprocess\.(run|Popen|call|check_output)\s*\(.*shell\s*=\s*True",
        "BUILTIN-CODE-SHELL-TRUE",
        "Subprocess execution with shell=True (command injection risk)",
        "high",
    ),
    (
        r"(?i)(cors\(.*origins\s*:\s*['\"]\*['\"]|access-control-allow-origin['\"]\s*:\s*['\"]\*['\"])",
        "BUILTIN-CODE-OPEN-CORS",
        "Wildcard CORS policy (Access-Control-Allow-Origin: *)",
        "medium",
    ),
    (
        r"(?i)\bdebug\s*=\s*true\b",
        "BUILTIN-CONFIG-DEBUG-MODE",
        "Debug mode enabled in configuration or application",
        "medium",
    ),
]


def scan_file_content(
    relative_path: str, content: str, finding_start_idx: int = 1
) -> List[Finding]:
    """Scan raw string content of a file with built-in secret and code tripwires."""
    findings: List[Finding] = []
    lines = content.splitlines()
    curr_idx = finding_start_idx

    # Check 1: Committed .env file
    norm_path = relative_path.replace("\\", "/").lower()
    if norm_path.endswith(".env") or "/.env" in norm_path or norm_path == ".env":
        f = Finding(
            id=f"BOB-{curr_idx:04d}",
            rule_id="BUILTIN-SECRET-COMMITTED-ENV",
            source="bob-builtin",
            category="secret",
            severity="high",
            title="Committed .env file detected in repository",
            file=relative_path,
            line=1,
            evidence=f"Committed file: {relative_path}",
        )
        findings.append(f)
        curr_idx += 1

    # Check 2: Frontend bundle / JS secret check
    is_frontend = norm_path.endswith((".js", ".jsx", ".ts", ".tsx", ".html"))

    # Line-by-line inspection
    for line_num, line in enumerate(lines, start=1):
        clean_line = line.strip()
        if not clean_line or clean_line.startswith(("#", "//", "/*", "*")):
            continue

        # Scan secrets
        for pat, rule_id, title, sev in SECRET_PATTERNS:
            m = re.search(pat, line)
            if m:
                raw_match = m.group(0)
                # Ignore fake/mock demo comments or test placeholders
                if "fake-demo-key" in line.lower() or "dummy" in line.lower() or "example" in line.lower():
                    # Keep decoy for test measurement, but mask it
                    pass
                f = Finding(
                    id=f"BOB-{curr_idx:04d}",
                    rule_id=rule_id,
                    source="bob-builtin",
                    category="secret",
                    severity=sev,
                    title=title,
                    file=relative_path,
                    line=line_num,
                    evidence=mask_secret(clean_line),
                )
                findings.append(f)
                curr_idx += 1
                break

        # Scan code patterns
        for pat, rule_id, title, sev in CODE_PATTERNS:
            m = re.search(pat, line)
            if m:
                # Extra check for frontend files
                cat = "secret" if is_frontend and "secret" in rule_id.lower() else "code"
                if "debug" in rule_id.lower():
                    cat = "config"
                f = Finding(
                    id=f"BOB-{curr_idx:04d}",
                    rule_id=rule_id,
                    source="bob-builtin",
                    category=cat,
                    severity=sev,
                    title=title,
                    file=relative_path,
                    line=line_num,
                    evidence=clean_line[:120],
                )
                findings.append(f)
                curr_idx += 1
                break

    return findings


def scan_directory_builtin(
    target_dir: Path, base_dir: Optional[Path] = None
) -> List[Finding]:
    """Scan all tracked/supported source files in target_dir using built-in rules."""
    findings: List[Finding] = []
    root = base_dir or target_dir
    idx = 1

    supported_exts = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".json",
        ".yaml",
        ".yml",
        ".env",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
    }
    skip_dirs = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".bob",
        "__pycache__",
        "dist",
        "build",
        ".pytest_cache",
        "AppData",
        "appdata",
        "Local Settings",
        ".cache",
        ".cargo",
        ".rustup",
        ".vscode",
        ".idea",
        "Windows",
        "Program Files",
        "Program Files (x86)",
        "Library",
    }
    files_scanned = 0
    max_scan_files = 5000

    for path in target_dir.rglob("*"):
        if files_scanned >= max_scan_files:
            break
        if path.is_file():
            # Check skip directories within target_dir
            try:
                rel_parts = set(path.relative_to(target_dir).parts[:-1])
            except ValueError:
                rel_parts = set(path.parts[:-1])

            if rel_parts.intersection(skip_dirs):
                continue

            # Support .env* files even without extension
            if path.name.startswith(".env") or path.suffix.lower() in supported_exts:
                files_scanned += 1
                try:
                    rel_path = str(path.relative_to(root).as_posix())
                except ValueError:
                    rel_path = str(path.as_posix())

                try:
                    # Ignore large files (>2MB)
                    if path.stat().st_size > 2_000_000:
                        continue
                    content = path.read_text(encoding="utf-8", errors="replace")
                    file_findings = scan_file_content(rel_path, content, idx)
                    findings.extend(file_findings)
                    idx += len(file_findings)
                except Exception:
                    continue

    return findings
