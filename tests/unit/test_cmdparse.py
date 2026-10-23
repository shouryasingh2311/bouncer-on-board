"""Unit tests for shell command install intent parser."""

from bob.cmdparse import extract_install_intents, parse_pkg_and_version, split_pipeline


def test_split_pipeline() -> None:
    assert split_pipeline("echo 1 && pip install requests") == ["echo 1", "pip install requests"]
    assert split_pipeline("cat file; npm i express") == ["cat file", "npm i express"]
    assert split_pipeline("pip install 'foo && bar'") == ["pip install 'foo && bar'"]


def test_parse_pkg_and_version() -> None:
    assert parse_pkg_and_version("requests==2.31.0", "pypi") == ("requests", "2.31.0")
    assert parse_pkg_and_version("flask>=2.0", "pypi") == ("flask", "2.0")
    assert parse_pkg_and_version("express@4.18.2", "npm") == ("express", "4.18.2")
    assert parse_pkg_and_version("@types/node@18.0.0", "npm") == ("@types/node", "18.0.0")


def test_extract_pip_intents() -> None:
    intents = extract_install_intents("pip install requests fastapi==0.100.0")
    assert len(intents) == 2
    assert intents[0].package == "requests"
    assert intents[0].ecosystem == "pypi"
    assert intents[1].package == "fastapi"
    assert intents[1].version == "0.100.0"


def test_extract_python_m_pip() -> None:
    intents = extract_install_intents("python -m pip install reqeusts")
    assert len(intents) == 1
    assert intents[0].package == "reqeusts"
    assert intents[0].ecosystem == "pypi"

    intents_py = extract_install_intents("py -m pip install boto3")
    assert len(intents_py) == 1
    assert intents_py[0].package == "boto3"


def test_extract_uv_intents() -> None:
    intents = extract_install_intents("uv pip install rich")
    assert len(intents) == 1
    assert intents[0].package == "rich"

    intents_add = extract_install_intents("uv add httpx")
    assert len(intents_add) == 1
    assert intents_add[0].package == "httpx"


def test_extract_npm_intents() -> None:
    intents_i = extract_install_intents("npm i express lodash")
    assert len(intents_i) == 2
    assert intents_i[0].package == "express"
    assert intents_i[0].ecosystem == "npm"
    assert intents_i[1].package == "lodash"

    intents_npx = extract_install_intents("npx create-react-app my-app")
    assert len(intents_npx) == 1
    assert intents_npx[0].package == "create-react-app"
    assert intents_npx[0].ecosystem == "npm"


def test_unverifiable_intents() -> None:
    intents = extract_install_intents("pip install git+https://github.com/foo/bar.git")
    assert len(intents) == 1
    assert intents[0].is_unverifiable is True

    intents_local = extract_install_intents("pip install ./package.whl")
    assert len(intents_local) == 1
    assert intents_local[0].is_unverifiable is True
