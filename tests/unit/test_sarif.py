"""Unit tests for SARIF 2.1.0 parser."""

from bob.scan.sarif import parse_sarif_content


def test_parse_gitleaks_sarif() -> None:
    sarif_data = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "gitleaks",
                        "rules": [
                            {"id": "generic-api-key", "shortDescription": {"text": "Generic API Key"}}
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "generic-api-key",
                        "level": "error",
                        "message": {"text": "Discovered potential generic API key"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "src/config.py"},
                                    "region": {
                                        "startLine": 10,
                                        "snippet": {"text": "api_key = 'sk-secret123456789'"},
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }

    findings = parse_sarif_content(sarif_data)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "generic-api-key"
    assert f.source == "gitleaks"
    assert f.category == "secret"
    assert f.severity == "critical"
    assert f.file == "src/config.py"
    assert f.line == 10
    # Must be masked
    assert "sk-secret123456789" not in f.evidence
    assert "****" in f.evidence


def test_parse_semgrep_sarif() -> None:
    sarif_data = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "semgrep",
                        "rules": [
                            {"id": "python.eval-injection", "shortDescription": {"text": "Eval injection"}}
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": "python.eval-injection",
                        "level": "warning",
                        "message": {"text": "Detected eval() call with untrusted input"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "src/app.py"},
                                    "region": {"startLine": 25, "snippet": {"text": "eval(user_input)"}},
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }

    findings = parse_sarif_content(sarif_data)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "python.eval-injection"
    assert f.source == "semgrep"
    assert f.category == "code"
    assert f.severity == "medium"
    assert f.file == "src/app.py"
    assert f.line == 25
    assert "eval(user_input)" in f.evidence
