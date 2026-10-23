"""
Pytest configuration and session fixtures for BOB integration tests.
Starts the local mock registry before any integration tests run.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Generator
import pytest

# Add src and workspace root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from demo.mock_registry.server import start_in_background


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "m1: Milestone 1 package gate tests")
    config.addinivalue_line("markers", "m2: Milestone 2 sensitive-path and intercept guard tests")
    config.addinivalue_line("markers", "m3: Milestone 3 scan tests")
    config.addinivalue_line("markers", "m4: Milestone 4 verify and AI triage tests")
    config.addinivalue_line("markers", "m5: Milestone 5 prompt injection and adapter tests")


@pytest.fixture(scope="session", autouse=True)
def mock_registry() -> Generator[str, None, None]:
    """Start mock registry HTTP server in a daemon thread on port 8765."""
    server, thread = start_in_background(host="127.0.0.1", port=8765)
    time.sleep(0.3)
    yield "http://127.0.0.1:8765"
    server.server_close()


@pytest.fixture(scope="session")
def bob_config_path() -> Path:
    """Return path to demo workdir config.yaml pointing at mock registry."""
    cfg = REPO_ROOT / "demo" / "workdir" / ".bob" / "config.yaml"
    return cfg
