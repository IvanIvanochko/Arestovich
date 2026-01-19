#!/usr/bin/env python3
"""Clean up incorrectly encoded Opus files."""

from pathlib import Path

audio_dir = Path(__file__).resolve().parent / "Molda Voice"
opus_files = list(audio_dir.glob("*.opus"))

if not opus_files:
    print("No .opus files found to clean up")
else:
    print(f"Found {len(opus_files)} .opus files:")
    for f in opus_files:
        print(f"  - {f.name}")
    
    confirm = input("\nDelete all .opus files? (yes/no): ").strip().lower()
    if confirm == "yes":
        for f in opus_files:
            f.unlink()
            print(f"✅ Deleted {f.name}")
        print("\nRun `!encode-audio` command to re-encode with proper settings")
    else:
        print("Cancelled")
