"""PyPI registry client for static metadata inspection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import httpx

from bob.config import Config


# Session cache to stay fast (<400ms target)
_PYPI_CACHE: Dict[str, Tuple[int, Dict[str, Any]]] = {}


def fetch_pypi_metadata(
    package_name: str, config: Config
) -> Tuple[int, Dict[str, Any]]:
    """Fetch package JSON from PyPI (or configured mock registry).

    Returns (status_code, response_json).
    """
    clean_name = package_name.strip().lower()
    if clean_name in _PYPI_CACHE:
        return _PYPI_CACHE[clean_name]

    base_url = config.get_pypi_base_url()
    url = f"{base_url}/{clean_name}/json"

    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            status_code = resp.status_code
            if status_code == 200:
                data = resp.json()
                _PYPI_CACHE[clean_name] = (status_code, data)
                return status_code, data
            elif status_code == 404:
                _PYPI_CACHE[clean_name] = (404, {})
                return 404, {}
            else:
                return status_code, {}
    except Exception:
        # Network failure / timeout
        return 0, {}


def extract_pypi_first_upload(data: Dict[str, Any]) -> Optional[datetime]:
    """Find the earliest upload timestamp across all PyPI releases."""
    releases = data.get("releases", {})
    if not releases:
        # Check urls if releases is empty
        urls = data.get("urls", [])
        if urls and isinstance(urls, list):
            iso_str = urls[0].get("upload_time_iso_8601") or urls[0].get("upload_time")
            if iso_str:
                return _parse_iso(iso_str)
        return None

    earliest: Optional[datetime] = None
    for ver, files in releases.items():
        if not files or not isinstance(files, list):
            continue
        for f in files:
            iso_str = f.get("upload_time_iso_8601") or f.get("upload_time")
            if iso_str:
                dt = _parse_iso(iso_str)
                if dt:
                    if earliest is None or dt < earliest:
                        earliest = dt
    return earliest


def has_pypi_provenance(data: Dict[str, Any]) -> bool:
    """Check if package metadata specifies a source repository or homepage."""
    info = data.get("info", {})
    proj_urls = info.get("project_urls") or {}
    if isinstance(proj_urls, dict):
        for k, v in proj_urls.items():
            if v and any(s in str(v).lower() for s in ("github.com", "gitlab.com", "bitbucket.org", "http://", "https://")):
                return True

    for field_name in ("home_page", "project_url", "package_url"):
        val = info.get(field_name)
        if val and str(val).strip() and str(val).lower() != "unknown":
            return True

    return False


def get_pypi_sdist_url(data: Dict[str, Any], version: Optional[str] = None) -> Optional[str]:
    """Find the sdist download URL for inspection."""
    releases = data.get("releases", {})
    target_files: List[Dict[str, Any]] = []

    if version and version in releases:
        target_files = releases[version]
    else:
        # Latest release files from urls or latest key
        target_files = data.get("urls", [])

    for f in target_files:
        if f.get("packagetype") == "sdist" or f.get("filename", "").endswith((".tar.gz", ".zip")):
            return f.get("url")
    return None


def _parse_iso(val: str) -> Optional[datetime]:
    try:
        # Normalise Z to +00:00 for fromisoformat
        s = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None
