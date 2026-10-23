"""Unit tests for sensitive path detection and self-protection guards."""

from bob.config import Config
from bob.guards.sensitive_paths import (
    check_command_sensitive_paths,
    check_self_protection,
    is_sensitive_path,
    normalise_path,
)


def test_normalise_path() -> None:
    assert normalise_path("C:\\Users\\test\\.env") == "c:/users/test/.env"
    assert normalise_path("./.ssh/id_rsa") == "./.ssh/id_rsa"


def test_is_sensitive_path_targets() -> None:
    assert is_sensitive_path(".env") is not None
    assert is_sensitive_path(".env.local") is not None
    assert is_sensitive_path(".env.production") is not None
    assert is_sensitive_path("~/.ssh/id_rsa") is not None
    assert is_sensitive_path(".ssh/id_ed25519") is not None
    assert is_sensitive_path(".aws/credentials") is not None
    assert is_sensitive_path(".npmrc") is not None
    assert is_sensitive_path("certs/server.pem") is not None
    assert is_sensitive_path(".kube/config") is not None
    assert is_sensitive_path("service-account-prod.json") is not None

    # Benign targets
    assert is_sensitive_path("README.md") is None
    assert is_sensitive_path("src/app.py") is None
    assert is_sensitive_path("tests/test_env.py") is None


def test_check_self_protection_bob_allow() -> None:
    hit = check_self_protection("bob allow demo-evil-lib")
    assert hit is not None
    assert hit.rule_id == "GUARD-BOB-SELF-PROTECT"

    hit_chained = check_self_protection("pip install foo && bob allow bar")
    assert hit_chained is not None
    assert hit_chained.rule_id == "GUARD-BOB-SELF-PROTECT"


def test_check_self_protection_dot_bob_tampering() -> None:
    hit_write = check_self_protection("echo '...' > .bob/allowlist.yaml")
    assert hit_write is not None
    assert hit_write.rule_id == "GUARD-BOB-SELF-PROTECT"

    hit_del = check_self_protection("rm -rf .bob")
    assert hit_del is not None
    assert hit_del.rule_id == "GUARD-BOB-SELF-PROTECT"

    # Benign command
    assert check_self_protection("git status") is None


def test_check_command_sensitive_paths() -> None:
    hit_cat = check_command_sensitive_paths("cat .env")
    assert hit_cat is not None
    assert hit_cat.rule_id == "GUARD-SENSITIVE-PATH"

    hit_win = check_command_sensitive_paths("type .ssh\\id_rsa")
    assert hit_win is not None
    assert hit_win.rule_id == "GUARD-SENSITIVE-PATH"

    hit_benign = check_command_sensitive_paths("cat README.md")
    assert hit_benign is None
