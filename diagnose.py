#!/usr/bin/env python3
"""Diagnostic script for Discord bot voice connection issues."""

import sys
import os
import discord
from pathlib import Path

print("="*60)
print("DISCORD BOT VOICE CONNECTION DIAGNOSTIC")
print("="*60)

# Check environment
print("\n1. ENVIRONMENT SETUP:")
print(f"   Python version: {sys.version.split()[0]}")
print(f"   Working directory: {os.getcwd()}")

# Check .env file
env_file = Path('.env')
if env_file.exists():
    print(f"   ✅ .env file found")
    required_keys = ['DISCORD_TOKEN', 'VOICE_CHANNEL_ID']
    from dotenv import load_dotenv
    load_dotenv()
    for key in required_keys:
        value = os.getenv(key)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"      ✅ {key}={masked}")
        else:
            print(f"      ❌ {key} not set")
else:
    print(f"   ❌ .env file not found")

# Check dependencies
print("\n2. DEPENDENCIES:")
deps = {
    'discord': 'discord.py',
    'nacl': 'PyNaCl',
    'dotenv': 'python-dotenv',
    'aiohttp': 'aiohttp'
}

for module, name in deps.items():
    try:
        m = __import__(module)
        version = getattr(m, '__version__', 'unknown')
        print(f"   ✅ {name}: {version}")
    except ImportError:
        print(f"   ❌ {name}: Not installed")

# Check voice capabilities
print("\n3. VOICE CAPABILITIES:")
try:
    import nacl.secret
    import nacl.utils
    print("   ✅ PyNaCl crypto (required for voice encryption)")
except Exception as e:
    print(f"   ❌ PyNaCl crypto: {e}")

try:
    discord.opus.is_loaded()
    print("   ✅ Opus codec loaded")
except Exception as e:
    print(f"   ⚠️  Opus codec: {e}")
    print("      Note: Windows may need manual libopus installation")
    print("      Download from: https://opus-codec.org/downloads/")

# Check ffmpeg
print("\n4. FFMPEG (Optional, for audio playback):")
import shutil
ffmpeg_path = shutil.which('ffmpeg')
if ffmpeg_path:
    print(f"   ✅ ffmpeg found at: {ffmpeg_path}")
else:
    ffmpeg_env = os.getenv('FFMPEG_PATH')
    if ffmpeg_env:
        print(f"   ℹ️  FFMPEG_PATH set to: {ffmpeg_env}")
    else:
        print("   ⚠️  ffmpeg not found (needed for audio playback)")

# Check permissions
print("\n5. PERMISSIONS:")
files_to_check = [
    'bot.py',
    'config.py',
    'events.py',
    'voice_commands.py'
]
for fname in files_to_check:
    fpath = Path(fname)
    if fpath.exists():
        print(f"   ✅ {fname}")
    else:
        print(f"   ❌ {fname}: missing")

print("\n" + "="*60)
print("SUMMARY:")
print("If all dependencies show ✅, the issue is likely:")
print("1. Invalid DISCORD_TOKEN")
print("2. Channel ID doesn't exist or bot lacks permissions")
print("3. Network/firewall blocking Discord voice")
print("4. Discord server has voice channel restrictions")
print("="*60)
