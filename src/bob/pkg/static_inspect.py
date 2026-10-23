"""Static inspection of package installation scripts without execution."""

from __future__ import annotations

import ast
import io
import re
import tarfile
from typing import Any, Dict, List, Optional
import zipfile


SUSPICIOUS_SCRIPT_PATTERNS = [
    (r"(?i)base64\.(b64)?decode", "Base64 decoding in setup/install script"),
    (r"(?i)Buffer\.from\(.+['\"]base64['\"]\)", "Base64 Buffer in install script"),
    (r"(?i)(exec|eval|compile)\s*\(", "Dynamic execution (exec/eval/compile)"),
    (r"(?i)(curl|wget|powershell|certutil)\b", "External downloader invoked"),
    (r"(?i)(\.ssh|\.aws|\.env|\.npmrc|id_rsa)", "Access to sensitive credentials file"),
    (r"(?i)os\.environ", "Mass environment inspection"),
    (r"(?i)process\.env", "Node process environment harvesting"),
]


class SetupPyASTInspector(ast.NodeVisitor):
    """AST visitor statically inspecting setup.py without executing code."""

    def __init__(self) -> None:
        self.findings: List[str] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = self._get_call_name(node.func)

        # Flag exec, eval, or compile calls
        if func_name in ("exec", "eval", "compile"):
            self.findings.append(f"Dynamic execution call '{func_name}()' detected")

        # Flag os.system, subprocess calls
        if func_name in ("os.system", "subprocess.call", "subprocess.run", "subprocess.Popen", "os.popen"):
            for arg in node.args:
                val = self._get_constant_str(arg)
                if val:
                    for pat, desc in SUSPICIOUS_SCRIPT_PATTERNS:
                        if re.search(pat, val):
                            self.findings.append(f"Shell execution invoking: {desc}")

        # Flag base64 decode calls feeding other functions
        if "b64decode" in func_name or "decode" in func_name:
            self.findings.append("Base64/binary string decoding function called in setup.py")

        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            val = node.value
            # Flag long obfuscated strings (>300 chars without whitespace)
            if len(val) > 300 and " " not in val[:100]:
                self.findings.append("Long obfuscated string literal detected in setup.py")
            for pat, desc in SUSPICIOUS_SCRIPT_PATTERNS:
                if re.search(pat, val):
                    self.findings.append(f"Suspicious payload pattern in string literal: {desc}")
        self.generic_visit(node)

    def _get_call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return ""

    def _get_constant_str(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


def inspect_python_setup_content(content: str) -> List[str]:
    """Parse and inspect setup.py string content with AST."""
    findings: List[str] = []
    try:
        tree = ast.parse(content)
        inspector = SetupPyASTInspector()
        inspector.visit(tree)
        findings.extend(inspector.findings)
    except SyntaxError:
        # Malformed syntax in setup.py is itself suspicious
        findings.append("Malformed setup.py syntax (failed static AST parse)")

    # Regex safety fallback
    for pat, desc in SUSPICIOUS_SCRIPT_PATTERNS:
        if re.search(pat, content):
            msg = f"Static regex tripwire hit: {desc}"
            if msg not in findings:
                findings.append(msg)

    return findings


def inspect_npm_lifecycle_scripts(scripts: Dict[str, str]) -> List[str]:
    """Inspect npm preinstall, install, and postinstall lifecycle scripts."""
    findings: List[str] = []
    lifecycle_hooks = ("preinstall", "install", "postinstall", "prepublish")

    for hook in lifecycle_hooks:
        cmd = scripts.get(hook)
        if not cmd or not isinstance(cmd, str):
            continue
        # Check against suspicious patterns
        for pat, desc in SUSPICIOUS_SCRIPT_PATTERNS:
            if re.search(pat, cmd):
                findings.append(f"npm lifecycle script '{hook}' contains suspicious pattern: {desc}")

    return findings


def extract_setup_py_from_tarball(archive_bytes: bytes) -> Optional[str]:
    """Safely extract setup.py from tarball bytes in memory."""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as tar:
            members = tar.getmembers()
            # Enforce safety limits
            if len(members) > 500:
                return None
            for m in members:
                # Prevent path traversal
                if m.name.startswith(("/", "\\", "..")) or ".." in m.name:
                    continue
                if m.name.endswith("setup.py") and m.size < 500_000:
                    extracted = tar.extractfile(m)
                    if extracted:
                        return extracted.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    return None
