# Project: discord_unmute_bot
# File: bot.py

import discord
from discord.ext import commands

from config import TOKEN, MONITORED_ROLE_ID
from voice_commands import join_voice, leave_voice, play_join
import events
from events import molda_rejoin_targets, molda_rejoin_tasks
from greetings import register_greeting_commands
from audio_encoder import encode_all_mp3s
from ffmpeg_helper import get_ffmpeg_exec

intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Register dynamic greeting commands (from `Molda Voice` files)
register_greeting_commands(bot)


@bot.command(name="join-channel")
@commands.has_permissions(administrator=True)
async def join_channel_cmd(ctx: commands.Context, channel_id: int):
    """Join a voice channel by ID. Usage: !join-channel <channel_id>"""
    await join_voice(ctx, bot, channel_id)


@bot.command(name="leave-channel")
@commands.has_permissions(administrator=True)
async def leave_channel_cmd(ctx: commands.Context):
    """Leave the current voice channel."""
    await leave_voice(ctx)


@bot.command(name="join-channel-molda")
@commands.has_permissions(administrator=True)
async def join_channel_molda_cmd(ctx: commands.Context, channel_id: int):
    """Join the molda voice channel with auto-rejoin enabled. Usage: !join-channel-molda <channel_id>"""
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
    
    try:
        success = await events._attempt_molda_connect(bot, channel_id, retry_count=3)
        if success:
            await ctx.send(f"✅ Successfully joined {channel.name} with auto-rejoin enabled!")
        else:
            await ctx.send(f"❌ Failed to join {channel.name} after retries. Channel may be unavailable or have connection issues.")
    except Exception as e:
        await ctx.send(f"❌ Error: {type(e).__name__}: {e}")


@bot.command(name="leave-channel-molda")
@commands.has_permissions(administrator=True)
async def leave_channel_molda_cmd(ctx: commands.Context):
    """Leave the molda voice channel and disable auto-rejoin."""
    from voice_commands import voice_connections
    
    guild_id = ctx.guild.id
    
    # Cancel auto-rejoin task if running
    if guild_id in molda_rejoin_tasks:
        task = molda_rejoin_tasks[guild_id]
        if not task.done():
            task.cancel()
        del molda_rejoin_tasks[guild_id]
    
    # Disable auto-rejoin
    molda_rejoin_targets.pop(guild_id, None)
    
    # Disconnect from voice
    if guild_id not in voice_connections or voice_connections[guild_id] is None:
        await ctx.send("I'm not in a voice channel!")
        return
    
    try:
        await voice_connections[guild_id].disconnect()
        voice_connections.pop(guild_id, None)
        await ctx.send("Left the voice channel and disabled auto-rejoin!")
    except Exception as e:
        await ctx.send(f"Failed to leave channel: {e}")


@bot.command(name="play-join")
@commands.has_permissions(administrator=True)
async def play_join_cmd(ctx: commands.Context, filename: str = None):
    """Play the configured join audio (admin only). Optionally specify filename in `Molda Voice/`.""" 
    await play_join(ctx, filename)


@bot.command(name="encode-audio")
@commands.has_permissions(administrator=True)
async def encode_audio_cmd(ctx: commands.Context):
    """Pre-encode all MP3 files to Opus format for lower memory usage (admin only)."""
    await ctx.send("Starting audio encoding... (this may take a while)")
    ffmpeg_exec = get_ffmpeg_exec()
    await encode_all_mp3s(ffmpeg_exec=ffmpeg_exec)
    await ctx.send("Audio encoding complete!")


@bot.event
async def on_ready():
    # Pre-encode MP3s to Opus on startup for lower memory usage
    print("[BOT] Pre-encoding audio files to Opus...")
    ffmpeg_exec = get_ffmpeg_exec()
    await encode_all_mp3s(ffmpeg_exec=ffmpeg_exec)
    await events.on_ready(bot)


@bot.event
async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
):
    await events.on_voice_state_update(member, before, after)


def main():
    if not TOKEN or MONITORED_ROLE_ID == 0:
        raise RuntimeError("Set DISCORD_TOKEN and MONITORED_ROLE_ID in .env")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()