"""Vulnerable demonstration application for BOB security scanning.

DO NOT USE IN PRODUCTION.
This file contains deliberate security vulnerabilities and test tokens
designed to evaluate static scanners and AI security triage:
1. Hardcoded OpenAI API Key (Secret Leak)
2. Hardcoded AWS Access Key ID (Secret Leak)
3. Raw SQL Injection via string interpolation
4. Dynamic code execution (eval) on untrusted input
5. Disabled TLS certificate validation (verify=False)
"""

import os
import sqlite3
import requests


# 1. Hardcoded Secret API Key
OPENAI_API_KEY = "sk-live-9876543210abcdef9876543210abcdef"
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"


def get_user_data(user_id: str):
    """Vulnerable to SQL Injection."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # Unsanitized string interpolation directly into SQL query
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    cursor.execute(query)
    return cursor.fetchall()


def calculate_user_expression(request_data: dict):
    """Vulnerable to arbitrary code execution."""
    # Untrusted expression passed directly to eval()
    raw_expr = request_data.get("calc")
    return eval(raw_expr)


def sync_remote_telemetry(payload: dict):
    """Vulnerable to Man-In-The-Middle (MITM) via disabled SSL verification."""
    url = "https://telemetry.internal.company.net/v1/event"
    # TLS verification disabled
    return requests.post(url, json=payload, verify=False)


if __name__ == "__main__":
    print("Vulnerable demo app loaded.")
