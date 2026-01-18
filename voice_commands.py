import asyncio
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
    """Join a voice channel by ID with retry logic. Usage: !join-channel <channel_id>"""
    channel = bot.get_channel(channel_id)
    
    if channel is None:
        await ctx.send(f"Channel with ID {channel_id} not found!")
        return
    
    if not isinstance(channel, discord.VoiceChannel):
        await ctx.send(f"Channel {channel_id} is not a voice channel!")
        return
    
    # Check bot permissions
    perms = channel.permissions_for(channel.guild.me)
    if not perms.connect:
        await ctx.send(f"Bot lacks CONNECT permission for {channel.name}!")
        return
    
    guild_id = ctx.guild.id
    
    # Disconnect from existing connection if any
    if guild_id in voice_connections:
        try:
            await voice_connections[guild_id].disconnect()
        except Exception as e:
            print(f"[VOICE] Error disconnecting: {e}")
    
    # Retry with exponential backoff
    retry_count = 3
    for attempt in range(retry_count):
        try:
            print(f"[VOICE] Join attempt {attempt + 1}/{retry_count}...")
            await asyncio.sleep(0.5 + (attempt * 1.0))  # Exponential backoff
            
            vc = await asyncio.wait_for(channel.connect(), timeout=15.0)
            voice_connections[guild_id] = vc
            await ctx.send(f"✅ Joined {channel.name}!")
            return
            
        except asyncio.TimeoutError:
            if attempt == retry_count - 1:
                await ctx.send(f"❌ Connection timed out after {retry_count} attempts. Server may be overloaded or unreachable.")
        except IndexError:
            # This is a Discord API issue - the channel doesn't provide encryption modes
            if attempt == retry_count - 1:
                await ctx.send(f"❌ **Channel Configuration Issue**: Discord is not providing encryption modes for this channel. This is a server-side Discord problem, not a bot issue.\n\n**Solutions:**\n1. Try a different voice channel\n2. Check if this channel has special Discord settings\n3. Contact your server administrator about the channel configuration")
                print(f"[VOICE] Channel {channel_id} has Discord encryption mode issue - cannot connect")
        except discord.Forbidden:
            await ctx.send(f"❌ Bot lacks permissions to join {channel.name}!")
            return
        except discord.HTTPException as e:
            if attempt == retry_count - 1:
                await ctx.send(f"❌ Connection error: {e}")
        except Exception as e:
            if attempt == retry_count - 1:
                await ctx.send(f"❌ Failed to join channel: {type(e).__name__}: {e}")


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
        # Try .opus version first if filename is .mp3
        if file_path.suffix.lower() == '.mp3':
            opus_path = file_path.with_suffix('.opus')
            if opus_path.exists():
                file_path = opus_path
    else:
        file_path = DEFAULT_JOIN_AUDIO
        # Try .opus version first
        opus_default = DEFAULT_JOIN_AUDIO.with_suffix('.opus')
        if opus_default.exists():
            file_path = opus_default

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
