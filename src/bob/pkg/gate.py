"""Package gate: combines registry metadata, OSV, heuristics, and static inspection."""

from __future__ import annotations

from typing import List, Optional, Tuple
import httpx

from bob.config import Config
from bob.models import Decision, Finding
from bob.pkg.heuristics import (
    calculate_age_score,
    check_naming_trope,
    check_typosquat,
)
from bob.pkg.npm import (
    extract_npm_first_upload,
    fetch_npm_metadata,
    get_npm_scripts,
    get_npm_tarball_url,
    has_npm_provenance,
)
from bob.pkg.osv import has_malicious_advisory, query_osv
from bob.pkg.pypi import (
    extract_pypi_first_upload,
    fetch_pypi_metadata,
    get_pypi_sdist_url,
    has_pypi_provenance,
)
from bob.pkg.static_inspect import (
    extract_setup_py_from_tarball,
    inspect_npm_lifecycle_scripts,
    inspect_python_setup_content,
)


def evaluate_package(
    ecosystem: str,
    package_name: str,
    version: Optional[str],
    config: Config,
) -> Decision:
    """Evaluate a package before installation, returning a Decision with score and findings."""
    eco = ecosystem.lower().strip()
    pkg = package_name.strip()
    findings: List[Finding] = []
    reasons: List[str] = []
    score = 0
    hard_block = False
    finding_idx = 1

    # 1. Fetch registry metadata
    if eco == "pypi":
        status_code, data = fetch_pypi_metadata(pkg, config)
    elif eco == "npm":
        status_code, data = fetch_npm_metadata(pkg, config)
    else:
        return Decision(
            action="warn",
            score=0,
            reasons=[f"Unsupported ecosystem '{ecosystem}'; skipping pre-install checks."],
        )

    # 1.1 Registry 404 => PKG-NOT-FOUND (Hard Block)
    if status_code == 404:
        f = Finding(
            id=f"BOB-{finding_idx:04d}",
            rule_id="PKG-NOT-FOUND",
            source="bob-pkg-gate",
            category="package",
            severity="critical",
            title="Package not found on registry (slopsquatting risk)",
            file=None,
            line=None,
            evidence=f"{eco}:{pkg}",
        )
        return Decision(
            action="block",
            score=100,
            reasons=[f"Package '{pkg}' does not exist on {eco.upper()} (likely AI hallucinated / slopsquatting vector)."],
            findings=[f],
        )

    # 1.2 Registry unreachable => follow offline_policy
    if status_code != 200:
        action = "block" if config.offline_policy.lower() == "block" else "warn"
        return Decision(
            action=action,
            score=50 if action == "block" else 20,
            reasons=[f"{eco.upper()} registry unreachable for '{pkg}' (policy: {config.offline_policy})."],
            findings=[],
        )

    # 2. Check OSV Malicious Advisories (MAL-) => PKG-MALICIOUS-ADVISORY (Hard Block)
    vulns = query_osv(pkg, eco, version)
    mal_id = has_malicious_advisory(vulns)
    if mal_id:
        hard_block = True
        finding_idx += 1
        findings.append(
            Finding(
                id=f"BOB-{finding_idx:04d}",
                rule_id="PKG-MALICIOUS-ADVISORY",
                source="bob-pkg-gate",
                category="package",
                severity="critical",
                title="Known malicious package advisory",
                file=None,
                line=None,
                evidence=f"{mal_id} targeting {pkg}",
            )
        )
        reasons.append(f"Package '{pkg}' flagged by OSV malicious advisory {mal_id}.")

    # 3. Check Typosquatting
    typo_match = check_typosquat(pkg, eco)
    if typo_match:
        top_name, dist = typo_match
        score += 40
        finding_idx += 1
        findings.append(
            Finding(
                id=f"BOB-{finding_idx:04d}",
                rule_id="PKG-TYPOSQUAT",
                source="bob-pkg-gate",
                category="package",
                severity="high",
                title="Possible typosquatting of popular package",
                file=None,
                line=None,
                evidence=f"'{pkg}' is distance {dist} from popular package '{top_name}'",
            )
        )
        reasons.append(f"Name '{pkg}' resembles popular package '{top_name}' (distance: {dist}).")

    # 4. Check Age
    if eco == "pypi":
        first_upload = extract_pypi_first_upload(data)
    else:
        first_upload = extract_npm_first_upload(data)

    age_score, days_old = calculate_age_score(first_upload, config.min_package_age_days)
    if age_score > 0 and days_old is not None:
        score += age_score
        finding_idx += 1
        sev = "high" if age_score >= 50 else "medium"
        findings.append(
            Finding(
                id=f"BOB-{finding_idx:04d}",
                rule_id="PKG-TOO-NEW",
                source="bob-pkg-gate",
                category="package",
                severity=sev,
                title="Package is brand new",
                file=None,
                line=None,
                evidence=f"First uploaded {days_old} day(s) ago (threshold: {config.min_package_age_days}d)",
            )
        )
        reasons.append(f"Package '{pkg}' was first uploaded only {days_old} day(s) ago.")

    # 5. Check LLM Naming Tropes
    trope_match = check_naming_trope(pkg, eco)
    if trope_match:
        base_pkg, trope_affix = trope_match
        score += 20
        finding_idx += 1
        findings.append(
            Finding(
                id=f"BOB-{finding_idx:04d}",
                rule_id="PKG-LLM-TROPE",
                source="bob-pkg-gate",
                category="package",
                severity="medium",
                title="Common LLM hallucination naming trope",
                file=None,
                line=None,
                evidence=f"Base '{base_pkg}' with affix '{trope_affix}'",
            )
        )
        reasons.append(f"Package '{pkg}' matches LLM-naming trope based on '{base_pkg}'.")

    # 6. Check Provenance (Repository or Homepage Link)
    has_prov = has_pypi_provenance(data) if eco == "pypi" else has_npm_provenance(data)
    if not has_prov:
        score += 15
        finding_idx += 1
        findings.append(
            Finding(
                id=f"BOB-{finding_idx:04d}",
                rule_id="PKG-NO-PROVENANCE",
                source="bob-pkg-gate",
                category="package",
                severity="low",
                title="Missing source repository or homepage link",
                file=None,
                line=None,
                evidence="No project URLs pointing to VCS repository or verified homepage",
            )
        )
        reasons.append(f"Package '{pkg}' metadata does not provide a repository or homepage link.")

    # 7. Static Inspection of Install Scripts (setup.py or npm lifecycle scripts)
    script_findings: List[str] = []
    if eco == "pypi":
        sdist_url = get_pypi_sdist_url(data, version)
        if sdist_url:
            try:
                with httpx.Client(timeout=4.0) as client:
                    resp = client.get(sdist_url)
                    if resp.status_code == 200:
                        setup_code = extract_setup_py_from_tarball(resp.content)
                        if setup_code:
                            script_findings.extend(inspect_python_setup_content(setup_code))
            except Exception:
                pass
    elif eco == "npm":
        # Inspect lifecycle scripts directly from packument
        scripts = get_npm_scripts(data, version)
        if scripts:
            script_findings.extend(inspect_npm_lifecycle_scripts(scripts))

    if script_findings:
        # Red flags add +60, capped at +100
        script_score = min(100, 60 * len(script_findings))
        score += script_score
        finding_idx += 1
        findings.append(
            Finding(
                id=f"BOB-{finding_idx:04d}",
                rule_id="PKG-INSTALL-SCRIPT",
                source="bob-pkg-gate",
                category="package",
                severity="critical",
                title="Suspicious install-script behavior detected statically",
                file=None,
                line=None,
                evidence="; ".join(script_findings[:3]),
            )
        )
        for sf in script_findings:
            reasons.append(f"Install script inspection flag: {sf}")

    # 8. Decision determination
    if hard_block or score >= 70:
        action = "block"
    elif score >= 30:
        action = "warn"
    else:
        action = "allow"

    return Decision(
        action=action,
        score=score,
        reasons=reasons,
        findings=findings,
    )
