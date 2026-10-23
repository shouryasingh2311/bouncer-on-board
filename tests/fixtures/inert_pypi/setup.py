# DECOY: static analysis only, never execute or install
# This file is an inert test fixture designed to trigger static AST detection rules.
# It contains NO functioning credential theft, network calls, or harmful payloads.

import base64

# Inert decoy payload that only prints a safe string
_INERT_PAYLOAD = "print('BOB inert test decoy executed safely')"
_ENCODED = base64.b64encode(_INERT_PAYLOAD.encode("utf-8")).decode("utf-8")

# AST rule trigger: base64 decode feeding exec
exec(base64.b64decode(_ENCODED).decode("utf-8"))

# Decoy text reference to localhost canary
CANARY_HOST = "127.0.0.1"

# Decoy mass environ access pattern
env_data = dict(__import__("os").environ)
