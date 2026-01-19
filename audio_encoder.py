import subprocess
import asyncio
from pathlib import Path
from typing import Optional

AUDIO_DIR = Path(__file__).resolve().parent / "Molda Voice" / "greetings"


async def encode_mp3_to_opus(
    mp3_file: Path, opus_file: Optional[Path] = None, ffmpeg_exec: Optional[str] = None
) -> Optional[Path]:
    """Convert an MP3 file to Opus format (more memory-efficient).
    
    Returns the path to the .opus file if successful, else None.
    """
    if not mp3_file.exists():
        print(f"[OPUS] Source file not found: {mp3_file}")
        return None

    if opus_file is None:
        opus_file = mp3_file.with_suffix(".opus")

    if opus_file.exists():
        print(f"[OPUS] Opus file already exists: {opus_file.name}")
        return opus_file

    cmd = [
        ffmpeg_exec or "ffmpeg",
        "-i", str(mp3_file),
        "-c:a", "libopus",
        "-vn",  # No video
        "-ar", "48000",  # Discord requires 48kHz
        "-ac", "2",  # Stereo
        "-b:a", "128k",  # Proper bitrate
        "-application", "voip",  # Optimize for voice
        "-y",
        str(opus_file)
    ]

    try:
        print(f"[OPUS] Encoding {mp3_file.name} to Opus...")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        
        if proc.returncode != 0:
            print(f"[OPUS] Encoding failed ({mp3_file.name}): {stderr.decode()}")
            return None

        print(f"[OPUS] Encoded: {opus_file.name}")
        return opus_file

    except asyncio.TimeoutError:
        print(f"[OPUS] Encoding timeout for {mp3_file.name}")
        return None
    except Exception as e:
        print(f"[OPUS] Encoding error ({mp3_file.name}): {e}")
        return None


async def encode_all_mp3s(ffmpeg_exec: Optional[str] = None) -> None:
    """Pre-encode all MP3 files in Molda Voice to Opus format."""
    if not AUDIO_DIR.exists():
        print("[OPUS] Molda Voice directory not found")
        return

    mp3_files = list(AUDIO_DIR.glob("*.mp3"))
    if not mp3_files:
        # Silently skip if no MP3 files (they may already be encoded)
        return

    print(f"[OPUS] Found {len(mp3_files)} MP3 files. Starting encoding...")
    for mp3_file in mp3_files:
        try:
            await encode_mp3_to_opus(mp3_file, ffmpeg_exec=ffmpeg_exec)
        except Exception as e:
            print(f"[OPUS] Skipped encoding for {mp3_file.name}: {e}")
            # Continue encoding other files even if one fails
            continue

    print("[OPUS] Encoding complete (failures may be acceptable; playback will fall back to MP3)")
