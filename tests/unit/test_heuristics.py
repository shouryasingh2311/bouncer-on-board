"""Unit tests for heuristics: Levenshtein distance, typosquatting, age, and tropes."""

from datetime import datetime, timedelta, timezone

from bob.pkg.heuristics import (
    calculate_age_score,
    check_naming_trope,
    check_typosquat,
    levenshtein_distance,
)


def test_levenshtein_distance() -> None:
    assert levenshtein_distance("", "") == 0
    assert levenshtein_distance("requests", "requests") == 0
    assert levenshtein_distance("requests", "reqeusts") == 2
    assert levenshtein_distance("express", "expres") == 1
    assert levenshtein_distance("flask", "django") > 4


def test_check_typosquat_pypi() -> None:
    # reqeusts -> distance 2 to requests
    res = check_typosquat("reqeusts", "pypi")
    assert res is not None
    top_matched, dist = res
    assert top_matched == "requests"
    assert dist == 2

    # Exact match is not a typosquat
    assert check_typosquat("requests", "pypi") is None

    # Unrelated name
    assert check_typosquat("completelyunrelatedpackage12345", "pypi") is None


def test_check_typosquat_npm() -> None:
    # expres -> distance 1 to express
    res = check_typosquat("expres", "npm")
    assert res is not None
    top_matched, dist = res
    assert top_matched == "express"
    assert dist == 1


def test_calculate_age_score() -> None:
    now = datetime.now(timezone.utc)

    # 3 days old: < 7d -> +50
    score, days = calculate_age_score(now - timedelta(days=3), min_age_days=14)
    assert score == 50
    assert days == 3

    # 10 days old: < 14d -> +35
    score, days = calculate_age_score(now - timedelta(days=10), min_age_days=14)
    assert score == 35
    assert days == 10

    # 20 days old: < 30d -> +15
    score, days = calculate_age_score(now - timedelta(days=20), min_age_days=14)
    assert score == 15
    assert days == 20

    # 400 days old: mature package -> 0
    score, days = calculate_age_score(now - timedelta(days=400), min_age_days=14)
    assert score == 0
    assert days == 400


def test_check_naming_trope() -> None:
    # requests-utils -> base 'requests' with '-utils'
    res = check_naming_trope("requests-utils", "pypi")
    assert res is not None
    base, sfx = res
    assert base == "requests"
    assert sfx == "-utils"

    # express-api -> base 'express' with '-api'
    res_npm = check_naming_trope("express-api", "npm")
    assert res_npm is not None
    base_npm, sfx_npm = res_npm
    assert base_npm == "express"

    # normal package
    assert check_naming_trope("my-unique-package", "pypi") is None
