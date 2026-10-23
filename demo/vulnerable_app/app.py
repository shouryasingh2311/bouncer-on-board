"""
Intentionally vulnerable demonstration web application for BOB scan.
Contains planted security anti-patterns (eval, string SQL, open CORS, disabled TLS, debug mode).
Requires ZERO third-party packages (uses stdlib http.server and sqlite3).
"""

from __future__ import annotations

import json
import sqlite3
import ssl
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from config import DEBUG, PORT


def init_db() -> None:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, role TEXT);")
    cursor.execute("INSERT INTO users VALUES (1, 'alice', 'admin');")
    cursor.execute("INSERT INTO users VALUES (2, 'bob', 'user');")
    conn.commit()
    conn.close()


class VulnerableAppHandler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        # Tripwire: Overly permissive CORS header
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_GET(self) -> None:
        path = self.path

        # Tripwire: String-built SQL injection
        if path.startswith("/user"):
            user_id = path.split("?id=")[-1] if "?id=" in path else "1"
            conn = sqlite3.connect(":memory:")
            cursor = conn.cursor()
            query = f"SELECT id, username, role FROM users WHERE id = '{user_id}'"
            try:
                cursor.execute(query)
                user = cursor.fetchone()
                body = json.dumps({"user": user, "debug": DEBUG}).encode("utf-8")
            except Exception as e:
                body = json.dumps({"error": str(e)}).encode("utf-8")
            finally:
                conn.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return

        # Tripwire: Disabled TLS certificate verification
        if path.startswith("/sync-external"):
            unverified_ctx = ssl._create_unverified_context()
            try:
                req = urllib.request.Request("https://example.com/api/data")
                with urllib.request.urlopen(req, context=unverified_ctx, timeout=2) as resp:
                    data = resp.read()
            except Exception:
                data = b'{"status": "external_skipped"}'

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Vulnerable App Demo Running")

    def do_POST(self) -> None:
        # Tripwire: eval on untrusted request input
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8", errors="replace")

        try:
            payload = json.loads(raw_body)
            expression = payload.get("expr", "1 + 1")
            # Insecure eval of user-supplied expression
            eval_result = eval(expression)
            response = {"result": eval_result}
        except Exception as err:
            response = {"error": str(err)}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))


if __name__ == "__main__":
    init_db()
    server = HTTPServer(("127.0.0.1", PORT), VulnerableAppHandler)
    print(f"Vulnerable demo app listening on http://127.0.0.1:{PORT} (debug={DEBUG})")
    server.serve_forever()
