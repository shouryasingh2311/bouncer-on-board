"""Unit tests for built-in tripwire scanner."""

from pathlib import Path
from bob.scan.builtin import scan_directory_builtin, scan_file_content


def test_scan_committed_env() -> None:
    findings = scan_file_content(".env", "DATABASE_URL=postgres://localhost\nSECRET_KEY=1234567890123456")
    assert any(f.rule_id == "BUILTIN-SECRET-COMMITTED-ENV" for f in findings)
    env_finding = next(f for f in findings if f.rule_id == "BUILTIN-SECRET-COMMITTED-ENV")
    assert env_finding.category == "secret"
    assert env_finding.severity == "high"


def test_scan_hardcoded_secrets() -> None:
    content = """
    # Hardcoded secrets test
    openai_key = "sk-1234567890abcdef1234567890"
    aws_id = "AKIAIOSFODNN7EXAMPLE"
    github_token = "ghp_123456789012345678901234567890123456"
    """
    findings = scan_file_content("config.py", content)
    rule_ids = {f.rule_id for f in findings}
    assert "BUILTIN-SECRET-API-KEY" in rule_ids
    assert "BUILTIN-SECRET-AWS-ID" in rule_ids
    assert "BUILTIN-SECRET-GITHUB-TOKEN" in rule_ids

    for f in findings:
        assert f.category == "secret"
        assert f.severity == "critical"
        # Secrets must be masked!
        assert "****" in f.evidence
        assert "sk-1234567890abcdef1234567890" not in f.evidence


def test_scan_code_vulnerabilities() -> None:
    content = """
    def handle_request(req):
        user_input = req.get("payload")
        eval(user_input)
        cursor.execute(f"SELECT * FROM accounts WHERE id = {req.get('id')}")
        resp = requests.get("https://internal.service", verify=False)
        debug = True
        return resp
    """
    findings = scan_file_content("app.py", content)
    rule_ids = {f.rule_id for f in findings}
    assert "BUILTIN-CODE-DYNAMIC-EVAL" in rule_ids
    assert "BUILTIN-CODE-SQL-INJECTION" in rule_ids
    assert "BUILTIN-CODE-TLS-DISABLED" in rule_ids
    assert "BUILTIN-CONFIG-DEBUG-MODE" in rule_ids

    eval_f = next(f for f in findings if f.rule_id == "BUILTIN-CODE-DYNAMIC-EVAL")
    assert eval_f.category == "code"
    assert eval_f.severity == "high"

    sql_f = next(f for f in findings if f.rule_id == "BUILTIN-CODE-SQL-INJECTION")
    assert sql_f.category == "code"
    assert sql_f.severity == "critical"


def test_scan_directory_clean(tmp_path: Path) -> None:
    (tmp_path / "hello.py").write_text("def hello():\n    return 'clean code'\n", encoding="utf-8")
    findings = scan_directory_builtin(tmp_path)
    assert len(findings) == 0


def test_scan_directory_with_vulnerabilities(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text("API_KEY = 'sk-1234567890abcdef1234567890'\n", encoding="utf-8")
    (tmp_path / ".env").write_text("DEBUG=True\n", encoding="utf-8")
    findings = scan_directory_builtin(tmp_path)
    assert len(findings) >= 2
    categories = {f.category for f in findings}
    assert "secret" in categories
