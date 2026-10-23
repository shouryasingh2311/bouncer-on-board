"""
Mock Registry HTTP Server for BOB Demo & Offline Integration Tests.

Serves PyPI-compatible JSON at /pypi/<name>/json and npm packuments at /npm/<name>.
Also serves generated archive bytes at /archives/pypi/<filename> and /archives/npm/<filename>.
All upload dates are computed dynamically relative to server startup ("N days ago")
so test suites and demos never become stale.
"""

from __future__ import annotations

import io
import json
import os
import tarfile
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Any


def _make_tar_gz(files: dict[str, str | bytes]) -> bytes:
    """Create in-memory .tar.gz archive containing specified files."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files.items():
            if isinstance(content, str):
                data = content.encode("utf-8")
            else:
                data = content
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = int(datetime.now(timezone.utc).timestamp())
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class MockRegistryHandler(BaseHTTPRequestHandler):
    server_version = "BOBMockRegistry/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        # Keep test runs clean unless DEBUG_MOCK_REGISTRY is set
        if os.environ.get("DEBUG_MOCK_REGISTRY"):
            super().log_message(format, *args)

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_404(self, message: str = "Not Found") -> None:
        self._send_json({"message": message}, status=404)

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        now = datetime.now(timezone.utc)

        if path == "" or path == "/healthz":
            self._send_json({"status": "ok", "server": "bob-mock-registry"})
            return

        # -------------------------------------------------------------
        # PyPI endpoints: /pypi/<name>/json
        # -------------------------------------------------------------
        if path.startswith("/pypi/"):
            parts = [p for p in path.split("/") if p]
            # Expecting ['pypi', '<name>', 'json']
            if len(parts) >= 2:
                pkg_name = parts[1]
            else:
                self._send_404()
                return

            host = f"http://{self.headers.get('Host', '127.0.0.1:8765')}"

            if pkg_name == "demo-good-lib":
                upload_time = (now - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "info": {
                        "name": "demo-good-lib",
                        "version": "1.0.0",
                        "summary": "Verified safe library for BOB demo",
                        "project_urls": {
                            "Homepage": "https://github.com/example/demo-good-lib",
                            "Source": "https://github.com/example/demo-good-lib",
                        },
                    },
                    "releases": {
                        "1.0.0": [{
                            "upload_time_iso_8601": upload_time,
                            "filename": "demo-good-lib-1.0.0.tar.gz",
                            "url": f"{host}/archives/pypi/demo-good-lib-1.0.0.tar.gz",
                            "packagetype": "sdist",
                        }]
                    },
                    "urls": [{
                        "upload_time_iso_8601": upload_time,
                        "filename": "demo-good-lib-1.0.0.tar.gz",
                        "url": f"{host}/archives/pypi/demo-good-lib-1.0.0.tar.gz",
                        "packagetype": "sdist",
                    }],
                })
                return

            if pkg_name == "demo-fresh-lib":
                upload_time = (now - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "info": {
                        "name": "demo-fresh-lib",
                        "version": "0.1.0",
                        "summary": "Brand new 3-day-old package with repository",
                        "project_urls": {
                            "Homepage": "https://github.com/example/demo-fresh-lib",
                        },
                    },
                    "releases": {
                        "0.1.0": [{
                            "upload_time_iso_8601": upload_time,
                            "filename": "demo-fresh-lib-0.1.0.tar.gz",
                            "url": f"{host}/archives/pypi/demo-fresh-lib-0.1.0.tar.gz",
                            "packagetype": "sdist",
                        }]
                    },
                    "urls": [{
                        "upload_time_iso_8601": upload_time,
                        "filename": "demo-fresh-lib-0.1.0.tar.gz",
                        "url": f"{host}/archives/pypi/demo-fresh-lib-0.1.0.tar.gz",
                        "packagetype": "sdist",
                    }],
                })
                return

            if pkg_name == "reqeusts":
                upload_time = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "info": {
                        "name": "reqeusts",
                        "version": "0.0.1",
                        "summary": "Typosquat of requests",
                        "project_urls": {},
                    },
                    "releases": {
                        "0.0.1": [{
                            "upload_time_iso_8601": upload_time,
                            "filename": "reqeusts-0.0.1.tar.gz",
                            "url": f"{host}/archives/pypi/reqeusts-0.0.1.tar.gz",
                            "packagetype": "sdist",
                        }]
                    },
                    "urls": [{
                        "upload_time_iso_8601": upload_time,
                        "filename": "reqeusts-0.0.1.tar.gz",
                        "url": f"{host}/archives/pypi/reqeusts-0.0.1.tar.gz",
                        "packagetype": "sdist",
                    }],
                })
                return

            if pkg_name == "requests-utils":
                upload_time = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "info": {
                        "name": "requests-utils",
                        "version": "0.1.0",
                        "summary": "LLM trope naming pattern without provenance",
                        "project_urls": {},
                    },
                    "releases": {
                        "0.1.0": [{
                            "upload_time_iso_8601": upload_time,
                            "filename": "requests-utils-0.1.0.tar.gz",
                            "url": f"{host}/archives/pypi/requests-utils-0.1.0.tar.gz",
                            "packagetype": "sdist",
                        }]
                    },
                    "urls": [{
                        "upload_time_iso_8601": upload_time,
                        "filename": "requests-utils-0.1.0.tar.gz",
                        "url": f"{host}/archives/pypi/requests-utils-0.1.0.tar.gz",
                        "packagetype": "sdist",
                    }],
                })
                return

            if pkg_name == "demo-evil-lib":
                upload_time = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "info": {
                        "name": "demo-evil-lib",
                        "version": "0.0.1",
                        "summary": "Inert decoy package with suspicious install script",
                        "project_urls": {},
                    },
                    "releases": {
                        "0.0.1": [{
                            "upload_time_iso_8601": upload_time,
                            "filename": "demo-evil-lib-0.0.1.tar.gz",
                            "url": f"{host}/archives/pypi/demo-evil-lib-0.0.1.tar.gz",
                            "packagetype": "sdist",
                        }]
                    },
                    "urls": [{
                        "upload_time_iso_8601": upload_time,
                        "filename": "demo-evil-lib-0.0.1.tar.gz",
                        "url": f"{host}/archives/pypi/demo-evil-lib-0.0.1.tar.gz",
                        "packagetype": "sdist",
                    }],
                })
                return

            # All other packages (including demo-missing-lib) 404
            self._send_404(f"Package '{pkg_name}' not found on mock PyPI")
            return

        # -------------------------------------------------------------
        # npm endpoints: /npm/<name>
        # -------------------------------------------------------------
        if path.startswith("/npm/"):
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                pkg_name = parts[1]
            else:
                self._send_404()
                return

            host = f"http://{self.headers.get('Host', '127.0.0.1:8765')}"

            if pkg_name == "demo-npm-good":
                created_time = (now - timedelta(days=350)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "_id": "demo-npm-good",
                    "name": "demo-npm-good",
                    "dist-tags": {"latest": "1.0.0"},
                    "time": {
                        "created": created_time,
                        "1.0.0": created_time,
                    },
                    "repository": {
                        "type": "git",
                        "url": "https://github.com/example/demo-npm-good",
                    },
                    "versions": {
                        "1.0.0": {
                            "name": "demo-npm-good",
                            "version": "1.0.0",
                            "scripts": {"test": "echo test"},
                            "dist": {
                                "tarball": f"{host}/archives/npm/demo-npm-good-1.0.0.tgz",
                            },
                        }
                    },
                })
                return

            if pkg_name == "demo-npm-evil":
                created_time = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
                self._send_json({
                    "_id": "demo-npm-evil",
                    "name": "demo-npm-evil",
                    "dist-tags": {"latest": "1.0.0"},
                    "time": {
                        "created": created_time,
                        "1.0.0": created_time,
                    },
                    "versions": {
                        "1.0.0": {
                            "name": "demo-npm-evil",
                            "version": "1.0.0",
                            "scripts": {
                                "postinstall": "node postinstall.js",
                            },
                            "dist": {
                                "tarball": f"{host}/archives/npm/demo-npm-evil-1.0.0.tgz",
                            },
                        }
                    },
                })
                return

            self._send_404(f"Package '{pkg_name}' not found on mock npm")
            return

        # -------------------------------------------------------------
        # Archive downloads: /archives/pypi/... and /archives/npm/...
        # -------------------------------------------------------------
        if path.startswith("/archives/pypi/"):
            filename = path.split("/")[-1]
            if "demo-evil-lib" in filename:
                # Serve the inert decoy setup.py
                setup_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "tests", "fixtures", "inert_pypi", "setup.py"
                )
                if os.path.exists(setup_path):
                    with open(setup_path, "r", encoding="utf-8") as f:
                        setup_code = f.read()
                else:
                    setup_code = "import base64\nexec(base64.b64decode('cHJpbnQoImluZXJ0Iik=')\n"

                tar_bytes = _make_tar_gz({
                    "demo-evil-lib-0.0.1/setup.py": setup_code,
                    "demo-evil-lib-0.0.1/PKG-INFO": "Metadata-Version: 2.1\nName: demo-evil-lib\nVersion: 0.0.1\n",
                })
                self._send_bytes(tar_bytes, "application/gzip")
                return
            else:
                # Clean standard library archive
                tar_bytes = _make_tar_gz({
                    "pkg/setup.py": "from setuptools import setup\nsetup(name='clean-pkg', version='1.0')\n",
                    "pkg/PKG-INFO": "Metadata-Version: 2.1\nName: clean-pkg\nVersion: 1.0\n",
                })
                self._send_bytes(tar_bytes, "application/gzip")
                return

        if path.startswith("/archives/npm/"):
            filename = path.split("/")[-1]
            if "demo-npm-evil" in filename:
                # Serve package with inert postinstall.js
                postinstall_path = os.path.join(
                    os.path.dirname(__file__), "..", "..", "tests", "fixtures", "inert_npm", "postinstall.js"
                )
                if os.path.exists(postinstall_path):
                    with open(postinstall_path, "r", encoding="utf-8") as f:
                        postinstall_code = f.read()
                else:
                    postinstall_code = "eval(Buffer.from('Y29uc29sZS5sb2coImluZXJ0Iik7', 'base64').toString('utf-8'));\n"

                tar_bytes = _make_tar_gz({
                    "package/package.json": json.dumps({"name": "demo-npm-evil", "scripts": {"postinstall": "node postinstall.js"}}),
                    "package/postinstall.js": postinstall_code,
                })
                self._send_bytes(tar_bytes, "application/gzip")
                return
            else:
                tar_bytes = _make_tar_gz({
                    "package/package.json": json.dumps({"name": "demo-npm-good", "version": "1.0.0"}),
                    "package/index.js": "module.exports = {};\n",
                })
                self._send_bytes(tar_bytes, "application/gzip")
                return

        self._send_404()


def run_mock_registry(host: str = "127.0.0.1", port: int = 8765) -> HTTPServer:
    server = HTTPServer((host, port), MockRegistryHandler)
    return server


def start_in_background(host: str = "127.0.0.1", port: int = 8765) -> tuple[HTTPServer, threading.Thread]:
    server = run_mock_registry(host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = run_mock_registry(port=port)
    print(f"BOB Mock Registry running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping mock registry...")
        server.server_close()
