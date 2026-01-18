import discord
from discord.ext import commands
from pathlib import Path

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
        await voice_connections[guild_id].disconnect()
    
    try:
        vc = await channel.connect()
        voice_connections[guild_id] = vc
        await ctx.send(f"Joined {channel.name}!")
    except Exception as e:
        await ctx.send(f"Failed to join channel: {e}")


async def leave_voice(ctx: commands.Context):
    """Leave the current voice channel."""
    guild_id = ctx.guild.id
    
    if guild_id not in voice_connections or voice_connections[guild_id] is None:
        await ctx.send("I'm not in a voice channel!")
        return
    
    await voice_connections[guild_id].disconnect()
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

    if filename:
        file_path = BASE_DIR / "Molda Voice" / filename
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
            # Use simple FFmpegPCMAudio instead of from_probe to avoid probe failures
            source = discord.FFmpegPCMAudio(
                str(file_path),
                executable=FFMPEG_EXEC,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
            )
            vc.play(source)
        except Exception as e:
            await ctx.send(f"Failed to play audio: {e}")
        await ctx.send(f"Playing {file_path.name}")
    except Exception as e:
        await ctx.send(f"Failed to play audio: {e}")
