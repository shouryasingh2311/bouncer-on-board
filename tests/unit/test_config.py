"""Unit tests for BOB config loader and core models."""

import os
from pathlib import Path
import tempfile
import yaml

from bob.config import Config, load_config
from bob.models import AITriage, Decision, Finding, compute_fingerprint, mask_secret


def test_config_defaults() -> None:
    cfg = Config()
    assert cfg.model == "gemma4:e2b"
    assert cfg.ollama_url == "http://localhost:11434"
    assert cfg.min_package_age_days == 14
    assert cfg.offline_policy == "warn"
    assert cfg.registry_overrides == {}
    assert cfg.fail_gate_on == ["critical", "high"]
    assert cfg.get_pypi_base_url() == "https://pypi.org/pypi"
    assert cfg.get_npm_base_url() == "https://registry.npmjs.org"


def test_config_registry_overrides() -> None:
    cfg = Config(
        registry_overrides={
            "pypi": "http://127.0.0.1:8765/pypi/",
            "npm": "http://127.0.0.1:8765/npm/",
        }
    )
    assert cfg.get_pypi_base_url() == "http://127.0.0.1:8765/pypi"
    assert cfg.get_npm_base_url() == "http://127.0.0.1:8765/npm"


def test_load_config_from_file() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(
            {
                "model": "gemma4:e4b",
                "min_package_age_days": 21,
                "offline_policy": "block",
                "registry_overrides": {"pypi": "http://mock/pypi"},
                "fail_gate_on": ["critical"],
            },
            tmp,
        )
        tmp_path = Path(tmp.name)

    try:
        cfg = load_config(tmp_path)
        assert cfg.model == "gemma4:e4b"
        assert cfg.min_package_age_days == 21
        assert cfg.offline_policy == "block"
        assert cfg.get_pypi_base_url() == "http://mock/pypi"
        assert cfg.fail_gate_on == ["critical"]
    finally:
        tmp_path.unlink()


def test_load_config_env_var(monkeypatch) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
        yaml.dump({"model": "custom-gemma"}, tmp)
        tmp_path = Path(tmp.name)

    try:
        monkeypatch.setenv("BOB_CONFIG", str(tmp_path))
        cfg = load_config()
        assert cfg.model == "custom-gemma"
    finally:
        tmp_path.unlink()


def test_mask_secret() -> None:
    assert mask_secret("") == ""
    assert mask_secret("abc") == "****"
    assert mask_secret("abcd") == "****"
    assert mask_secret("sk-1234567890") == "sk-1****"


def test_finding_and_fingerprint() -> None:
    f1 = Finding(
        id="BOB-0001",
        rule_id="PKG-NOT-FOUND",
        source="bob-pkg-gate",
        category="package",
        severity="critical",
        title="Package not found",
        file=None,
        line=None,
        evidence="fastapi-jwt-session",
    )
    assert len(f1.fingerprint) == 64
    d = f1.to_dict()
    assert d["id"] == "BOB-0001"
    assert d["rule_id"] == "PKG-NOT-FOUND"
    assert d["fingerprint"] == f1.fingerprint


def test_decision_to_dict() -> None:
    finding = Finding(
        id="BOB-0002",
        rule_id="PKG-TOO-NEW",
        source="bob-pkg-gate",
        category="package",
        severity="medium",
        title="Package is brand new",
        file="requirements.txt",
        line=1,
        evidence="demo-fresh-lib (2 days old)",
    )
    decision = Decision(
        action="warn",
        score=35,
        reasons=["Package younger than 14 days"],
        findings=[finding],
    )
    d = decision.to_dict()
    assert d["action"] == "warn"
    assert d["score"] == 35
    assert len(d["findings"]) == 1
    assert d["findings"][0]["id"] == "BOB-0002"
