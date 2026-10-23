"""Unit tests for Cloud AI client (Gemini & OpenAI-compatible) and triage integration."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from bob.ai.cloud_client import (
    query_cloud_triage,
    query_gemini_triage,
    query_openai_compatible_triage,
    validate_cloud_credentials,
)
from bob.ai.triage import triage_findings
from bob.config import Config
from bob.models import Finding


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        id="BOB-0001",
        rule_id="BUILTIN-SECRET-API-KEY",
        source="bob-builtin",
        category="secret",
        severity="critical",
        title="OpenAI API key hardcoded",
        file="app.py",
        line=10,
        evidence="sk-live-1234567890abcdef1234567890",
    )


def test_validate_cloud_credentials_empty():
    ok, msg = validate_cloud_credentials("gemini", "", "gemini-1.5-flash")
    assert not ok
    assert "empty" in msg.lower()


def test_validate_gemini_credentials_success():
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        ok, msg = validate_cloud_credentials("gemini", "dummy_key", "gemini-1.5-flash")
        assert ok
        assert "verified" in msg.lower()


def test_validate_gemini_credentials_failure():
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_get.return_value = mock_resp

        ok, msg = validate_cloud_credentials("gemini", "bad_key", "gemini-1.5-flash")
        assert not ok
        assert "invalid api key" in msg.lower()


def test_validate_openai_credentials_success():
    with patch("httpx.Client.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        ok, msg = validate_cloud_credentials("openai", "dummy_key", "gpt-4o-mini")
        assert ok
        assert "verified" in msg.lower()


def test_query_gemini_triage_success(sample_finding):
    fake_json = {
        "verdict": "likely_true_positive",
        "explanation": "Real secret exposed in production file.",
        "suggested_fix": "Move key to environment variable.",
    }
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": json.dumps(fake_json)}]
                    }
                }
            ]
        }
        mock_post.return_value = mock_resp

        result = query_gemini_triage("test_key", "gemini-1.5-flash", sample_finding)
        assert result is not None
        assert result["verdict"] == "likely_true_positive"
        assert "environment" in result["suggested_fix"].lower()


def test_query_openai_compatible_triage_success(sample_finding):
    fake_json = {
        "verdict": "likely_false_positive",
        "explanation": "Test dummy key in mock file.",
        "suggested_fix": "None needed.",
    }
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {"content": json.dumps(fake_json)}
                }
            ]
        }
        mock_post.return_value = mock_resp

        result = query_openai_compatible_triage(
            "https://api.openai.com/v1", "test_key", "gpt-4o-mini", sample_finding
        )
        assert result is not None
        assert result["verdict"] == "likely_false_positive"


def test_triage_findings_with_cloud_and_axiom2(sample_finding):
    """Verify cloud triage runs and Axiom 2 prevents downranking critical items."""
    cfg = Config(
        ai_provider="gemini",
        api_key="valid_key",
        model="gemini-1.5-flash",
    )
    fake_json = {
        "verdict": "likely_false_positive",
        "explanation": "AI thinks this is a test key.",
        "suggested_fix": "No action.",
    }
    with patch("bob.ai.triage.query_cloud_triage", return_value=fake_json):
        updated, model_disp, explained, downranked = triage_findings([sample_finding], cfg)

        assert "gemini" in model_disp.lower()
        assert explained == 1
        assert downranked == 0  # CRITICAL findings can NEVER be downranked
        assert updated[0].severity == "critical"
        assert updated[0].ai.verdict == "likely_true_positive"
        assert "Security Axiom 2 forbids" in updated[0].ai.explanation
