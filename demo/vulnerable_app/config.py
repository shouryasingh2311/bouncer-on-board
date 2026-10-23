# Configuration for vulnerable demo app
# All credentials here are synthetic fake keys for scanner testing only.

import os

# FAKE-DEMO-KEY: Planted high-entropy API secret
OPENAI_API_KEY = "sk-proj-demo_fake_key_99887766554433221100aabbccddeeff"  # FAKE-DEMO-KEY

# FAKE-DEMO-KEY: Planted cloud token
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # FAKE-DEMO-KEY

# App operational settings
DEBUG = True
DATABASE_NAME = "demo_vulnerable.db"
PORT = 8000
