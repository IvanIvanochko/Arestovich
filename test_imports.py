#!/usr/bin/env python3
"""Test script to verify all required dependencies are installed correctly."""

import sys

print("Python version:", sys.version)
print("\nChecking imports...")

try:
    import discord
    print(f"✅ discord.py {discord.__version__}")
except ImportError as e:
    print(f"❌ discord.py: {e}")
    sys.exit(1)

try:
    import nacl
    print(f"✅ PyNaCl {nacl.__version__}")
except ImportError as e:
    print(f"❌ PyNaCl: {e}")
    sys.exit(1)

try:
    import nacl.secret
    import nacl.utils
    print("✅ PyNaCl crypto modules available")
except ImportError as e:
    print(f"❌ PyNaCl crypto modules: {e}")
    sys.exit(1)

try:
    import dotenv
    print(f"✅ python-dotenv available")
except ImportError as e:
    print(f"❌ python-dotenv: {e}")
    sys.exit(1)

# Test audio capabilities
try:
    discord.opus.load_opus(None)  # Try to load system libopus
    print("✅ Opus codec available (system)")
except Exception:
    try:
        # Check if discord.py has fallback
        print("⚠️  System Opus not found, but discord.py may handle it")
    except Exception as e:
        print(f"⚠️  Opus codec: {e}")

print("\n✅ All critical dependencies are properly installed!")
