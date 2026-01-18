import os
from pathlib import Path
import re
from typing import Dict, Optional

from voice_commands import play_join

AUDIO_DIR = Path(__file__).resolve().parent / "Molda Voice"
_pattern = re.compile(r"(?P<name>[^_/\\]+)_Molda\.(mp3|opus)$", re.IGNORECASE)

# name (lowercase) -> filename (basename)
name_to_filename: Dict[str, str] = {}
# member_id -> filename
id_to_filename: Dict[int, str] = {}

# Scan audio files
for p in sorted(AUDIO_DIR.glob("*")):
    m = _pattern.match(p.name)
    if not m:
        continue
    name = m.group("name")
    name_key = name.lower()
    name_to_filename[name_key] = p.name

# Resolve tokens from env vars. Token name can be uppercase or capitalized.
for name_key, filename in list(name_to_filename.items()):
    candidates = [name_key.upper(), name_key.capitalize()]
    found = False
    for token in candidates:
        val = os.getenv(token)
        if val:
            try:
                member_id = int(val)
                id_to_filename[member_id] = filename
                found = True
                break
            except ValueError:
                # skip invalid env values
                pass
    if not found:
        # no token set for this name; skip mapping but command will still be registered
        pass


def get_greeting_for_member(member_id: int) -> Optional[str]:
    """Return basename filename for member_id if mapped via env token."""
    return id_to_filename.get(member_id)


def register_greeting_commands(bot):
    """Dynamically add admin-only commands for available greetings.

    Command names: `play-audio-greeting-<name>` where `<name>` is the lowercase name from file.
    """
    from discord.ext import commands

    for name_key, filename in name_to_filename.items():
        cmd_name = f"play-audio-greeting-{name_key}"

        async def _cmd(ctx, _filename=filename):
            # Admin check
            if not ctx.author.guild_permissions.administrator:
                await ctx.send("This command is for administrators only.")
                return
            await play_join(ctx, _filename)

        # Add the command to the bot
        bot.add_command(commands.Command(_cmd, name=cmd_name))