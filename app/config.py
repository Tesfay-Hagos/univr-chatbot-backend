"""
UniVR Chatbot - Configuration Module
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

# Store naming prefix - stores will be named: {STORE_PREFIX}-{domain}
STORE_PREFIX = os.getenv("STORE_PREFIX", "univr")

# Application Settings
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Validation - warn if API key is missing
if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not set!")
    print("   → Copy .env.example to .env and add your API key")
    print("   → Domains/documents will NOT be available")
    print()
