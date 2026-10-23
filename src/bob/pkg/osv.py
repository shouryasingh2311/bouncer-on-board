"""OSV HTTP API client for detecting known vulnerabilities and malicious packages."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx

OSV_QUERY_URL = "https://api.osv.dev/v1/query"


def query_osv(
    package_name: str, ecosystem: str, version: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Query OSV API for advisories targeting a specific package."""
    # Map ecosystems to OSV standard names
    eco_map = {
        "pypi": "PyPI",
        "npm": "npm",
    }
    target_eco = eco_map.get(ecosystem.lower(), ecosystem)

    payload: Dict[str, Any] = {
        "package": {
            "name": package_name,
            "ecosystem": target_eco,
        }
    }
    if version:
        payload["version"] = version

    try:
        with httpx.Client(timeout=4.0) as client:
            resp = client.post(OSV_QUERY_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("vulns", [])
    except Exception:
        # Graceful degradation if OSV is unreachable
        return []

    return []


def has_malicious_advisory(vulns: List[Dict[str, Any]]) -> Optional[str]:
    """Check if any advisory ID represents a known malicious package (starts with MAL-)."""
    for v in vulns:
        vuln_id = str(v.get("id", "")).upper()
        if vuln_id.startswith("MAL-"):
            return vuln_id
    return None
