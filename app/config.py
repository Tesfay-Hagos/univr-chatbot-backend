"""
UniVR Chatbot - Configuration Module
"""

import os
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
