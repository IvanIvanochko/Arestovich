import os
import stat
import tarfile
import tempfile
import urllib.request
from pathlib import Path
import shutil


def get_ffmpeg_exec() -> str | None:
    """Return path to ffmpeg executable.

    Order:
    - `FFMPEG_PATH` env var if set and valid
    - system `ffmpeg` (shutil.which)
    - try to download a static build and extract `ffmpeg` into `.ffmpeg/`
    Returns None if not found.
    """
    env_path = os.getenv("FFMPEG_PATH")
    if env_path and Path(env_path).is_file():
        return env_path

    which_path = shutil.which("ffmpeg")
    if which_path:
        return which_path

    dest_dir = Path(__file__).resolve().parent / ".ffmpeg"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / "ffmpeg"
    if dest.exists():
        return str(dest)

    # Attempt to download a static ffmpeg build (amd64 Linux)
    url = "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    try:
        with tempfile.TemporaryDirectory() as td:
            archive_path = Path(td) / "ffmpeg.tar.xz"
            print(f"[FFMPEG] Downloading ffmpeg from {url} ...")
            urllib.request.urlretrieve(url, archive_path)
            with tarfile.open(archive_path, mode="r:xz") as tf:
                for member in tf.getmembers():
                    if member.isfile() and member.name.endswith("/ffmpeg"):
                        # extract only the ffmpeg binary
                        member.name = Path(member.name).name
                        tf.extract(member, path=td)
                        extracted = Path(td) / member.name
                        shutil.move(str(extracted), str(dest))
                        dest.chmod(dest.stat().st_mode | stat.S_IEXEC)
                        print(f"[FFMPEG] ffmpeg extracted to {dest}")
                        return str(dest)
    except Exception as e:
        print("[FFMPEG] Failed to download/extract ffmpeg:", e)

    return None
