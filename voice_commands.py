import discord
from discord.ext import commands
from pathlib import Path
import asyncio

from ffmpeg_helper import get_ffmpeg_exec


voice_connections: dict[int, discord.VoiceClient] = {}

# Default audio directory and file
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_JOIN_AUDIO = BASE_DIR / "Molda Voice" / "New_comers_molda.mp3"

# Resolve ffmpeg executable once at import
FFMPEG_EXEC = get_ffmpeg_exec()
if not FFMPEG_EXEC:
    print("[FFMPEG] ffmpeg executable not found. Set FFMPEG_PATH env var or ensure ffmpeg is available.")


async def join_voice(ctx: commands.Context, bot: commands.Bot, channel_id: int):
    """Join a voice channel by ID. Usage: !join-channel <channel_id>"""
    channel = bot.get_channel(channel_id)
    
    if channel is None:
        await ctx.send(f"Channel with ID {channel_id} not found!")
        return
    
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send(f"Channel {channel_id} is not a voice channel!")
        return
    
    guild_id = ctx.guild.id
    
    # Disconnect from existing connection if any
    if guild_id in voice_connections:
        try:
            await voice_connections[guild_id].disconnect(force=True)
        except Exception as e:
            print(f"[VOICE] Error disconnecting: {e}")
    
    try:
        # Try to connect with timeout and reconnect enabled
        vc = await asyncio.wait_for(channel.connect(reconnect=True), timeout=10)
        voice_connections[guild_id] = vc
        await ctx.send(f"Joined {channel.name}!")
    except asyncio.TimeoutError:
        await ctx.send(f"Connection timeout. Check your network and try again.")
    except discord.errors.ConnectionClosed as e:
        await ctx.send(f"Connection closed with code {e.code}. Try again later.")
    except Exception as e:
        await ctx.send(f"Failed to join channel: {e}")


async def leave_voice(ctx: commands.Context):
    """Leave the current voice channel."""
    guild_id = ctx.guild.id
    
    if guild_id not in voice_connections or voice_connections[guild_id] is None:
        await ctx.send("I'm not in a voice channel!")
        return
    
    try:
        await voice_connections[guild_id].disconnect(force=True)
    except Exception as e:
        print(f"[VOICE] Error disconnecting: {e}")
    finally:
        voice_connections.pop(guild_id, None)
    await ctx.send("Left the voice channel!")


async def play_join(ctx: commands.Context, filename: str | None = None):
    """Play a join audio file in the guild's connected voice channel.
    `filename` is optional and should be the name of a file inside `Molda Voice`.
    """
    guild_id = ctx.guild.id

    if guild_id not in voice_connections or voice_connections[guild_id] is None:
        await ctx.send("I'm not in a voice channel!")
        return

    vc = voice_connections[guild_id]
    
    # Check if voice client is still connected
    if not vc or not getattr(vc, "channel", None):
        await ctx.send("Voice connection lost!")
        voice_connections.pop(guild_id, None)
        return

    if filename:
        file_path = BASE_DIR / "Molda Voice" / filename
        # For explicit filenames, don't convert - use as-is
    else:
        file_path = DEFAULT_JOIN_AUDIO

    if not file_path.exists():
        await ctx.send(f"Audio file not found: {file_path.name}")
        return

    try:
        if vc.is_playing():
            vc.stop()
        if FFMPEG_EXEC is None:
            await ctx.send("ffmpeg not available on the server. Set FFMPEG_PATH or install ffmpeg.")
            return
        try:
            source = await discord.FFmpegOpusAudio.from_probe(str(file_path), executable=FFMPEG_EXEC)
            vc.play(source)
            await ctx.send(f"Playing {file_path.name}")
        except Exception as e:
            await ctx.send(f"Failed to play audio: {e}")
    except Exception as e:
        await ctx.send(f"Failed to play audio: {e}")
