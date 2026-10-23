"""npm registry client for static packument inspection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
import httpx

from bob.config import Config


_NPM_CACHE: Dict[str, Tuple[int, Dict[str, Any]]] = {}


def fetch_npm_metadata(
    package_name: str, config: Config
) -> Tuple[int, Dict[str, Any]]:
    """Fetch package packument from npm registry (or configured mock registry).

    Returns (status_code, response_json).
    """
    clean_name = package_name.strip()
    if clean_name in _NPM_CACHE:
        return _NPM_CACHE[clean_name]

    base_url = config.get_npm_base_url()
    # Handle scoped packages @scope/pkg
    url = f"{base_url}/{clean_name}"

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            status_code = resp.status_code
            if status_code == 200:
                data = resp.json()
                _NPM_CACHE[clean_name] = (status_code, data)
                return status_code, data
            elif status_code == 404:
                _NPM_CACHE[clean_name] = (404, {})
                return 404, {}
            else:
                return status_code, {}
    except Exception:
        return 0, {}


def extract_npm_first_upload(data: Dict[str, Any]) -> Optional[datetime]:
    """Extract creation time from npm packument."""
    time_map = data.get("time", {})
    created_str = time_map.get("created")
    if created_str:
        return _parse_iso(created_str)

    # Fallback to earliest timestamp in time dict
    earliest: Optional[datetime] = None
    for k, v in time_map.items():
        if k in ("modified",):
            continue
        if isinstance(v, str):
            dt = _parse_iso(v)
            if dt and (earliest is None or dt < earliest):
                earliest = dt
    return earliest


def has_npm_provenance(data: Dict[str, Any]) -> bool:
    """Check if npm metadata contains repository or homepage information."""
    repo = data.get("repository")
    if repo:
        if isinstance(repo, str) and repo.strip():
            return True
        if isinstance(repo, dict) and repo.get("url"):
            return True

    homepage = data.get("homepage")
    if homepage and isinstance(homepage, str) and homepage.strip():
        return True

    return False


def get_npm_scripts(
    data: Dict[str, Any], version: Optional[str] = None
) -> Dict[str, str]:
    """Retrieve install scripts from target or latest npm version."""
    versions = data.get("versions", {})
    target_version = version

    if not target_version:
        target_version = data.get("dist-tags", {}).get("latest")

    if not target_version and versions:
        # Pick last version key
        target_version = list(versions.keys())[-1]

    if target_version and target_version in versions:
        ver_obj = versions[target_version]
        return ver_obj.get("scripts", {})

    return {}


def get_npm_tarball_url(
    data: Dict[str, Any], version: Optional[str] = None
) -> Optional[str]:
    """Get tarball download URL for static archive inspection."""
    versions = data.get("versions", {})
    target_version = version or data.get("dist-tags", {}).get("latest")
    if not target_version and versions:
        target_version = list(versions.keys())[-1]

    if target_version and target_version in versions:
        dist = versions[target_version].get("dist", {})
        return dist.get("tarball")

    return None


def _parse_iso(val: str) -> Optional[datetime]:
    try:
        s = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
